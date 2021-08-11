from crownstone_core import Conversion
from crownstone_core.Exceptions import CrownstoneError, CrownstoneException
from crownstone_core.packets.ResultPacket import ResultPacket
from crownstone_core.packets.serviceDataParsers.containers.elements.AdvCrownstoneErrorBitmask import \
    AdvCrownstoneErrorBitmask
from crownstone_core.protocol.BlePackets import ControlStateGetPacket, ControlStateSetPacket
from crownstone_core.protocol.BluenetTypes import StateType, ResultValue
from crownstone_core.protocol.SwitchState import SwitchState


class StateHandler:
    def __init__(self, bluetoothCore):
        self.core = bluetoothCore
        
    async def getSwitchState(self) -> SwitchState:
        stateVal = await self._getState(StateType.SWITCH_STATE)
        return SwitchState(stateVal[0])

    async def getTime(self) -> int:
        """
        :returns: posix timestamp (uint32)
        """
        stateVal = await self._getState(StateType.TIME)
        return Conversion.uint8_array_to_uint32(stateVal)

    async def getDimmingAllowed(self) -> bool:
        stateVal = await self._getState(StateType.PWM_ALLOWED)
        # TODO: convert to uint8?
        return stateVal[0] != 0

    async def getSwitchLocked(self) -> bool:
        stateVal = await self._getState(StateType.SWITCH_LOCKED)
        # TODO: convert to uint8?
        return stateVal[0] != 0

    async def getPowerUsage(self) -> float:
        """
        :returns: Power usage in Watt.
        """
        stateVal = await self._getState(StateType.POWER_USAGE)
        powerUsage = Conversion.uint8_array_to_int32(stateVal) / 1000.0
        return powerUsage

    async def getErrors(self) -> AdvCrownstoneErrorBitmask:
        """
        :returns: Errors
        """
        stateVal = await self._getState(StateType.ERROR_BITMASK)
        return AdvCrownstoneErrorBitmask(Conversion.uint8_array_to_uint32(stateVal))

    async def getChipTemperature(self) -> float:
        """
        :returns: Chip temperature in °C.
        """
        stateVal = await self._getState(StateType.TEMPERATURE)
        return Conversion.uint8_to_int8(stateVal[0])



    """
    ---------------  UTIL  ---------------
    """
    
    
    async def _getState(self, stateType) -> list:
        """
        Write get state command, and read result.
        :param stateType: StateType
        """
        resultPacket = await self.core.control._writeControlAndGetResult(ControlStateGetPacket(stateType).serialize())

        # The payload of the resultPacket is padded with stateType and ID at the beginning
        # TODO: write a packet for this.
        state = []
        for i in range(6, len(resultPacket.payload)):
            state.append(resultPacket.payload[i])

        return state

    async def _setState(self, packet: ControlStateSetPacket):
        """
        Write set state command, and check result.
        """
        await self.core.control._writeControlAndGetResult(packet.serialize())
