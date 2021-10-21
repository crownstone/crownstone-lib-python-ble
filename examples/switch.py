#!/usr/bin/env python3

"""
This example shows you how to switch a Crownstone using the python library.
You can also dim the Crownstone by using  1-99 as values. For that to work, make sure dimming is enabled on the Crownstone.

You may notice that your smartphone switches your Crownstones much quicker.
This is because this library currently only switches via a connection, instead of via a broadcast.

Unfortunately, the macOS version of the library will not be able to use MAC addresses, see: https://github.com/hbldh/bleak/issues/284
In order to find which handle corresponds with which Crownstone, you can first scan for Crownstones, find their Crownstone ID and use that to correlate them.
"""

# Asyncio provides the API for using async/await methods.
import asyncio

# Import the Crownstone BLE library in order to use it.
from crownstone_core.Exceptions import CrownstoneException, CrownstoneBleException

from crownstone_ble import CrownstoneBle


# Initialize the Crownstone BLE library.
core = CrownstoneBle()

# We're loading some dummy encryption keys into the library.
# These keys should be the same as used for setup.
# The keys can be 16 character ASCII, or 32 character hexstrings.
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")

async def switch_crownstone():
    # Change this address to the address of your crownstone.
    # You could use the scanning example to find the address.
    crownstone_address = "AA:BB:CC:DD:EE:FF"

    try:
        print(f"Connecting to {crownstone_address}...")
        await core.connect(crownstone_address)

        print("Connected, switch the Crownstone off.")
        await core.control.setSwitch(0)

        print("Waiting 1 second.")
        await asyncio.sleep(1)

        print("Switch the Crownstone on.")
        await core.control.setSwitch(100)

        print("Done! Disconnect and shut down.")
        await core.control.disconnect()
    except (CrownstoneException, CrownstoneBleException) as e:
        print(e)
        print("")
        print(f"Oops, something went wrong. "
              f"Are you sure you set the correct Crownstone MAC address? "
              f"And did you set the correct keys?")

    await core.shutDown()

# This is where we actually start running the example.
# Python does not allow us to run async functions like they're normal functions.
try:
    asyncio.run(switch_crownstone())
except KeyboardInterrupt:
    # this catches the CONTROL+C case, which can otherwise result in arbitrary interrupt errors.
    print("Stopping the example.")