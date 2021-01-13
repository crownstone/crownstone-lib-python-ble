#!/usr/bin/env python3

"""An example that scans for your Crownstones"""

import time

import json

# Function that's called when new information is received from Crownstones with use the keys you provide in core.setSettings
from crownstone_ble import CrownstoneBle


def showNewData(data):
    print("New data received!")
    print(json.dumps(data, indent=2))
    print("-------------------")


# Initialize the Bluetooth Core.
# Fill in the correct hciIndex, see the readme.
# Fill in the correct keys, see the readme.
core = CrownstoneBle(hciIndex=0)

keys = ["adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey",
        "MyGoodMeshAppKey", "MyGoodMeshNetKey"]
print("We're loading some default encryption keys into the library:", ", ".join(keys))
core.setSettings(*keys)

for i in range(20):
	# note: cannot use large values for startScanning. See doc.
	print("Scanning for Crownstones..")
	core.startScanning(3)

core.shutDown()
