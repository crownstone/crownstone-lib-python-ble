from crownstone_core.packets.Advertisement import Advertisement


class ScanData:

    def __init__(self):
        self.address       = None
        self.rssi          = None
        self.name          = None
        self.operationMode = None
        self.serviceUUID   = None
        self.deviceType    = None
        self.payload       = None
        self.validated     = None

    def __str__(self):
        return \
           f"address:       {self.address              }\n" \
           f"rssi:          {self.rssi                 }\n" \
           f"name:          {self.name                 }\n" \
           f"operationMode: {self.operationMode        }\n" \
           f"serviceUUID:   {self.serviceUUID          }\n" \
           f"deviceType:    {self.deviceType.__str__() }\n" \
           f"payload:       {self.payload              }\n" \
           f"validated:     {self.validated            }\n"


def fillScanDataFromAdvertisement(advertisement: Advertisement, validated: bool):
    data = ScanData()

    data.address        = advertisement.address.lower()
    data.rssi           = advertisement.rssi
    data.name           = advertisement.name
    data.operationMode  = advertisement.operationMode
    data.serviceUUID    = advertisement.serviceUUID
    data.payload        = advertisement.serviceData.payload
    data.deviceType     = advertisement.serviceData.deviceType
    data.validated      = validated

    return data