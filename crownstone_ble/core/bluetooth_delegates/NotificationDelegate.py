import logging

from crownstone_core.Exceptions import CrownstoneBleException
from crownstone_core.util.EncryptionHandler import EncryptionHandler

LAST_PACKET_INDEX = 0xFF

_LOGGER = logging.getLogger(__name__)

class NotificationDelegate:
    """
    Merges notifications and decrypts the merged data.
    The decrypted data is then placed in the "result" variable.
    """

    def __init__(self, callback, settings):
        self.callback = callback
        self.dataCollected = []
        self.result = None
        self.settings = settings

    def handleNotification(self, uuid, data):
        self.merge(data)

    def merge(self, data):
        self.dataCollected += data[1:]
        _LOGGER.debug(f"Received part {data[0]}")

        if data[0] == LAST_PACKET_INDEX:
            _LOGGER.debug(f"Received last part. Merged data: {self.dataCollected}")
            result = self.checkPayload()
            self.result = result
            self.dataCollected = []
            if self.callback is not None:
                self.callback()


    def checkPayload(self):
        # try:
        return EncryptionHandler.decrypt(self.dataCollected, self.settings)

        # except CrownstoneBleException as err:
        #     print(err)

    def reset(self):
        self.result = None
        self.dataCollected = []
