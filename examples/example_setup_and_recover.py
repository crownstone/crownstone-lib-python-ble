#!/usr/bin/env python3


import time
from crownstone_ble import CrownstoneBle

print("===========================================\n\nStarting Example\n\n===========================================")
print("This is an example that performs the setup of a Crownstone, and then recovers it again.\n")

# Initialize the Bluetooth Core.
# Fill in the correct hciIndex, see the readme.
core = CrownstoneBle(hciIndex=0)


print("We're loading some default encryption keys into the library: \"adminKeyForCrown\", \"memberKeyForHome\", \"basicKeyForOther\", \"MyServiceDataKey\", \"aLocalizationKey\", \"MyGoodMeshAppKey\", \"MyGoodMeshNetKey\".\n")
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")

print("Searching for the nearest setup Crownstone. This is with a threshold of RSSI: -40, so it will use a close available setup Crownstones.\n")
print("Keep in mind that the RSSI in setup mode is low to protect the key exchange so even if you're close, it can still be around -80.\n")

# get the nearest crownstone in setup mode. We expect it to be atleast within the -70db range
nearestStone = core.getNearestSetupCrownstone(rssiAtLeast=-40, returnFirstAcceptable=True)

print("Search Results:", nearestStone)

if nearestStone is not None:
    # setup the nearest Crownstone if we can find one
    print("Starting setup on ", nearestStone["address"])
    core.setupCrownstone(
        nearestStone["address"],
        crownstoneId=1,
        sphereId=1,  #required FW 3+
        meshDeviceKey="IamTheMeshKeyJey",  #required FW 3+
        ibeaconUUID="1843423e-e175-4af0-a2e4-31e32f729a8a",
        ibeaconMajor=123,
        ibeaconMinor=456
    )

    # wait for setup to finish and the crownstone to reboot
    print("Sleeping until Crownstone is in Normal mode and ready.")
    time.sleep(2)

    # reset the Crownstone back into setup mode
    print("Starting the Factory Reset Process")
    core.control.recovery(nearestStone["address"])
    time.sleep(1)
    # print("command disconnect")
    # core.control.disconnect()
else:
    print("No stones found in setup mode...")
# clean up all pending processes
print("Core shutdown")
core.shutDown()

print("===========================================\n\nFinished Example\n\n===========================================")