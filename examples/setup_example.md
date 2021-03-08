# Setup a Crownstone

This example shows you how to setup a Crownstone using the python library. Since you don't do it using our consumer app for this setup, it will not show up in there.

Here is the full example code, we'll go over the parts below:

```python
import asyncio
from crownstone_ble import CrownstoneBle

# Initialize the Bluetooth Core.
core = CrownstoneBle()

# We're loading some default encryption keys into the library. These keys can be 16 character ASCII, or 32 character hexstrings.
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")

async def setup_procedure():
    # Searching for the nearest setup Crownstone. This is with a threshold of RSSI: -100, so it will use any available setup Crownstones.
    nearestStone = await core.getNearestSetupCrownstone(rssiAtLeast=-100, returnFirstAcceptable=True)

    # Let's see if we have found a Crownstone in setup mode nearby
    if nearestStone is not None:
        # Setup the nearest Crownstone with a few example parameters.
        await core.setupCrownstone(
            nearestStone.address,
            crownstoneId=1,
            sphereId=1,
            meshDeviceKey="IamTheMeshKeyJey",
            ibeaconUUID="1843423e-e175-4af0-a2e4-31e32f729a8a",
            ibeaconMajor=123,
            ibeaconMinor=456
        )

        # Wait for setup to finish and the crownstone to reboot in normal mode.
        if await core.isCrownstoneInNormalMode(nearestStone.address, scanDuration=10, waitUntilInRequiredMode=True):
            # Reset the Crownstone back into setup mode just for the sake of the example.
            await core.connect(nearestStone.address)

            # now that we're connected, perform the factory reset.
            await core.control.commandFactoryReset()

            # sleep a little to allow the Crownstone to reboot.
            await asyncio.sleep(1)
        else:
            print("Not in normal mode")
    else:
        print("No stones found in setup mode...")

    # clean up all pending processes
    print("Core shutdown")
    await core.shutDown()

# this is where we actually start running the example
# Python does not allow us to run async functions like they're normal functions.
# Since we support Python3.6 as a minimum we can't use asyncio.run (introduced in 3.7)
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_procedure())
except KeyboardInterrupt:
    # this catches the CONTROL+C case, which can otherwise result is arbitrary interrupt errors.
    print("Closing the procedure.")
```

## Step by step explanation

### Imports

These are the modules that we use in this example. 
Asyncio provides the API for using async/await methods. Finally, we import the CrownstoneBle lib in order to use it.
```python
import asyncio
from crownstone_ble import CrownstoneBle
```

### Initialization
This creates an instance of the library and loads your sphere's keys into it.
```python
core = CrownstoneBle()
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")
```

### Async wrapper
Since the entire library used async methods for all asynchronous processes, we need to wrap the actual usage inside an async function.
This is how Python does this. If you don't know how it works, look it up online. 
```python
async def setup_procedure():
    ...
```

### Get nearest Crownstone in setup mode
This will scan for Crownstones nearby using the `getNearestSetupCrownstone` method. If nothing is found, the result would be `None`.
If we have a result, we move on to the next phase.
```python
nearestStone = await core.getNearestSetupCrownstone(rssiAtLeast=-100, returnFirstAcceptable=True)
if nearestStone is not None:
    ...
else:
    print("No stones found in setup mode...")
```

### Performing setup
Now that we found the nearest setup crownstone, we identify it by it's address and use the `setupCrownstone` method to perform setup.
This method uses the keys you set earlier, as well as the method arguments to perform the setup.

You can freely choose the crownstoneId, but ensure that it's unique within your sphere. The sphereId will be used to broadcast switch commands via phones.
More information can be found in the documentation.
```python
# Setup the nearest Crownstone with a few example parameters.
await core.setupCrownstone(
    nearestStone.address,
    crownstoneId=1,
    sphereId=1,
    meshDeviceKey="IamTheMeshKeyJey",
    ibeaconUUID="1843423e-e175-4af0-a2e4-31e32f729a8a",
    ibeaconMajor=123,
    ibeaconMinor=456
)

# Wait for setup to finish and the crownstone to reboot in normal mode.
if await core.isCrownstoneInNormalMode(nearestStone.address, scanDuration=10, waitUntilInRequiredMode=True):
    ...
```
We end by checking if this Crownstone is actually in normal mode after the setup has completed.


### Putting it back into setup mode
For the purpose of a varied example, we will now put it back into setup mode.
```python
# Reset the Crownstone back into setup mode just for the sake of the example.
await core.connect(nearestStone.address)

# now that we're connected, perform the factory reset.
await core.control.commandFactoryReset()

# sleep a little to allow the Crownstone to reboot.
await asyncio.sleep(1)
```

### Cleaning up the lib
When you're all done, call the shutDown method to close any running processes.
```python
# clean up all pending processes
print("Core shutdown")
await core.shutDown()
```

### Running async code
We wrap this part in a try-except in order to catch the SIGINT interrupts (like control+c on linux) and close the example without large errors.
`If we use asyncio.run, this will not work reliably.`
```python
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_procedure())
except KeyboardInterrupt:
    # this catches the CONTROL+C case, which can otherwise result is arbitrary interrupt errors.
    print("Closing the procedure.")
```
