#!/usr/bin/env python3

import json, sys
from os import path

from crownstone_ble import CrownstoneBle, BleEventBus, BleTopics
from util.config import getToolConfig, loadKeysFromConfig, setupDefaultCommandLineArguments, macFilterPassed

parser = setupDefaultCommandLineArguments('Scan for any Crownstones continuously and print the results.')
parser.add_argument('--verbose', default=False,
                    help='Verbose will show the full advertisement content, not just a single line summary.')
parser.add_argument('--macFilter', default=None, type=str,
                    help='Optional mac filter to only show results for this mac address.')

try:
    file_path = path.dirname(path.realpath(__file__))
    [tool_config, args] = getToolConfig(file_path, parser)
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


# this prints a small overview of all incoming scans.
def printAdvertisements(data):
    if macFilterPassed(args.macFilter, data["address"]):
        print(f'{data["address"]} {data["name"]} {data["rssi"]} serviceUUID = 0x{data["serviceUUID"]:02x}')

# this CAN be used for more information. This is used when verbose is on.
def printFullAdvertisements(data):
    if macFilterPassed(args.macFilter, data["address"]):
        print("Scanned device:", json.dumps(data, indent=2))

if args.verbose:
    BleEventBus.subscribe(BleTopics.rawAdvertisement, printFullAdvertisements)
else:
    BleEventBus.subscribe(BleTopics.rawAdvertisement, printAdvertisements)

try:
    # this will start scanning
    print("Scanning for any ble devices with service data for 1 minute...")
    core.startScanning(60)
except KeyboardInterrupt:
    print("Stopping scanner...")

core.shutDown()
