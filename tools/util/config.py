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
    parser.add_argument('--scanBackEnd', default=None, choices=["Bluepy", "Aio"],
                        help='This is either "Bluepy" or "Aio". This determines which backend is used for scanning.')
    parser.add_argument('--sphereUID', default=None,
                        help='This is the uint8 value sphereId which is used for broadcast switches. Until then it is not required.')
    return parser



def loadToolConfig(path_to_config):
    fileReader = JsonFileStore(path_to_config)
    data = fileReader.getData()
    return data

def loadKeysFromConfig(data, ble_lib):
    if data["absolutePathToKeyFile"] is not None:
        if path.exists(data["absolutePathToKeyFile"]):
            ble_lib.loadSettingsFromFile(data["absolutePathToKeyFile"])
        else:
            raise FileNotFoundError("the provided absolutePathToKeyFile provided is invalid.")
    else:
        if data["keys"] is not None:
            ble_lib.loadSettingsFromDictionary(data)
        else:
            raise ValueError("The tool_config.json needs keys if the absolutePathToKey is not provided. Check the template.")

def getToolConfig(file_path, parser):
    config = None
    if path.exists(path.join(file_path, "tool_config.json")):
        config = loadToolConfig(path.join(file_path, "tool_config.json"))
    elif path.exists(path.join(file_path, "config", "tool_config.json")):
        config = loadToolConfig(path.join(file_path, "config", "tool_config.json"))
    elif path.exists(path.join(file_path, "config", "tool_config.template.json")):
        config = loadToolConfig(path.join(file_path, "config", "tool_config.template.json"))
    else:
        config = {"hciIndex": 0, "scanBackEnd": "Bluepy"}

    args = parser.parse_args()
    if args.hciIndex is not None:
        config["hciIndex"] = args.hciIndex
    if args.keyFile is not None:
        config["absolutePathToKeyFile"] = args.keyFile
    if args.scanBackEnd is not None:
        config["scanBackEnd"] = args.scanBackEnd
    if args.sphereUID is not None:
        config["sphereUID"] = args.scanBackEnd

    return [config, args]



