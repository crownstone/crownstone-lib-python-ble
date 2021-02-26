from os import path

from crownstone_ble import CrownstoneBle
from util.config import getToolConfig, loadKeysFromConfig, setupDefaultCommandLineArguments

parser = setupDefaultCommandLineArguments("Switch a Crownstone, either via connection or via broadcast.")
parser.add_argument('--targetAddress', default=None,  help='The MAC address of the Crownstone you want to switch')
parser.add_argument('--crownstoneId',  default=None,  help='The CrownstoneId (1 .. 255) of the Crownstone you want to switch')
parser.add_argument('--broadcast',     default=False, type=bool, help='Determine if you want to broadcast the switch command or do it via BLE connection. Default will connect.')
parser.add_argument('--switchTo',      required=True, type=int, help='0 .. 100 || 255. Switch the Crownstone. 0 is off, 1 .. 99 is dimming, 100 is fully on, 255 is on to whatever behaviour thinks it should be.')


file_path           = path.dirname(path.realpath(__file__))
[tool_config, args] = getToolConfig(file_path, parser)

if args.broadcast:
    if args.crownstoneId is None:
        raise ValueError("crownstoneId is required to use broadcast.")
    if tool_config["sphereUID"] is None:
        raise ValueError("sphereUID is required to use broadcast.")

elif args.targetAddress is None:
    raise ValueError("targetAddress is required if you do not broadcast.")

# create the library instance
core = CrownstoneBle(hciIndex=tool_config["hciIndex"], scanBackend=tool_config["scanBackEnd"])

# load the encryption keys into the library
loadKeysFromConfig(core, tool_config)


try:
    if args.broadcast:
        core.broadcast.switchCrownstone(tool_config["sphereUID"], args.crownstoneId, args.switchTo)
    else:
        core.connect(args.targetAddress)
        core.control.setSwitch(args.switchTo)
        core.disconnect()
except KeyboardInterrupt:
    print("Stopping switch action...")


core.shutDown()