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
print("We're loading some default encryption keys into the library: \"adminKeyForCrown\", \"memberKeyForHome\", \"basicKeyForOther\", \"MyServiceDataKey\", \"aLocalizationKey\", \"MyGoodMeshAppKey\", \"MyGoodMeshNetKey\".\n")
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")


print("Scanning for Crownstones..")
core.startScanning(60)
core.shutDown()
