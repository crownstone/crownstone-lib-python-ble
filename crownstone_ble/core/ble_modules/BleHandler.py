import asyncio
import logging

import bleak.exc
from bleak import BleakClient, BleakScanner

from crownstone_core.Exceptions import CrownstoneBleException, CrownstoneError
from crownstone_core.core.modules.EncryptionSettings import EncryptionSettings
from crownstone_core.protocol.BluenetTypes import ProcessType
from crownstone_core.util.EncryptionHandler import EncryptionHandler

from crownstone_ble.Exceptions import BleError
from crownstone_ble.core.BleEventBus import BleEventBus

from crownstone_ble.core.bluetooth_delegates.BleakScanDelegate import BleakScanDelegate
from crownstone_ble.core.bluetooth_delegates.NotificationDelegate import NotificationDelegate
from crownstone_ble.core.modules.Validator import Validator
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics

_LOGGER = logging.getLogger(__name__)

CCCD_UUID = 0x2902


class ActiveClient:

    def __init__(self, address, cleanupCallback, bleAdapterAddress):
        self.address = address
        if bleAdapterAddress is None:
            self.client = BleakClient(address)
        else:
            self.client = BleakClient(address, adapter=bleAdapterAddress)
        self.cleanupCallback = cleanupCallback
        self.client.set_disconnected_callback(self.forcedDisconnect)

        # Dict with service UUID as key, handle as value.
        self.services = {}

        # Dict with characteristic UUID as key, handle as value.
        self.characteristics = {}

        # Current callbacks for notifications, in the form of: def handleNotification(uuid: str, data)
        # Characteristic UUID is key, callback is value.
        self.notificationCallbacks = {}

        # Notifications we subscribed to.
        # Handle as key, UUID as value.
        self.notificationSubscriptions = {}

    def forcedDisconnect(self, data):
        BleEventBus.emit(SystemBleTopics.forcedDisconnect, self.address)
        self.cleanupCallback()

    async def isConnected(self):
        return await self.client.is_connected()

    async def subscribeNotifications(self, characteristicUuid: str, callback):
        _LOGGER.debug(f"register callback for notifications to uuid={characteristicUuid}")
        if characteristicUuid in self.notificationCallbacks:
            _LOGGER.error(f"There is already a callback registered for {characteristicUuid}")

        if characteristicUuid not in self.notificationSubscriptions.values():
            # handle = self.characteristics.get(uuid, None)
            # if handle is not None:
            _LOGGER.debug(f"subscribe to uuid={characteristicUuid}")
            handle = self.characteristics[characteristicUuid]
            await self.client.start_notify(characteristicUuid, self._resultNotificationHandler)
            self.notificationSubscriptions[handle] = characteristicUuid
        self.notificationCallbacks[characteristicUuid] = callback

    def unsubscribeNotifications(self, characteristicUuid: str):
        _LOGGER.debug(f"remove callback for notifications to uuid={characteristicUuid}")
        self.notificationCallbacks.pop(characteristicUuid, None)

    def _resultNotificationHandler(self, characteristicHandle, data):
        uuid = self.notificationSubscriptions.get(characteristicHandle, None)
        if uuid is None:
            _LOGGER.error(f"UUID not found for handle {characteristicHandle}")
        callback = self.notificationCallbacks.get(uuid, None)
        if callback is not None:
            callback(uuid, data)



