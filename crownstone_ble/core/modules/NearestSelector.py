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
        
        
    def handleAdvertisement(self, advertisement):
        if "serviceData" not in advertisement:
            return
        
        if advertisement["address"].lower() in self.addressesToExcludeSet:
            return
        
        if self.setupModeOnly and not advertisement["serviceData"]["setupMode"]:
            return
        
        
        if not self.setupModeOnly and advertisement["serviceData"]["setupMode"]:
            return
            
            
        if advertisement["rssi"] < self.rssiAtLeast:
            return
        
        self.deviceList.append(advertisement)
        
        if self.returnFirstAcceptable:
            BleEventBus.emit(SystemBleTopics.abortScanning, True)
            
            
    def getNearest(self):
        
        if len(self.deviceList) == 0:
            return None
        
        nearest = self.deviceList[0]
        
        for adv in self.deviceList:
            if nearest["rssi"] < adv["rssi"] < 0:
                nearest = adv
            
        return {
            "name": nearest["name"],
            "address": nearest["address"],
            "rssi" : nearest["rssi"],
            "setupMode": nearest["serviceData"]["setupMode"],
            "id" : nearest["serviceData"]["id"]
        }
        
        
        
        