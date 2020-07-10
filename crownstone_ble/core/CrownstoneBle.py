from crownstone_core.Exceptions import CrownstoneError, CrownstoneBleException, CrownstoneException
from crownstone_core.core.modules.EncryptionSettings import EncryptionSettings
from crownstone_core.topics.Topics import Topics
from crownstone_core.util.JsonFileStore import JsonFileStore

from crownstone_ble.Exceptions import BleError
from crownstone_ble.constants import ScanBackends
from crownstone_ble.core.BleEventBus import BleEventBus
from crownstone_ble.core.ble_modules.BleHandler import BleHandler
from crownstone_ble.core.ble_modules.BroadcastHandler import BroadcastHandler
from crownstone_ble.core.ble_modules.ControlHandler import ControlHandler
from crownstone_ble.core.ble_modules.SetupHandler import SetupHandler
from crownstone_ble.core.ble_modules.StateHandler import StateHandler
from crownstone_ble.core.modules.Gatherer import Gatherer
from crownstone_ble.core.modules.NearestSelector import NearestSelector
from crownstone_ble.core.modules.NormalModeChecker import NormalModeChecker
from crownstone_ble.core.modules.RssiChecker import RssiChecker
from crownstone_ble.core.modules.SetupChecker import SetupChecker
from crownstone_ble.topics.SystemBleTopics import SystemBleTopics