class BleHandler:

    def __init__(self, settings: EncryptionSettings, bleAdapterAddress: str=None):
        # bleAdapterAddress is the MAC address of the adapter you want to use.

        self.settings = settings
        self.bleAdapterAddress = bleAdapterAddress

        # Connection
        self.activeClient: ActiveClient or None = None

        # Scanning
        self.scanner = BleakScanner(adapter=bleAdapterAddress)
        self.scanningActive = False
        self.scanAborted = False
        scanDelegate = BleakScanDelegate(self.settings)
        self.scanner.register_detection_callback(scanDelegate.handleDiscovery)

        # Event bus
        self.subscriptionIds = []
        self.validator = Validator()
        self.subscriptionIds.append(BleEventBus.subscribe(SystemBleTopics.abortScanning, lambda x: self.abortScan()))

        # To be moved to active client or notification handler.
        self.notificationLoopActive = False


    async def shutDown(self):
        for subscriptionId in self.subscriptionIds:
            BleEventBus.unsubscribe(subscriptionId)
        await self.disconnect()
        await self.stopScanning()


    async def is_connected_guard(self):
        connected = await self.is_connected()
        if not connected:
            _LOGGER.debug(f"Could not perform action since the client is not connected!.")
            raise CrownstoneBleException("Not connected.")


    async def is_connected(self, address = None) -> bool:
        """
        Check if connected to a BLE device.
        :param address: When not None, check if connected to given address.
        :returns:       True when connected.
        """
        if self.activeClient is None:
            return False
        if address is not None:
            if self.activeClient.address.lower() != address.lower():
                return False
        connected = await self.activeClient.client.is_connected()
        if connected:
            return True


    def resetClient(self):
        self.activeClient = None


    async def connect(self, address, timeout: int = 5, attempts: int = 3) -> bool:
        # Always clean up cached setup key for a new connection.
        self.settings.exitSetup()

        # TODO: Check if activeClient is already set.
        self.activeClient = ActiveClient(address, lambda: self.resetClient(), self.bleAdapterAddress)

        _LOGGER.info(f"Connecting to {address}")
        connected = False
        for i in range(0, attempts):
            connected = await self.connectAttempt(timeout)
            if connected:
                break
        if not connected:
            raise CrownstoneBleException(CrownstoneError.CONNECTION_FAILED)

        _LOGGER.info(f"Connected")
        serviceSet = await self.activeClient.client.get_services()
        self.activeClient.services = {}
        self.activeClient.characteristics = {}
        for key, service in serviceSet.services.items():
            self.activeClient.services[service.uuid] = key
        for key, characteristic in serviceSet.characteristics.items():
            self.activeClient.characteristics[characteristic.uuid] = characteristic.handle

        self.activeClient.notificationCallbacks = {}
        self.activeClient.notificationSubscriptions = {}

        return connected

    async def connectAttempt(self, timeout: int) -> bool:
        # this can throw an error when the connection fails.
        # these BleakErrors are nicely human readable.
        # TODO: document/convert these errors.
        try:
            _LOGGER.debug(f"Connecting..")
            connected = await self.activeClient.client.connect(timeout = timeout)
        except bleak.BleakError as err:
            _LOGGER.info(f"Failed to connect: {err}")
            connected = False
        except TimeoutError as err:
            _LOGGER.info(f"Failed to connect: {err}")
            connected = False
        return connected


    async def disconnect(self):
        if self.activeClient is not None:
            self.settings.exitSetup()
            await self.activeClient.client.disconnect()
            self.activeClient = None


    async def waitForPeripheralToDisconnect(self, timeout: int = 10):
        if self.activeClient is not None:
            if await self.activeClient.isConnected():
                waiting = True
                def disconnectListener(data):
                    nonlocal waiting
                    waiting = False

                listenerId = BleEventBus.subscribe(SystemBleTopics.forcedDisconnect, disconnectListener)

                timer = 0
                while waiting and timer < 10:
                    await asyncio.sleep(0.1)
                    timer += 0.1

                self.settings.exitSetup()
                BleEventBus.unsubscribe(listenerId)

                self.activeClient = None


    async def scan(self, duration=3):
        _LOGGER.debug(f"scan duration={duration}")
        await self.startScanning()
        while duration > 0 and self.scanAborted == False:
            await asyncio.sleep(0.1)
            duration -= 0.1
        await self.stopScanning()


    async def startScanning(self):
        _LOGGER.debug(f"startScanning scanningActive={self.scanningActive}")
        if not self.scanningActive:
            self.scanAborted = False
            self.scanningActive = True
            await self.scanner.start()


    async def stopScanning(self):
        _LOGGER.debug(f"stopScanning scanningActive={self.scanningActive}")
        if self.scanningActive:
            self.scanningActive = False
            self.scanAborted = False
            await self.scanner.stop()


    def abortScan(self):
        _LOGGER.debug("abortScan")
        self.scanAborted = True

    def hasService(self, serviceUUID) -> bool:
        _LOGGER.debug(f"hasService serviceUUID={serviceUUID}")
        return serviceUUID in self.activeClient.services

    def hasCharacteristic(self, characteristicUUID) -> bool:
        _LOGGER.debug(f"hasCharacteristic characteristicUUID={characteristicUUID}")
        return characteristicUUID in self.activeClient.characteristics

    async def writeToCharacteristic(self, serviceUUID, characteristicUUID, content):
        _LOGGER.debug(f"writeToCharacteristic serviceUUID={serviceUUID} characteristicUUID={characteristicUUID} content={content}")
        await self.is_connected_guard()
        encryptedContent = EncryptionHandler.encrypt(content, self.settings)
        payload = self._preparePayload(encryptedContent)
        await self.activeClient.client.write_gatt_char(characteristicUUID, payload, response=True)


    async def writeToCharacteristicWithoutEncryption(self, serviceUUID, characteristicUUID, content, response=True):
        _LOGGER.debug(f"writeToCharacteristicWithoutEncryption serviceUUID={serviceUUID} characteristicUUID={characteristicUUID} content={content}")
        await self.is_connected_guard()
        payload = self._preparePayload(content)
        await self.activeClient.client.write_gatt_char(characteristicUUID, payload, response=response)


    async def readCharacteristic(self, serviceUUID, characteristicUUID):
        _LOGGER.debug(f"readCharacteristic serviceUUID={serviceUUID} characteristicUUID={characteristicUUID}")
        data = await self.readCharacteristicWithoutEncryption(serviceUUID, characteristicUUID)
        if self.settings.isEncryptionEnabled():
            return EncryptionHandler.decrypt(data, self.settings)


    async def readCharacteristicWithoutEncryption(self, serviceUUID, characteristicUUID):
        _LOGGER.debug(f"readCharacteristicWithoutEncryption serviceUUID={serviceUUID} characteristicUUID={characteristicUUID}")
        await self.is_connected_guard()
        return await self.activeClient.client.read_gatt_char(characteristicUUID)


    async def setupSingleNotification(self, serviceUUID, characteristicUUID, writeCommand, timeout = None):
        if timeout is None:
            timeout = 12.5

        _LOGGER.debug(f"setupSingleNotification serviceUUID={serviceUUID} characteristicUUID={characteristicUUID}")
        await self.is_connected_guard()

        # setup the collecting of the notification data.
        _LOGGER.debug(f"setupSingleNotification: subscribe for notifications.")
        notificationDelegate = NotificationDelegate(self._killNotificationLoop, self.settings)
        await self.activeClient.subscribeNotifications(characteristicUUID, notificationDelegate.handleNotification)

        # execute something that will trigger the notifications
        _LOGGER.debug(f"setupSingleNotification: writeCommand().")
        await writeCommand()

        # wait for the results to come in.
        self.notificationLoopActive = True
        loopCount = 0
        pollInterval = 0.1
        while self.notificationLoopActive and loopCount < (timeout / pollInterval):
            await asyncio.sleep(pollInterval)
            loopCount += 1


        if notificationDelegate.result is None:
            if self.activeClient is not None:
                self.activeClient.unsubscribeNotifications(characteristicUUID)
            raise CrownstoneBleException(BleError.NO_NOTIFICATION_DATA_RECEIVED, "No notification data received.")

        if self.activeClient is not None:
            self.activeClient.unsubscribeNotifications(characteristicUUID)
        return notificationDelegate.result


    async def setupNotificationStream(self, serviceUUID, characteristicUUID, writeCommand, resultHandler, timeout):
        _LOGGER.debug(f"setupNotificationStream serviceUUID={serviceUUID} characteristicUUID={characteristicUUID} timeout={timeout}")
        await self.is_connected_guard()

        # Collect all merged notifications in a queue, so we can process them all.
        mergedNotifications = []
        def onMergedNotification():
            mergedNotifications.append(notificationDelegate.result)
            notificationDelegate.reset()

        # Subscribe for notifications and let the delegate merge them.
        _LOGGER.debug(f"setupNotificationStream: subscribe for notifications.")
        notificationDelegate = NotificationDelegate(onMergedNotification, self.settings)
        await self.activeClient.subscribeNotifications(characteristicUUID, notificationDelegate.handleNotification)

        # Execute something that will trigger the notifications.
        _LOGGER.debug(f"setupNotificationStream: writeCommand().")
        await writeCommand()

        # Wait for the results to come in.
        self.notificationLoopActive = True
        loopCount = 0
        successful = False
        pollInterval = 0.1
        while self.notificationLoopActive and loopCount < (timeout / pollInterval):
            await asyncio.sleep(pollInterval)
            _LOGGER.debug(f"loopActive={self.notificationLoopActive} loopCount={loopCount}")
            loopCount += 1
            if len(mergedNotifications):
                command = resultHandler(mergedNotifications.pop(0))
                if command == ProcessType.ABORT_ERROR:
                    _LOGGER.debug("abort")
                    self.notificationLoopActive = False
                    self.activeClient.unsubscribeNotifications(characteristicUUID)
                    raise CrownstoneBleException(BleError.ABORT_NOTIFICATION_STREAM_W_ERROR, "Aborting the notification stream because the resultHandler raised an error.")
                elif command == ProcessType.FINISHED:
                    _LOGGER.debug("finished")
                    self.notificationLoopActive = False
                    successful = True
                elif command == ProcessType.CONTINUE:
                    _LOGGER.debug("continue")

        if not successful:
            self.activeClient.unsubscribeNotifications(characteristicUUID)
            raise CrownstoneBleException(BleError.NOTIFICATION_STREAM_TIMEOUT, "Notification stream not finished within timeout.")

        # remove subscription from this characteristic
        self.activeClient.unsubscribeNotifications(characteristicUUID)

    def _killNotificationLoop(self):
        _LOGGER.debug("_killNotificationLoop")
        self.notificationLoopActive = False


    def _preparePayload(self, data: list or bytes or bytearray):
        return bytearray(data)




