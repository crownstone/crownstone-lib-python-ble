#!/usr/bin/env python3

""" Experimental tool to upload a microapp to a Crownstone. """

import asyncio
import logging
from os import path
import datetime
import pprint

from crownstone_ble import CrownstoneBle, BleEventBus, BleTopics
from tools.util.config import getToolConfig, loadKeysFromConfig, setupDefaultCommandLineArguments, macFilterPassed

tool_version = "1.0.0"


def checkFilePath(path_to_file, filename):
    if path_to_file is None or filename is None:
        return None

    full_path = path.join(path_to_file, filename)
    if not path.exists(full_path):
        return None

    return full_path

def findDfuFile(path_to_file, filename):
    checkedPath = checkFilePath(path_to_file,filename)
    if checkedPath is not None:
        return checkedPath

    checkedPath = checkFilePath(path_to_file + "/dfu_images", filename)
    if checkedPath is not None:
        return checkedPath

    return None

def overwriteDfuConfWithArgIfAvailable(conf, parsed_args, argname):
    """
    Overwrites the 'dfu' section of tool_config.json with commandline arguments when given argname is available.
    """
    arg_val = getattr(parsed_args, argname)
    if arg_val is not None:
        conf['dfu'][argname] = arg_val

def validateDfuConf(file_path, conf):
    """
    Checks if the dfu_images files exist and adjusts conf to have the full paths rather than just filenames.
    DFU files are also found if they are put in /file_path/dfu_images/.
    """
    if conf['dfu'] is None:
        raise ValueError("'dfu' section of conf not found")

    zipFile = conf['dfu']['zipFile']
    binFile = conf['dfu']['binFile']
    datFile = conf['dfu']['datFile']

    if zipFile is not None:
        if binFile is not None or datFile is not None:
            raise ValueError("if zipFile is specified, cannot specify binFile and/or datFile")

        zipFilePath = findDfuFile(file_path, zipFile)
        if zipFilePath is None:
            raise ValueError(F"parameter zipFile set, but file {zipFile} not found")
        conf['dfu']['zipFile'] = zipFilePath

        return True

    if binFile is not None and datFile is not None:
        binFilePath = findDfuFile(file_path, binFile)
        if binFilePath is None:
            raise ValueError(F"parameter binFile set, but file {binFile} not found")
        conf['dfu']['binFile'] = binFilePath

        datFilePath = findDfuFile(file_path, datFile)
        if datFilePath is None:
            raise ValueError(F"parameter datFile set, but file {datFile} not found")
        conf['dfu']['datFile'] = datFilePath

        return True

    raise ValueError("need either a zip file or both a bin and a dat file for dfu")

def toolSetup():
    parser = setupDefaultCommandLineArguments('Scan for any Crownstones continuously and print the results.')
    parser.add_argument('-a', '--bleAddress', required=True, help='The MAC address/handle of the Crownstone you want to connect to')
    parser.add_argument('-z', '--zipFile', default=None, help='zip file describing the binary to upload')
    parser.add_argument('-b', '--binFile', default=None, help='Binary of the application to upload')
    parser.add_argument('-d', '--datFile', default=None, help='Dat file describing the binary to upload')

    try:
        file_path = path.dirname(path.realpath(__file__))
        [tool_config, parsed_args] = getToolConfig(file_path, parser)
    except Exception as e:
        print("ERROR", e)
        quit()

    overwriteDfuConfWithArgIfAvailable(tool_config, parsed_args, 'zipFile')
    overwriteDfuConfWithArgIfAvailable(tool_config, parsed_args, 'binFile')
    overwriteDfuConfWithArgIfAvailable(tool_config, parsed_args, 'datFile')

    try:
        validateDfuConf(file_path, tool_config)
    except ValueError as e:
        print("ERROR dfu conf validation failed", e)
        quit()

    # create the library instance
    print(f'Initializing tool with bleAdapterAddress={tool_config["bleAdapterAddress"]}')
    cs_ble = CrownstoneBle(bleAdapterAddress=tool_config["bleAdapterAddress"])

    # load the encryption keys into the library
    try:
        loadKeysFromConfig(cs_ble, tool_config)
    except Exception as e:
        print("ERROR", e)
        quit()

    return tool_config, cs_ble, parsed_args

async def terminate(cs_ble):
    print("terminating crownstone bluetooth core")
    await cs_ble.disconnect()
    await cs_ble.shutDown()

async def main(cs_ble, conf):
    printer = pprint.PrettyPrinter(indent=4)

    print("Main")
    printer.pprint(conf)

    # ----------------------------------------
    # set up the transport layer
    # ----------------------------------------
    dfu_transport = None
    # ble_backend = DfuTransportBle(serial_port=str(port),
    #                               att_mtu=att_mtu,
    #                               target_device_name=str(name),
    #                               target_device_addr=str(address))
    # ble_backend.register_events_callback(DfuEvent.PROGRESS_EVENT, update_progress)
    # dfu = Dfu(zip_file_path=package, dfu_transport=ble_backend, connect_delay=connect_delay)

    # ----------------------------------------
    # send init packet
    with open(conf['dfu']['datFile'], 'rb') as f:
        fileContent = f.read()
        dfu_transport.send_init_packet(fileContent)

    # send firmware file
    with open(conf['dfu']['binFile'], 'rb') as f:
        fileContent = f.read()
        dfu_transport.send_firmware(fileContent)

    dfu_transport.close()

    # await core.connect(args.bleAddress)
    # chunkSize = 192
    # # await core._dev.uploadMicroapp(appData, appIndex, chunkSize)


    while True:
        await asyncio.sleep(1)
        print("main loop sleeps")

    await terminate(cs_ble)


if __name__ == "__main__":
    conf, cs_ble, parsed_args = toolSetup()

    try:
        # asyncio.run does not work here.
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(cs_ble, conf))
    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        terminate()
