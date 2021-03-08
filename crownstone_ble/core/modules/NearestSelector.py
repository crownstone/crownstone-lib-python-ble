from crownstone_ble.core.container.ScanData import ScanData
from crownstone_core.Enums import CrownstoneOperationMode

from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics


class NearestSelector:
    
    def __init__(self, setupModeOnly=False, rssiAtLeast=-100, returnFirstAcceptable=False, addressesToExcludeSet=None):
        self.setupModeOnly = setupModeOnly
        self.rssiAtLeast = rssiAtLeast
        self.returnFirstAcceptable = returnFirstAcceptable
        if addressesToExcludeSet is None:
            self.addressesToExcludeSet = set()
        else:
            self.addressesToExcludeSet = addressesToExcludeSet
        self.deviceList = []
        self.nearest = None
        
        
    def handleAdvertisement(self, scanData: ScanData):
        if scanData.address in self.addressesToExcludeSet:
            return
        
        if self.setupModeOnly and not scanData.operationMode == CrownstoneOperationMode.SETUP:
            return

        # TODO: this is actually normalModeOnly, maybe change setupModeOnly to operationMode to filter for.
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
            
        return nearest


