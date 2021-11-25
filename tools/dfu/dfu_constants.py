from tools.dfu.ble_uuid import *


##### CONSTANTS defining nordic services
class DFUAdapter:
    BASE_UUID = BLEUUIDBase([0x8E, 0xC9, 0x00, 0x00, 0xF3, 0x15, 0x4F, 0x60,
                                 0x9F, 0xB8, 0x83, 0x88, 0x30, 0xDA, 0xEA, 0x50])

    # Bootloader characteristics
    CP_UUID     = BLEUUID(0x0001, BASE_UUID)
    DP_UUID     = BLEUUID(0x0002, BASE_UUID)

    CONNECTION_ATTEMPTS   = 3
    ERROR_CODE_POS        = 2
    LOCAL_ATT_MTU         = 200 # used to be 247 in Nordic, what size should it be?


##### protocol constants
class DfuTransportBle:
    DEFAULT_TIMEOUT     = 20
    RETRIES_NUMBER      = 5

    OP_CODE = {
        'CreateObject'          : 0x01,
        'SetPRN'                : 0x02,
        'CalcChecSum'           : 0x03,
        'Execute'               : 0x04,
        'ReadObject'            : 0x06,
        'Response'              : 0x60,
    }

    RES_CODE = {
            'InvalidCode'           : 0x00,
            'Success'               : 0x01,
            'NotSupported'          : 0x02,
            'InvalidParameter'      : 0x03,
            'InsufficientResources' : 0x04,
            'InvalidObject'         : 0x05,
            'InvalidSignature'      : 0x06,
            'UnsupportedType'       : 0x07,
            'OperationNotPermitted' : 0x08,
            'OperationFailed'       : 0x0A,
            'ExtendedError'         : 0x0B,
        }

    EXT_ERROR_CODE = [
        "No extended error code has been set. This error indicates an implementation problem.",
        "Invalid error code. This error code should never be used outside of development.",
        "The format of the command was incorrect. This error code is not used in the current implementation, because @ref NRF_DFU_RES_CODE_OP_CODE_NOT_SUPPORTED and @ref NRF_DFU_RES_CODE_INVALID_PARAMETER cover all possible format errors.",
        "The command was successfully parsed, but it is not supported or unknown.",
        "The init command is invalid. The init packet either has an invalid update type or it is missing required fields for the update type (for example, the init packet for a SoftDevice update is missing the SoftDevice size field).",
        "The firmware version is too low. For an application, the version must be greater than or equal to the current application. For a bootloader, it must be greater than the current version. This requirement prevents downgrade attacks.""",
        "The hardware version of the device does not match the required hardware version for the update.",
        "The array of supported SoftDevices for the update does not contain the FWID of the current SoftDevice.",
        "The init packet does not contain a signature, but this bootloader requires all updates to have one.",
        "The hash type that is specified by the init packet is not supported by the DFU bootloader.",
        "The hash of the firmware image cannot be calculated.",
        "The type of the signature is unknown or not supported by the DFU bootloader.",
        "The hash of the received firmware image does not match the hash in the init packet.",
        "The available space on the device is insufficient to hold the firmware.",
        "The requested firmware to update was already present on the system.",
    ]