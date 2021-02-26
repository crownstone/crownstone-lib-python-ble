from crownstone_core.util.JsonFileStore import JsonFileStore
from os import path
import argparse

def setupDefaultCommandLineArguments(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--hciIndex', dest='hciIndex', metavar='I', type=int, nargs='?', default=None,
                        help='The hci-index of the BLE chip')
    parser.add_argument('--keyFile', default=None,
                        help='The json file with key information, expected values: admin, member, guest, basic,' +
                             'serviceDataKey, localizationKey, meshApplicationKey, and meshNetworkKey')
    parser.add_argument('--configFile', default=None,
                        help='The json all data required to configure the tools. See the template file or README.md for more information.')
    parser.add_argument('--scanBackEnd', default=None, choices=["Bluepy", "Aio"],
                        help='This is either "Bluepy" or "Aio". This determines which backend is used for scanning.')
    parser.add_argument('--sphereUID', default=None,
                        help='This is the uint8 value sphereId which is used for broadcast switches. Until then it is not required.')
    return parser



def loadToolConfig(path_to_config):
    fileReader = JsonFileStore(path_to_config)
    data = fileReader.getData()
    return data

def loadKeysFromConfig(ble_lib, tool_config):
    if "absolutePathToKeyFile" in tool_config and tool_config["absolutePathToKeyFile"] is not None:
        if "~" in tool_config["absolutePathToKeyFile"]:
            print("Usage of variables or ~ in the absolutePathToKeyFile is not allowed.")
            print("When executing the tools as sudo (as some might) this would lead to a different file since it would resolve to /root/ instead of /home/<username/.")
            print("To avoid common errors, this is not allowed.")
            raise ValueError("Invalid absolutePathToKeyFile.")
        if path.exists(tool_config["absolutePathToKeyFile"]):
            ble_lib.loadSettingsFromFile(tool_config["absolutePathToKeyFile"])
        else:
            raise FileNotFoundError("The provided path to the keyfile is invalid. Provided:" + tool_config["absolutePathToKeyFile"])
    else:
        if "keys" not in tool_config or tool_config["keys"] is None:
            raise ValueError("The tool_config.json needs keys if the absolutePathToKey is not provided. Check the template.")
        else:
            ble_lib.loadSettingsFromDictionary(tool_config["keys"])

def getToolConfig(file_path, parser):
    config = None
    args = parser.parse_args()
    if args.configFile is not None:
        if path.exists(args.configFile):
            config = loadToolConfig(args.configFile)
        else:
            raise FileNotFoundError("The provided configFile in the commandline argument cannot be found. Double check the path.")

    if config is None:
        # search for the tool config either in the root dir of the tools, or the config dir of the tools.
        # if it's not there, load default settings for hciIndex and scanBackend
        if path.exists(path.join(file_path, "tool_config.json")):
            config = loadToolConfig(path.join(file_path, "tool_config.json"))
        elif path.exists(path.join(file_path, "config", "tool_config.json")):
            config = loadToolConfig(path.join(file_path, "config", "tool_config.json"))
        else:
            config = {"hciIndex": 0, "scanBackEnd": "Bluepy"}

        # as a backup, check if there is a key file in the root of the tools or the config dir of the tools.
        if "absolutePathToKeyFile" not in config and "keys" not in config:
            if path.exists(path.join(file_path, "keyFile.json")):
                config["absolutePathToKeyFile"] = path.join(file_path, "keyFile.json")
            elif path.exists(path.join(file_path, "config", "keyFile.json")):
                config["absolutePathToKeyFile"] = path.join(file_path, "config", "keyFile.json")

    # finally, commandline args will overwrite anything in the tools.
    args = parser.parse_args()
    if args.hciIndex is not None:
        config["hciIndex"] = args.hciIndex
    if args.keyFile is not None:
        if path.exists(args.keyFile):
            config["absolutePathToKeyFile"] = args.keyFile
        else:
            raise FileNotFoundError("The provided keyfile in the commandline argument cannot be found. Double check the path. Provided: " + args.keyFile)
    if args.scanBackEnd is not None:
        config["scanBackEnd"] = args.scanBackEnd
    if args.sphereUID is not None:
        config["sphereUID"] = args.scanBackEnd

    return [config, args]


def macFilterPassed(mac_to_filter_for, adv_mac):
    if mac_to_filter_for is not None:
        if mac_to_filter_for.lower() == adv_mac.lower():
            return True
    else:
        return True
    return False

