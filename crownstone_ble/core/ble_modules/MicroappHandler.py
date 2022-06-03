import logging

from crownstone_core.packets.microapp.MicroappHeaderPacket import MicroappHeaderPacket
from crownstone_core.packets.microapp.MicroappInfoPacket import MicroappInfoPacket
from crownstone_core.packets.microapp.MicroappUploadPacket import MicroappUploadPacket
from crownstone_core.protocol.BlePackets import ControlPacket
from crownstone_core.protocol.BluenetTypes import ControlType
from crownstone_ble.core.ble_modules.ControlHandler import ControlHandler

_LOGGER = logging.getLogger(__name__)


class MicroappHandler:
    def __init__(self, control: ControlHandler):
        self.control = control
        pass

    # It looks like the UART python library cannot send large commands.
    MAX_CHUNK_SIZE = 32

    async def getMicroappInfo(self) -> MicroappInfoPacket:
        resultPacket = await self.control._writeControlAndGetResult(ControlPacket(ControlType.MICROAPP_GET_INFO).serialize())
        _LOGGER.info(f"getMicroappInfo {resultPacket}")
        infoPacket = MicroappInfoPacket(resultPacket.payload)
        return infoPacket

    async def uploadMicroapp(self, data: bytearray, index: int = 0, protocol: int = 0, chunkSize: int = MAX_CHUNK_SIZE):
        chunkSize = min(chunkSize, MicroappHandler.MAX_CHUNK_SIZE)

        for i in range(0, len(data), chunkSize):
            chunk = data[i : i + chunkSize]
            # Pad the chunk with 0xFF, so the size is a multiple of 4.
            if len(chunk) % 4:
                if isinstance(chunk, bytes):
                    chunk = bytearray(chunk)
                chunk.extend((4 - (len(chunk) % 4)) * [0xFF])
            await self._uploadMicroappChunk(index, protocol, chunk, i)

    async def _uploadMicroappChunk(self, index: int, protocol: int, data: bytearray, offset: int):
        _LOGGER.info(f"Upload microapp chunk index={index} offset={offset} size={len(data)}")
        header = MicroappHeaderPacket(appIndex=index, protocol=protocol)
        packet = MicroappUploadPacket(header, offset, data)
        controlPacket = ControlPacket(ControlType.MICROAPP_UPLOAD).loadByteArray(packet.serialize()).serialize()
        await self.control._writeControlAndWaitForSuccess(controlPacket)
        _LOGGER.info(f"uploaded chunk offset={offset}")

    async def validateMicroapp(self, index, protocol):
        packet = MicroappHeaderPacket(index, protocol)
        controlPacket = ControlPacket(ControlType.MICROAPP_VALIDATE).loadByteArray(packet.serialize()).serialize()
        await self.control._writeControlAndGetResult(controlPacket)

    async def enableMicroapp(self, index, protocol):
        packet = MicroappHeaderPacket(index, protocol)
        controlPacket = ControlPacket(ControlType.MICROAPP_ENABLE).loadByteArray(packet.serialize()).serialize()
        await self.control._writeControlAndGetResult(controlPacket)

    async def removeMicroapp(self, index, protocol):
        packet = MicroappHeaderPacket(index, protocol)
        controlPacket = ControlPacket(ControlType.MICROAPP_REMOVE).loadByteArray(packet.serialize()).serialize()
        await self.control._writeControlAndWaitForSuccess(controlPacket)
        _LOGGER.info(f"Removed app {index}")