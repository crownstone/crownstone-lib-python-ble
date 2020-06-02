#!/usr/bin/env python3


import time

from BluenetLib import ScanBackends
from BluenetLib.BLE import BluenetBle

print("===========================================\n\nStarting Example\n\n===========================================")
print("This is an example that looks for a close Crownstone, and attempts to recover it.\n")

# Initialize the Bluetooth Core.
# Fill in the correct hciIndex, see the readme.
core = BluenetBle(hciIndex=0)

print("We're loading some default encryption keys into the library: \"adminKeyForCrown\", \"memberKeyForHome\", \"basicKeyForOther\", \"MyServiceDataKey\", \"aLocalizationKey\", \"MyGoodMeshAppKey\", \"MyGoodMeshNetKey\".\n")
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")

print("Searching for the nearest Crownstone. This is with a threshold of RSSI: -40, so it will use a close available Crownstones.\n")

# get the nearest crownstone in setup mode. We expect it to be atleast within the -70db range
nearestStone = core.getNearestCrownstone(rssiAtLeast=-40, returnFirstAcceptable=True)

print("Search Results:", nearestStone)

if nearestStone is not None:
    # reset the Crownstone back into setup mode
    print("Starting the Factory Reset Process")
    core.control.recovery(nearestStone["address"])
else:
    print("No stones found in setup mode...")
# clean up all pending processes
print("Core shutdown")
core.shutDown()

print("===========================================\n\nFinished Example\n\n===========================================")