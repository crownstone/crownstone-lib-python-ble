class Gatherer:
    
    def __init__(self):
        self.deviceList = {}
        
    def handleAdvertisement(self, advertisement, validated=False):
        if "serviceData" not in advertisement:
            return
        
        rssi = float(advertisement["rssi"])
        if float(advertisement["rssi"]) >= 0:
            rssi = None
        
        if advertisement["address"] not in self.deviceList:
            self.deviceList[advertisement["address"]] = { "address": advertisement["address"].lower(), "setupMode": advertisement["serviceData"]["setupMode"], "validated": validated, "rssi": rssi }
        elif validated:
            self.deviceList[advertisement["address"]]["validated"] = True

        self.deviceList[advertisement["address"]]["setupMode"] = advertisement["serviceData"]["setupMode"]
        
        if self.deviceList[advertisement["address"]]["rssi"] is None:
            self.deviceList[advertisement["address"]]["rssi"]  = rssi
        else:
            self.deviceList[advertisement["address"]]["rssi"]  = 0.9*self.deviceList[advertisement["address"]]["rssi"] + 0.1*advertisement["rssi"]
        
    
    def getCollection(self):
        collectionArray = []
        for address, device in self.deviceList.items():
            collectionArray.append(device)
            
        return collectionArray