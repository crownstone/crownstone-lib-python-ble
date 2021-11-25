#!/usr/bin/env python3

""" Experimental tool to upload a microapp to a Crownstone. """

import asyncio
import logging
from os import path
import datetime
import pprint
import subprocess


from crownstone_core.Exceptions import CrownstoneBleException

from crownstone_ble import CrownstoneBle, BleEventBus, BleTopics
from tools.dfu.dfu_constants import DFUAdapter
from tools.dfu.dfu_transport_ble import CrownstoneDfuOverBle
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

def overwriteConfWithArgIfAvailable(conf, parsed_args, argname, section = None):
    """
    Overwrites the 'dfu' section of tool_config.json with commandline arguments when given argname is available.
    """
    arg_val = getattr(parsed_args, argname)
    if arg_val is not None:
        if section is not None:
            conf[section][argname] = arg_val
        else:
            conf[argname] = arg_val

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

def validateAddressConf(conf):
    if conf.get('bleAdapterAddress') is None:
        raise ValueError("need bleAdapterAddress for setup of crownstone")

    if conf.get('bleAddress') is None:
        raise ValueError("need bleAddress of target device for dfu")

def loadToolConfig():
    parser = setupDefaultCommandLineArguments('Scan for any Crownstones continuously and print the results.')
    parser.add_argument('-a', '--bleAddress', required=True, help='The MAC address/handle of the Crownstone you want to connect to')
    parser.add_argument('-z', '--zipFile', default=None, help='zip file describing the binary to upload')
    parser.add_argument('-b', '--binFile', default=None, help='Binary of the application to upload')
    parser.add_argument('-d', '--datFile', default=None, help='Dat file describing the binary to upload')

    file_path = path.dirname(path.realpath(__file__))
    [tool_config, parsed_args] = getToolConfig(file_path, parser)

    overwriteConfWithArgIfAvailable(tool_config, parsed_args, 'zipFile', section='dfu')
    overwriteConfWithArgIfAvailable(tool_config, parsed_args, 'binFile', section='dfu')
    overwriteConfWithArgIfAvailable(tool_config, parsed_args, 'datFile', section='dfu')
    overwriteConfWithArgIfAvailable(tool_config, parsed_args, 'bleAddress')

    validateDfuConf(file_path, tool_config)
    validateAddressConf(tool_config)

    return tool_config

async def terminate(cs_ble):
    print("terminating crownstone bluetooth core")
    await cs_ble.disconnect()
    await cs_ble.shutDown()


def validateDeviceIsInDfu(cs_ble):
    print("checking dfu characteristics")
    print("services available:", cs_ble.ble.activeClient.services)
    print("characteristics available:", cs_ble.ble.activeClient.characteristics)
    retval = True
    if not cs_ble.ble.hasCharacteristic(DFUAdapter.CP_UUID.toString()):
        print("dfu control point characteristic missing :", DFUAdapter.CP_UUID.toString())
        retval = False
    if not cs_ble.ble.hasCharacteristic(DFUAdapter.DP_UUID.toString()):
        print("dfu data point characteristic missing :", DFUAdapter.DP_UUID.toString())
        retval = False

    # BleHandler.hasService...

    return retval

async def main(cs_ble, conf):
    printer = pprint.PrettyPrinter(indent=4)

    print("dfu_write_application main() entered with the following config")
    printer.pprint(conf)

    # -----------------------------------------
    # connect and put target device in dfu mode
    # -----------------------------------------

    print("--- DFU constants: ---")
    print("CP_UUID: ", DFUAdapter.CP_UUID.toString())
    print("DP_UUID: ", DFUAdapter.DP_UUID.toString())
    print("----------------------")

    await cs_ble.connect(conf['bleAddress'],timeout=10)
    print("connected to target device")

    if not validateDeviceIsInDfu(cs_ble):
        print("device not in fdu mode, sending dfu command")
        await cs_ble.control.putInDfuMode()
        print("target device command go to DFU sent")
        await cs_ble.ble.waitForPeripheralToDisconnect()
        print("target device disconnected")

        print("attempt to clear the bluetooth cache on your system")
        try:
            output = subprocess.check_output("bluetoothctl -- remove {0}".format(conf['bleAddress']), shell=True)
        except subprocess.CalledProcessError as e:
            print("failed to clear cache using bluetoothhctl")
            print(output)
            print("continueing dfu attempt")

        print("reconnecting")
        await cs_ble.connect(conf['bleAddress'], timeout=10, ignoreEncryption=True)  # reconnect

        print("target device reconnected and should now be ready for dfu")
        if not validateDeviceIsInDfu(cs_ble):
            raise CrownstoneBleException("Device is not in dfu mode")
    else:
        print("already in dfu mode attempting to continu/recover")

    # ----------------------------------------
    # execute dfu
    # ----------------------------------------

    dfu_transport = CrownstoneDfuOverBle(cs_ble)

    print("opening dfu transport")
    await dfu_transport.open()

    print("sending init packet")
    # send init packet
    with open(conf['dfu']['datFile'], 'rb') as f:
        fileContent = f.read()
        await dfu_transport.send_init_packet(fileContent)

    print("sending firmware")
    # send firmware file
    with open(conf['dfu']['binFile'], 'rb') as f:
        fileContent = f.read()
        await dfu_transport.send_firmware(fileContent)

    await dfu_transport.close()

    # chunkSize = 192
    # # await core._dev.uploadMicroapp(appData, appIndex, chunkSize)


    while True:
        await asyncio.sleep(1)
        print("main loop sleeps")

    await terminate(cs_ble)


if __name__ == "__main__":
    conf = loadToolConfig()

    print(f'Initializing tool with bleAdapterAddress={conf["bleAdapterAddress"]}')
    cs_ble = CrownstoneBle(bleAdapterAddress=conf["bleAdapterAddress"])

    # load the encryption keys into the library
    loadKeysFromConfig(cs_ble, conf)

    loop = asyncio.get_event_loop()
    try:
        # asyncio.run does not work here.
        loop.run_until_complete(main(cs_ble, conf))
    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        loop.run_until_complete(terminate(cs_ble))
