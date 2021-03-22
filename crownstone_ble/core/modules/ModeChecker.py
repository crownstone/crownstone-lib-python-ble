from crownstone_core.Enums import CrownstoneOperationMode

from crownstone_ble.core.container.ScanData import ScanData
from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics


class ModeChecker:

    def __init__(self, address: str, targetMode: CrownstoneOperationMode or None, waitUntilInTargetMode=False):
        self.address = address.lower()
        self.result = None
        self.targetMode = targetMode
        self.waitUntilInTargetMode = waitUntilInTargetMode

    def handleAdvertisement(self, scanData: ScanData):
        if scanData.address != self.address:
            return

        self.result = scanData.operationMode

        if self.targetMode is not None and self.result != self.targetMode and self.waitUntilInTargetMode:
            pass
        elif self.targetMode is None and self.result == CrownstoneOperationMode.UNKNOWN:
            # if we're looking for a mode, we'll wait for the duration of the timeout in the hope it will be something other than unknown
            pass
        else:
            BleEventBus.emit(SystemBleTopics.abortScanning, True)

    def getResult(self):
        return self.result

