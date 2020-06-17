import bluetooth._bluetooth as bluez
from time import sleep

from crownstone_core import Conversion
from crownstone_core.core.modules.EncryptionSettings import UserLevel
from crownstone_core.protocol.BluenetTypes import BroadcastTypes
from crownstone_core.util.EncryptionHandler import EncryptionHandler
from crownstone_core.util.RC5 import RC5

from crownstone_ble.thirdParty.py_bluetooth_utils.bluetooth_utils import start_le_advertising, stop_le_advertising


class BroadcastHandler:

    def __init__(self, bluetoothCore, hciIndex):
        self.core = bluetoothCore
        self.broadcaster = Broadcaster(hciIndex, self.core.settings)

    def switchCrownstone(self, sphereUID, crownstoneId, switchState):
        """
        switchState is in the range of [0 .. 1]
        """
        convertedSwitchState = int(min(1, max(0, switchState)) * 100)
        self._switchCrownstone(sphereUID, crownstoneId, convertedSwitchState)

    def turnOnCrownstone(self, sphereUID, crownstoneId):
        self._switchCrownstone(sphereUID, crownstoneId, 255)

    def turnOffCrownstone(self, sphereUID, crownstoneId):
        self._switchCrownstone(sphereUID, crownstoneId, 0)

    def _switchCrownstone(self, sphereUID, crownstoneId, switchState):
        """
        Switchstate here is conforming to the Crownstone protocol, range 0..255
        """
        stoneSwitchPackets = [[crownstoneId, switchState]]

        packet = [BroadcastTypes.MULTI_SWITCH.value, len(stoneSwitchPackets) * 2]
        for switchPacket in stoneSwitchPackets:
            packet += switchPacket

        self.broadcaster.cast(sphereUID, packet)



class Broadcaster:

    def __init__(self, hciIndex, settings):
        self.broadcastCounter = 0
        self.hciIndex = hciIndex
        self.deviceToken = 0xf0
        self.settings = settings

    def cast(self, sphereUID, payload):
        uint16ServiceNumbers = BroadcastProtocol.getUInt16ServiceNumbers(
            self.broadcastCounter,
            self.deviceToken,
            sphereUID,
            UserLevel.basic,
            self.settings.localizationKey
        )

        commandPayload = BroadcastProtocol.getEncryptedServiceUUID(
            self.settings.basicKey,
            payload,
            Conversion.uint16_array_to_uint8_array(uint16ServiceNumbers),
            Conversion.uint32_to_uint8_array(0xCAFEBABE) # this is a shortcut, we will use timestamps at firmware v5 so it is immune to repeat attacks.
        )


        try:
            socket = bluez.hci_open_dev(self.hciIndex)
        except:
            print("Cannot open bluetooth device %i" % self.hciIndex)
            raise
        payload = [
            0x02, 0x01, 0x1A, # prefix
            0x11, 0x07, *list(commandPayload),
            0x09, 0x03, *Conversion.uint16_array_to_uint8_array(uint16ServiceNumbers),
        ]

        payload += [0] * (31-len(payload))

        try:
            start_le_advertising(socket, min_interval=20, max_interval=40, data=payload)
            sleep(1.5)
        except:
            stop_le_advertising(socket)
            raise



class BroadcastProtocol:

    """/**
     * Payload is 12 bytes, this method will add the validation and encrypt the thing
     **/
     """
    @staticmethod
    def getEncryptedServiceUUID(key, data, IV, validationNonce):
        encryptedData = EncryptionHandler.encryptBroadcast(data, key, IV, validationNonce)
        return encryptedData


    @staticmethod
    def getUInt16ServiceNumbers(broadcastCounter, deviceToken, sphereUID, accessLevel, key):
        result = []

        firstPart = broadcastCounter << 8

        protocolVersion = 0

        RC5Component = BroadcastProtocol.getRC5Payload(firstPart, key)
        result.append(BroadcastProtocol._constructProtocolBlock(protocolVersion, sphereUID, accessLevel))
        result.append(BroadcastProtocol._getFirstRC5Block(deviceToken, RC5Component))
        result.append(BroadcastProtocol._getSecondRC5Block(RC5Component))
        result.append(BroadcastProtocol._getThirdRC5Block(RC5Component))

        return result


    """ 
     * This is an UInt32 which will be encrypted
     * | ----------- First Part ---------- |
     * | Counter         | Reserved        | LocationId  | Profile Index | RSSI Calibration | Flag: t2t enabled | Flag: ignore for behaviour | Flag: reserved |
     * | 0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 | 0 0 0         | 0 0 0 0          | 0                 | 0                          | 0              |
     * | 8b              | 8b              | 6b          | 3b            | 4b               | 1b                | 1b                         | 1b             |
     *
     * The first part will be a validation nonce in the background.
     *
     """
    @staticmethod
    def getRC5Payload(firstPart, key):
        rc5Payload = 0

        rc5Payload += firstPart << 16

        rc5Payload += (0 & 0x0000003F) << 10 # locationId, ignore

        rc5Payload += (0 & 0x00000007) << 7 # profile Index, ignore

        rc5Payload += (8 & 0x0000000F) << 3 # rssi offset, ignore (value 0 results in 8)

        # tap to toggle
        rc5Payload += 0 << 2 #, ignore
        
        # ignore for Behaviour
        rc5Payload += 1 << 1

        rc5Encryptor = RC5(key,32,12)
        return rc5Encryptor.encrypt(rc5Payload)


    """/**
    * This is an UInt16 is constructed from an index flag, then a protocol,  the Sphere passkey and the access level
    *
    * | Index |  Protocol version |  Sphere UID      |  Access Level |
    * | 0 0   |  0 0 0            |  0 0 0 0 0 0 0 0 |  0 0 0        |
    * | 2b    |  3b               |  8b              |  3b           |
    *
    """
    @staticmethod
    def _constructProtocolBlock(protocolVersion, spherePasskey, accessLevel):
        block = 0

        block += (protocolVersion & 0x0007) << 11
        if spherePasskey is not None:
            block += (spherePasskey & 0x00FF) << 3
        
        block += accessLevel.value & 0x0007

        return block


    """ 
     * TThe first chunk of RC5 data and reserved chunk of public bits
     *
     * | Index |  Reserved  |  Device Token     |  First chunk of RC5Data  |
     * | 0 1   |  0 0       |  0 0 0 0 0 0 0 0  |  0 0 0 0   |
     * | 2b    |  2b        |  8b                     |  4b          |
     *
    """
    @staticmethod
    def _getFirstRC5Block(deviceToken, RC5):
        block = 0

        block += 1 << 14 # place index

        # place device token
        block += deviceToken << 4

        block += (RC5 & 0xF0000000) >> 28

        return block
    

    """ 
     *
     * | Index |  RC chunk 2                       |
     * | 1 0   |  0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0  |
     * | 2b    |  14b                              |
     *
    """
    @staticmethod
    def _getSecondRC5Block(RC5):
        block = 0

        block += 1 << 15 # place index
        block += (RC5 & 0x0FFFC000) >> 14

        return block
    

    """ 
     *
     * | Index |  RC chunk 3                       |
     * | 1 1   |  0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0  |
     * | 2b    |  14b                              |
     *
    """
    @staticmethod
    def _getThirdRC5Block(RC5):
        block = 0

        block += 3 << 14 # place index
        block += RC5 & 0x00003FFF

        return block
