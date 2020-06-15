#!/usr/bin/env python3

import argparse
from crownstone_ble import CrownstoneBle

parser = argparse.ArgumentParser(description='Search for any Crownstone and print their information')
parser.add_argument('--hciIndex', dest='hciIndex', metavar='I', type=int, nargs='?', default=0,
        help='The hci-index of the BLE chip')
parser.add_argument('keyFile', 
        help='The json file with key information, expected values: admin, member, guest, basic,' + 
        'serviceDataKey, localizationKey, meshApplicationKey, and meshNetworkKey')

args = parser.parse_args()

print("===========================================\n\nStarting Example\n\n===========================================")
print("\nThis is an example that scans for any Crownstone, and prints the results.\n")

# Initialize the Bluetooth Core.
core = CrownstoneBle(hciIndex=args.hciIndex)
core.loadSettingsFromFile(args.keyFile)

print("Searching for Crownstones in range, this will take a while.\n")

crownstonesInRange = core.getCrownstonesByScanning()

for stoneInRange in crownstonesInRange:
    print(stoneInRange)

# clean up all pending processes
print("\nCore shutdown\n\n")
core.shutDown()

print("===========================================\n\nFinished Example\n\n===========================================")

