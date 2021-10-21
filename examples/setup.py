#!/usr/bin/env python3

"""
Example that looks for a Crownstone in setup mode, and performs the setup with dummy values.
After the setup, the Crownstone will be factory reset, so it returns to setup mode.
"""

import asyncio

from crownstone_core.Enums import CrownstoneOperationMode
from crownstone_ble import CrownstoneBle
from crownstone_core.Exceptions import CrownstoneException

# Initialize the Bluetooth Core.
core = CrownstoneBle()

# We're loading some default encryption keys into the library. These keys can be 16 character ASCII, or 32 character hexstrings.
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")

async def setup_procedure():
    print("Searching for the nearest setup Crownstone...")
    nearestStone = await core.getNearestSetupCrownstone()

    if nearestStone is None:
        print("No stones found in setup mode, stopping the example.")
        await core.shutDown()
        return
    print(f"Found a Crownstone in setup mode.")

    print(f"Setup Crownstone with MAC address {nearestStone.address}, using dummy IDs and keys.")
    await core.setupCrownstone(
        nearestStone.address,
        crownstoneId=1,
        sphereId=1,
        meshDeviceKey="IamTheMeshKeyJey",
        ibeaconUUID="1843423e-e175-4af0-a2e4-31e32f729a8a",
        ibeaconMajor=123,
        ibeaconMinor=456
    )
    print(f"Setup complete!")

    try:
        print(f"Waiting for Crownstone to reboot and show up in normal mode...")
        await core.waitForMode(nearestStone.address, CrownstoneOperationMode.NORMAL, scanDuration=10)
        print(f"Success!")
    except CrownstoneException as e:
        print(f"Did not see the Crownstone in normal mode, setup up probably failed: {e}")

    print(f"Reset the Crownstone back into setup mode just for the sake of the example.")

    print(f"Connecting...")
    await core.connect(nearestStone.address)

    print(f"Connected, perform factory reset.")
    await core.control.commandFactoryReset()
    print(f"Factory reset complete!")

    try:
        print(f"Waiting for Crownstone to reboot and show up in setup mode...")
        await core.waitForMode(nearestStone.address, CrownstoneOperationMode.SETUP, scanDuration=10)
    except CrownstoneException as e:
        print(f"Did not see the Crownstone in setup mode, factory reset probably failed: {e}")

    # Clean up all pending processes.
    print("All done! Shutting down.")
    await core.shutDown()

# This is where we actually start running the example.
# Python does not allow us to run async functions like they're normal functions.
try:
    asyncio.run(setup_procedure())
except KeyboardInterrupt:
    # this catches the CONTROL+C case, which can otherwise result is arbitrary interrupt errors.
    print("Closing the procedure.")
