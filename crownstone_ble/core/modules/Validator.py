from crownstone_ble.core.container.ScanDataUtil import fillScanDataFromAdvertisement
from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.core.modules.StoneAdvertisementTracker import StoneAdvertisementTracker
from crownstone_ble.topics.BleTopics import BleTopics
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics

"""
Class that validates advertisements from topic 'SystemBleTopics.rawAdvertisementClass'.

Each MAC address will have its own 'StoneAdvertisementTracker'.

On each 'SystemBleTopics.rawAdvertisementClass', this class will:
- Call 'update()' on the StoneAdvertisementTracker of that MAC address.
- Emit 'BleTopics.advertisement', if the address is validated.
- Emit 'BleTopics.newDataAvailable' if the address is validated, and the rawAdvertisement has service data.
- Emit 'BleTopics.rawAdvertisement' for all incoming Crownstone messages.

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
        data = fillScanDataFromAdvertisement(advertisement, self.trackedCrownstones[advertisement.address].verified)
        BleEventBus.emit(BleTopics.rawAdvertisement, data)
        if self.trackedCrownstones[advertisement.address].verified:
            BleEventBus.emit(BleTopics.advertisement, data)

            if not self.trackedCrownstones[advertisement.address].duplicate:
                BleEventBus.emit(BleTopics.newDataAvailable, data)
