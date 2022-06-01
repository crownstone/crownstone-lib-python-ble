import asyncio
import logging
from typing import List

from crownstone_core.Exceptions import CrownstoneException, CrownstoneBleException, CrownstoneError
from crownstone_core.packets.assetFilter.FilterCommandPackets import FilterSummariesPacket, FilterSummaryPacket
from crownstone_core.packets.assetFilter.builders.AssetFilter import AssetFilter
from crownstone_core.packets.assetFilter.util import AssetFilterMasterCrc
from crownstone_core.packets.assetFilter.util.AssetFilterChunker import FilterChunker
from crownstone_core.packets.assetFilter.util.AssetFilterSyncer import AssetFilterSyncer
from crownstone_core.packets.ResultPacket import ResultPacket
from crownstone_core.packets.SessionDataPacket import SessionDataPacket
from crownstone_core.protocol.BluenetTypes import ProcessType, ResultValue
from crownstone_core.protocol.Characteristics import CrownstoneCharacteristics, SetupCharacteristics
from crownstone_core.protocol.ControlPackets import ControlPacketsGenerator
from crownstone_core.protocol.Services import CSServices
from crownstone_core.util.EncryptionHandler import EncryptionHandler, CHECKSUM

from crownstone_ble.Exceptions import BleError

_LOGGER = logging.getLogger(__name__)

