import logging

from crownstone_ble.Exceptions import BleError
from crownstone_core.Exceptions import CrownstoneBleException
from crownstone_core.packets.ResultPacket import ResultPacket
from crownstone_core.protocol.BluenetTypes import ProcessType, ResultValue
from crownstone_core.protocol.Characteristics import SetupCharacteristics
from crownstone_core.protocol.ControlPackets import ControlPacketsGenerator
from crownstone_core.protocol.Services import CSServices

from crownstone_ble.core.ble_modules.ControlHandler import ProcessSessionNoncePacket

_LOGGER = logging.getLogger(__name__)

class SetupHandler:
    def __init__(self, bluetoothCore):
        self.core = bluetoothCore

    async def setup(self, address, sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor):
        await self.core.ble.connect(address)
        try:
            await self.fastSetupV2(sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor)
        except CrownstoneBleException as e:
            if e.type is not BleError.NOTIFICATION_STREAM_TIMEOUT:
                raise e

        # Disconnect before scanning.
        await self.core.ble.waitForPeripheralToDisconnect()


    async def fastSetupV2(self, sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor):
        if not self.core.settings.initializedKeys:
            raise CrownstoneBleException(BleError.NO_ENCRYPTION_KEYS_SET, "Keys are not initialized so I can't put anything on the Crownstone. Make sure you call .setSettings(adminKey, memberKey, basicKey, serviceDataKey, localizationKey, meshApplicationKey, meshNetworkKey")

        await self.handleSetupPhaseEncryption()
        await self.core.ble.setupNotificationStream(
            CSServices.SetupService,
            SetupCharacteristics.Result,
            lambda: self._writeFastSetupV2(sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor),
            lambda notificationResult: self._handleResult(notificationResult),
            3
        )

        _LOGGER.info("Closing setup.")
        self.core.settings.exitSetup()


    async def _writeFastSetupV2(self, sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor):
        packet = ControlPacketsGenerator.getSetupPacket(
            crownstoneId,
            sphereId,
            self.core.settings.adminKey,
            self.core.settings.memberKey,
            self.core.settings.basicKey,
            self.core.settings.serviceDataKey,
            self.core.settings.localizationKey,
            meshDeviceKey,
            self.core.settings.meshApplicationKey,
            self.core.settings.meshNetworkKey,
            ibeaconUUID,
            ibeaconMajor,
            ibeaconMinor
        )

        _LOGGER.info("Writing setup data to Crownstone...")
        await self.core.ble.writeToCharacteristic(CSServices.SetupService, SetupCharacteristics.SetupControl, packet)

    def _handleResult(self, result):
        response = ResultPacket(result)
        if response.valid:
            if response.resultCode == ResultValue.WAIT_FOR_SUCCESS:
                _LOGGER.info("Waiting for setup data to be stored on Crownstone...")
                return ProcessType.CONTINUE
            elif response.resultCode == ResultValue.SUCCESS:
                _LOGGER.info("Setup data stored...")
                return ProcessType.FINISHED
            else:
                _LOGGER.warning("Unexpected notification data. Aborting...")
                return ProcessType.ABORT_ERROR
        else:
            _LOGGER.warning("Invalid notification data. Aborting...")
            return ProcessType.ABORT_ERROR


    async def handleSetupPhaseEncryption(self):
        sessionKey         = await self.core.ble.readCharacteristicWithoutEncryption(CSServices.SetupService, SetupCharacteristics.SessionKey)
        sessionNoncePacket = await self.core.ble.readCharacteristicWithoutEncryption(CSServices.SetupService, SetupCharacteristics.SessionData)

        self.core.settings.loadSetupKey(sessionKey)
        ProcessSessionNoncePacket(sessionNoncePacket, sessionKey, self.core.settings)

