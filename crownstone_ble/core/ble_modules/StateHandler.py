from crownstone_core import Conversion
from crownstone_core.Exceptions import CrownstoneError, CrownstoneException
from crownstone_core.packets.ResultPacket import ResultPacket
from crownstone_core.protocol.BlePackets import ControlStateGetPacket
from crownstone_core.protocol.BluenetTypes import StateType
from crownstone_core.protocol.Characteristics import CrownstoneCharacteristics
from crownstone_core.protocol.Services import CSServices


class StateHandler:
    def __init__(self, bluetoothCore):
        self.core = bluetoothCore
        
    def getSwitchState(self):
        return self._getState(StateType.SWITCH_STATE)[0]
    
    def getSwitchStateFloat(self):
        switchState = self._getState(StateType.SWITCH_STATE)[0]
        
        returnState = 0.0
        if switchState == 128:
            returnState = 1.0
        elif switchState <= 100:
            returnState = 0.01 * switchState * 0.99
        
        return returnState
    
    def getTime(self):
        bytesResult = self._getState(StateType.TIME)
        return Conversion.uint8_array_to_uint32(bytesResult)
    
    
    
    
    """
    ---------------  UTIL  ---------------
    """
    
    
    def _writeToState(self):
        pass
    
    def _getState(self, stateType):
        """
        :param stateType: StateType
        """
        result = self.core.ble.setupSingleNotification(CSServices.CrownstoneService, CrownstoneCharacteristics.Result, lambda: self._requestState(stateType))

        resultPacket = ResultPacket(result)
        if resultPacket.valid:
            # the payload of the resultPacket is padded with stateType and ID at the beginning

            state = []
            for i in range(6, len(resultPacket.payload)):
                state.append(resultPacket.payload[i])

            return state
        else:
            raise CrownstoneException(CrownstoneError.INCORRECT_RESPONSE_LENGTH, "Result is invalid")

    def _requestState(self, stateType):
        self.core.ble.writeToCharacteristic(
            CSServices.CrownstoneService,
            CrownstoneCharacteristics.Control,
            ControlStateGetPacket(stateType).getPacket()
        )