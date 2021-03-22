from bleak import BleakClient, BleakScanner
from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics


class ActiveClient:

    def __init__(self, address, cleanupCallback, bleAdapterAddress):
        self.address = address
        self.client = BleakClient(address, adapter=bleAdapterAddress)
        self.services = None
        self.cleanupCallback = cleanupCallback
        self.client.set_disconnected_callback(self.forcedDisconnect)

    def forcedDisconnect(self, data):
        BleEventBus.emit(SystemBleTopics.forcedDisconnect, self.address)
        self.cleanupCallback()

    async def isConnected(self):
        return await self.client.is_connected()
