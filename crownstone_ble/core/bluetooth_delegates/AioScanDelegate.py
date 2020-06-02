from crownstone_core.packets.Advertisement import Advertisement

from crownstone_ble.AioCrownstoneParser import AioCrownstoneParser
from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics


class AioScanDelegate:
    
    def __init__(self, settings):
        self.settings = settings

    def handleDiscovery(self, hciEvent):
        parsedCrownstoneData = AioCrownstoneParser(hciEvent)
        self.parsePayload(parsedCrownstoneData)

    def parsePayload(self, parsedCrownstoneData):
        advertisement = Advertisement(
            parsedCrownstoneData.address,
            parsedCrownstoneData.rssi,
            parsedCrownstoneData.name,
            parsedCrownstoneData.valueArr,
            parsedCrownstoneData.serviceUUID
        )

        if advertisement.serviceData.opCode <= 5:
            advertisement.decrypt(self.settings.basicKey)
        elif advertisement.serviceData.opCode >= 7:
            advertisement.decrypt(self.settings.serviceDataKey)

        print("parsing a packet", advertisement.isCrownstoneFamily())
        if advertisement.isCrownstoneFamily():
            BleEventBus.emit(SystemBleTopics.rawAdvertisement, advertisement)