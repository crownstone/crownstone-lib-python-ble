from bluepy.btle import DefaultDelegate
from crownstone_core.packets.Advertisement import Advertisement

from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics

SERVICE_DATA_ADTYPE = 22
NAME_ADTYPE         = 8
FLAGS_ADTYPE        = 1

class ScanDelegate(DefaultDelegate):
    
    def __init__(self, settings):
        self.settings = settings
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        valueText = dev.getValueText(SERVICE_DATA_ADTYPE)
        nameText = dev.getValueText(NAME_ADTYPE)
        if valueText is not None:
            self.parsePayload(dev.addr, dev.rssi, nameText, valueText)
          
    def parsePayload(self, address, rssi, nameText, valueText):
        advertisement = Advertisement(address, rssi, nameText, valueText)

        if advertisement.serviceData.opCode <= 5:
            advertisement.decrypt(self.settings.basicKey)
        elif advertisement.serviceData.opCode >= 7:
            advertisement.decrypt(self.settings.serviceDataKey)

        if advertisement.isCrownstoneFamily():
            BleEventBus.emit(SystemBleTopics.rawAdvertisement, advertisement)