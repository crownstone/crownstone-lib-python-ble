from crownstone_core.packets.Advertisement import Advertisement
from crownstone_ble.core.container.ScanData import ScanData


def fillScanDataFromAdvertisement(advertisement: Advertisement, validated: bool):
    data = ScanData()

    data.address        = advertisement.address.lower()
    data.rssi           = advertisement.rssi
    data.name           = advertisement.name
    data.operationMode  = advertisement.operationMode
    data.payload        = advertisement.serviceData.payload
    data.deviceType     = advertisement.serviceData.deviceType
    data.validated      = validated

    return data