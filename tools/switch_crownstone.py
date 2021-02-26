#!/usr/bin/env python3

from os import path

from crownstone_ble import CrownstoneBle
from util.config import getToolConfig, loadKeysFromConfig, setupDefaultCommandLineArguments

parser = setupDefaultCommandLineArguments("Switch a Crownstone, either via connection or via broadcast.")
parser.add_argument('--targetAddress', default=None,  help='The MAC address of the Crownstone you want to switch')
parser.add_argument('--crownstoneId',  default=None,  type=int, help='The CrownstoneId (1 .. 255) of the Crownstone you want to switch')
parser.add_argument('--broadcast',     default=False, type=bool, help='Determine if you want to broadcast the switch command or do it via BLE connection. Default will connect.')
parser.add_argument('--switchTo',      required=True, type=int, help='0 .. 100 || 255. Switch the Crownstone. 0 is off, 1 .. 99 is dimming, 100 is fully on, 255 is on to whatever behaviour thinks it should be.')


try:
    file_path = path.dirname(path.realpath(__file__))
    [tool_config, args] = getToolConfig(file_path, parser)

    if args.broadcast:
        if args.crownstoneId is None:
            raise ValueError("crownstoneId is required to use broadcast.")
        if tool_config["sphereUID"] is None:
            raise ValueError("sphereUID is required to use broadcast.")

    elif args.targetAddress is None:
        raise ValueError("targetAddress is required if you do not broadcast.")

except Exception as e:
    print("ERROR", e)
    quit()

# create the library instance
print(f'Initializing tool with hciIndex={tool_config["hciIndex"]}, scanBackend={tool_config["scanBackEnd"]}')
core = CrownstoneBle(hciIndex=tool_config["hciIndex"], scanBackend=tool_config["scanBackEnd"])

# load the encryption keys into the library
try:
    loadKeysFromConfig(core, tool_config)
except Exception as e:
    print("ERROR", e)
    core.shutDown()
    quit()



try:
    if args.broadcast:
        core.broadcast.switchCrownstone(tool_config["sphereUID"], args.crownstoneId, args.switchTo)
    else:
        print("Connecting...")
        core.connect(args.targetAddress)
        print("Connected. Writing...")
        core.control.setSwitch(args.switchTo)
        print("Written. Disconnecting...")
        core.disconnect()
        print("Disconnected.")
except KeyboardInterrupt:
    print("Stopping switch action...")


core.shutDown()