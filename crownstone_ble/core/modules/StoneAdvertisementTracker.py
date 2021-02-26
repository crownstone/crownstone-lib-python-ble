import logging
import time

_LOGGER = logging.getLogger(__name__)

AMOUNT_OF_REQUIRED_MATCHES = 2

"""
Class that validates advertisements from a single MAC address.

Each 'update()':
- Checks if the advertisement can be validated, and sets .verified = True if so.
- Calculates average RSSI. <REMOVED>
        
<removed>
    Each 'tick()':
    - Removes RSSI measurements that are older than <rssiTimeoutDuration> seconds, and recalculates average RSSI.
    - Calls 'cleanupCallback' if no advertisement has been received for <timeoutDuration> seconds.
</removed>

TODO:
- Move checking of opcode and checking of validation value to the service data parser.
    - Alex: good point, these should be util methods on the service data class.
- Use locks, currently only 'handlePayload()' acquires a lock, so that doesn't prevent concurrency issues.
    - Alex: Fully removed locks and threading.
- Clarify which variables are private, which are public, and which are config.
- Remove or explain rssiTimeoutList.
    - Alex: removed.
"""
class StoneAdvertisementTracker:

    def __init__(self, cleanupCallback):
        self.rssi = None
        self.name = ""
        self.address = None
        self.crownstoneId = 0
        self.cleanupCallback = None
        self.uniqueIdentifier = 0
        self.verified = False
        self.dfu = False
        
        # config
        self.timeoutDuration = 10  # seconds
        self.consecutiveMatches = 0
        
        self.timeoutTime = time.time() + self.timeoutDuration

        self.cleanupCallback = cleanupCallback

    def checkForCleanup(self):
        now = time.time()
        # check time in self.timeoutTime with current time
        if self.timeoutTime <= now:
            _LOGGER.debug(f"Timeout {self.address}")
            self.cleanupCallback()


    def update(self, advertisement):
        self.name = advertisement.name
        self.address = advertisement.address

        if advertisement.isCrownstoneFamily():
            self.handlePayload(advertisement)

    def handlePayload(self, advertisement):
        # this field can be manipulated during the loop in calculate. To avoid this, we lock the threads for the duration of the loop
        self.rssi = advertisement.rssi

        if advertisement.isInDFUMode():
            self.verified = True
            self.dfu = True
            self.consecutiveMatches = 0
        else:
            self.verify(advertisement.serviceData)

        self.timeoutTime = time.time() + self.timeoutDuration


    # check if we consistently get the ID of this crownstone.
    def verify(self, serviceData):
        if serviceData.isInSetupMode():
            self.verified = True
            self.consecutiveMatches = 0
        else:
            if not serviceData.dataReadyForUse:
                _LOGGER.debug(f"Invalidate {self.address}, dataReadyForUse={serviceData.dataReadyForUse}")
                self.invalidateDevice(serviceData)
            else:
                _LOGGER.debug(f"Check {self.address}"
                              f", id={serviceData.crownstoneId}"
                              f", uniqueIdentifier={serviceData.uniqueIdentifier}"
                              f", validation={serviceData.validation}"
                              f", opCode={serviceData.opCode}"
                              f", stateOfExternalCrownstone={serviceData.stateOfExternalCrownstone}")

                if self.uniqueIdentifier != serviceData.uniqueIdentifier:
                    if serviceData.validation != 0 and serviceData.opCode == 5:
                        if serviceData.validation == 0xFA and serviceData.dataType != 1: # datatype 1 is the error packet
                            self.addValidMeasurement(serviceData)
                        elif serviceData.validation != 0xFA and serviceData.dataType != 1: # datatype 1 is the error packet
                            self.invalidateDevice(serviceData)
                    elif serviceData.validation != 0 and serviceData.opCode == 3:
                        if serviceData.dataType != 1:
                            if serviceData.validation == 0xFA:
                                self.addValidMeasurement(serviceData)
                            elif serviceData.validation != 0xFA:
                                self.invalidateDevice(serviceData)
                        else:
                            pass # do nothing, skip these messages (usually error states)
                    else:
                        if not serviceData.stateOfExternalCrownstone:
                            if serviceData.crownstoneId == self.crownstoneId:
                                self.addValidMeasurement(serviceData)
                            else:
                                self.invalidateDevice(serviceData)
        
        self.uniqueIdentifier = serviceData.uniqueIdentifier
        

    
    def addValidMeasurement(self, serviceData):
        _LOGGER.debug(f"addValidMeasurement {self.address}")
        if self.consecutiveMatches >= AMOUNT_OF_REQUIRED_MATCHES:
            self.verified = True
            self.consecutiveMatches = 0
        else:
            self.consecutiveMatches += 1
        
        self.crownstoneId = serviceData.crownstoneId


    def invalidateDevice(self, serviceData):
        if not serviceData.stateOfExternalCrownstone:
            self.crownstoneId = serviceData.crownstoneId
        
        self.consecutiveMatches = 0
        self.verified = False
