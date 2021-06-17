from crownstone_core import Conversion
from crownstone_core.protocol.BlePackets import ControlStateGetPacket, ControlStateSetPacket
from crownstone_core.protocol.BluenetTypes import StateType
from crownstone_ble import CrownstoneBle

class DevHandler:
    def __init__(self, bluetoothCore: CrownstoneBle):
        self.core = bluetoothCore
        
    async def setCurrentThresholdDimmer(self, currentAmp: float):
        packet = ControlStateSetPacket(StateType.CURRENT_CONSUMPTION_THRESHOLD_DIMMER)
        packet.loadUInt16(currentAmp * 1000)
        await self.core.state._setState(StateType.SWITCH_STATE, packet)

    async def getCurrentThresholdDimmer(self) -> float:
        rawState = await self.core.state._getState(StateType.CURRENT_CONSUMPTION_THRESHOLD_DIMMER)
        packet = ControlStateSetPacket(StateType.CURRENT_CONSUMPTION_THRESHOLD_DIMMER)
        currentThresholdMilliAmp = Conversion.uint8_array_to_uint16(rawState)
        return currentThresholdMilliAmp / 1000.0
