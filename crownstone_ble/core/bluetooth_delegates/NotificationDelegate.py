from crownstone_core.Exceptions import CrownstoneBleException
from crownstone_core.util.EncryptionHandler import EncryptionHandler

LAST_PACKET_INDEX = 0xFF

class NotificationDelegate:

    def __init__(self, callback, settings):
        self.callback = callback
        self.dataCollected = []
        self.result = None
        self.settings = settings

    def handleNotification(self, cHandle, data):
        self.merge(data)

    def merge(self, data):
        self.dataCollected += data[1:]

        if data[0] == LAST_PACKET_INDEX:
            result = self.checkPayload()
            self.result = result
            self.dataCollected = []
            self.callback()


    def checkPayload(self):
        try:
            return EncryptionHandler.decrypt(self.dataCollected, self.settings)

        except CrownstoneBleException as err:
            print(err)
