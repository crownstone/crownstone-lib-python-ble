# Switch a Crownstone

This example shows you how to switch a Crownstone using the python library. You can also dim the Crownstone by using  1-99 as values. Make sure dimming is enabled on this Crownstone before you do. If not, anything larger than 0 is just ON.

Here is the full example code, we'll go over the parts below:

```python
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
core = CrownstoneBle(hciIndex=0)
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")
```

### Async wrapper
Since the entire library used async methods for all asynchronous processes, we need to wrap the actual usage inside an async function.
This is how Python does this. If you don't know how it works, look it up online. 
```python
async def switch_crownstone():
    ...
```

### Switching the Crownstone
The Crownstone BLE lib will only interact with Crownstones via Bluetooth connections. You may notice that your smartphone switches your Crownstones much quicker.
This secure broadcast mechanism currently not implemented in this library. If you want to build an integration, like a hub, which should quickly switch the Crownstones, 
we'd like to recommend the UART library combined with the Crownstone USB dongle.

This part of the example will connect to an imaginary MAC address, switch it off, wait, back on, disconnect and shutdown. Unfortunately, the macOS version of the library will not be able to use
MAC addresses. [More information here.](https://github.com/hbldh/bleak/issues/284) 

In order to find which handle corresponds with which Crownstone, you can first scan for Crownstones, find their Crownstone ID and use that to correlate them.
```python
await core.connect('AA:BB:CC:DD:EE:FF')
await core.control.setSwitch(0)
await asyncio.sleep(1)
await core.control.setSwitch(100)
await core.control.disconnect()
core.shutDown()
```

### Running async code
We wrap this part in a try-except in order to catch the SIGINT interrupts (like control+c on linux) and close the example without large errors.
Since we use Python 3.6, we can't use asyncio.run. This means we first get an event loop, and then using that to run the async function we defined.
```python
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(switch_crownstone())
except KeyboardInterrupt:
    # this catches the CONTROL+C case, which can otherwise result is arbitrary interrupt errors.
    print("Closing the procedure.")
```
