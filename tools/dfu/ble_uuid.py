### Some constants defined below the class definitions
from enum import Enum


class BLEUUIDBase(object):
    def __init__(self, vs_uuid_base=None, uuid_type=None):
        assert isinstance(vs_uuid_base, (list, type(None))), "Invalid argument type"
        assert isinstance(uuid_type, (int, type(None))), "Invalid argument type"
        if (vs_uuid_base is None) and uuid_type is None:
            self.base = [
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x10,
                0x00,
                0x80,
                0x00,
                0x00,
                0x80,
                0x5F,
                0x9B,
                0x34,
                0xFB,
            ]
        else:
            self.base = vs_uuid_base

        self.__array = None

    # @classmethod
    # def from_c(cls, uuid):
    #     return cls(uuid_type=uuid.type)

    # def to_c(self):
    #     lsb_list = self.base[::-1]
    #     self.__array = util.list_to_uint8_array(lsb_list)
    #     uuid = driver.ble_uuid128_t()
    #     uuid.uuid128 = self.__array.cast()
    #     return uuid


class BLEUUID(object):
    class Standard(Enum):
        unknown = 0x0000
        service_primary = 0x2800
        service_secondary = 0x2801
        characteristic = 0x2803
        cccd = 0x2902
        battery_level = 0x2A19
        heart_rate = 0x2A37

    def __init__(self, value, base=BLEUUIDBase()):
        assert isinstance(base, BLEUUIDBase), "Invalid argument type"
        self.base = base
        try:
            self.value = (
                value
                if isinstance(value, BLEUUID.Standard)
                else BLEUUID.Standard(value)
            )
        except ValueError:
            self.value = value

    def __setstate__(self, state):
        try:
            self.value = BLEUUID.Standard(state["value"])
        except ValueError:
            self.value = state["value"]
        self.base = state["base"]

    def __getstate__(self):
        if isinstance(self.value, BLEUUID.Standard):
            return {"value": self.value.value, "base": self.base}
        return {"value": self.value, "base": self.base}

    def __str__(self):
        if isinstance(self.value, BLEUUID.Standard):
            return "0x{:04X} ({})".format(self.value.value, self.value)
        else:
            return "0x{:04X}".format(self.value)

    def __repr__(self):
        if isinstance(self.value, BLEUUID.Standard):
            return "<BLEUUID obj: 0x{:04X} ({})>".format(self.value.value, self.value)
        else:
            return "<BLEUUID obj: 0x{:04X}>".format(self.value)

    def __eq__(self, other):
        if not isinstance(other, BLEUUID):
            return False
        return (self.value == other.value) and (self.base.type == other.base.type) and \
            (self.base.base is None or other.base.base is None or self.base.base == other.base.base)

    def __hash__(self):
        return hash(self.value * (self.base.type or 1))

    # @classmethod
    # def from_c(cls, uuid):
    #     return cls(value=uuid.uuid, base=BLEUUIDBase.from_c(uuid))
    #
    # def to_c(self):
    #     assert self.base.type is not None, "Vendor specific UUID not registered"
    #     uuid = driver.ble_uuid_t()
    #     if isinstance(self.value, BLEUUID.Standard):
    #         uuid.uuid = self.value.value
    #     else:
    #         uuid.uuid = self.value
    #     uuid.type = self.base.type
    #     return uuid
