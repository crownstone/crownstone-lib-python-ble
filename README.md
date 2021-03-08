# Crownstone BLE

We're using Bleak as bluetooth backend, which supports Windows, MacOS and Linux.

Since the Crownstone communicates through BLE, we can use BLE to tell it to do things!

This library works with Python 3.7 and higher.


# Installing the library

If you want to use python virtual environments, take a look at the [README_VENV](/README_VENV.MD)

We use `pip3` in the example below because pip is usually the python 2 client. If you're using virtual environments, it could be that pip3 does not exist there. In that case, use pip.
```
pip3 install crownstone_ble
```

You can also build the library from the project itself by:

```
sudo python3 setup.py install
```

# Async functions

This library uses async methods. This is part of Python and uses the asyncio core module to do this. Async methods must be awaited.
If you're unsure about how to use these, there's a million guides and tutorials online. We will assume you know how to use these in the rest of the documentation.

# Documentation

To use Crownstone BLE, you first import it from crownstone_ble.

```python
from crownstone_ble import CrownstoneBle

ble = CrownstoneBle(bleAdapterAddress="00:32:FA:DE:15:02")
```

CrownstoneBle is composed of a number of top level methods and modules for specific commands. We will first describe these top level methods.

### `__init__(bleAdapterAddress=None)`
 When initializing the CrownstoneBle class, you can provide an bleAdapterAddress if you're on linux. You can get these addressed by running:
 ```
 hcitool dev
 ```
 These addresses are in the "00:32:FA:DE:15:02" format.
 The constructor is not explicitly called with __init__, but like this:
```python
ble = CrownstoneBle(bleAdapterAddress="00:32:FA:DE:15:02")
```
On other platforms you can't currently define which bleAdapter to use.

<br/>

### `async isCrownstoneInSetupMode(address: string, scanDuration=3)`
This will scan (blocking) for scanDuration. After which it will return True or False, depending if the Crownstone with this address (like "f7:19:a4:ef:ea:f6") is in setup mode or not.

<br/>

### `async shutDown()`
Shut down the BLE module. This is should be done on closing your script.

<br/>

