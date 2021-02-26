from crownstone_core import Conversion

from crownstone_ble.topics.BleTopics import BleTopics
from crownstone_core.packets.Advertisement import Advertisement

from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics

SERVICE_DATA_ADTYPE = 22
NAME_ADTYPE         = 8
FLAGS_ADTYPE        = 1

class BleakScanDelegate:

    def __init__(self, settings):
        self.settings = settings

    def handleDiscovery(self, device, advertisement_data):
        serviceData = advertisement_data.service_data
        for serviceUUID, serviceData in serviceData.items():
            longUUID = serviceUUID.lower()
            if "0000c001-0000-1000-8000-00805f9b34fb" in longUUID:
                shortUUID = int(longUUID[4:8], 16)
                self.parsePayload(device.address, device.rssi, device.name, list(serviceData), shortUUID)


    def parsePayload(self, address, rssi, nameText, serviceDataArray, serviceUUID):
        advertisement = Advertisement(address, rssi, nameText, serviceDataArray, serviceUUID)

        if advertisement.serviceData.opCode <= 5:
            advertisement.decrypt(self.settings.basicKey)
        elif advertisement.serviceData.opCode >= 7:
            advertisement.decrypt(self.settings.serviceDataKey)

        if advertisement.isCrownstoneFamily():
            BleEventBus.emit(SystemBleTopics.rawAdvertisementClass, advertisement)