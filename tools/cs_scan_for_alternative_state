#!/usr/bin/env python3
import asyncio
from os import path

from crownstone_ble.core.container.ScanData import ScanData
from crownstone_core.packets.serviceDataParsers.containers.elements.AdvTypes import AdvType

from crownstone_ble import CrownstoneBle, BleEventBus, BleTopics
from util.config import getToolConfig, loadKeysFromConfig, setupDefaultCommandLineArguments, macFilterPassed

parser = setupDefaultCommandLineArguments('Scan for alternative state packets and print the asset filter master versions when a new datapoint comes in.')
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
print(f'Initializing tool with bleAdapterAddress={tool_config["bleAdapterAddress"]}')
core = CrownstoneBle(bleAdapterAddress=tool_config["bleAdapterAddress"])

# load the encryption keys into the library
try:
    loadKeysFromConfig(core, tool_config)
except Exception as e:
    print("ERROR", e)
    quit()


inMemoryDb = {}
typeDistribution = {}
scansSeen = 0
alternativeStates = 0

# this prints a small overview of all incoming scans.
def printAdvertisements(data: ScanData):
    if data.payload is None:
        return

    global scansSeen
    global alternativeStates
    global inMemoryDb
    global typeDistribution

    scansSeen += 1
    if data.payload.type not in typeDistribution:
        typeDistribution[data.payload.type] = 0
    typeDistribution[data.payload.type] += 1

    if data.payload.type == AdvType.ALTERNATIVE_STATE:
        inMemoryDb[data.payload.crownstoneId] = data.payload.assetFilterMasterVersion
        print(inMemoryDb)
        alternativeStates += 1
    elif scansSeen % 50 == 0:
        print("Processed", scansSeen, "advertisements.", alternativeStates, "found in alternativeState mode.")


BleEventBus.subscribe(BleTopics.advertisement, printAdvertisements)

async def scan():
    print("Starting scan for Crownstones that belong in your sphere. Will print on each alternative state.")
    await core.ble.scan(duration=600)
    await core.shutDown()

try:
    # asyncio.run does not work here.
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scan())
except KeyboardInterrupt:
    print("Closing the test.")
