#!/usr/bin/env python3

""" Experimental tool to upload a microapp to a Crownstone. """

import asyncio
import logging
from os import path
import datetime

from crownstone_ble import CrownstoneBle, BleEventBus, BleTopics
from tools.util.config import getToolConfig, loadKeysFromConfig, setupDefaultCommandLineArguments, macFilterPassed

tool_version = "1.0.0"


def toolSetup():
    parser = setupDefaultCommandLineArguments('Scan for any Crownstones continuously and print the results.')
    parser.add_argument('-a', '--bleAddress', required=True, help='The MAC address/handle of the Crownstone you want to connect to')
    parser.add_argument('-z', '--zipFile', default=None, help='zip file describing the binary to upload')
    parser.add_argument('-b', '--binFile', default=None, help='Binary of the application to upload')
    parser.add_argument('-d', '--datFile', default=None, help='Dat file describing the binary to upload')

    # return None, None, None
    try:
        file_path = path.dirname(path.realpath(__file__))
        [ble_config, parsed_args] = getToolConfig(file_path, parser)
    except Exception as e:
        print("ERROR", e)
        quit()

    # create the library instance
    print(f'Initializing tool with bleAdapterAddress={ble_config["bleAdapterAddress"]}')
    crownstoneBle = CrownstoneBle(bleAdapterAddress=ble_config["bleAdapterAddress"])

    # load the encryption keys into the library
    try:
        loadKeysFromConfig(crownstoneBle, ble_config)
    except Exception as e:
        print("ERROR", e)
        quit()

    return ble_config, crownstoneBle, parsed_args

async def terminate(cs_ble):
    print("terminating crownstone bluetooth core")
    await cs_ble.disconnect()
    await cs_ble.shutDown()

async def main(cs_ble, args):
    print("Main")
    # with open(args.file, "rb") as f:
    #     appData = f.read()
    #
    # print("First 32 bytes of the binary:")
    # print(list(appData[0:32]))
    #
    # await core.connect(args.bleAddress)
    #
    # chunkSize = 192
    # print(f"{datetime.datetime.now()} Start uploading with chunkSize={chunkSize}")
    # # await core._dev.uploadMicroapp(appData, appIndex, chunkSize)
    # print(f"{datetime.datetime.now()} Upload done")
    #
    # print("Validate..")
    # # await core._dev.validateMicroapp(appIndex)
    # print("Validate done")

    while True:
        await asyncio.sleep(1)
        print("main loop sleeps")

    await terminate(cs_ble)


if __name__ == "__main__":
    conf, cs_ble, parsed_args = toolSetup()

    try:
        # asyncio.run does not work here.
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(cs_ble, parsed_args))
    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        terminate()
