from bluepy.btle import DefaultDelegate
from crownstone_core.Exceptions import CrownstoneBleException
from crownstone_core.util.EncryptionHandler import EncryptionHandler

LAST_PACKET_INDEX = 0xFF

class PeripheralDelegate(DefaultDelegate):
    
    def __init__(self, callback, settings):
        DefaultDelegate.__init__(self)
        self.callback = callback
        self.dataCollected = []
        self.settings = settings

    def handleNotification(self, cHandle, data):
        self.merge(data)
        
    def merge(self, data):
        self.dataCollected += data[1:]
        
        if data[0] == LAST_PACKET_INDEX:
            data = self.checkPayload()
            self.dataCollected = []
            self.callback(data)
                
       
    def checkPayload(self):
        try:
            return EncryptionHandler.decrypt(self.dataCollected, self.settings)
        except CrownstoneBleException as err:
            print(err)
        