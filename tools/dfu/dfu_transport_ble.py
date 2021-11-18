import queue
import struct

from tools.dfu.dfu_constants import DFUAdapter, DfuTransportBle
from tools.dfu.dfu_exceptions import *


import binascii
import logging
logger = logging.getLogger(__name__)


class CrownstoneDfuOverBle:
    def __init__(self, crownstoneBle):
        self.crownstone_ble = crownstoneBle

    # def open(self):
    #
    #     super().open()
    #
    #     self.dfu_adapter.open()
    #     self.target_device_name, self.target_device_addr = self.dfu_adapter.connect(
    #                                                     target_device_name = self.target_device_name,
    #                                                     target_device_addr = self.target_device_addr)
    #     self.__set_prn()
    #
    # def close(self):
    #
    #     # Get bonded status and BLE keyset from DfuAdapter
    #     self.bonded = self.dfu_adapter.bonded
    #     self.keyset = self.dfu_adapter.keyset
    #
    #     super().close()
    #     self.dfu_adapter.close()

    RETRIES_NUMBER = 3

    ### ----- the adapter layer for crownstone_ble -----

    def get_notifications(self, timeout):
        """
        TODO(Arend): hook up for __get_response to BleHandler notifications
        """
        pass

    def write_cmd(self, uuid, data):
        ## TODO (Arend) hookup to BleHandler
        pass

    def write_req(self, uuid, data):
        ## TODO (Arend) hookup to BleHandler
        pass


    ### ----- utility forwarders that were pulled up from ble_adapter.py:classBLEAdapter

    def write_control_point(self, data):
        self.write_req(self.conn_handle, DFUAdapter.CP_UUID, data) ## ble_gattc_write (... BLEGattWriteOperation.write_req ...)
        # waits for result from gattc_evt_write_rsp and returns it

    def write_data_point(self, data):
        self.write_cmd(self.conn_handle, DFUAdapter.DP_UUID, data)  ## ble_gattc_write  (... BLEGattWriteOperation.write_cmd ...)
        # waits for result from on_gattc_evt_write_cmd_tx_complete and returns it

    ### -------- main protocol methods -----------

    def send_init_packet(self, init_packet):
        response = self.__select_command()

        assert len(init_packet) <= response['max_size'], 'Init command is too long'

        if self.try_to_recover_before_send_init(response, init_packet):
            return

        for r in range(DfuTransportBle.RETRIES_NUMBER):
            try:
                self.__create_command(len(init_packet))
                self.__stream_data(data=init_packet)
                self.__execute()
            except ValidationException:
                pass
            break
        else:
            raise DfuException("Failed to send init packet")

    def send_firmware(self, firmware):
        response = self.__select_data()
        self.try_to_recover_before_send_firmware(response, firmware)

        for i in range(response['offset'], len(firmware), response['max_size']):
            data = firmware[i:i + response['max_size']]
            for r in range(DfuTransportBle.RETRIES_NUMBER):
                try:
                    self.__create_data(len(data))
                    response['crc'] = self.__stream_data(data=data, crc=response['crc'], offset=i)
                    self.__execute()
                except ValidationException:
                    pass
                break
            else:
                raise DfuException("Failed to send firmware")
            self._send_event(event_type=DfuEvent.PROGRESS_EVENT, progress=len(data))

    ### ------------ recovery methods -----------

    def try_to_recover_before_send_init(self, select_cmd_response, init_packet):
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
                self.__stream_data(data=init_packet[select_cmd_response['offset']:],
                                   crc=expected_crc,
                                   offset=select_cmd_response['offset'])
            except ValidationException:
                return False

        self.__execute()
        return True


    def try_to_recover_before_send_firmware(self, resp, firmw):
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
                resp['crc'] = self.__stream_data(data=to_send,
                                                     crc=resp['crc'],
                                                     offset=resp['offset'])
                resp['offset'] += len(to_send)
            except ValidationException:
                # Remove corrupted data.
                resp['offset'] -= remainder
                resp['crc'] = binascii.crc32(firmw[:resp['offset']]) & 0xFFFFFFFF
                return

        self.__execute()
        self._send_event(event_type=DfuEvent.PROGRESS_EVENT, progress=resp['offset'])

    def validate_crc(self, crc, resp, offset):
        if crc != resp['crc']:
            raise ValidationException('Failed CRC validation.\n' \
                                      + 'Expected: {} Received: {}.'.format(crc, resp['crc']))
        if offset != resp['offset']:
            raise ValidationException('Failed offset validation.\n' \
                                      + 'Expected: {} Received: {}.'.format(offset, resp['offset']))

    ### -------------- nordic protocol commands -----------

    def __create_command(self, size):
        self.__create_object(0x01, size)

    def __create_data(self, size):
        self.__create_object(0x02, size)

    def __create_object(self, object_type, size):
        self.write_control_point([DfuTransportBle.OP_CODE['CreateObject'], object_type]\
                                            + list(struct.pack('<L', size)))
        self.__get_response(DfuTransportBle.OP_CODE['CreateObject'])

    def __set_prn(self):
        logger.debug("BLE: Set Packet Receipt Notification {}".format(self.prn))
        self.write_control_point([DfuTransportBle.OP_CODE['SetPRN']] + list(struct.pack('<H', self.prn)))
        self.__get_response(DfuTransportBle.OP_CODE['SetPRN'])

    def __calculate_checksum(self):
        self.write_control_point([DfuTransportBle.OP_CODE['CalcChecSum']])
        response = self.__get_response(DfuTransportBle.OP_CODE['CalcChecSum'])

        (offset, crc) = struct.unpack('<II', bytearray(response))
        return {'offset': offset, 'crc': crc}

    def __execute(self):
        self.write_control_point([DfuTransportBle.OP_CODE['Execute']])
        self.__get_response(DfuTransportBle.OP_CODE['Execute'])

    def __select_command(self):
        return self.__select_object(0x01)

    def __select_data(self):
        return self.__select_object(0x02)

    def __select_object(self, object_type):
        logger.debug("BLE: Selecting Object: type:{}".format(object_type))
        self.write_control_point([DfuTransportBle.OP_CODE['ReadObject'], object_type])
        response = self.__get_response(DfuTransportBle.OP_CODE['ReadObject'])

        (max_size, offset, crc)= struct.unpack('<III', bytearray(response))
        logger.debug("BLE: Object selected: max_size:{} offset:{} crc:{}".format(max_size, offset, crc))
        return {'max_size': max_size, 'offset': offset, 'crc': crc}

    ### ------------ raw data communication ------------

    def __stream_data(self, data, crc=0, offset=0):
        logger.debug("BLE: Streaming Data: len:{0} offset:{1} crc:0x{2:08X}".format(len(data), offset, crc))

        current_pnr = 0
        for i in range(0, len(data), self.dfu_adapter.packet_size):
            to_transmit = data[i:i + self.dfu_adapter.packet_size]
            self.write_cmd(DFUAdapter.DP_UUID, data)
            crc = binascii.crc32(to_transmit, crc) & 0xFFFFFFFF
            offset += len(to_transmit)
            current_pnr += 1
            if self.prn == current_pnr:
                current_pnr = 0
                response = self.__get_checksum_response()
                self.validate_crc(crc, response, offset)

        response = self.__calculate_checksum()
        self.validate_crc(crc, response, offset)

        return crc

    def __get_response(self, operation):
        """
        waits for a notify of the device with OP_CODE == operation and return if possible.
        """
        def get_dict_key(dictionary, value):
            return next((key for key, val in list(dictionary.items()) if val == value), None)

        try:
            resp = self.get_notifications(timeout=DfuTransportBle.DEFAULT_TIMEOUT)
            # resp = self.dfu_adapter.notifications_q.get(timeout=DfuTransportBle.DEFAULT_TIMEOUT) # <--- original nordic call
        except queue.Empty:
            raise DfuException('Timeout: operation - {}'.format(get_dict_key(DfuTransportBle.OP_CODE,
                                                                             operation)))

        if resp[0] != DfuTransportBle.OP_CODE['Response']:
            raise DfuException('No Response: 0x{:02X}'.format(resp[0]))

        if resp[1] != operation:
            raise DfuException('Unexpected Executed OP_CODE.\n' \
                               + 'Expected: 0x{:02X} Received: 0x{:02X}'.format(operation, resp[1]))

        if resp[2] == DfuTransport.RES_CODE['Success']:
            return resp[3:]

        elif resp[2] == DfuTransport.RES_CODE['ExtendedError']:
            try:
                data = DfuTransport.EXT_ERROR_CODE[resp[3]]
            except IndexError:
                data = "Unsupported extended error type {}".format(resp[3])
            raise DfuException('Extended Error 0x{:02X}: {}'.format(resp[3], data))
        else:
            raise DfuException('Response Code {}'.format(get_dict_key(DfuTransport.RES_CODE, resp[2])))

    def __get_checksum_response(self):
        response = self.__get_response(DfuTransportBle.OP_CODE['CalcChecSum'])

        (offset, crc) = struct.unpack('<II', bytearray(response))
        return {'offset': offset, 'crc': crc}