### `setSettings(adminKey: string, memberKey: string, basicKey: string, serviceDataKey: string, localizationKey: string, meshApplicationKey: string, meshNetworkKey: string, referenceId="PythonLib")`
The Crownstone uses encryption by default. There are 3 keys used. You can find more information on that in the [protocol](https://github.com/crownstone/bluenet/blob/master/docs/PROTOCOL.md).
These keys are 16 characters long like "adminKeyForCrown" or 32 characters as a hex string like "9332b7abf19b86ff48156d88c687def6". The referenceId is optional. If you know what you're doing, you can disable the encryption but it should never be required.

<br/>

### `loadSettingsFromFile(path: string)`
As an alternative to using setSettings, you can load it from a json file. The path is relative to the script being executed. An example of this json file is:
```
{
 "admin":  "adminKeyForCrown",
 "member": "memberKeyForHome",
 "basic":  "basicKeyForOther",
 "serviceDataKey":  "MyServiceDataKey",
 "localizationKey":  "aLocalizationKey",
 "meshApplicationKey":  "MyGoodMeshAppKey",
 "meshNetworkKey":  "MyGoodMeshNetKey",
}
```

<br/>

### `async connect(address: string)`
This will connect to the Crownstone with the provided MAC address. You get get this address by scanning or getting the nearest Crownstone. More on this below.

<br/>

### `async setupCrownstone(address: string, sphereId: int, crownstoneId: int, meshDeviceKey: string, ibeaconUUID: string, ibeaconMajor: uint16, ibeaconMinor: uint16)`
New Crownstones are in setup mode. In this mode they are open to receiving encryption keys. This method facilitates this process. No manual connection is required.
- address is the MAC address.
- sphereId is a uint8 id for this Crownstone's sphere (Required for FW 3.0.0+)
- crownstoneId is a uint8 id for this Crownstone
- meshDeviceKey is a 16 character string (Required for FW 3.0.0+)
- ibeaconUUID is a string like "d8b094e7-569c-4bc6-8637-e11ce4221c18"
- ibeaconMajor is a number between 0 and 65535
- ibeaconMinor is a number between 0 and 65535

<br/>

### `async disconnect()`
This will disconnect from the connected Crownstone.

<br/>

### `async getCrownstonesByScanning(scanDuration=3)`
This will scan for scanDuration in seconds and return an array of the Crownstone it has found. This is an array of dictionaries that look like this:
```
{
   "address": string,      # mac address like "f7:19:a4:ef:ea:f6"
   "setupMode": boolean,   # is this Crownstone in setup mode?
   "validated": boolean,   # if True, this Crownstone belongs to your Sphere (ie. it can be decrypted by the provided keys).
   "rssi": Float           # average of the rssi of this Crownstone. If None, there have been no valid measurements.
}
```
This array can be directly put in the 'addressesToExclude' field of the 'getNearest..' methods.

<br/>

### `async startScanning(scanDuration=3)`
This will start scanning for Crownstones in a background thread. The scanDuration denotes how long we will scan for.
Once scanning is active, BleTopics.advertisement events will be triggered with the advertisements of the
Crownstones that share our encryption keys or are in setup mode.

<br/>

### `async stopScanning()`
This will stop an active scan.

<br/>

### `async getNearestCrownstone(rssiAtLeast=-100, scanDuration=3, returnFirstAcceptable=False, addressesToExclude=[]) -> ScanData or None`
This will search for the nearest Crownstone. It will return ANY Crownstone, not just the ones sharing our encryption keys.
- rssiAtLeast, you can use this to indicate a maximum distance
- scanDuration, the amount of time we scan (in seconds)
- returnFirstAcceptable, if this is True, we return on the first Crownstone in the rssiAtLeast range. If it is False, we will scan for the timeout duration and return the closest one.
- addressesToExclude, this is an array of either address strings (like "f7:19:a4:ef:ea:f6") or an array of dictionaries that each contain an address field (like what you get from "getCrownstonesByScanning").

If anything was found, the ScanData will be returned. [This datatype is defined here.](#ScanData)

<br/>

### `async getNearestValidatedCrownstone(rssiAtLeast=-100, scanDuration=3, returnFirstAcceptable=False, addressesToExclude=[]) -> ScanData or None`
Same as getNearestCrownstone but will only search for Crownstones with the same encryption keys.
If anything was found, the ScanData will be returned. [This datatype is defined here.](#ScanData)

<br/>

### `async getNearestSetupCrownstone(rssiAtLeast=-100, scanDuration=3, returnFirstAcceptable=False, addressesToExclude=[]) -> ScanData or None`
Same as getNearestCrownstone but will only search for Crownstones in setup mode.
If anything was found, the ScanData will be returned. [This datatype is defined here.](#ScanData)


# Control Module

The modules contain groups of methods. You can access them like this:
```python
import asyncio
from crownstone_ble import CrownstoneBle

# initialize the Bluetooth Core
ble = CrownstoneBle()

async def example():
    # set the switch stat eusing the control module
    await ble.connect(address) # address is a mac address (or handle on OSX)
    await ble.control.setSwitch(0)
    await ble.disconnect()

loop = asyncio.get_event_loop()
loop.run_until_complete(example())
```


Methods:

### `async setSwitch(switchVal: int)`
You can switch the Crownstone. 0 for off, 100 for on, between 0 and 100 to dim. There are also special values to be found in SwitchValSpecial. If you want to dim, make sure dimming is enabled. You can enable this using the allowDimming method.
### `async commandFactoryReset()`
Assuming you have the encryption keys, you can use this method to put the Crownstone back into setup mode.
### `async allowDimming(allow: bool)`
Enable or disable dimming on this Crownstone. Required if you want to dim with setSwitchState.
### `async disconnect()`
Tell the Crownstone to disconnect from you. This can help if your Bluetooth stack does not reliably disconnect.
### `async lockSwitch(lock: bool)`
Lock the switch. If locked, it's switchState cannot be changed.
### `async reset()`
Restart the Crownstone.

<br /> 

### `async setRelay(turnOn: bool)`
DEVELOPMENT ONLY: you can switch the relay. True for on, False for off. Use the setSwitch instead.
### `async setDimmer(intensity)`
DEVELOPMENT ONLY: you can switch the IGBTs. 0 for off, 100 for on, in between for dimming. Use the setSwitch instead.

# State Module

This is used to get state variables from the Crownstone. [https://github.com/crownstone/bluenet/blob/master/docs/PROTOCOL.md#state-packet-1]

The modules contain groups of methods. You can access them like this:
```python
import asyncio
from crownstone_ble import CrownstoneBle

# initialize the Bluetooth Core
ble = CrownstoneBle()

async def example():
    # set the switch state using the control module
    await ble.connect(address)
    switchstate = await ble.state.getSwitchState()
    await ble.disconnect()

loop = asyncio.get_event_loop()
loop.run_until_complete(example())
```


### `async getSwitchState()`
Get the switch state as SwitchState class.
### `async getTime()`
Get the time on the Crownstone as a timestamp since epoch in seconds. This has been corrected for location.



# EventBus

## API

### `once(TopicName: string, functionPointer)`
This will subscribe for a single event. After this event, the listener will be removed automatically. It still returns a unsubscriptionId if you want to cleanup before the event occurs.

### `subscribe(TopicName: string, functionPointer)`
Returns a subscription ID that can be used to unsubscribe again with the unsubscribe method

### `unsubscribe(subscriptionId: number)`
This will stop the invocation of the function you provided in the subscribe method, unsubscribing you from the event.


## Events
These events are available for the BLE part of this lib:

### `BleTopics.newDataAvailable`
This is a topic to which events are posted which are unique. The same message will be repeated on the advertisement and the rawAdvertisement packets.

### `BleTopics.rawAdvertisement`
This topic will broadcast all incoming Crownstone scans, including those that do not belong to your sphere (ie. can't be decrypted with your keys). 

### `BleTopics.advertisement`
This topic will broadcast all incoming Crownstone scans which belong to your sphere (ie. which can be decrypted with your keys).


### Data format
All these events contain the same data format:
<a href="#ScanData" />
```python
class ScanData:

    def __init__(self):
        self.address       = None    # this is the handle of the device that broadcast the advertisement. This is usually a MAC address, but on OSX it is a handle.
        self.rssi          = None    # the signal strength indicator
        self.name          = None    # name of the device
        self.operationMode = None    # CrownstoneOperationMode enum (SETUP, NORMAL, DFU, UNKNOWN)
        self.serviceUUID   = None    # the UUID of the scanned service
        self.deviceType    = None    # type of Crownstone 
        self.payload       = None    # See below.
        self.validated     = None    # Whether your provided keys could decrypt this advertisement
```
These fields are always filled. The payload will differ depending on what sort of data is advertised. [You can see all possible types here.](https://github.com/crownstone/crownstone-lib-python-core/tree/master/crownstone_core/packets/serviceDataParsers/containers)
These payloads all have a `type` field [which is defined here.](https://github.com/crownstone/crownstone-lib-python-core/blob/master/crownstone_core/packets/serviceDataParsers/containers/elements/AdvTypes.py)
Payloads come in these flavours:

- [CROWNSTONE_STATE](https://github.com/crownstone/crownstone-lib-python-core/blob/master/crownstone_core/packets/serviceDataParsers/containers/AdvCrownstoneState.py) 
- [CROWNSTONE_ERROR](https://github.com/crownstone/crownstone-lib-python-core/blob/master/crownstone_core/packets/serviceDataParsers/containers/AdvErrorPacket.py) 
- [EXTERNAL_STATE](https://github.com/crownstone/crownstone-lib-python-core/blob/master/crownstone_core/packets/serviceDataParsers/containers/AdvExternalCrownstoneState.py)   
- [EXTERNAL_ERROR](https://github.com/crownstone/crownstone-lib-python-core/blob/master/crownstone_core/packets/serviceDataParsers/containers/AdvExternalErrorPacket.py)   
- [ALTERNATIVE_STATE](https://github.com/crownstone/crownstone-lib-python-core/blob/master/crownstone_core/packets/serviceDataParsers/containers/AdvAlternativeState.py)
- [HUB_STATE](https://github.com/crownstone/crownstone-lib-python-core/blob/master/crownstone_core/packets/serviceDataParsers/containers/AdvHubState.py)        
- [MICROAPP_DATA](https://github.com/crownstone/crownstone-lib-python-core/blob/master/crownstone_core/packets/serviceDataParsers/containers/AdvMicroappData.py)    
- [SETUP_STATE](https://github.com/crownstone/crownstone-lib-python-core/blob/master/crownstone_core/packets/serviceDataParsers/containers/AdvCrownstoneSetupState.py)    



## Usage
You can obtain the eventBus directly from the lib:
```python
from crownstone_ble import BleEventBus, BleTopics

# simple example function to print the data you receive
def showNewData(data):
	print("received new data: ", data)

# Set up event listeners
subscriptionId = BleEventBus.subscribe(BleTopics.newDataAvailable, showNewData)

# unsubscribe again
BleEventBus.unsubscribe(subscriptionId)
```



## Bluetooth on Linux

If bluetooth seems stuck, try
sudo rfkill block bluetooth
sudo rfkill unblock bluetooth

### running
Something about threading when setup is complete --you don't have Python 3.5


