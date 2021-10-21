#!/usr/bin/env python3

"""
This example will scan for Crownstones in your sphere, and print their current state, which includes:
- Power usage
- Switch state (on/off/dimmed)
The sphere is identified by the keys you load into the library.
"""

# Asyncio provides the API for using async/await methods.
import asyncio

# Import the Crownstone BLE library in order to use it.
from crownstone_ble import CrownstoneBle, BleEventBus, BleTopics


# Initialize the Crownstone BLE library.
core = CrownstoneBle()

# We're loading some dummy encryption keys into the library.
# These keys should be the same as used for setup.
# The keys can be 16 character ASCII, or 32 character hexstrings.
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")


# In order to actually get data when a Crownstone is scanned, we need to subscribe to a topic on the eventbus.
# We create a small function that just prints the data here for example purposes.
def showNewData(data):
    print("New data received!")
    print(data)
    print("-------------------")

# In this case we've subscribed to the `BleTopics.newDataAvailable` topic. You could also subscribe to other events.
BleEventBus.subscribe(BleTopics.newDataAvailable, showNewData)


# Since the entire library used async methods for all asynchronous processes, we need to wrap the actual usage inside an async function.
# Explaining asyncio is beyond the scope of this example, you should be able to find plenty of information about it elsewhere.
async def scan():
    print("Start scanning for 60 seconds..")
    print("Each time new data from a Crownstone in your sphere (or in setup mode) is scanned, it will be posted to BleTopics.newDataAvailable.")
    await core.startScanning(60)

    print("Done, shutting down.")
    await core.shutDown()


# This is where we actually start running the example.
# Python does not allow us to run async functions like they're normal functions.
try:
    asyncio.run(scan())
except KeyboardInterrupt:
    # this catches the CONTROL+C case, which can otherwise result is arbitrary interrupt errors.
    print("Stopping the example.")