# Crownstone BLE

### This only works on linux due to the usage of BlueZ.


Since the Crownstone communicates through BLE, we can use BLE to tell it to do things!

This library works with Python 3.5 and higher. It does not work with Python 3.4...

# Requirements

We need libbluetooth-dev for developing with BLE.

```
sudo apt-get install build-essential libbluetooth-dev libglib2.0-dev python3-setuptools python3-dev
```

# Installing Crownstone BLE

If you want to use python virtual environments, take a look at the [README_VENV](/README_VENV.MD)

You can use the setup.py to install CrownstoneBLE. If you are on other platforms than Linux, you can use setup.py to install just Crownstone.

```
sudo python3 setup.py install
```

Allow non-sudo use of the ble scanner

```
sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/local/lib/python3.7/site-packages/bluepy/bluepy-helper
```

# Running Example

You either have to run example scripts as `sudo`:

```
sudo python3 ./examples/example_continuous_scanning.py
```

Or you have to manually give permissions first:

```
sudo setcap 'cap_net_raw,cap_net_admin+eip' ./examples/example_continuous_scanning.py
python3 ./examples/example_continuous_scanning.py
```

# Documentation

To use Crownstone BLE, you first import it from crownstone_ble.

```python
from crownstone_ble import CrownstoneBle

ble = CrownstoneBle(hciIndex=0)
```

CrownstoneBle is composed of a number of top level methods and modules for specific commands. We will first describe these top level methods.


##### `__init__(hciIndex=0)`
> When initializing the CrownstoneBle class, you can provide an hciIndex. On linux, 0 means /dev/hci0, 1 /dev/hci1 etc. Usually 0 is the right one. You can check which one you need with:
> ```
> hciconfig
> ```
> The constructor is not explicitly called with __init__, but like this:
>```python
>ble = CrownstoneBle(hciIndex=0)
>```


##### `isCrownstoneInSetupMode(address: string, scanDuration=3)`
> This will scan (blocking) for scanDuration. After which it will return True or False, depending if the Crownstone with this address (like "f7:19:a4:ef:ea:f6") is in setup mode or not.

##### `shutDown()`
> Shut down the BLE module. This is should be done on closing your script

