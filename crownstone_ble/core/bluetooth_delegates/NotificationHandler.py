from crownstone_core.Exceptions import CrownstoneBleException
from crownstone_core.protocol.BluenetTypes import ProcessType
from crownstone_core.util.EncryptionHandler import EncryptionHandler

from crownstone_ble.Exceptions import BleError
from crownstone_ble.core.ble_modules.ActiveClient import ActiveClient

LAST_PACKET_INDEX = 0xFF

class NotificationHandler:

    def __init__(self, settings, activeClient : ActiveClient, characteristicUUID: str, resultCallback):
        self.resultCallback = resultCallback
        self.characteristicUUID = characteristicUUID
        self.activeClient = activeClient
        self.settings = settings

        self.loopActive = False
        self.dataCollected = []

        self.error = None
        self.successful = False

    async def init(self):
        await self.activeClient.client.start_notify(self.characteristicUUID, self.handleNotification)
        self.loopActive = True

    def handleNotification(self, cHandle, data):
        self.merge(data)

    def merge(self, data):
        self.dataCollected += data[1:]

        if data[0] == LAST_PACKET_INDEX:
            result = self.checkPayload()
            self.dataCollected = []
            command = self.resultCallback(result)
            if command == ProcessType.ABORT_ERROR:
                self.error = BleError.ABORT_NOTIFICATION_STREAM_W_ERROR
                self.loopActive = False
            elif command == ProcessType.FINISHED:
                self.successful = True
                self.loopActive = False

    def isActive(self):
        if self.error is not None:
            raise CrownstoneBleException(self.error, "Aborting the notification stream because the resultHandler raised an error.")
        return self.loopActive

    def checkPayload(self):
        try:
            return EncryptionHandler.decrypt(self.dataCollected, self.settings)

        except CrownstoneBleException as err:
            self.error = BleError.INVALID_ENCRYPTION_PACKAGE
