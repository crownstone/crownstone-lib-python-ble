#!/usr/bin/env python3

"""An example that switches a Crownstone via broadcast."""

import argparse
from crownstone_ble import CrownstoneBle

parser = argparse.ArgumentParser(description='Switch a Crownstone via broadcast.')
parser.add_argument('-H', '--hciIndex', dest='hciIndex', type=int, nargs='?', default=0,
        help='The hci index of the BLE chip')
parser.add_argument('-U', '--sphere', dest='sphereUid', type=int, nargs='?', default=0,
        help='The sphere UID')
parser.add_argument('-I', '--id', dest='stoneId', type=int, nargs='?', default=0,
        help='The crownstone ID')
parser.add_argument('-k', '--keyfile', dest='keyFile', type=str, nargs='?', default='example_key_file.txt',
        help='The json file with keys.')
parser.add_argument('switchCmd', type=int, default=1,
        help='Turn on/off [1/0].')

args = parser.parse_args()
print("Using hci:", args.hciIndex, ", sphere UID:", args.sphereUid, ", crownstone ID:", args.stoneId, ", key file:", args.keyFile)


print("===========================================\n\nStarting Example\n\n===========================================")

# Initialize the Bluetooth Core.
core = CrownstoneBle(hciIndex=args.hciIndex)
core.loadSettingsFromFile(args.keyFile)

try:
    switchVal = 0
    if args.switchCmd > 0:
        switchVal = 100
    print("Broadcast switch command", switchVal)
    core.broadcast.switchCrownstone(args.sphereUid, args.stoneId, switchVal)
except Exception as err:
    print("Failed to broadcast, maybe try to run with sudo?")
    print("Error:", err)

core.shutDown()

print("===========================================\n\nFinished Example\n\n===========================================")
