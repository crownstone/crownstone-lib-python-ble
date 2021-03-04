from crownstone_ble.core.container.Containers import ScanData
from crownstone_core.Enums import CrownstoneOperationMode

from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics


class NearestSelector:
    
    def __init__(self, setupModeOnly=False, rssiAtLeast=-100, returnFirstAcceptable=False, addressesToExcludeSet=set()):
        self.setupModeOnly = setupModeOnly
        self.rssiAtLeast = rssiAtLeast
        self.returnFirstAcceptable = returnFirstAcceptable
        self.addressesToExcludeSet = addressesToExcludeSet
        self.deviceList = []
        self.nearest = None
        
        
    def handleAdvertisement(self, scanData: ScanData):
        if scanData.address.lower() in self.addressesToExcludeSet:
            return
        
        if self.setupModeOnly and not scanData.operationMode == CrownstoneOperationMode.SETUP:
            return

        if not self.setupModeOnly and scanData.operationMode == CrownstoneOperationMode.SETUP:
            return
            
        if scanData.rssi < self.rssiAtLeast:
            return
        
        self.deviceList.append(scanData)
        
        if self.returnFirstAcceptable:
            BleEventBus.emit(SystemBleTopics.abortScanning, True)
            
            
    def getNearest(self):
        if len(self.deviceList) == 0:
            return None
        
        nearest = self.deviceList[0]
        
        for adv in self.deviceList:
            if nearest.rssi < adv.rssi < 0:
                nearest = adv
            
        return CrownstoneSummary(
            nearest.name,
            nearest.address,
            nearest.rssi,
            nearest.operationMode == CrownstoneOperationMode.SETUP,
            nearest.payload.crownstoneId,
            nearest.validated
        )


class CrownstoneSummary:

    def __init__(self, name, address, rssi, setupMode, crownstoneId, validated):
        self.name         = name
        self.address      = address
        self.rssi         = rssi
        self.setupMode    = setupMode
        self.validated    = validated
        self.crownstoneId = crownstoneId
