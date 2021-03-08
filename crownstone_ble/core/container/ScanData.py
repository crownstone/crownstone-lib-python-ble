class ScanData:

    def __init__(self):
        self.address       = None
        self.rssi          = None
        self.name          = None
        self.operationMode = None
        self.deviceType    = None
        self.payload       = None
        self.validated     = None

    def __str__(self):
        return \
           f"address:       {self.address              }\n" \
           f"rssi:          {self.rssi                 }\n" \
           f"name:          {self.name                 }\n" \
           f"operationMode: {self.operationMode        }\n" \
           f"deviceType:    {self.deviceType.__str__() }\n" \
           f"payload:       {self.payload              }\n" \
           f"validated:     {self.validated            }\n"
