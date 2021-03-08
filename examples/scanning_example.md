# Scanning for Crownstones

This example will scan for Crownstones in your sphere. The sphere is identified by the keys you load into the library.

Here is the full example code, we'll go over the parts below:

```python
import asyncio

from crownstone_ble import CrownstoneBle, BleEventBus, BleTopics

# Initialize the Bluetooth Core.
core = CrownstoneBle()

# We're loading some default encryption keys into the library. These keys can be 16 character ASCII, or 32 character hexstrings.
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")

def showNewData(data):
    print(f"New data received! \n{data}" )
    print("-------------------")


BleEventBus.subscribe(BleTopics.newDataAvailable, showNewData)

async def scan():
    await core.startScanning(60)
    await core.shutDown()

# this is where we actually start running the example
# Python does not allow us to run async functions like they're normal functions.
# Since we support Python3.6 as a minimum we can't use asyncio.run (introduced in 3.7)
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scan())
except KeyboardInterrupt:
    # this catches the CONTROL+C case, which can otherwise result is arbitrary interrupt errors.
    print("Closing the procedure.")
```

## Step by step explanation

### Imports

These are the modules that we use in this example. Asyncio provides the API for using async/await methods. Finally, we import the CrownstoneBle lib, the eventbus and the topics we can subscribe to.
```python
import asyncio

from crownstone_ble import CrownstoneBle, BleEventBus, BleTopics
```

### Initialization
This creates an instance of the library and loads your sphere's keys into it.
```python
core = CrownstoneBle()
core.setSettings("adminKeyForCrown", "memberKeyForHome", "basicKeyForOther", "MyServiceDataKey", "aLocalizationKey", "MyGoodMeshAppKey", "MyGoodMeshNetKey")
```

### Subscription
In order to actually get data when a Crownstone is scanned, we need to subscribe to a topic on the eventbus.
We create a small function which just prints the data here for example purposes.

In this case we've subscribed to the `BleTopics.newDataAvailable` topic. You could also subscribe to other events. For this see the documentation.
```python
def showNewData(data):
    print(f"New data received! \n{data}" )
    print("-------------------")


BleEventBus.subscribe(BleTopics.newDataAvailable, showNewData)
```

### Async scanning
Since the entire library used async methods for all asynchronous processes, we need to wrap the actual usage inside an async function.
This is how Python does this. If you don't know how it works, look it up online. 

This method will scan for 60 seconds, during which the events will come in, and be printed by the `showNewData` method.
After this, the lib will shut down.
```python
async def scan():
    await core.startScanning(60)
    await core.shutDown()
```


### Running async code
We wrap this part in a try-except in order to catch the SIGINT interrupts (like control+c on linux) and close the example without large errors.
`If we use asyncio.run, this will not work reliably.`
```python
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scan())
except KeyboardInterrupt:
    # this catches the CONTROL+C case, which can otherwise result is arbitrary interrupt errors.
    print("Closing the procedure.")
```
