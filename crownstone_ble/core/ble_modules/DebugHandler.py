from crownstone_core.Exceptions import CrownstoneError, CrownstoneException
from crownstone_core.packets.ResultPacket import ResultPacket
from crownstone_core.packets.debug.AdcChannelSwapsPacket import AdcChannelSwapsPacket
from crownstone_core.packets.debug.AdcRestartsPacket import AdcRestartsPacket
from crownstone_core.packets.debug.BootloaderInfoPacket import BootloaderInfoPacket, BOOTLOADER_INFO_PROTOCOL
from crownstone_core.packets.debug.PowerSamplesPacket import PowerSamplesPacket
from crownstone_core.packets.debug.SwitchHistoryPacket import SwitchHistoryListPacket
from crownstone_core.protocol.BluenetTypes import ResultValue
from crownstone_core.protocol.Characteristics import CrownstoneCharacteristics, DeviceCharacteristics
from crownstone_core.protocol.ControlPackets import ControlPacket, ControlType
from crownstone_core.protocol.ControlPackets import ControlPacketsGenerator
from crownstone_core.protocol.Services import CSServices
from crownstone_core.util.Conversion import Conversion


class DebugHandler:
	def __init__(self, bluetoothCore):
		self.core = bluetoothCore

	async def getHardwareVersion(self) -> str:
		""" Get the hardware version of the Crownstone as string. """
		buf = await self.core.ble.readCharacteristicWithoutEncryption(CSServices.DeviceInformation, DeviceCharacteristics.HardwareRevision)
		return Conversion.uint8_array_to_string(buf)

	async def getFirmwareVersion(self) -> str:
		""" Get the firmware version of the Crownstone as string. """
		buf = await self.core.ble.readCharacteristicWithoutEncryption(CSServices.DeviceInformation, DeviceCharacteristics.FirmwareRevision)
		return Conversion.uint8_array_to_string(buf)

	async def getBootloaderVersion(self) -> str:
		""" Get the bootloader version of the Crownstone as simple string. """
		bootloaderInfo = await self.getBootloaderInfo()
		if bootloaderInfo.protocol != BOOTLOADER_INFO_PROTOCOL:
			raise CrownstoneException(CrownstoneError.PROTOCOL_NOT_SUPPORTED)
		bootloaderVersion = f"{bootloaderInfo.major}.{bootloaderInfo.minor}.{bootloaderInfo.patch}"
		if bootloaderInfo.preReleaseVersion != 255:
			bootloaderVersion += f".{bootloaderInfo.preReleaseVersion}"
		return bootloaderVersion

	async def getBootloaderInfo(self) -> BootloaderInfoPacket:
		controlPacket = ControlPacket(ControlType.GET_BOOTLOADER_VERSION).serialize()
		result = await self._writeControlAndGetResult(controlPacket)
		if result.resultCode != ResultValue.SUCCESS:
			raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, "Result: " + str(result.resultCode))
		return BootloaderInfoPacket(result.payload)

	async def getUptime(self):
		""" Get the uptime of the crownstone in seconds. """
		controlPacket = ControlPacket(ControlType.GET_UPTIME).serialize()
		result = await self._writeControlAndGetResult(controlPacket)
		if result.resultCode != ResultValue.SUCCESS:
			raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, "Result: " + str(result.resultCode))
		return Conversion.uint8_array_to_uint32(result.payload)

	async def getAdcRestarts(self):
		"""	Get number of ADC restarts since boot. Returns an AdcRestartsPacket. """
		controlPacket = ControlPacket(ControlType.GET_ADC_RESTARTS).serialize()
		result = await self._writeControlAndGetResult(controlPacket)
		if result.resultCode != ResultValue.SUCCESS:
			raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, "Result: " + str(result.resultCode))
		return AdcRestartsPacket(result.payload)

	async def getAdcChannelSwaps(self):
		""" Get number of ADC channel swaps since boot. Returns an AdcChannelSwapsPacket. """
		controlPacket = ControlPacket(ControlType.GET_ADC_CHANNEL_SWAPS).serialize()
		result = await self._writeControlAndGetResult(controlPacket)
		if result.resultCode != ResultValue.SUCCESS:
			raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, "Result: " + str(result.resultCode))
		return AdcChannelSwapsPacket(result.payload)

	async def getSwitchHistory(self):
		""" Get the switch history. Returns a SwitchHistoryListPacket. """
		controlPacket = ControlPacket(ControlType.GET_SWITCH_HISTORY).serialize()
		result = await self._writeControlAndGetResult(controlPacket)
		if result.resultCode != ResultValue.SUCCESS:
			raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, "Result: " + str(result.resultCode))
		return SwitchHistoryListPacket(result.payload)

	async def getPowerSamples(self, samplesType):
		""" Get all power samples of the given type. Returns a list of PowerSamplesPacket. """
		allSamples = []
		index = 0
		while True:
			result = await self._getPowerSamples(samplesType, index)
			if result.resultCode == ResultValue.WRONG_PARAMETER:
				return allSamples
			elif result.resultCode == ResultValue.SUCCESS:
				samples = PowerSamplesPacket(result.payload)
				allSamples.append(samples)
				index += 1
			else:
				raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, "Result: " + str(result.resultCode))

	async def getPowerSamplesAtIndex(self, samplesType, index):
		""" Get power samples of given type at given index. Returns a PowerSamplesPacket. """
		result = await self._getPowerSamples(samplesType, index)
		if result.resultCode != ResultValue.SUCCESS:
			raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, "Result: " + str(result.resultCode))
		return PowerSamplesPacket(result.payload)

	async def _getPowerSamples(self, samplesType, index):
		""" Get power samples of given type at given index, but don't check result code. """
		controlPacket = ControlPacketsGenerator.getPowerSamplesRequestPacket(samplesType, index)
		return await self._writeControlAndGetResult(controlPacket)

	async def _writeControlPacket(self, packet):
		""" Write the control packet. """
		await self.core.control._writeControlPacket(packet)

	async def _writeControlAndGetResult(self, controlPacket) -> ResultPacket:
		return await self.core.control._writeControlAndGetResult(controlPacket)
