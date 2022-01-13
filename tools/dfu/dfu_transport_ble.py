import asyncio
import struct

from crownstone_ble.Exceptions import BleError
from crownstone_core.Exceptions import CrownstoneBleException
from tools.dfu.dfu_constants import DFUAdapter, DfuTransportBle
from tools.dfu.dfu_exceptions import *


import binascii
import logging
logger = logging.getLogger(__name__)


class CrownstoneDfuOverBle:
    ServiceUuid = 0xFE59 # "CrownstoneDfuOverBle WriteCommand" # no clue what this is supposed to be

    ### ----- init and 'open/close'-ing -----

    def __init__(self, crownstoneBle):
        self.crownstone_ble = crownstoneBle
        self.prn = 0 # default from nordic

    async def open(self):
        await self.__set_prn()

    async def close(self): # (async because open is async)
        pass


    ### ----- the adapter layer for crownstone_ble -----

    async def writeCharacteristicWithoutResponse(self, char_uuid, data):
        await self.crownstone_ble.ble.writeToCharacteristicWithoutEncryption(
            CrownstoneDfuOverBle.ServiceUuid,
            char_uuid,
            data,
            response=False)

    async def writeCharacteristicForResponse(self, char_uuid, data):
        writemethod = lambda: self.crownstone_ble.ble.writeToCharacteristicWithoutEncryption(
                                                    CrownstoneDfuOverBle.ServiceUuid,
                                                    char_uuid,
                                                    data)
        try:
            result = await self.receiveRawNotification(
                                                        CrownstoneDfuOverBle.ServiceUuid,
                                                        char_uuid,
                                                        writemethod,
                                                        DfuTransportBle.DEFAULT_TIMEOUT)
        except CrownstoneBleException as e:
            print("failed to execute writeCharacteristicForResponse")
            print(e)
            raise

        return result

    async def receiveRawNotification(self, serviceUUID, characteristicUUID, writeCommand, timeout=None):
        """
        adapted from BleHandler.setupSingleNotification, which uses a wrapper (notificationDelegate) that is too thick.
        """
        if timeout is None:
            timeout = 12.5

        notificationReceived = False
        notificationData = None

        def onReceiveNotification(uuid, data):
            nonlocal notificationReceived
            nonlocal notificationData

            notificationReceived = True
            notificationData = data

        ble_client = self.crownstone_ble.ble.activeClient

        # setup the collecting of the notification data.
        await ble_client.subscribeNotifications(characteristicUUID, onReceiveNotification)

        # execute the command that will trigger the notifications
        await writeCommand()

        # wait for the results to come in.
        loopCount = 0
        pollInterval = 0.1
        while not notificationReceived and loopCount < (timeout / pollInterval):
            await asyncio.sleep(pollInterval)
            loopCount += 1

        ble_client.unsubscribeNotifications(characteristicUUID)

        if notificationData is None:
            raise CrownstoneBleException(BleError.NO_NOTIFICATION_DATA_RECEIVED, "No notification data received.")

        return notificationData


    ### ----- utility forwarders that were pulled up from ble_adapter.py:classBLEAdapter

    async def write_control_point(self, data):
        return await self.writeCharacteristicForResponse(DFUAdapter.CP_UUID.toString(), data)

    async def write_data_point(self, data):
        return await self.writeCharacteristicWithoutResponse(DFUAdapter.DP_UUID.toString(), data)

    ### -------- main protocol methods -----------

    async def send_init_packet(self, init_packet):
        response = await self.__select_command()

        assert len(init_packet) <= response['max_size'], 'Init command is too long'

        if await self.try_to_recover_before_send_init(response, init_packet):
            return

        for r in range(DfuTransportBle.RETRIES_NUMBER):
            try:
                print("call send `create command`")
                await self.__create_command(len(init_packet))
                print("send init packet data")
                await self.__stream_data(data=init_packet)
                print("send execute command")
                await self.__execute()
            except ValidationException:
                pass
            break
        else:
            raise DfuException("Failed to send init packet")

    async def send_firmware(self, firmware):
        response = await self.__select_data()
        await self.try_to_recover_before_send_firmware(response, firmware)

        for i in range(response['offset'], len(firmware), response['max_size']):
            data = firmware[i:i + response['max_size']]
            for r in range(DfuTransportBle.RETRIES_NUMBER):
                try:
                    await self.__create_data(len(data))
                    response['crc'] = await self.__stream_data(data=data, crc=response['crc'], offset=i)
                    await self.__execute()
                except ValidationException:
                    pass
                break
            else:
                raise DfuException("Failed to send firmware")

    ### ------------ recovery methods -----------

    async def try_to_recover_before_send_init(self, select_cmd_response, init_packet):
        """
        validate select cmd response and send missing part if necessary.
        return true if recovery was tried.
        return false if recovery failed to validate or it wasn't necessary to recover.
        """
        if select_cmd_response['offset'] == 0 or select_cmd_response['offset'] > len(init_packet):
            # There is no init packet or present init packet is too long.
            return False

        expected_crc = (binascii.crc32(init_packet[:select_cmd_response['offset']]) & 0xFFFFFFFF)

        if expected_crc != select_cmd_response['crc']:
            # Present init packet is invalid.
            return False

        if len(init_packet) > select_cmd_response['offset']:
            # Send missing part.
            try:
                await self.__stream_data(data=init_packet[select_cmd_response['offset']:],
                                   crc=expected_crc,
                                   offset=select_cmd_response['offset'])
            except ValidationException:
                return False

        await self.__execute()
        return True


    async def try_to_recover_before_send_firmware(self, resp, firmw):
        if resp['offset'] == 0:
            # Nothing to recover
            return

        expected_crc = binascii.crc32(firmw[:resp['offset']]) & 0xFFFFFFFF
        remainder = resp['offset'] % resp['max_size']

        if expected_crc != resp['crc']:
            # Invalid CRC. Remove corrupted data.
            resp['offset'] -= remainder if remainder != 0 else resp['max_size']
            resp['crc'] = binascii.crc32(firmw[:resp['offset']]) & 0xFFFFFFFF
            return

        if (remainder != 0) and (resp['offset'] != len(firmw)):
            # Send rest of the page.
            try:
                to_send = firmw[resp['offset']: resp['offset'] + resp['max_size'] - remainder]
                resp['crc'] = await self.__stream_data(data=to_send,
                                                     crc=resp['crc'],
                                                     offset=resp['offset'])
                resp['offset'] += len(to_send)
            except ValidationException:
                # Remove corrupted data.
                resp['offset'] -= remainder
                resp['crc'] = binascii.crc32(firmw[:resp['offset']]) & 0xFFFFFFFF
                return

        await self.__execute()

    def validate_crc(self, crc, resp, offset):
        if crc != resp['crc']:
            raise ValidationException('Failed CRC validation.\n' \
                                      + 'Expected: {} Received: {}.'.format(crc, resp['crc']))
        if offset != resp['offset']:
            raise ValidationException('Failed offset validation.\n' \
                                      + 'Expected: {} Received: {}.'.format(offset, resp['offset']))

    ### -------------- nordic protocol commands -----------

    async def __create_command(self, size):
        await self.__create_object(0x01, size)

    async def __create_data(self, size):
        await self.__create_object(0x02, size)

    async def __create_object(self, object_type, size):
        raw_response = await self.write_control_point([DfuTransportBle.OP_CODE['CreateObject'], object_type]\
                                            + list(struct.pack('<L', size)))
        self.__parse_response(raw_response, DfuTransportBle.OP_CODE['CreateObject'])

    async def __set_prn(self):
        logger.debug("BLE: Set Packet Receipt Notification {}".format(self.prn))
        raw_response = await self.write_control_point([DfuTransportBle.OP_CODE['SetPRN']] + list(struct.pack('<H', self.prn)))
        self.__parse_response(raw_response, DfuTransportBle.OP_CODE['SetPRN'])

    async def __calculate_checksum(self):
        raw_response = await self.write_control_point([DfuTransportBle.OP_CODE['CalcChecSum']])
        response = self.__parse_response(raw_response, DfuTransportBle.OP_CODE['CalcChecSum'])

        (offset, crc) = struct.unpack('<II', bytearray(response))
        return {'offset': offset, 'crc': crc}

    async def __execute(self):
        raw_response = await self.write_control_point([DfuTransportBle.OP_CODE['Execute']])
        self.__parse_response(raw_response, DfuTransportBle.OP_CODE['Execute'])

    async def __select_command(self):
        return await self.__select_object(0x01)

    async def __select_data(self):
        return await self.__select_object(0x02)

    async def __select_object(self, object_type):
        logger.debug("BLE: Selecting Object: type:{}".format(object_type))
        raw_response = await self.write_control_point([DfuTransportBle.OP_CODE['ReadObject'], object_type])
        response = self.__parse_response(raw_response, DfuTransportBle.OP_CODE['ReadObject'])

        (max_size, offset, crc)= struct.unpack('<III', bytearray(response))
        logger.debug("BLE: Object selected: max_size:{} offset:{} crc:{}".format(max_size, offset, crc))
        return {'max_size': max_size, 'offset': offset, 'crc': crc}

    ### ------------ raw data communication ------------

    async def __stream_data(self, data, crc=0, offset=0):
        logger.debug("BLE: Streaming Data: len:{0} offset:{1} crc:0x{2:08X}".format(len(data), offset, crc))

        current_pnr = 0

        for i in range(0, len(data), DFUAdapter.LOCAL_ATT_MTU):
            to_transmit = data[i:i + DFUAdapter.LOCAL_ATT_MTU]
            raw_response = await self.write_data_point(to_transmit)
            crc = binascii.crc32(to_transmit, crc) & 0xFFFFFFFF
            offset += len(to_transmit)
            current_pnr += 1
            if self.prn == current_pnr:
                current_pnr = 0
                response = self.__parse_checksum_response(raw_response)
                self.validate_crc(crc, response, offset)

        response = await self.__calculate_checksum()
        self.validate_crc(crc, response, offset)

        return crc

    def __parse_response(self, raw_response, operation):
        """
        Parses a raw response (notification) and checks for errors.
        """
        def get_dict_key(dictionary, value):
            return next((key for key, val in list(dictionary.items()) if val == value), None)

        if raw_response is None:
            raise CrownstoneBleException(BleError.NO_NOTIFICATION_DATA_RECEIVED, "cannot parse empty response")

        print("raw response to operation {0}:".format(operation),", ".join(["0x{0:02X}".format(x) for x in raw_response]))

        if raw_response[0] != DfuTransportBle.OP_CODE['Response']:
            raise DfuException('No Response: 0x{:02X}'.format(raw_response[0]))

        if raw_response[1] != operation:
            raise DfuException('Unexpected Executed OP_CODE.\n' \
                               + 'Expected: 0x{:02X} Received: 0x{:02X}'.format(operation, raw_response[1]))

        if raw_response[2] == DfuTransportBle.RES_CODE['Success']:
            return raw_response[3:]

        elif raw_response[2] == DfuTransportBle.RES_CODE['ExtendedError']:
            try:
                data = DfuTransportBle.EXT_ERROR_CODE[raw_response[3]]
            except IndexError:
                data = "Unsupported extended error type {}".format(raw_response[3])
            raise DfuException('Extended Error 0x{:02X}: {}'.format(raw_response[3], data))
        else:
            raise DfuException('Response Code {}'.format(get_dict_key(DfuTransportBle.RES_CODE, raw_response[2])))

    def __parse_checksum_response(self, raw_response):
        response = self.__parse_response(raw_response, DfuTransportBle.OP_CODE['CalcChecSum'])

        (offset, crc) = struct.unpack('<II', bytearray(response))
        return {'offset': offset, 'crc': crc}