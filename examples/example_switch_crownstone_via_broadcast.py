#!/usr/bin/env python3

"""An example that turns on a Crownstone with given MAC address."""

from crownstone_ble import CrownstoneBle

print("===========================================\n\nStarting Example\n\n===========================================")

# Initialize the Bluetooth Core.
# Fill in the correct hciIndex, see the readme.
# Fill in the correct keys, see the readme.
core = CrownstoneBle(hciIndex=0)
print("We're loading some default encryption keys into the library: \"adminKeyForCrown\", \"memberKeyForHome\", \"basicKeyForOther\", \"MyServiceDataKey\", \"aLocalizationKey\", \"MyGoodMeshAppKey\", \"MyGoodMeshNetKey\".\n")
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")

core.setSettings(
    "74158b0fcd8f9e881af352155dfe8591",
    "5a8af34ecaccffc9cbc330d2020b73b8",
    "d28c6fa28b15fe45616c1a9097a718db",
    "fde40811c90ce46823d7ae38d5124cd3",
    "6633f4e46601b17c604588f0d9b47725",
    "5a293bdb0a5af45b2b1fdb42dde18ac5",
    "7ae4f61214077fa8f04fc4d61f736fc7"
)

# get the SphereUID from somewhere
sphereUID = 253
# select the uid of the crownstone to switch
crownstoneId = 5
state = 0 # 0 = off, you can choose anything between [0..1]

core.broadcast.switchCrownstone(sphereUID, crownstoneId, state)

core.shutDown()

print("===========================================\n\nFinished Example\n\n===========================================")

