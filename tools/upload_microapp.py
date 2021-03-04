#!/usr/bin/env python3

"""

  This tool allows the user to perform commands for the Microapp.

    TODO: explain what all the actions do.
        request
        upload
        validate
        enable
        disable
        all       -- This does request, upload, validate and enable

    TODO: Decide on API

"""

import asyncio
from sys import path

from crownstone_ble import CrownstoneBle
from crownstone_core.packets.MicroappPacket import MicroappUploadCmd, MicroappRequestCmd, MicroappValidateCmd, MicroappEnableCmd

from tools.util.config import setupDefaultCommandLineArguments, getToolConfig, loadKeysFromConfig

parser = setupDefaultCommandLineArguments("Microapp commands.")
parser.add_argument('bleAddress',
        help='The BLE address of Crownstone to switch')
parser.add_argument('microapp', 
        help='The microapp (.obj) file to be sent.')
parser.add_argument('action',
        help='The action to be done (request, upload, validate, enable, disable, all).')

try:
    file_path = path.dirname(path.realpath(__file__))
    [tool_config, args] = getToolConfig(file_path, parser)
except Exception as e:
    print("ERROR", e)
    quit()


# Each action can be executed individually or at once.
actions = set()
if args.action == 'request':
    actions.add('request')
if args.action == 'upload':
    actions.add('upload')
if args.action == 'validate':
    actions.add('validate')
if args.action == 'enable':
    actions.add('enable')
if args.action == 'disable':
    actions.add('disable')
if args.action == 'all':
    actions.add('request')
    actions.add('upload')
    actions.add('validate')
    actions.add('enable')


# create the library instance
print(f'Initializing tool with bleAdapterAddress={tool_config["bleAdapterAddress"]}')
core = CrownstoneBle(bleAdapterAddress=tool_config["bleAdapterAddress"])

# load the encryption keys into the library
try:
    loadKeysFromConfig(core, tool_config)
except Exception as e:
    print("ERROR", e)
    quit()


# --------------------- Starting the bluetooth part --------------------- #
async def performMicroAppActions():
    print("Connecting to", args.bleAddress)
    try:
        await core.connect(args.bleAddress)
    except:
        print(f"Something went wrong while connecting to {args.bleAddress}")
        core.shutDown()
        quit()

    print("Read microapp to be sent", args.microapp)
    with open(args.microapp, "rb") as fileHandle:
        micro_app_content = fileHandle.read()

    # Only support for a single app (for now)
    app_id = 0

    # We are at microapp protocol version 0. This version has to be supported by both the python lib and the firmware
    # version at the Crownstone you are uploading to.
    protocol = 0

    # The chunk size should be the same as on the Crownstone. The chunk size depends on the MTU settings of the
    # firmware. It is therefore considered dynamic. We check if we use the proper chunk_size with a request.
    chunk_size = 40

    # Offset of dummy_main in executable (use nm, objdump, readelf, etc.)
    offset=0xB4

    # Location of _mainCRTStartup
    offset=0x40

    offset=0x0

    if 'request' in actions:
        print('Request a new app upload')
        cmd = MicroappRequestCmd(protocol, app_id, micro_app_content, chunk_size)
        await core.control.requestMicroapp(cmd)

    if 'upload' in actions:
        print('Upload the data itself (this is a sequence of commands)')
        cmd = MicroappUploadCmd(protocol, app_id, micro_app_content, chunk_size)
        await core.control.sendMicroapp(cmd)

    if 'validate' in actions:
        print('Validate')
        cmd = MicroappValidateCmd(protocol, app_id, micro_app_content, chunk_size)
        await core.control.validateMicroapp(cmd)

    if 'enable' in actions:
        print('Enable the app')
        cmd = MicroappEnableCmd(protocol, app_id, True, offset)
        await core.control.enableMicroapp(cmd)

    if 'disable' in actions:
        print('Disable the app')
        cmd = MicroappEnableCmd(protocol, app_id, False, 0x00)
        await core.control.enableMicroapp(cmd)

    print("Make sure commands have been received, sleep for 4 seconds...")
    await asyncio.sleep(4)

    print("Disconnect")
    await core.control.disconnect()
    await core.shutDown()

    print("===========================================\n\nFinished microapp actions\n\n===========================================")

try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(performMicroAppActions())
except KeyboardInterrupt:
    print("Closing the microapp tool.")