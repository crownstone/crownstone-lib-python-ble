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
    print(f'{data["address"]} - {data["name"]} - {data["rssi"]} - {data["serviceUUID"]}')

# this CAN be used for more information. This is used when verbose is on.
def printFullAdvertisements(data):
    print("Scanned device:", json.dumps(data, indent=2))

if args.verbose:
    BleEventBus.subscribe(BleTopics.advertisement, printAdvertisements)
else:
    BleEventBus.subscribe(BleTopics.advertisement, printFullAdvertisements)

# this will start scanning
for i in range(20):
	# note: cannot use large values for startScanning. See doc.
	print("Scanning for Crownstones in your sphere..")
	core.startScanning(3)

core.shutDown()