##### `setSettings(adminKey: string, memberKey: string, basicKey: string, serviceDataKey: string, localizationKey: string, meshApplicationKey: string, meshNetworkKey: string, referenceId="PythonLib")`
> The Crownstone uses encryption by default. There are 3 keys used. You can find more information on that in the [protocol](https://github.com/crownstone/bluenet/blob/master/docs/PROTOCOL.md).
These keys are 16 characters long like "adminKeyForCrown" or 32 characters as a hex string like "9332b7abf19b86ff48156d88c687def6". The referenceId is optional. If you know what you're doing, you can disable the encryption but it should never be required.


##### `loadSettingsFromFile(path: string)`
> As an alternative to using setSettings, you can load it from a json file. The path is relative to the script being executed. An example of this json file is:
>```
>{
>  "admin":  "adminKeyForCrown",
>  "member": "memberKeyForHome",
>  "basic":  "basicKeyForOther",
>  "serviceDataKey":  "MyServiceDataKey",
>  "localizationKey":  "aLocalizationKey",
>  "meshApplicationKey":  "MyGoodMeshAppKey",
>  "meshNetworkKey":  "MyGoodMeshNetKey",
>}
>```

##### `connect(address: string)`
> This will connect to the Crownstone with the provided MAC address. You get get this address by scanning or getting the nearest Crownstone. More on this below.

##### `setupCrownstone(address: string, sphereId: int, crownstoneId: int, meshDeviceKey: string, ibeaconUUID: string, ibeaconMajor: uint16, ibeaconMinor: uint16)`
> New Crownstones are in setup mode. In this mode they are open to receiving encryption keys. This method facilitates this process. No manual connection is required.
> - address is the MAC address.
> - sphereId is a uint8 id for this Crownstone's sphere (Required for FW 3.0.0+)
> - crownstoneId is a uint8 id for this Crownstone
> - meshDeviceKey is a 16 character string (Required for FW 3.0.0+)
> - ibeaconUUID is a string like "d8b094e7-569c-4bc6-8637-e11ce4221c18"
> - ibeaconMajor is a number between 0 and 65535
> - ibeaconMinor is a number between 0 and 65535

##### `disconnect()`
> This will disconnect from the connected Crownstone.

##### `getCrownstonesByScanning(scanDuration=3)`
> This will scan for scanDuration in seconds and return an array of the Crownstone it has found. This is an array of dictionaries that look like this:
>```
>{
>    "address": string,      # mac address like "f7:19:a4:ef:ea:f6"
>    "setupMode": boolean,   # is this Crownstone in setup mode?
>    "validated": boolean,   # does this Crownstone share our encryption key set?
>    "rssi": Float           # average of the rssi of this Crownstone. If None, there have been no valid measurements.
>}
>```
>This array can be directly put in the 'addressesToExclude' field of the 'getNearest..' methods.

##### `startScanning(scanDuration=3)`
> This will start scanning for Crownstones in a background thread. The scanDuration denotes how long we will scan for. Once scanning is active, Topic.advertisement events will be triggered with the advertisements of the Crownstones that share our encryption keys or are in setup mode.

##### `stopScanning()`
> This will stop an active scan.

##### `getNearestCrownstone(rssiAtLeast=-100, scanDuration=3, returnFirstAcceptable=False, addressesToExclude=[])`
> This will search for the nearest Crownstone. It will return ANY Crownstone, not just the ones sharing our encryption keys.
> - rssiAtLeast, you can use this to indicate a maximum distance
> - scanDuration, the amount of time we scan (in seconds)
> - returnFirstAcceptable, if this is True, we return on the first Crownstone in the rssiAtLeast range. If it is False, we will scan for the timeout duration and return the closest one.
> - addressesToExclude, this is an array of either address strings (like "f7:19:a4:ef:ea:f6") or an array of dictionaries that each contain an address field (like what you get from "getCrownstonesByScanning").

##### `getNearestValidatedCrownstone(rssiAtLeast=-100, scanDuration=3, returnFirstAcceptable=False, addressesToExclude=[])`
> Same as getNearestCrownstone but will only search for Crownstones with the same encryption keys.

##### `getNearestSetupCrownstone(rssiAtLeast=-100, scanDuration=3, returnFirstAcceptable=False, addressesToExclude=[])`
> Same as getNearestCrownstone but will only search for Crownstones in setup mode.


## Control Module

The modules contain groups of methods. You can access them like this:
```python
from crownstone_ble import CrownstoneBle

# initialize the Bluetooth Core
ble = CrownstoneBle()

# set the switch stat eusing the control module
ble.connect(address) # address is a mac address
ble.control.setSwitch(0)
ble.disconnect()
```


Methods:

##### `setSwitch(switchVal: int)`
> You can switch the Crownstone. 0 for off, 100 for on, between 0 and 100 to dim. There are also special values to be found in SwitchValSpecial. If you want to dim, make sure dimming is enabled. You can enable this using the allowDimming method.
##### `setRelay(turnOn: bool)`
> DEVELOPMENT ONLY: you can switch the relay. True for on, False for off. Use the setSwitch instead.
##### `setDimmer(intensity)`
> DEVELOPMENT ONLY: you can switch the IGBTs. 0 for off, 100 for on, in between for dimming. Use the setSwitch instead.
##### `commandFactoryReset()`
> Assuming you have the encryption keys, you can use this method to put the Crownstone back into setup mode.
##### `allowDimming(allow: bool)`
> Enable or disable dimming on this Crownstone. Required if you want to dim with setSwitchState.
##### `disconnect()`
> Tell the Crownstone to disconnect from you. This can help if your Bluetooth stack does not reliably disconnect.
##### `lockSwitch(lock: bool)`
> Lock the switch. If locked, it's switchState cannot be changed.
##### `reset()`
> Restart the Crownstone.


## State Module

This is used to get state variables from the Crownstone. [https://github.com/crownstone/bluenet/blob/master/docs/PROTOCOL.md#state-packet-1]

The modules contain groups of methods. You can access them like this:
```python
from crownstone_ble import CrownstoneBle

# initialize the Bluetooth Core
ble = CrownstoneBle()

# set the switch state using the control module
ble.connect(address)
switchstate = ble.state.getSwitchState()
ble.disconnect()
```


##### `getSwitchState()`
> Get the switch state as SwitchState class.
##### `getTime()`
> Get the time on the Crownstone as a timestamp since epoch in seconds. This has been corrected for location.


## EventBus

You can obtain the eventBus directly from the lib:

```
from CrownstoneLib import CrownstoneEventBus, Topics
```

##### `subscribe(TopicName: enum, functionPointer)`
> Returns a subscription ID that can be used to unsubscribe again with the unsubscribe method

##### `unsubscribe(subscriptionId: number)`
> This will stop the invocation of the function you provided in the subscribe method, unsubscribing you from the event.

These can be used like this:

```python

# simple example function to print the data you receive
def showNewData(data):
	print("received new data: ", data)


# Set up event listeners
CrownstoneEventBus.subscribe(Topics.newDataAvailable, showNewData)

# unsubscribe again
CrownstoneEventBus.unsubscribe(subscriptionId)
```

## Events

These events are available for the BLE part of this lib:

##### `Topics.newDataAvailable`
> This is a topic with a summary of the data of an advertisement. If you care about the power usage, you can get it from here.
 For the full advertisement, you can use the Topics.advertisement as shown below.
> Data format is a dictionary with the fields shown below:
>```python
> {
>     id:                           int    # crownstone id (0-255)
>     setupMode:                    bool   # is in setup mode
>     switchState:                  int
>     temperature:                  int    # chip temp in Celcius
>     powerFactor:                  int    # factor between real and apparent
>     powerUsageReal:               int    # power usage in watts (W)
>     powerUsageApparent:           int    # power usage in VA
>     accumulatedEnergy:            int
>     timestamp:                    int    # time on Crownstone seconds since epoch with locale correction
>     dimmingAvailable:             bool   # dimming is available for use (it is not in the first 60 seconds after boot)
>     dimmingAllowed:               bool   # this Crownstone can dim
>     switchLocked:                 bool   # this Crownstone is switch-locked
>     hasError:                     bool   # this crownstone has an error, if the crownstone has an error, the errors: {} dict is only valid if errorMode: true. This boolean is always valid.
>     errorMode:                    bool   # summary type errorMode : the errors JSON is valid. This alternates with normal advertisements
>     errors: {
>         overCurrent:              bool
>         overCurrentDimmer:        bool
>         temperatureChip:          bool
>         temperatureDimmer:        bool
>         dimmerOnFailure:          bool
>         dimmerOffFailure:         bool
>         bitMask:                  int
>     }
>     timeIsSet:                    bool   # this crownstone knows what time it is
> }
>```


##### `Topics.advertisement`
> Data format is a dictionary with the fields shown below:
>```python
> {
>   name: string
>   rssi: int
>   address: string   # mac address
>   serviceUUID: string
>   serviceData: {
>     opCode:                       int
>     dataType:                     int
>     stateOfExternalCrownstone:    int    # adv contains state of external crownstone
>     hasError:                     bool   # this crownstone has an error
>     setupMode:                    bool   # is in setup mode
>     id:                           int    # crownstone id (0-255)
>     switchState:                  int
>     flagsBitmak:                  int
>     temperature:                  int    # chip temp
>     powerFactor:                  int    # factor between real and appearent
>     powerUsageReal:               int    # usage in watts (W)
>     powerUsageApparent:           int    # usage in VA
>     accumulatedEnergy:            int
>     timestamp:                    int    # time on Crownstone seconds since epoch with locale correction
>     dimmingAvailable:             bool   # dimming is available for use (it is not in the first 60 seconds after boot)
>     dimmingAllowed:               bool   # this Crownstone can dim
>     switchLocked:                 bool   # this Crownstone is switch-locked
>     errorMode:                    bool   # advertisement type errorMode : the errors JSON is valid. This alternates with normal advertisements
>     errors: {
>         overCurrent:              bool
>         overCurrentDimmer:        bool
>         temperatureChip:          bool
>         temperatureDimmer:        bool
>         dimmerOnFailure:          bool
>         dimmerOffFailure:         bool
>         bitMask:                  int
>     }
>     uniqueElement:                int    # something that identifies this advertisement uniquely. Can be used to skip duplicate payloads
>     timeIsSet:                    bool   # this crownstone knows what time it is
> }
>```



# Troubleshooting

### installation
old request module (ImportError: cannot import name 'DependencyWarning') --> check [https://github.com/nickoala/telepot/issues/80]

cant find bluetooth.h
```
sudo apt install libbluetooth-dev
```

/bluez-5.47/attrib/gatt.c:190: undefined reference to `bswap_128'\n/tmp/ccT6fQZS.o: In function `get_uuid128':\n/home/pi/gits/bluepy/bluepy/./bluez-5.47/attrib/gatt.c:204: undefined reference to `bswap_128'\ncollect2: error: ld returned 1 exit status\nMakefile:28: recipe for target 'bluepy-helper' failed\nmake: *** [bluepy-helper] Error 1\nmake: Leaving directory '/home/pi/gits/bluepy/bluepy'\n"
You will need to manually install bluez
```
sudo apt purge bluez
wget http://www.kernel.org/pub/linux/bluetooth/bluez-5.47.tar.xz
tar -xf bluez-5.47.tar.xz
cd bluez-5.47

sudo apt-get install libical-dev
./configure --prefix=/usr --mandir=/usr/share/man --sysconfdir=/etc --localstatedir=/var --enable-library --disable-udev
make
sudo make install
```

ZipImportError: bad local file header --> update python-setuptools

helper not found --> go into the bluepy folder and sudo make -B

## Bluetooth on Linux

If bluetooth seems stuck, try
sudo rfkill block bluetooth
sudo rfkill unblock bluetooth

### running
Something about threading when setup is complete --> you don't have Python 3.5


