from bluepy.btle import BTLEException

from crownstone_core.protocol.BluenetTypes import ProcessType

from crownstone_ble.Exceptions import BleError
from crownstone_core.Exceptions import CrownstoneException, CrownstoneException
from crownstone_core.packets.SessionDataPacket import SessionDataPacket
from crownstone_core.protocol.Characteristics import CrownstoneCharacteristics
from crownstone_core.protocol.ControlPackets import ControlPacketsGenerator
from crownstone_core.protocol.Services import CSServices
from crownstone_core.util.EncryptionHandler import EncryptionHandler, CHECKSUM
from crownstone_core.packets.ResultPacket import ResultPacket
from crownstone_core.Exceptions import CrownstoneError, CrownstoneException
from crownstone_core.protocol.BluenetTypes import ResultValue
from crownstone_core.packets.PowerSamplesPacket import PowerSamplesPacket

class DebugHandler:
	def __init__(self, bluetoothCore):
		self.core = bluetoothCore

	def getPowerSamples(self, samplesType):
		""" Get all power samples of the given type. """
		allSamples = []
		index = 0
		while True:
			result = self._getPowerSamples(samplesType, index)
			if (result.resultCode == ResultValue.WRONG_PARAMETER):
				return allSamples
			elif (result.resultCode == ResultValue.SUCCESS):
				samples = PowerSamplesPacket(result.payload)
				allSamples.append(samples)
				index += 1
			else:
				raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, "Result: " + str(result.resultCode))

	def getPowerSamplesAtIndex(self, samplesType, index):
		""" Get power samples of given type at given index. """
		result = self._getPowerSamples(samplesType, index)
		if (result.resultCode != ResultValue.SUCCESS):
			raise CrownstoneException(CrownstoneError.RESULT_NOT_SUCCESS, "Result: " + str(result.resultCode))
		return result

	def _getPowerSamples(self, samplesType, index):
		""" Get power samples of given type at given index, but don't check result code. """
		controlPacket = ControlPacketsGenerator.getPowerSamplesRequestPacket(samplesType, index)
		return self._writeControlAndGetResult(controlPacket)

	def _writeControlPacket(self, packet):
		""" Write the control packet. """
		self.core.ble.writeToCharacteristic(CSServices.CrownstoneService, CrownstoneCharacteristics.Control, packet)

	def _writeControlAndGetResult(self, controlPacket):
		""" Writes the control packet, and returns the result packet. """
		result = self.core.ble.setupSingleNotification(CSServices.CrownstoneService, CrownstoneCharacteristics.Result, lambda: self._writeControlPacket(controlPacket))
		resultPacket = ResultPacket(result)
		if resultPacket.valid != True:
			raise CrownstoneException(CrownstoneError.INCORRECT_RESPONSE_LENGTH, "Result is invalid")
		return resultPacket
