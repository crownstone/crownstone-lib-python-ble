import threading

from crownstone_ble.topics.BleTopics import BleTopics

from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.core.modules.StoneAdvertisementTracker import StoneAdvertisementTracker
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics

"""
Class that validates advertisements from topic 'SystemBleTopics.rawAdvertisementClass'.

Each MAC address will have its own 'StoneAdvertisementTracker'.
A separate thread will call 'tick()' at a regular interval.

On each 'SystemBleTopics.rawAdvertisementClass', this class will:
- Call 'update()' on the StoneAdvertisementTracker of that MAC address.
- Emit 'Topics.advertisement', if the address is validated.
- Emit 'Topics.newDataAvailable' if the address is validated, and the rawAdvertisement has service data.

TODO:
- Use locks, currently only 'tick()' acquires a lock, so that doesn't prevent concurrency issues.
- Rename this class, as it also keeps up the average RSSI.
- Use advertisements without service data to update the average RSSI.
"""
class Validator:

    def __init__(self):
        BleEventBus.subscribe(SystemBleTopics.rawAdvertisementClass, self.checkAdvertisement)
        self.tickTimer = None
        self._lock = threading.Lock()
        self.scheduleTick()
        self.trackedCrownstones = {}


    def scheduleTick(self):
        if self.tickTimer is not None:
            self.tickTimer.cancel()

        self.tickTimer = threading.Timer(1, lambda: self.tick())
        self.tickTimer.start()


    def tick(self):
        with self._lock:
            allKeys = []
            # we first collect keys because we might delete items from this list during ticks
            for key, trackedStone in self.trackedCrownstones.items():
                allKeys.append(key)

            for key in allKeys:
                self.trackedCrownstones[key].tick()

        self.scheduleTick()


    def removeStone(self, address):
        del self.trackedCrownstones[address]


    def checkAdvertisement(self, advertisement):
        if advertisement.address not in self.trackedCrownstones:
            self.trackedCrownstones[advertisement.address] = StoneAdvertisementTracker(lambda: self.removeStone(advertisement.address))
        
        self.trackedCrownstones[advertisement.address].update(advertisement)

        # forward all scans over this topic. It is located here instead of the delegates so it would be easier to convert the json to classes.
        BleEventBus.emit(BleTopics.rawAdvertisement, advertisement.getDictionary())
        if self.trackedCrownstones[advertisement.address].verified:
            BleEventBus.emit(BleTopics.advertisement, advertisement.getDictionary())

            if advertisement.hasScanResponse:
                BleEventBus.emit(BleTopics.newDataAvailable, advertisement.getSummary())



    def shutDown(self):
        if self.tickTimer is not None:
            self.tickTimer.cancel()
