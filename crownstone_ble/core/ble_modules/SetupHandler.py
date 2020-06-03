from crownstone_ble.Exceptions import BleError
from crownstone_core.Exceptions import CrownstoneBleException
from crownstone_core.packets.ResultPacket import ResultPacket
from crownstone_core.protocol.BluenetTypes import ProcessType, ResultValue
from crownstone_core.protocol.Characteristics import SetupCharacteristics
from crownstone_core.protocol.ControlPackets import ControlPacketsGenerator
from crownstone_core.protocol.Services import CSServices

from crownstone_ble.core.ble_modules.ControlHandler import ProcessSessionNoncePacket


class SetupHandler:
    def __init__(self, bluetoothCore):
        self.core = bluetoothCore

    def setup(self, address, sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor):
        characteristics = self.core.ble.getCharacteristics(CSServices.SetupService)
        try:
            self.fastSetupV2(sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor)
        except CrownstoneBleException as e:
            if e.type is not BleError.NOTIFICATION_STREAM_TIMEOUT:
                raise e
        isNormalMode = self.core.isCrownstoneInNormalMode(address, 10, waitUntilInRequiredMode=True)
        if not isNormalMode:
            raise CrownstoneBleException(BleError.SETUP_FAILED, "The setup has failed.")


    def fastSetupV2(self, sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor):
        if not self.core.settings.initializedKeys:
            raise CrownstoneBleException(BleError.NO_ENCRYPTION_KEYS_SET, "Keys are not initialized so I can't put anything on the Crownstone. Make sure you call .setSettings(adminKey, memberKey, basicKey, serviceDataKey, localizationKey, meshApplicationKey, meshNetworkKey")

        self.handleSetupPhaseEncryption()
        self.core.ble.setupNotificationStream(
            CSServices.SetupService,
            SetupCharacteristics.Result,
            lambda: self._writeFastSetupV2(sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor),
            lambda notificationResult: self._handleResult(notificationResult),
            3
        )

        print("CrownstoneBLE: Closing Setup V2.")
        self.core.settings.exitSetup()


    def _writeFastSetupV2(self, sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor):
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

        print("CrownstoneBLE: Writing setup data to Crownstone...")
        self.core.ble.writeToCharacteristic(CSServices.SetupService, SetupCharacteristics.SetupControl, packet)

    def _handleResult(self, result):
        response = ResultPacket(result)
        if response.valid:
            if response.resultCode == ResultValue.WAIT_FOR_SUCCESS:
                print("CrownstoneBLE: Waiting for setup data to be stored on Crownstone...")
                return ProcessType.CONTINUE
            elif response.resultCode == ResultValue.SUCCESS:
                print("CrownstoneBLE: Data stored...")
                return ProcessType.FINISHED
            else:
                print("CrownstoneBLE: Unexpected notification data. Aborting...")
                return ProcessType.ABORT_ERROR
        else:
            print("CrownstoneBLE: Invalid notification data. Aborting...")
            return ProcessType.ABORT_ERROR


    def handleSetupPhaseEncryption(self):
        sessionKey   = self.core.ble.readCharacteristicWithoutEncryption(CSServices.SetupService, SetupCharacteristics.SessionKey)
        sessionNoncePacket = self.core.ble.readCharacteristicWithoutEncryption(CSServices.SetupService, SetupCharacteristics.SessionData)

        self.core.settings.loadSetupKey(sessionKey)
        ProcessSessionNoncePacket(sessionNoncePacket, sessionKey, self.core.settings)

