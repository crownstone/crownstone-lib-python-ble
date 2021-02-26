from crownstone_ble.topics.BleTopics import BleTopics

from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.core.modules.StoneAdvertisementTracker import StoneAdvertisementTracker
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics

"""
Class that validates advertisements from topic 'SystemBleTopics.rawAdvertisementClass'.

Each MAC address will have its own 'StoneAdvertisementTracker'.

On each 'SystemBleTopics.rawAdvertisementClass', this class will:
- Call 'update()' on the StoneAdvertisementTracker of that MAC address.
- Emit 'BleTopics.advertisement', if the address is validated.
- Emit 'BleTopics.newDataAvailable' if the address is validated, and the rawAdvertisement has service data.

TODO:
- Use locks, currently only 'tick()' acquires a lock, so that doesn't prevent concurrency issues. 
    - Alex: Locks removed for ease of use. This is no longer threaded. Tick removed and renamed to cleanupExpiredTrackers
- Rename this class, as it also keeps up the average RSSI.
    - Alex: it doenst though.. the StoneAdvertisementTrackers do that. This one just feeds the StoneAdvertisementTrackers
            Also, rssi average is completely removed since nothing was using it.
- Use advertisements without service data to update the average RSSI.
    - Alex: average RSSI is not used anywhere. removed from class entirely.
    
The threading part is removed. This adds a little overhead since the cleanup is called every checkAdvertisement. On the other hand, not threading is usually no issues.
"""
class Validator:

    def __init__(self):
        BleEventBus.subscribe(SystemBleTopics.rawAdvertisementClass, self.checkAdvertisement)
        self.trackedCrownstones = {}


    def cleanupExpiredTrackers(self):
        allKeys = []
        # we first collect keys because we might delete items from this list during ticks
        for key, trackedStone in self.trackedCrownstones.items():
            allKeys.append(key)

        for key in allKeys:
            self.trackedCrownstones[key].checkForCleanup()


    def removeStone(self, address):
        del self.trackedCrownstones[address]


    def checkAdvertisement(self, advertisement):
        self.cleanupExpiredTrackers()

        if advertisement.address not in self.trackedCrownstones:
            self.trackedCrownstones[advertisement.address] = StoneAdvertisementTracker(lambda: self.removeStone(advertisement.address))

        self.trackedCrownstones[advertisement.address].update(advertisement)

        # forward all scans over this topic. It is located here instead of the delegates so it would be easier to convert the json to classes.
        BleEventBus.emit(BleTopics.rawAdvertisement, advertisement.getDictionary())
        if self.trackedCrownstones[advertisement.address].verified:
            BleEventBus.emit(BleTopics.advertisement, advertisement.getDictionary())

            if advertisement.hasScanResponse:
                BleEventBus.emit(BleTopics.newDataAvailable, advertisement.getSummary())
