#!/usr/bin/env python3
import asyncio
import logging
from os import path
import datetime

from crownstone_ble import CrownstoneBle, BleEventBus, BleTopics
from util.config import getToolConfig, loadKeysFromConfig, setupDefaultCommandLineArguments, macFilterPassed


parser = setupDefaultCommandLineArguments('Scan for any Crownstones continuously and print the results.')
parser.add_argument('-a', '--bleAddress', required=True, help='The MAC address/handle of the Crownstone you want to connect to')
parser.add_argument('-f', '--file', default=None, help='Microapp binary to upload')
parser.add_argument('-v', '--verbose', default=False,
                    help='Verbose will show the full advertisement content, not just a single line summary.')

#logging.basicConfig(format='%(levelname)-7s: %(message)s', level=logging.DEBUG)

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

async def main():
    print("Main")
    with open(args.file, "rb") as f:
        buf = f.read()

    await core.connect(args.bleAddress)
    # info = await core.control.getMicroappInfo()
    # print(info)

    chunkSize = 192
    print(f"{datetime.datetime.now()} Start upload with chunkSize={chunkSize}")
    await core.control.uploadMicroapp(buf, 0, chunkSize)
    print(f"{datetime.datetime.now()} Upload done")
    await core.disconnect()
    await core.shutDown()

try:
    # asyncio.run does not work here.
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
except KeyboardInterrupt:
    print("Stopping.")
