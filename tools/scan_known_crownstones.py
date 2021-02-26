import json
from os import path

from crownstone_ble import CrownstoneBle, BleEventBus, BleTopics
from util.config import getToolConfig, loadKeysFromConfig, setupDefaultCommandLineArguments

parser = setupDefaultCommandLineArguments('Scan for Crownstones in your sphere and print the results.')
parser.add_argument('--verbose', default=False, help='Verbose will show the full advertisement content, not just a single line summary.')

file_path           = path.dirname(path.realpath(__file__))
[tool_config, args] = getToolConfig(file_path, parser)

# create the library instance
core = CrownstoneBle(hciIndex=tool_config["hciIndex"], scanBackend=tool_config["scanBackEnd"])

# load the encryption keys into the library
loadKeysFromConfig(core, tool_config)

# this prints a small overview of all incoming scans.
def printAdvertisements(data):
    print(f'{data["address"]} {data["name"]} {data["rssi"]} serviceUUID = 0x{data["serviceUUID"]:02x}')

# this CAN be used for more information. This is used when verbose is on.
def printFullAdvertisements(data):
    print("Scanned device:", json.dumps(data, indent=2))

if args.verbose:
    BleEventBus.subscribe(BleTopics.advertisement, printFullAdvertisements)
else:
    BleEventBus.subscribe(BleTopics.advertisement, printAdvertisements)

try:
    # this will start scanning
    print("Scanning for Crownstones in your Sphere with for 1 minute...")
    print("It may take a few seconds before the results come in since it requires a few advertisements to verify if they belong to your Sphere.")
    core.startScanning(60)
except KeyboardInterrupt:
    print("Stopping scanner...")

core.shutDown()
