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
  --bleAdapterAddress [I]        bleAdapterAddress of the BLE chip you want to use (linux only). This is usually a mac address.
  --keyFile KEYFILE     The json file with key information, expected values:
                        admin, member, guest, basic,serviceDataKey,
                        localizationKey, meshApplicationKey, and
                        meshNetworkKey
```

## Tool config

This is the tool config format. It is shown in /config/tool_config.template.json.

#### Obtaining keys

Go to [my.crownstone](my.crownstone.rocks) and copy the access token to your clipboard.
Click of the [Crownstone REST API explorer](https://my.crownstone.rocks/explorer/), and set your access tokes.
Now you are able to make calls to the API.

To get your sphere keys go to the *users/me* tab, click the *try it out* button, and copy your ID from the response body.
With this ID you can access your keys on the */users/{id}/keysV2* tab. Fill your ID into the form and the response body should display the keys and key types. These have to be formatted like shown bellow.
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
  "bleAdapterAddress": null
}
```
#### absolutePathToKeyFile
If this is defined, the keys are ignored. The tool will look for a key_file at that path instead.

#### keys
These are the keys that belong to your sphere. They are used to decrypt the advertisements and to encrypt the communication during connections.

#### bleAdapterAddress
The bleAdapterAddress of the BLE chip you want the library to use.


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

| command&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | explanation |
|--------- | --- |
| --bleAdapterAddress    | bleAdapterAddress of the BLE chip you want to use (linux only). This is usually a mac address. |
| --keyFile     | The json file with key information, expected values: admin, member, guest, basic, serviceDataKey, localizationKey, meshApplicationKey, and meshNetworkKey |
| --configFile  | The json all data required to configure the tools. See the template file or the definition above for more information. |

## Available tools

Currently, available tools are:
### scan_any_crownstones.py
This will scan for any ble items available. Additional parameters are:
#### --verbose      
> Verbose will show the full advertisement content, not just a single line summary.
#### --macFilter      
> Optional mac filter to only show results for this mac address.
  
### scan_known_crownstones.py
This will scan for any Crownstones in your Sphere. This requires the keys you set to match those on the Crownstones. Additional parameters are:
#### --verbose      
> Verbose will show the full advertisement content, not just a single line summary.
#### --macFilter      
> Optional mac filter to only show results for this mac address.

### switch_crownstone.py
This will scan for any Crownstones in your Sphere. This requires the keys you set to match those on the Crownstones. Additional parameters are:
#### --bleAddress
> The MAC address of the Crownstone you want to switch. This is required if you do not switch via broadcast.
#### --switchTo
> ##### MANDATORY
> The switch state. It is either between 0 and 100, or 255. 0 is off, 1 .. 99 is dimming, 100 is fully on, 255 is on to whatever behaviour thinks it should be.


### upload_microapp.py
TODO: finalize and document
