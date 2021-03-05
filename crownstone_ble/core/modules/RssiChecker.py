from crownstone_ble.core.container.ScanData import ScanData

class RssiChecker:

    def __init__(self, address):
        self.address = address.lower()
        self.result = []


    def handleAdvertisement(self, scanData: ScanData):
        if scanData.address != self.address:
            return

        self.result.append(scanData.rssi)


    def getResult(self):
        if len(self.result) == 0:
            return None

        sumResult = 0
        for res in self.result:
            sumResult += res
        return sumResult / len(self.result)


