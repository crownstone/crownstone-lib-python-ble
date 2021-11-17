import queue
import struct

from tools.dfu.dfu_transport import DfuTransport, DfuEvent
from tools.dfu.dfu_exceptions import *


import binascii
import logging
logger = logging.getLogger(__name__)


class DfuTransportBle(DfuTransport):

    DEFAULT_TIMEOUT     = 20
    RETRIES_NUMBER      = 3

    def __init__(self,
                 serial_port,
                 att_mtu,
                 target_device_name=None,
                 target_device_addr=None,
                 baud_rate=1000000,
                 prn=0):
        super().__init__()
        DFUAdapter.LOCAL_ATT_MTU = att_mtu
        self.baud_rate          = baud_rate
        self.serial_port        = serial_port
        self.att_mtu            = att_mtu
        self.target_device_name = target_device_name
        self.target_device_addr = target_device_addr
        self.dfu_adapter        = None
        self.prn                = prn

        self.bonded             = False
        self.keyset             = None

    def open(self):
        if self.dfu_adapter:
            raise IllegalStateException('DFU Adapter is already open')

        super().open()
        driver           = DfuBLEDriver(serial_port = self.serial_port,
                                        baud_rate   = self.baud_rate)
        adapter          = BLEAdapter(driver)
        self.dfu_adapter = DFUAdapter(adapter=adapter, bonded=self.bonded, keyset=self.keyset)
        self.dfu_adapter.open()
        self.target_device_name, self.target_device_addr = self.dfu_adapter.connect(
                                                        target_device_name = self.target_device_name,
                                                        target_device_addr = self.target_device_addr)
        self.__set_prn()

    def close(self):

        # Get bonded status and BLE keyset from DfuAdapter
        self.bonded = self.dfu_adapter.bonded
        self.keyset = self.dfu_adapter.keyset

        if not self.dfu_adapter:
            raise IllegalStateException('DFU Adapter is already closed')
        super().close()
        self.dfu_adapter.close()
        self.dfu_adapter = None

    def send_init_packet(self, init_packet):
        def try_to_recover():
            if response['offset'] == 0 or response['offset'] > len(init_packet):
                # There is no init packet or present init packet is too long.
                return False

            expected_crc = (binascii.crc32(init_packet[:response['offset']]) & 0xFFFFFFFF)

            if expected_crc != response['crc']:
                # Present init packet is invalid.
                return False

            if len(init_packet) > response['offset']:
                # Send missing part.
                try:
                    self.__stream_data(data     = init_packet[response['offset']:],
                                       crc      = expected_crc,
                                       offset   = response['offset'])
                except ValidationException:
                    return False

            self.__execute()
            return True

        response = self.__select_command()
        assert len(init_packet) <= response['max_size'], 'Init command is too long'

        if try_to_recover():
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
        def try_to_recover():
            if response['offset'] == 0:
                # Nothing to recover
                return

            expected_crc = binascii.crc32(firmware[:response['offset']]) & 0xFFFFFFFF
            remainder    = response['offset'] % response['max_size']

            if expected_crc != response['crc']:
                # Invalid CRC. Remove corrupted data.
                response['offset'] -= remainder if remainder != 0 else response['max_size']
                response['crc']     = binascii.crc32(firmware[:response['offset']]) & 0xFFFFFFFF
                return

            if (remainder != 0) and (response['offset'] != len(firmware)):
                # Send rest of the page.
                try:
                    to_send             = firmware[response['offset'] : response['offset'] + response['max_size'] - remainder]
                    response['crc']     = self.__stream_data(data   = to_send,
                                                             crc    = response['crc'],
                                                             offset = response['offset'])
                    response['offset'] += len(to_send)
                except ValidationException:
                    # Remove corrupted data.
                    response['offset'] -= remainder
                    response['crc']     = binascii.crc32(firmware[:response['offset']]) & 0xFFFFFFFF
                    return

            self.__execute()
            self._send_event(event_type=DfuEvent.PROGRESS_EVENT, progress=response['offset'])

        response = self.__select_data()
        try_to_recover()

        for i in range(response['offset'], len(firmware), response['max_size']):
            data = firmware[i:i+response['max_size']]
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

    def __set_prn(self):
        logger.debug("BLE: Set Packet Receipt Notification {}".format(self.prn))
        self.dfu_adapter.write_control_point([DfuTransportBle.OP_CODE['SetPRN']] + list(struct.pack('<H', self.prn)))
        self.__get_response(DfuTransportBle.OP_CODE['SetPRN'])

    def __create_command(self, size):
        self.__create_object(0x01, size)

    def __create_data(self, size):
        self.__create_object(0x02, size)

    def __create_object(self, object_type, size):
        self.dfu_adapter.write_control_point([DfuTransportBle.OP_CODE['CreateObject'], object_type]\
                                            + list(struct.pack('<L', size)))
        self.__get_response(DfuTransportBle.OP_CODE['CreateObject'])

    def __calculate_checksum(self):
        self.dfu_adapter.write_control_point([DfuTransportBle.OP_CODE['CalcChecSum']])
        response = self.__get_response(DfuTransportBle.OP_CODE['CalcChecSum'])

        (offset, crc) = struct.unpack('<II', bytearray(response))
        return {'offset': offset, 'crc': crc}

    def __execute(self):
        self.dfu_adapter.write_control_point([DfuTransportBle.OP_CODE['Execute']])
        self.__get_response(DfuTransportBle.OP_CODE['Execute'])

    def __select_command(self):
        return self.__select_object(0x01)

    def __select_data(self):
        return self.__select_object(0x02)

    def __select_object(self, object_type):
        logger.debug("BLE: Selecting Object: type:{}".format(object_type))
        self.dfu_adapter.write_control_point([DfuTransportBle.OP_CODE['ReadObject'], object_type])
        response = self.__get_response(DfuTransportBle.OP_CODE['ReadObject'])

        (max_size, offset, crc)= struct.unpack('<III', bytearray(response))
        logger.debug("BLE: Object selected: max_size:{} offset:{} crc:{}".format(max_size, offset, crc))
        return {'max_size': max_size, 'offset': offset, 'crc': crc}

    def __get_checksum_response(self):
        response = self.__get_response(DfuTransportBle.OP_CODE['CalcChecSum'])

        (offset, crc) = struct.unpack('<II', bytearray(response))
        return {'offset': offset, 'crc': crc}

    def __stream_data(self, data, crc=0, offset=0):
        logger.debug("BLE: Streaming Data: len:{0} offset:{1} crc:0x{2:08X}".format(len(data), offset, crc))
        def validate_crc():
            if (crc != response['crc']):
                raise ValidationException('Failed CRC validation.\n'\
                                + 'Expected: {} Received: {}.'.format(crc, response['crc']))
            if (offset != response['offset']):
                raise ValidationException('Failed offset validation.\n'\
                                + 'Expected: {} Received: {}.'.format(offset, response['offset']))

        current_pnr = 0
        for i in range(0, len(data), self.dfu_adapter.packet_size):
            to_transmit     = data[i:i + self.dfu_adapter.packet_size]
            self.dfu_adapter.write_data_point(list(to_transmit))
            crc     = binascii.crc32(to_transmit, crc) & 0xFFFFFFFF
            offset += len(to_transmit)
            current_pnr    += 1
            if self.prn == current_pnr:
                current_pnr = 0
                response    = self.__get_checksum_response()
                validate_crc()

        response = self.__calculate_checksum()
        validate_crc()

        return crc

    def __get_response(self, operation):
        def get_dict_key(dictionary, value):
            return next((key for key, val in list(dictionary.items()) if val == value), None)

        try:
            resp = self.dfu_adapter.notifications_q.get(timeout=DfuTransportBle.DEFAULT_TIMEOUT)
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
