#!/usr/bin/env python3

"""An example that turns on a Crownstone with given MAC address."""

import argparse
from crownstone_ble import CrownstoneBle

parser = argparse.ArgumentParser(description='Search for any Crownstone and print their information')
parser.add_argument('--hciIndex', dest='hciIndex', metavar='I', type=int, nargs='?', default=0,
        help='The hci-index of the BLE chip')
parser.add_argument('keyFile', 
        help='The json file with key information, expected values: admin, member, guest, basic,' + 
        'serviceDataKey, localizationKey, meshApplicationKey, and meshNetworkKey')
parser.add_argument('bleAddress', 
        help='The BLE address of Crownstone to switch')
parser.add_argument('switch', type=int,
        help='Turn on/off [1/0]')

args = parser.parse_args()

print("===========================================\n\nStarting Example\n\n===========================================")

# Initialize the Bluetooth Core.
core = CrownstoneBle(hciIndex=args.hciIndex)
core.loadSettingsFromFile(args.keyFile)

print("Connecting to", args.bleAddress)

core.connect(args.bleAddress)

print("Switch on/off", args.switch)
core.control.setSwitchState(args.switch)

print("Disconnect")
core.control.disconnect()

core.shutDown()

print("===========================================\n\nFinished Example\n\n===========================================")