class CrownstoneBle:
    
    def __init__(self, hciIndex = 0, scanBackend = ScanBackends.Bluepy):
        self.settings  = EncryptionSettings()
        self.control   = ControlHandler(self)
        self.broadcast = BroadcastHandler(self, hciIndex)
        self.setup     = SetupHandler(self)
        self.state     = StateHandler(self)
        self.ble       = BleHandler(self.settings, hciIndex, scanBackend)
        
    def shutDown(self):
        self.ble.shutDown()
    
    def setSettings(self, adminKey, memberKey, basicKey, serviceDataKey, localizationKey, meshApplicationKey, meshNetworkKey, referenceId = "PythonLib"):
        self.settings.loadKeys(adminKey, memberKey, basicKey, serviceDataKey, localizationKey, meshApplicationKey, meshNetworkKey, referenceId)
        
        
    def loadSettingsFromFile(self, path):
        fileReader = JsonFileStore(path)
        data = fileReader.getData()
        
        if "admin" not in data:
            raise CrownstoneBleException(CrownstoneError.ADMIN_KEY_REQURED)
        if "member" not in data:
            raise CrownstoneBleException(CrownstoneError.MEMBER_KEY_REQUIRED)
        if "basic" not in data:
            raise CrownstoneBleException(CrownstoneError.BASIC_KEY_REQURED)
        if "serviceDataKey" not in data:
            raise CrownstoneBleException(CrownstoneError.SERVICE_DATA_KEY_REQUIRED)
        if "localizationKey" not in data:
            raise CrownstoneBleException(CrownstoneError.LOCALIZATION_KEY_REQUIRED)
        if "meshApplicationKey" not in data:
            raise CrownstoneBleException(CrownstoneError.MESH_APP_KEY)
        if "meshNetworkKey" not in data:
            raise CrownstoneBleException(CrownstoneError.MESH_NETWORK_KEY)

        self.setSettings(data["admin"], data["member"], data["basic"], data["serviceDataKey"], data["localizationKey"], data["meshApplicationKey"], data["meshNetworkKey"])
        

    def connect(self, address, ignoreEncryption=False, connectionSettings=None):
        self.ble.connect(address, connectionSettings)
        if not ignoreEncryption:
            try:
                self.control.getAndSetSessionNone()
            except CrownstoneBleException as err:
                # the only relevant error here is this one. If it is any other, the Crownstone is in the wrong mode
                if err.type is BleError.COULD_NOT_VALIDATE_SESSION_NONCE:
                    raise err


    def setupCrownstone(self, address, sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor):
        self.connect(address)
        self.setup.setup(address, sphereId, crownstoneId, meshDeviceKey, ibeaconUUID, ibeaconMajor, ibeaconMinor)
        self.disconnect()
        
    
    def disconnect(self):
        self.ble.disconnect()
    
    def startScanning(self, scanDuration=3):
        self.ble.startScanning(scanDuration)

    def stopScanning(self):
        self.ble.stopScanning()

    def getCrownstonesByScanning(self, scanDuration=3):
        gatherer = Gatherer()
    
        subscriptionIdValidated = BleEventBus.subscribe(Topics.advertisement,             lambda advertisementData: gatherer.handleAdvertisement(advertisementData, True)          )
        subscriptionIdAll       = BleEventBus.subscribe(SystemBleTopics.rawAdvertisement, lambda advertisement: gatherer.handleAdvertisement(advertisement.getDictionary(), False) )
    
        self.ble.startScanning(scanDuration=scanDuration)
    
        BleEventBus.unsubscribe(subscriptionIdValidated)
        BleEventBus.unsubscribe(subscriptionIdAll)
        
        return gatherer.getCollection()

    def isCrownstoneInSetupMode(self, address, scanDuration=3, waitUntilInRequiredMode=False):
        # print("Checking if it is in setup mode, address", address)
        checker = SetupChecker(address, waitUntilInRequiredMode)
        subscriptionId = BleEventBus.subscribe(Topics.advertisement, checker.handleAdvertisement)

        self.ble.startScanning(scanDuration=scanDuration)

        BleEventBus.unsubscribe(subscriptionId)

        return checker.getResult()

    def isCrownstoneInNormalMode(self, address, scanDuration=3, waitUntilInRequiredMode=False):
        # print("Checking if it is in normal mode, address", address)
        checker = NormalModeChecker(address, waitUntilInRequiredMode)
        subscriptionId = BleEventBus.subscribe(SystemBleTopics.rawAdvertisement, lambda advertisement: checker.handleAdvertisement(advertisement.getDictionary()))

        self.ble.startScanning(scanDuration=scanDuration)

        BleEventBus.unsubscribe(subscriptionId)

        return checker.getResult()

    def getRssiAverage(self, address, scanDuration=3):
        checker = RssiChecker(address)
        subscriptionId = BleEventBus.subscribe(SystemBleTopics.rawAdvertisement, lambda advertisement: checker.handleAdvertisement(advertisement.getDictionary()))

        self.ble.startScanning(scanDuration=scanDuration)

        BleEventBus.unsubscribe(subscriptionId)

        return checker.getResult()

    def getNearestCrownstone(self, rssiAtLeast=-100, scanDuration=3, returnFirstAcceptable=False, addressesToExclude=[]):
        return self._getNearest(False, rssiAtLeast, scanDuration, returnFirstAcceptable, False, addressesToExclude)
    
    
    def getNearestValidatedCrownstone(self, rssiAtLeast=-100, scanDuration=3, returnFirstAcceptable=False, addressesToExclude=[]):
        return self._getNearest(False, rssiAtLeast, scanDuration, returnFirstAcceptable, True, addressesToExclude)
    
    
    def getNearestSetupCrownstone(self, rssiAtLeast=-100, scanDuration=3, returnFirstAcceptable=False, addressesToExclude=[]):
        return self._getNearest(True, rssiAtLeast, scanDuration, returnFirstAcceptable, True, addressesToExclude)
    

    def _getNearest(self, setup, rssiAtLeast, scanDuration, returnFirstAcceptable, validated, addressesToExclude):
        addressesToExcludeSet = set()
        for data in addressesToExclude:
            if isinstance(data, dict):
                if "address" in data:
                    addressesToExcludeSet.add(data["address"].lower())
                else:
                    raise CrownstoneException(CrownstoneError.INVALID_ADDRESS, "Addresses to Exclude is either an array of addresses (like 'f7:19:a4:ef:ea:f6') or an array of dicts with the field 'address'")
            else:
                addressesToExcludeSet.add(data.lower())

        selector = NearestSelector(setup, rssiAtLeast, returnFirstAcceptable, addressesToExcludeSet)
    
        topic = Topics.advertisement
        if not validated:
            topic = SystemBleTopics.rawAdvertisement
            subscriptionId = BleEventBus.subscribe(topic, lambda advertisement: selector.handleAdvertisement(advertisement.getDictionary()))
        else:
            subscriptionId = BleEventBus.subscribe(topic, lambda advertisementData: selector.handleAdvertisement(advertisementData))
    

        
        self.ble.startScanning(scanDuration=scanDuration)
    
        BleEventBus.unsubscribe(subscriptionId)
        
        return selector.getNearest()