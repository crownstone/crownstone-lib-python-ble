import asyncio
import logging

from crownstone_core.Exceptions import CrownstoneException, CrownstoneBleException, CrownstoneError
from crownstone_core.packets.microapp.MicroappHeaderPacket import MicroappHeaderPacket
from crownstone_core.packets.microapp.MicroappInfoPacket import MicroappInfoPacket
from crownstone_core.packets.microapp.MicroappUploadPacket import MicroappUploadPacket
from crownstone_core.packets.ResultPacket import ResultPacket
from crownstone_core.packets.SessionDataPacket import SessionDataPacket
from crownstone_core.protocol.BlePackets import ControlPacket
from crownstone_core.protocol.BluenetTypes import ProcessType, ControlType, ResultValue
from crownstone_core.protocol.Characteristics import CrownstoneCharacteristics, SetupCharacteristics
from crownstone_core.protocol.ControlPackets import ControlPacketsGenerator
from crownstone_core.protocol.Services import CSServices
from crownstone_core.util.EncryptionHandler import EncryptionHandler, CHECKSUM

from crownstone_ble.Exceptions import BleError

_LOGGER = logging.getLogger(__name__)

class ControlHandler:
    def __init__(self, bluetoothCore):
        self.core = bluetoothCore

    async def getAndSetSessionNone(self):
        # read the nonce
        if self.core.ble.hasCharacteristic(CrownstoneCharacteristics.SessionData):
            rawNonce = await self.core.ble.readCharacteristicWithoutEncryption(CSServices.CrownstoneService, CrownstoneCharacteristics.SessionData)
            ProcessSessionNoncePacket(rawNonce, self.core.settings.basicKey, self.core.settings)
        elif self.core.ble.hasCharacteristic(SetupCharacteristics.SessionData):
            sessionKey = await self.core.ble.readCharacteristicWithoutEncryption(CSServices.SetupService, SetupCharacteristics.SessionKey)
            sessionNoncePacket = await self.core.ble.readCharacteristicWithoutEncryption(CSServices.SetupService, SetupCharacteristics.SessionData)

            self.core.settings.loadSetupKey(sessionKey) # This also sets user level to "setup", make sure you "exitSetup()" on disconnect!
            ProcessSessionNoncePacket(sessionNoncePacket, sessionKey, self.core.settings)

    async def setSwitch(self, switchVal: int):
        """
        :param switchVal: 0% .. 100% or special value (SwitchValSpecial).
        """
        await self._writeControlPacket(ControlPacketsGenerator.getSwitchCommandPacket(switchVal))

    async def setRelay(self, turnOn: bool):
        """
        :param turnOn: True to turn relay on.
        """
        await self._writeControlPacket(ControlPacketsGenerator.getRelaySwitchPacket(turnOn))

    async def setDimmer(self, intensity: int):
        """
         :param intensity: percentage [0..100]
        """
        await self._writeControlPacket(ControlPacketsGenerator.getDimmerSwitchPacket(intensity))

    async def putInDfuMode(self):
        """
        Puts the crownstone in DFU mode.
        """
        await self._writeControlPacket(ControlPacketsGenerator.getPutInDFUPacket())

    async def commandFactoryReset(self):
        """
          If you have the keys, you can use this to put the crownstone back into factory default mode
        """
        await self._writeControlPacket(ControlPacketsGenerator.getCommandFactoryResetPacket())

    async def allowDimming(self, allow: bool):
        """
        :param allow: True to allow dimming
        """
        await self._writeControlPacket(ControlPacketsGenerator.getAllowDimmingPacket(allow))

    async def resetErrors(self, bitmask: int = 0xFFFFFFFF):
        """
        Resets errors.
        @param bitmask: A 32b bitmask of the errors to reset.
        """
        await self._writeControlPacket(ControlPacketsGenerator.getResetErrorPacket(bitmask))

    async def disconnect(self):
        """
        Force the Crownstone to disconnect from you.
        """
        try:
            #print("Send disconnect command")
            await self._writeControlPacket(ControlPacketsGenerator.getDisconnectPacket())
        except Exception as err:
            # TODO: catch this error if it is something like already disconnected
            #print("Unknown error")
            raise err

        try:
            # Disconnect from this side as well.
            #print("Disconnect from this side as well")
            self.core.ble.disconnect()
        except Exception as err:
            #print("Unknown error")
            raise err


    async def lockSwitch(self, lock):
        """
        :param lock: bool
        """
        await self._writeControlPacket(ControlPacketsGenerator.getLockSwitchPacket(lock))


    async def reset(self):
        await self._writeControlPacket(ControlPacketsGenerator.getResetPacket())



    async def recovery(self, address):
        await self.core.connect(address, ignoreEncryption=True)
        await self._recoveryByFactoryReset()
        await self._checkRecoveryProcess()
        await self.core.disconnect()
        await asyncio.sleep(5)
        await self.core.connect(address, ignoreEncryption=True)
        await self._recoveryByFactoryReset()
        await self._checkRecoveryProcess()
        await self.core.disconnect()
        await asyncio.sleep(2)

    async def _recoveryByFactoryReset(self):
        packet = ControlPacketsGenerator.getFactoryResetPacket()
        return self.core.ble.writeToCharacteristicWithoutEncryption(
            CSServices.CrownstoneService,
            CrownstoneCharacteristics.FactoryReset,
            packet
        )

    async def _checkRecoveryProcess(self):
        result = self.core.ble.readCharacteristicWithoutEncryption(CSServices.CrownstoneService, CrownstoneCharacteristics.FactoryReset)
        if result[0] == 1:
            return True
        elif result[0] == 2:
            raise CrownstoneException(BleError.RECOVERY_MODE_DISABLED, "The recovery mechanism has been disabled by the Crownstone owner.")
        else:
            raise CrownstoneException(BleError.NOT_IN_RECOVERY_MODE, "The recovery mechanism has expired. It is only available briefly after the Crownstone is powered on.")



    async def getMicroappInfo(self) -> MicroappInfoPacket:
        controlPacket = ControlPacket(ControlType.MICROAPP_GET_INFO).getPacket()
        result = await self.core.ble.setupSingleNotification(
            CSServices.CrownstoneService,
            CrownstoneCharacteristics.Result,
            lambda: self._writeControlPacket(controlPacket)
        )
        _LOGGER.info(f"getMicroappInfo {result}")
        resultPacket = ResultPacket(result)
        _LOGGER.info(f"getMicroappInfo {resultPacket}")
        infoPacket = MicroappInfoPacket(resultPacket.payload)
        return infoPacket

    async def uploadMicroapp(self, data: bytearray, index: int = 0, chunkSize: int = 128):
        for i in range(0, len(data), chunkSize):
            chunk = data[i : i + chunkSize]
            # Pad the chunk with 0xFF, so the size is a multiple of 4.
            if len(chunk) % 4:
                if isinstance(chunk, bytes):
                    chunk = bytearray(chunk)
                chunk.extend((4 - (len(chunk) % 4)) * [0xFF])
            await self.uploadMicroappChunk(index, chunk, i)

    async def uploadMicroappChunk(self, index: int, data: bytearray, offset: int):
        _LOGGER.info(f"Upload microapp chunk index={index} offset={offset} size={len(data)}")
        header = MicroappHeaderPacket(appIndex=index)
        packet = MicroappUploadPacket(header, offset, data)
        controlPacket = ControlPacket(ControlType.MICROAPP_UPLOAD).loadByteArray(packet.toBuffer()).getPacket()

        def handleResult(notificationData):
            result = ResultPacket(notificationData)
            if result.valid:
                if result.resultCode == ResultValue.WAIT_FOR_SUCCESS:
                    _LOGGER.info("Waiting for data to be stored on Crownstone.")
                    return ProcessType.CONTINUE
                elif result.resultCode == ResultValue.SUCCESS or result.resultCode == ResultValue.SUCCESS_NO_CHANGE:
                    _LOGGER.info("Data stored.")
                    return ProcessType.FINISHED
                else:
                    _LOGGER.warning(f"Failed: {result.resultCode}")
                    return ProcessType.ABORT_ERROR
            else:
                _LOGGER.warning("Invalid result.")
                return ProcessType.ABORT_ERROR

        await self.core.ble.setupNotificationStream(
            CSServices.CrownstoneService,
            CrownstoneCharacteristics.Result,
            lambda: self._writeControlPacket(controlPacket),
            lambda notification: handleResult(notification),
            5
        )
        _LOGGER.info(f"uploaded chunk offset={offset}")
        # TODO: return the final result?

    async def validateMicroapp(self, index):
        packet = MicroappHeaderPacket(index)
        controlPacket = ControlPacket(ControlType.MICROAPP_VALIDATE).loadByteArray(packet.toBuffer()).getPacket()
        result = await self.core.ble.setupSingleNotification(
            CSServices.CrownstoneService,
            CrownstoneCharacteristics.Result,
            lambda: self._writeControlPacket(controlPacket)
        )
        resultPacket = ResultPacket(result)
        if resultPacket.resultCode != ResultValue.SUCCESS:
            raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, f"result={resultPacket.resultCode}")

    async def enableMicroapp(self, index):
        packet = MicroappHeaderPacket(index)
        controlPacket = ControlPacket(ControlType.MICROAPP_ENABLE).loadByteArray(packet.toBuffer()).getPacket()
        result = await self.core.ble.setupSingleNotification(
            CSServices.CrownstoneService,
            CrownstoneCharacteristics.Result,
            lambda: self._writeControlPacket(controlPacket)
        )
        resultPacket = ResultPacket(result)
        if resultPacket.resultCode != ResultValue.SUCCESS:
            raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, f"result={resultPacket.resultCode}")

    async def removeMicroapp(self, index):
        packet = MicroappHeaderPacket(index)
        controlPacket = ControlPacket(ControlType.MICROAPP_REMOVE).loadByteArray(packet.toBuffer()).getPacket()

        def handleResult(notificationData):
            result = ResultPacket(notificationData)
            if result.valid:
                if result.resultCode == ResultValue.WAIT_FOR_SUCCESS:
                    _LOGGER.info("Waiting for data to be erased on Crownstone.")
                    return ProcessType.CONTINUE
                elif result.resultCode == ResultValue.SUCCESS or result.resultCode == ResultValue.SUCCESS_NO_CHANGE:
                    _LOGGER.info("Data erased.")
                    return ProcessType.FINISHED
                else:
                    _LOGGER.warning(f"Failed: {result.resultCode}")
                    return ProcessType.ABORT_ERROR
            else:
                _LOGGER.warning("Invalid result.")
                return ProcessType.ABORT_ERROR

        await self.core.ble.setupNotificationStream(
            CSServices.CrownstoneService,
            CrownstoneCharacteristics.Result,
            lambda: self._writeControlPacket(controlPacket),
            lambda notification: handleResult(notification),
            5
        )
        _LOGGER.info(f"Removed app {index}")

    """
    ---------------  UTIL  ---------------
    """




    async def _readControlPacket(self, packet):
        if self.core.ble.hasCharacteristic(SetupCharacteristics.SetupControl):
            return await self.core.ble.readCharacteristic(CSServices.SetupService, SetupCharacteristics.SetupControl)
        else:
            return await self.core.ble.readCharacteristic(CSServices.CrownstoneService, CrownstoneCharacteristics.Control)

    async def _writeControlPacket(self, packet):
        if self.core.ble.hasCharacteristic(SetupCharacteristics.SetupControl):
            await self.core.ble.writeToCharacteristic(CSServices.SetupService, SetupCharacteristics.SetupControl, packet)
        else:
            await self.core.ble.writeToCharacteristic(CSServices.CrownstoneService, CrownstoneCharacteristics.Control, packet)


    async def _writeControlAndGetResult(self, controlPacket, acceptedResultValues = [ResultValue.SUCCESS, ResultValue.SUCCESS_NO_CHANGE]) -> ResultPacket:
        """
        Writes the control packet, checks the result value, and returns the result packet.
        @param controlPacket:          Serialized control packet to write.
        @param acceptedResultValues:   List of result values that are ok.
        @return:                       The result packet.
        """
        if self.core.ble.hasCharacteristic(SetupCharacteristics.Result):
            result = await self.core.ble.setupSingleNotification(CSServices.SetupService, SetupCharacteristics.Result, lambda: self._writeControlPacket(controlPacket))
        else:
            result = await self.core.ble.setupSingleNotification(CSServices.CrownstoneService, CrownstoneCharacteristics.Result, lambda: self._writeControlPacket(controlPacket))
        resultPacket = ResultPacket(result)
        if not resultPacket.valid:
            raise CrownstoneException(CrownstoneError.INCORRECT_RESPONSE_LENGTH, "Result is invalid")
        if resultPacket.resultCode not in acceptedResultValues:
            raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, f"Result code is {resultPacket.resultCode}")

        return resultPacket

def ProcessSessionNoncePacket(encryptedPacket, key, settings):
    # decrypt it
    decrypted = EncryptionHandler.decryptECB(encryptedPacket, key)

    packet = SessionDataPacket(decrypted)
    if packet.validation == CHECKSUM:
        # load into the settings object
        settings.setSessionNonce(packet.sessionNonce)
        settings.setValidationKey(packet.validationKey)
        settings.setCrownstoneProtocolVersion(packet.protocol)
    else:
        raise CrownstoneBleException(BleError.COULD_NOT_VALIDATE_SESSION_NONCE, "Could not validate the session nonce.")
