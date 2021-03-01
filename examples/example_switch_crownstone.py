"""An example that turns on a Crownstone with given MAC address."""
import asyncio
from crownstone_ble import CrownstoneBle

# Initialize the Bluetooth Core.
core = CrownstoneBle(hciIndex=0)

# We're loading some default encryption keys into the library. These keys can be 16 character ASCII, or 32 character hexstrings.
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")

async def switch_crownstone():
    # Connecting to AA:BB:CC:DD:EE:FF
    await core.connect('AA:BB:CC:DD:EE:FF')

    # Switch this Crownstone off
    await core.control.setSwitch(0)

    # sleep for 1 second before we switch again
    await asyncio.sleep(1)

    # Switch this Crownstone fully on
    await core.control.setSwitch(100)

    # We're done now, disconnect
    await core.control.disconnect()

    core.shutDown()

# this is where we actually start running the example
# Python does not allow us to run async functions like they're normal functions.
# Since we support Python3.6 as a minimum we can't use asyncio.run (introduced in 3.7)
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(switch_crownstone())
except KeyboardInterrupt:
    # this catches the CONTROL+C case, which can otherwise result is arbitrary interrupt errors.
    print("Closing the procedure.")
