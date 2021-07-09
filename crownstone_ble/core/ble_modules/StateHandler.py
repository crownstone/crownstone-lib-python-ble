from crownstone_core import Conversion
from crownstone_core.Exceptions import CrownstoneError, CrownstoneException
from crownstone_core.packets.CrownstoneErrors import CrownstoneErrors
from crownstone_core.packets.ResultPacket import ResultPacket
from crownstone_core.protocol.BlePackets import ControlStateGetPacket, ControlStateSetPacket
from crownstone_core.protocol.BluenetTypes import StateType, ResultValue
from crownstone_core.protocol.SwitchState import SwitchState


class StateHandler:
    def __init__(self, bluetoothCore):
        self.core = bluetoothCore
        
    async def getSwitchState(self) -> SwitchState:
        # TODO: check result code
        rawSwitchState = await self._getState(StateType.SWITCH_STATE)
        return SwitchState(rawSwitchState[0])

    async def getTime(self) -> int:
        """
        @return: posix timestamp (uint32)
        """
        # TODO: check result code
        bytesResult = await self._getState(StateType.TIME)
        return Conversion.uint8_array_to_uint32(bytesResult)

    async def getDimmingAllowed(self) -> bool:
        stateVal = await self._getState(StateType.PWM_ALLOWED)
        # TODO: convert to uint8?
        return stateVal != 0

    async def getSwitchLocked(self) -> bool:
        stateVal = await self._getState(StateType.SWITCH_LOCKED)
        # TODO: convert to uint8?
        return stateVal != 0

    async def getPowerUsage(self) -> float:
        """
        @return: Power usage in Watt.
        """
        stateVal = await self._getState(StateType.POWER_USAGE)
        powerUsage = Conversion.uint8_array_to_int32(stateVal) / 1000.0
        return powerUsage

    async def getErrors(self) -> CrownstoneErrors:
        """
        @return: Errors
        """
        stateVal = await self._getState(StateType.ERROR_BITMASK)
        return CrownstoneErrors(Conversion.uint8_array_to_uint32(stateVal))

    async def getChipTemperature(self) -> float:
        """
        @return: Chip temperature in °C.
        """
        stateVal = await self._getState(StateType.TEMPERATURE)
        return Conversion.uint8_to_int8(stateVal)



    """
    ---------------  UTIL  ---------------
    """
    
    
    async def _getState(self, stateType) -> list:
        """
        Write get state command, and read result.
        :param stateType: StateType
        """
        resultPacket = await self.core.control._writeControlAndGetResult(ControlStateGetPacket(stateType).getPacket())

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
        await self.core.control._writeControlAndGetResult(packet.getPacket())
