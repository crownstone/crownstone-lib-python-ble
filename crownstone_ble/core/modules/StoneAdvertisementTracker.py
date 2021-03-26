import logging
import time

from crownstone_core.Enums import CrownstoneOperationMode
from crownstone_core.packets.Advertisement import Advertisement
from crownstone_core.packets.ServiceData import ServiceData
from crownstone_core.packets.serviceDataParsers.containers.elements.AdvTypes import AdvType

_LOGGER = logging.getLogger(__name__)

AMOUNT_OF_REQUIRED_MATCHES = 2

"""
Class that validates advertisements from a single MAC address.

Each 'update()':
- Checks if the advertisement can be validated, and sets .verified = True if so.
"""
class StoneAdvertisementTracker:

    def __init__(self, cleanupCallback):
        self.address           = None
        self.uniqueIdentifier = None
        self.crownstoneId     = 0
        self.cleanupCallback  = None
        self.verified         = False
        self.duplicate        = False

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


    def update(self, advertisement: Advertisement):
        self.address = advertisement.address

        if advertisement.isCrownstoneFamily():
            self.handlePayload(advertisement)


    def handlePayload(self, advertisement: Advertisement):
        if advertisement.operationMode == CrownstoneOperationMode.DFU:
            self.verified = True
            self.consecutiveMatches = 0
        elif advertisement.operationMode == CrownstoneOperationMode.SETUP:
            self.verified = True
            self.consecutiveMatches = 0
        else:
            self.verify(advertisement.serviceData)

        self.timeoutTime = time.time() + self.timeoutDuration

        if hasattr(advertisement.serviceData.payload, "uniqueIdentifier"):
            self.uniqueIdentifier = advertisement.serviceData.payload.uniqueIdentifier



    # check if we consistently get the ID of this crownstone.
    def verify(self, serviceData):
        if not hasattr(serviceData.payload, "uniqueIdentifier"):
            return

        if not serviceData.decrypted:
            _LOGGER.debug(f"Invalidate {self.address}, decrypted={serviceData.decrypted}")
            self.invalidateDevice(serviceData)
            return

        if not hasattr(serviceData.payload, "validation") or not hasattr(serviceData.payload, "crownstoneId"):
            return

        _LOGGER.debug(f"Check {self.address}"
                      f", id={serviceData.payload.crownstoneId}"
                      f", uniqueIdentifier={serviceData.payload.uniqueIdentifier}"
                      f", validation={serviceData.payload.validation}"
                      f", opCode={serviceData.opCode}"
                      f", advType={serviceData.payload.type}")

        if self.uniqueIdentifier == serviceData.payload.uniqueIdentifier:
            self.duplicate = True
            return

        self.duplicate = False

        if serviceData.opCode == 7:
            if serviceData.payload.validation == 0xFA:
                if serviceData.payload.type == AdvType.EXTERNAL_STATE or serviceData.payload.type == AdvType.EXTERNAL_ERROR:
                    # this is an external state payload, this means that the crownstoneId does not belong to the crownstone that broadcast it.
                    return

                if serviceData.payload.crownstoneId == self.crownstoneId:
                    self.addValidMeasurement(serviceData)
                else:
                    self.invalidateDevice(serviceData)
            else:
                self.invalidateDevice(serviceData)

    def addValidMeasurement(self, serviceData: ServiceData):
        _LOGGER.debug(f"addValidMeasurement {self.address}")
        if self.consecutiveMatches >= AMOUNT_OF_REQUIRED_MATCHES:
            self.verified = True
            self.consecutiveMatches = 0
        else:
            self.consecutiveMatches += 1
        
        self.crownstoneId = serviceData.payload.crownstoneId


    def invalidateDevice(self, serviceData: ServiceData):
        if serviceData.payload.type != AdvType.EXTERNAL_STATE and serviceData.payload.type != AdvType.EXTERNAL_ERROR:
            self.crownstoneId = serviceData.payload.crownstoneId
        
        self.consecutiveMatches = 0
        self.verified = False
