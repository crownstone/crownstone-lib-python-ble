#!/usr/bin/env python3
from aioblescan import aioblescan

class AioCrownstoneParser(object):

    def __init__(self, hciEvent):
        self.hciEvent = hciEvent
        self.address = None
        self.rssi = None
        self.serviceUUID = None
        self.name = None
        self.valueText = None
        self.valueArr = None

        self.hasAdvertisement = False
        self.dataParser(self.hciEvent)

    def dataParser(self, data):
        for d in data.payload:
            if isinstance(d, aioblescan.HCI_CC_Event):
                pass
            elif isinstance(d, aioblescan.Byte):
                pass
                # print("Byte", d.name, d.val)
            elif isinstance(d, aioblescan.UIntByte):
                pass
                # print("UIntByte", d.name, d.val)
            elif isinstance(d, aioblescan.EnumByte):
                pass
                # print("EnumByte", d.name, d.val)
            elif isinstance(d, aioblescan.MACAddr):
                self.address = d.val
                # print("MACAddr", d.name, d.val)
            elif isinstance(d, aioblescan.IntByte):
                if d.name == 'rssi':
                    self.rssi = d.val
                # print("IntByte", d.name, d.val)
            elif isinstance(d, aioblescan.Itself):
                # print("Itself", d.name, d.val)
                self.valueText = d.val
                self.valueArr  = self.dataToBytes(d.val)
            elif isinstance(d, aioblescan.NBytes):
                self.serviceUUID = self.dataToNum(d.val)
            elif isinstance(d, aioblescan.String):
                self.name = d.val
                # print("String", d.name, d.val)
            elif isinstance(d, aioblescan.BitFieldByte):
                pass
                # print("BitFieldByte", d.name, d._val)
            elif isinstance(d, aioblescan.Adv_Data):
                self.dataParser(d)
            elif isinstance(d, aioblescan.HCI_LE_Meta_Event):
                self.dataParser(d)
            elif isinstance(d, aioblescan.HCI_LEM_Adv_Report):
                self.hasAdvertisement = True
                self.dataParser(d)
            else:
                pass
                # print(d)

    def dataToBytes(self, data):
        arr = []
        for b in data:
            arr.append(b)

        return arr

    def dataToNum(self, data):
        res = 0
        counter = len(data)-1
        for b in data:
            res += b << 8*counter
            counter -= 1
        return res


    def show(self):
        if self.hasAdvertisement:
            print("Address:", self.address, "RSSI:", self.rssi, "Length:", len(self.valueArr), "ServiceUUID:", hex(self.serviceUUID), "Data:", self.valueArr, "Name:", self.name)
