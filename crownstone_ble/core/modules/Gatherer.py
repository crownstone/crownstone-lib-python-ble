from crownstone_core.Enums import CrownstoneOperationMode
from crownstone_ble.core.container.ScanData import ScanData


class Gatherer:
    
    def __init__(self):
        self.deviceList = {}
        
    def handleAdvertisement(self, scanData: ScanData):
        rssi = float(scanData.rssi)
        if float(scanData.rssi) >= 0:
            rssi = None
        
        if scanData.address not in self.deviceList:
            self.deviceList[scanData.address] = {"address": scanData.address.lower(), "setupMode": None, "validated": scanData.validated, "rssi": rssi}

        self.deviceList[scanData.address]["validated"] = True
        self.deviceList[scanData.address]["setupMode"] = scanData.operationMode == CrownstoneOperationMode.SETUP
        
        if self.deviceList[scanData.address]["rssi"] is None:
            self.deviceList[scanData.address]["rssi"] = rssi
        else:
            self.deviceList[scanData.address]["rssi"]  = 0.9 * self.deviceList[scanData.address]["rssi"] + 0.1 * rssi
        
    
    def getCollection(self):
        collectionArray = []
        for address, device in self.deviceList.items():
            collectionArray.append(device)
            
        return collectionArray

