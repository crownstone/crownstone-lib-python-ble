import asyncio
import sys
import time

import aioblescan
from crownstone_core.util.LogUtil import tfs

counter = 0
prev = time.time()
start = time.time()



class AioScanner:

    def __init__(self, hciIndex = 0):
        self.event_loop = None
        self.bluetoothControl = None
        self.connection = None
        self.timeRequestStart = 0
        self.eventReceived = False
        self.hciIndex = hciIndex
        self.delegate = None

        self.scanRunning = False

        self.scanDuration = 0

    def withDelegate(self, delegate):
        self.delegate = delegate
        return self

    def start(self, duration):
        self.scanRunning = True
        self.scanDuration = duration
        self.scan()

    def stop(self):
        self.scanRunning = False

    def scan(self, attempt = 0):
        print(tfs(), "Attempt Scanning")
        self.eventReceived = False
        event_loop = asyncio.new_event_loop()
        bluetoothSocket = aioblescan.create_bt_socket(self.hciIndex)
        transportProcess = event_loop._create_connection_transport(bluetoothSocket, aioblescan.BLEScanRequester, None, None)
        self.connection, self.bluetoothControl = event_loop.run_until_complete(transportProcess)

        print(tfs(), "Connection made!")
        self.bluetoothControl.process = self.parsingProcess

        self.timeRequestStart = time.time()
        self.bluetoothControl.send_scan_request()
        print(tfs(), "Scan command sent!")

        alreadyCleanedUp = False

        try:
            event_loop.run_until_complete(self.awaitEventSleep(1))
            if not self.eventReceived:
                if attempt < 10:
                    print(tfs(), 'Retrying... Closing event loop', attempt)
                    self.cleanup(event_loop)
                    alreadyCleanedUp = True
                    self.scan(attempt + 1)
                    return
                else:
                    pass

            event_loop.run_until_complete(self.awaitActiveSleep(self.scanDuration))
        except KeyboardInterrupt:
            print('keyboard interrupt')
        finally:
            print("")
            if not alreadyCleanedUp:
                print(tfs(), 'closing event loop', attempt)
                self.cleanup(event_loop)


    async def awaitEventSleep(self, duration):
        while self.eventReceived == False and duration > 0:
            await asyncio.sleep(0.05)
            duration -= 0.05

    async def awaitActiveSleep(self, duration):
        while self.scanRunning == True and duration > 0:
            await asyncio.sleep(0.05)
            duration -= 0.05

    def cleanup(self, event_loop):
        print(tfs(), "Cleaning up")
        self.bluetoothControl.stop_scan_request()
        self.connection.close()
        event_loop.close()


    def parsingProcess(self, data):
        ev=aioblescan.HCI_Event()
        xx=ev.decode(data)

        hasAdvertisement = self.dataParser(ev)
        if hasAdvertisement and self.delegate is not None:
            self.delegate.handleDiscovery(ev)

    def dataParser(self, data):
        #parse Data required for the scanner
        advertisementReceived = False
        for d in data.payload:
            if isinstance(d, aioblescan.aioblescan.HCI_CC_Event):
                self.checkHCI_CC_EVENT(d)
            elif isinstance(d, aioblescan.Adv_Data):
                advertisementReceived = self.dataParser(d) or advertisementReceived
            elif isinstance(d, aioblescan.HCI_LE_Meta_Event):
                advertisementReceived = self.dataParser(d) or advertisementReceived
            elif isinstance(d, aioblescan.aioblescan.HCI_LEM_Adv_Report):
                self.eventReceived = True
                advertisementReceived = True
        return advertisementReceived


    def checkHCI_CC_EVENT(self, event):
        for d in event.payload:
            if isinstance(d, aioblescan.aioblescan.OgfOcf):
                if d.ocf == b'\x0b':
                    print(tfs(),"Settings received")
                elif d.ocf == b'\x0c':
                    print(tfs(), "Scan command received")
            # if isinstance(d, aioblescan.aioblescan.Itself):
            #     print("byte", d.name)
            # if isinstance(d, aioblescan.aioblescan.UIntByte):
            #     print("UIntByte", d.val)

    def parseAdvertisement(self, decodedHciEvent):
        global counter
        if counter % 50 == 0:
            counter = 0
            print(".")
        else:
            sys.stdout.write(".")
        counter+= 1
        # decodedHciEvent.show()
