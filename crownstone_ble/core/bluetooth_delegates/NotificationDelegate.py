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
        self.previousPart = -1 # Start at -1, so that we can check if received part > previous part
        self.dataCollected = []
        self.result = None
        self.settings = settings

    def handleNotification(self, uuid, data):
        self.merge(data)

    def merge(self, data):
        part = data[0]

        if self.result is not None:
            _LOGGER.debug(f"Last part already received, ignoring this part.")
            return

        # Ignore the case where we receive the same part twice.
        if part == self.previousPart:
            _LOGGER.debug(f"Already received part {part}, ignoring this part.")
            return

        # Check the part number.
        if part != LAST_PACKET_INDEX and part != self.previousPart + 1:
            _LOGGER.debug(f"Receive part {part}, expected part {self.previousPart + 1}")
            self.reset()
            return
        self.previousPart = part

        self.dataCollected += data[1:]
        _LOGGER.debug(f"Received part {part}")

        if data[0] == LAST_PACKET_INDEX:
            _LOGGER.debug(f"Received last part. Merged data: {self.dataCollected}")
            result = self.checkPayload()
            self.reset()
            self.result = result
            _LOGGER.debug(f"Result: {result}")
            if self.callback is not None:
                self.callback()

    def checkPayload(self):
        try:
            return EncryptionHandler.decrypt(self.dataCollected, self.settings)
        except CrownstoneBleException as err:
            _LOGGER.debug(f"Failed to decrypt: {err.message}")

    def reset(self):
        self.previousPart = -1
        self.dataCollected = []
        self.result = None
