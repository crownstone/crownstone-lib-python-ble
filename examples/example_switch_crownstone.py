#!/usr/bin/env python3

"""An example that turns on a Crownstone with given MAC address."""

import argparse
from crownstone_ble import CrownstoneBle

parser = argparse.ArgumentParser(description='Search for any Crownstone and print their information')
parser.add_argument('-H', '--hci', dest='hciIndex', type=int, nargs='?', default=0,
        help='The hci index of the BLE chip.')
parser.add_argument('-k', '--keyfile', dest='keyFile', type=str, nargs='?', default='example_key_file.txt',
        help='The json file with keys.')
parser.add_argument('macAddress', type=str,
        help='The bluetooth MAC address of Crownstone to switch.')
parser.add_argument('switchCmd', type=int, default=1,
        help='Turn on/off [1/0].')

args = parser.parse_args()

print("===========================================\n\nStarting Example\n\n===========================================")

# Initialize the Bluetooth Core.
core = CrownstoneBle(hciIndex=args.hciIndex)
core.loadSettingsFromFile(args.keyFile)

print("Connecting to", args.macAddress)

core.connect(args.macAddress)

switchVal = 0
if args.switchCmd > 0:
        switchVal = 100
print("Set switch to", switchVal)
core.control.setSwitch(switchVal)

print("Disconnect")
core.control.disconnect()

core.shutDown()

print("===========================================\n\nFinished Example\n\n===========================================")