class ControlHandler:
    def __init__(self, bluetoothCore):
        self.core = bluetoothCore

    async def _getAndSetSessionNonce(self):
        """
        Reads the session nonce, and uses it to set settings.
        """
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
        :param switchVal:    Percentage: 0 - 100, or special value (SwitchValSpecial).
        """
        await self._writeControlAndGetResult(ControlPacketsGenerator.getSwitchCommandPacket(switchVal))

    async def setRelay(self, turnOn: bool):
        """
        Deprecated, use setSwitch() instead.
        Set the relay, regardless of the dimmer.

        :param turnOn:       True to turn relay on.
        """
        _LOGGER.warning("setRelay is deprecated. Use setSwitch() instead.")
        await self._writeControlAndGetResult(ControlPacketsGenerator.getRelaySwitchPacket(turnOn))

    async def setDimmer(self, intensity: int):
        """
        Deprecated, use setSwitch() instead.

        :param intensity:    Percentage: 0 - 100.
        """
        _LOGGER.warning("setDimmer is deprecated. Use setSwitch() instead.")
        await self._writeControlAndGetResult(ControlPacketsGenerator.getDimmerSwitchPacket(intensity))

    async def putInDfuMode(self):
        """
        Puts the crownstone in DFU mode.
        """
        await self._writeControlAndGetResult(ControlPacketsGenerator.getPutInDFUPacket())

    async def commandFactoryReset(self):
        """
        If you have the keys, you can use this to put the crownstone back into factory default mode
        """
        await self._writeControlAndGetResult(ControlPacketsGenerator.getCommandFactoryResetPacket())

    async def allowDimming(self, allow: bool):
        """
        :param allow:        True to allow dimming.
        """
        await self._writeControlAndGetResult(ControlPacketsGenerator.getAllowDimmingPacket(allow))

    async def resetErrors(self, bitmask: int = 0xFFFFFFFF):
        """
        Resets errors.
        :param bitmask:      A 32b bitmask of the errors to reset.
        """
        await self._writeControlAndGetResult(ControlPacketsGenerator.getResetErrorPacket(bitmask))

    async def disconnect(self):
        """
        Make the Crownstone to disconnect from you.
        """
        try:
            # Only wait for a short time, because we don't expect a result packet.
            await self._writeControlAndGetResult(ControlPacketsGenerator.getDisconnectPacket(), [ResultValue.SUCCESS], 1)
        except CrownstoneBleException as err:
            if err.type == BleError.NO_NOTIFICATION_DATA_RECEIVED:
                _LOGGER.info(f"Ignoring expected error: {err}")
            else:
                raise err

        # Disconnect from this side as well.
        await self.core.ble.disconnect()


    async def lockSwitch(self, lock: bool):
        """
        Lock the switch, so that it will stay on or off.
        Can not be used in combination with dimming.

        :param lock:         True to lock the switch.
        """
        await self._writeControlAndGetResult(ControlPacketsGenerator.getLockSwitchPacket(lock))


    async def reset(self):
        """
        Let the Crownstone reboot.
        """
        await self._writeControlAndGetResult(ControlPacketsGenerator.getResetPacket())

    async def recovery(self, address):
        """
        Recover a Crownstone when you don't have the keys.
        Can only be used within 10 seconds after the Crownstone has been powered on.
        Connects, performs recovery, and disconnects.

        :param address:      The MAC address of the Crownstone to recover.
        """
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

    async def setFilters(self, filters: List[AssetFilter], masterVersion: int = None) -> int:
        """
        Makes sure the given filters are set at the Crownstone.
        Uploads and removes filters where necessary.
        :param filters:           The asset filter to be uploaded.
        :param masterVersion:     The new master version. If None, the master version will be increased by 1.
        :return:                  The new master version.
        """
        _LOGGER.info(f"setFilters")
        summaries = await self.getFilterSummaries()
        syncer = AssetFilterSyncer(summaries, filters, masterVersion)
        if not syncer.commitRequired:
            return syncer.masterVersion

        for filterId in syncer.removeIds:
            await self.removeFilter(filterId)

        for filter in filters:
            if filter.getFilterId() in syncer.uploadIds:
                await self.uploadFilter(filter)

        await self.commitFilterChanges(syncer.masterVersion, filters)
        return syncer.masterVersion

    async def getFilterSummaries(self) -> FilterSummariesPacket:
        """
        Get a summary of the filters that are on the Crownstones.
        This can be used to determine:
        - Which filters should be changed.
        - What the next master version should be.
        - How much space there is left for new filters.
        - The new master CRC.

        :return:   The filter summaries packet.
        """
        _LOGGER.info(f"getFilterSummaries")
        resultPacket = await self._writeControlAndGetResult(ControlPacketsGenerator.getGetFilterSummariesPacket())
        return FilterSummariesPacket(resultPacket.payload)

    async def uploadFilter(self, filter: AssetFilter):
        """
        Upload an asset filter to the Crownstones.
        Once all changes are made, don't forget to commit them.

        :param filter:  The asset filter to be uploaded.
        """
        _LOGGER.info(f"uploadFilter {filter}")
        chunker = FilterChunker(filter, 128)
        for i in range(0, chunker.getAmountOfChunks()):
            chunk = chunker.getChunk()
            await self._writeControlAndGetResult(ControlPacketsGenerator.getUploadFilterPacket(chunk))

    async def removeFilter(self, filterId):
        """
        Remove an asset filter from the Crownstones.
        Once all changes are made, don't forget to commit them.

        :param filterId:     The filter ID to be removed.
        """
        _LOGGER.info(f"removeFilter id={filterId}")
        await self._writeControlAndGetResult(ControlPacketsGenerator.getRemoveFilterPacket(filterId))

    async def commitFilterChanges(self, masterVersion: int, filters: List[AssetFilter], filterSummaries: List[FilterSummaryPacket] = None):
        """
        Commit the changes made by upload and/or remove.

        :param masterVersion:     The new master version, should be higher than previous master version.
        :param filters:           A list of asset filters with filter ID, that are uploaded to the Crowstone.
        :param filterSummaries :  A list of filter summaries that are already on the Crownstone.
        """
        _LOGGER.info(f"commitFilterChanges masterVersion={masterVersion}")
        masterCrc = AssetFilterMasterCrc.get_master_crc_from_filters(filters, filterSummaries)
        await self._writeControlAndGetResult(ControlPacketsGenerator.getCommitFilterChangesPacket(masterVersion, masterCrc))



    ##############################################
    #################### UTIL ####################
    ##############################################

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


    async def _writeControlAndGetResult(self, controlPacket, acceptedResultValues = [ResultValue.SUCCESS, ResultValue.SUCCESS_NO_CHANGE], timeout = None) -> ResultPacket:
        """
        Writes the control packet, checks the result value, and returns the result packet.
        :param controlPacket:          Serialized control packet to write.
        :param acceptedResultValues:   List of result values that are ok.
        :returns:                      The result packet.
        """
        if self.core.ble.hasCharacteristic(SetupCharacteristics.Result):
            result = await self.core.ble.setupSingleNotification(CSServices.SetupService, SetupCharacteristics.Result, lambda: self._writeControlPacket(controlPacket), timeout)
        else:
            result = await self.core.ble.setupSingleNotification(CSServices.CrownstoneService, CrownstoneCharacteristics.Result, lambda: self._writeControlPacket(controlPacket), timeout)
        resultPacket = ResultPacket(result)
        if not resultPacket.valid:
            raise CrownstoneException(CrownstoneError.INCORRECT_RESPONSE_LENGTH, "Result is invalid")
        if resultPacket.resultCode not in acceptedResultValues:
            raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, f"Result code is {resultPacket.resultCode}")

        return resultPacket

    async def _writeControlAndWaitForSuccess(self, controlPacket, timeout = 5, acceptedResultValues = [ResultValue.SUCCESS, ResultValue.SUCCESS_NO_CHANGE]):
        """
        Writes the control packet, and waits for success.
        :param controlPacket:          Serialized control packet to write.
        :param timeout:                Timeout in seconds.
        :param acceptedResultValues:   List of result values that are considered a success.
        """
        def handleResult(notificationData):
            result = ResultPacket(notificationData)
            if result.valid:
                if result.resultCode == ResultValue.WAIT_FOR_SUCCESS:
                    _LOGGER.debug("Waiting for success.")
                    return ProcessType.CONTINUE
                elif result.resultCode in acceptedResultValues:
                    _LOGGER.debug("Success.")
                    return ProcessType.FINISHED
                else:
                    _LOGGER.warning(f"Result code: {result.resultCode}")
                    return ProcessType.ABORT_ERROR
            else:
                _LOGGER.warning("Invalid result packet.")
                return ProcessType.ABORT_ERROR

        if self.core.ble.hasCharacteristic(SetupCharacteristics.Result):
            service = CSServices.SetupService
            resultCharacteristic = SetupCharacteristics.Result
        else:
            service = CSServices.CrownstoneService
            resultCharacteristic = CrownstoneCharacteristics.Result

        await self.core.ble.setupNotificationStream(
            service,
            resultCharacteristic,
            lambda: self._writeControlPacket(controlPacket),
            lambda notification: handleResult(notification),
            timeout
        )

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
