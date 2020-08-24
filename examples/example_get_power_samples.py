#!/usr/bin/env python3

"""An example that retrieves power samples from a Crownstone with given MAC address."""

import argparse
from crownstone_ble import CrownstoneBle
from crownstone_core.protocol.BluenetTypes import PowerSamplesType
import traceback

parser = argparse.ArgumentParser(description='Search for any Crownstone and print their information')
parser.add_argument('--hciIndex', dest='hciIndex', metavar='I', type=int, nargs='?', default=0,
        help='The hci-index of the BLE chip')
parser.add_argument('keyFile', 
        help='The json file with key information, expected values: admin, member, guest, basic,' + 
        'serviceDataKey, localizationKey, meshApplicationKey, and meshNetworkKey')
parser.add_argument('bleAddress', 
        help='The BLE address of Crownstone to switch')

args = parser.parse_args()

print("===========================================\n\nStarting Example\n\n===========================================")

# Initialize the Bluetooth Core.
core = CrownstoneBle(hciIndex=args.hciIndex)
core.loadSettingsFromFile(args.keyFile)

try:
    print("Connecting to", args.bleAddress)
    core.connect(args.bleAddress)

    try:
        print("Retrieving power samples..")
        powerSamples = core.debug.getPowerSamples(PowerSamplesType.NOW_UNFILTERED)
        print("Power samples:")
        for samples in powerSamples:
            print(samples.toString())

    except Exception as err:
        print("Failed to get power samples:", err)
#        traceback.print_exc()

    print("Disconnect")
    core.control.disconnect()

except Exception as err:
    print("Failed to connect:", err)



core.shutDown()

print("===========================================\n\nFinished Example\n\n===========================================")
