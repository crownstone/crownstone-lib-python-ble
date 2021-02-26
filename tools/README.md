# Tools
 
These tools are meant to be used as quick-access to common functionality. These are more advanced examples, which mostly consist of
support code in order to be configurable.

The difference between examples and tools is that the examples are meant to show how the library is used. These are meant for documentation purposes,
not as readily executable scripts. Because each sphere has different keys and differences between environments these are not simply executable.

Tools are configured via:
- tool_config.json
    - You can find a template of this in the /config folder. Fill it with your settings in order for all tools to work.
- key_file.json
    - You can choose to use a key_file.json in a different location on your computer if you don't want to put keys in a repository (even though tool_config.json is in .gitignore). You can configure your tool_config to do this.
- command line arguments
    - These override the tool_config
```
--help            show this help message and exit
  --hciIndex [I]        The hci-index of the BLE chip
  --keyFile KEYFILE     The json file with key information, expected values:
                        admin, member, guest, basic,serviceDataKey,
                        localizationKey, meshApplicationKey, and
                        meshNetworkKey
  --scanBackEnd {Bluepy,Aio}
                        This is either "Bluepy" or "Aio". This determines
                        which backend is used for scanning.
  --sphereUID SPHEREUID
                        This is the uint8 value sphereId which is used for
                        broadcast switches. Until then it is not required.
```

## Tool config

This is the tool config format. It is shown in /config/tool_config.template.json.
```
{
  "absolutePathToKeyFile": null,
  "keys": {
    "admin":              "adminKeyForCrown",
    "member":             "memberKeyForHome",
    "basic":              "basicKeyForOther",
    "serviceDataKey":     "MyServiceDataKey",
    "localizationKey":    "aLocalizationKey",
    "meshApplicationKey": "MyGoodMeshAppKey",
    "meshNetworkKey":     "MyGoodMeshNetKey"
  },
  "sphereUID": null,
  "hciIndex": 0,
  "scanBackEnd": "Bluepy"
}
```
#### absolutePathToKeyFile
If this is defined, the keys are ignored. The tool will look for a key_file at that path instead.

#### keys
These are the keys that belong to your sphere. They are used to decrypt the advertisements and to encrypt the communication during connections.

#### sphereUID
This is the uint8 value sphereId which is used for broadcast switches. For anything else, this value is not required.

#### hciIndex
The hci-index of the BLE chip you want the library to use.

#### scanBackEnd
Determine which scan backend you prefer. It can be either "Bluepy" or "Aio". If you have issues with scans, try the other one.


## Key file
This is the format of the key_file.json. You can use it via the absolutePathToKeyFile config or via the keyFile command line argument.
```
{
  "admin":              "adminKeyForCrown",
  "member":             "memberKeyForHome",
  "basic":              "basicKeyForOther",
  "serviceDataKey":     "MyServiceDataKey",
  "localizationKey":    "aLocalizationKey",
  "meshApplicationKey": "MyGoodMeshAppKey",
  "meshNetworkKey":     "MyGoodMeshNetKey"
}
```

## commandLine arguments
These arguments are available for all tools. A tool may have different arguments as well, those are listed as additional parameters below the tool.

| command&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | explanation |
|--------- | --- |
| --hciIndex    | The hci-index of the BLE chip |
| --keyFile     | The json file with key information, expected values: admin, member, guest, basic, serviceDataKey, localizationKey, meshApplicationKey, and meshNetworkKey |
| --configFile  | The json all data required to configure the tools. See the template file or the definition above for more information. |
| --scanBackEnd | This is either "Bluepy" or "Aio". This determines which backend is used for scanning. |
| --sphereUID   | This is the uint8 value sphereId which is used for broadcast switches. Until then it is not required. |

## Available tools

Currently available tools are:
### scan_any_crownstones.py
This will scan for any ble items available. Additional parameters are:
#### --verbose      
> Verbose will show the full advertisement content, not just a single line summary.
  
### scan_known_crownstones.py
This will scan for any Crownstones in your Sphere. This requires the keys you set to match those on the Crownstones. Additional parameters are:
#### --verbose      
> Verbose will show the full advertisement content, not just a single line summary.
  
### switch_crownstone.py
This will scan for any Crownstones in your Sphere. This requires the keys you set to match those on the Crownstones. Additional parameters are:
#### --targetAddress
> The MAC address of the Crownstone you want to switch. This is required if you do not switch via broadcast.
#### --crownstoneId
> The CrownstoneId [1 .. 255] of the Crownstone you want to switch. This is required if you do not switch via connection.
#### --broadcast
> Determine if you want to broadcast the switch command or do it via BLE connection. If this is not set, the switch will be done via connection.
#### --switchTo
> ##### MANDATORY
> The switch state. It is either between 0 and 100, or 255. 0 is off, 1 .. 99 is dimming, 100 is fully on, 255 is on to whatever behaviour thinks it should be.