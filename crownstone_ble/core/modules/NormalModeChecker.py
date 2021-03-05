from crownstone_core.Enums import CrownstoneOperationMode
from crownstone_ble.core.container.ScanData import ScanData
from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics


class NormalModeChecker:

    def __init__(self, address, waitUntilInRequiredMode=False):
        self.address = address.lower()
        self.result = False
        self.waitUntilInRequiredMode = waitUntilInRequiredMode

    def handleAdvertisement(self, scanData: ScanData):
        if scanData.address != self.address:
            return

        self.result = scanData.operationMode == CrownstoneOperationMode.NORMAL

        if not self.result and self.waitUntilInRequiredMode:
            pass
        else:
            BleEventBus.emit(SystemBleTopics.abortScanning, True)

    def getResult(self):
        return self.result

