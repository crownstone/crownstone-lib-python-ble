import logging

from crownstone_core import Conversion
from crownstone_core.packets.microapp.MicroappHeaderPacket import MicroappHeaderPacket
from crownstone_core.packets.microapp.MicroappInfoPacket import MicroappInfoPacket
from crownstone_core.packets.microapp.MicroappUploadPacket import MicroappUploadPacket
from crownstone_core.protocol.BlePackets import ControlStateGetPacket, ControlStateSetPacket, ControlPacket
from crownstone_core.protocol.BluenetTypes import StateType, ControlType

_LOGGER = logging.getLogger(__name__)

class DevHandler:
    def __init__(self, bluetoothCore):
        self.core = bluetoothCore
        
    async def setCurrentThresholdDimmer(self, currentAmp: float):
        packet = ControlStateSetPacket(StateType.CURRENT_CONSUMPTION_THRESHOLD_DIMMER)
        packet.loadUInt16(currentAmp * 1000)
        await self.core.state._setState(StateType.SWITCH_STATE, packet)

    async def getCurrentThresholdDimmer(self) -> float:
        rawState = await self.core.state._getState(StateType.CURRENT_CONSUMPTION_THRESHOLD_DIMMER)
        currentThresholdMilliAmp = Conversion.uint8_array_to_uint16(rawState)
        return currentThresholdMilliAmp / 1000.0

    async def getMicroappInfo(self) -> MicroappInfoPacket:
        resultPacket = await self._writeControlAndGetResult(ControlPacket(ControlType.MICROAPP_GET_INFO).serialize())
        _LOGGER.info(f"getMicroappInfo {resultPacket}")
        infoPacket = MicroappInfoPacket(resultPacket.payload)
        return infoPacket

    async def uploadMicroapp(self, data: bytearray, index: int = 0, chunkSize: int = 128):
        for i in range(0, len(data), chunkSize):
            chunk = data[i : i + chunkSize]
            # Pad the chunk with 0xFF, so the size is a multiple of 4.
            if len(chunk) % 4:
                if isinstance(chunk, bytes):
                    chunk = bytearray(chunk)
                chunk.extend((4 - (len(chunk) % 4)) * [0xFF])
            await self.uploadMicroappChunk(index, chunk, i)

    async def uploadMicroappChunk(self, index: int, data: bytearray, offset: int):
        _LOGGER.info(f"Upload microapp chunk index={index} offset={offset} size={len(data)}")
        header = MicroappHeaderPacket(appIndex=index)
        packet = MicroappUploadPacket(header, offset, data)
        controlPacket = ControlPacket(ControlType.MICROAPP_UPLOAD).loadByteArray(packet.serialize()).serialize()
        await self._writeControlAndWaitForSuccess(controlPacket)
        _LOGGER.info(f"uploaded chunk offset={offset}")
        # TODO: return the final result?

    async def validateMicroapp(self, index):
        packet = MicroappHeaderPacket(index)
        controlPacket = ControlPacket(ControlType.MICROAPP_VALIDATE).loadByteArray(packet.serialize()).serialize()
        await self._writeControlAndGetResult(controlPacket)

    async def enableMicroapp(self, index):
        packet = MicroappHeaderPacket(index)
        controlPacket = ControlPacket(ControlType.MICROAPP_ENABLE).loadByteArray(packet.serialize()).serialize()
        await self._writeControlAndGetResult(controlPacket)

    async def removeMicroapp(self, index):
        packet = MicroappHeaderPacket(index)
        controlPacket = ControlPacket(ControlType.MICROAPP_REMOVE).loadByteArray(packet.serialize()).serialize()
        await self._writeControlAndWaitForSuccess(controlPacket)
        _LOGGER.info(f"Removed app {index}")