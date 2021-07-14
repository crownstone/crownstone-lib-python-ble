from crownstone_core.Enums import CrownstoneOperationMode
from crownstone_core.protocol.Services import DFU_ADVERTISEMENT_SERVICE_UUID

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
            longUUID = serviceUUID
            if "0000c001-0000-1000-8000-00805f9b34fb" in longUUID:
                shortUUID = int(longUUID[4:8], 16)
                self.parsePayload(device.address, device.rssi, device.name, list(serviceData), shortUUID)
            elif DFU_ADVERTISEMENT_SERVICE_UUID in longUUID:
                self.parsePayload(device.address, device.rssi, device.name, list(serviceData), DFU_ADVERTISEMENT_SERVICE_UUID)


    def parsePayload(self, address, rssi, nameText, serviceDataArray, serviceUUID):
        advertisement = Advertisement(address, rssi, nameText, serviceDataArray, serviceUUID)
        if advertisement.isCrownstoneFamily():
            if advertisement.operationMode == CrownstoneOperationMode.SETUP:
                advertisement.parse()
                BleEventBus.emit(SystemBleTopics.rawAdvertisementClass, advertisement)
            else:
                try:
                    advertisement.parse(self.settings.serviceDataKey)
                except:
                    # fail silently. If we can't parse this, we just to propagate this message
                    pass

                BleEventBus.emit(SystemBleTopics.rawAdvertisementClass, advertisement)
