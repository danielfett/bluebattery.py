from hummable.bledevice import BLEDevice
from .bbcharacteristics import BCLog, BCLive, BCSec


class BlueBattery(BLEDevice):
    FILTERS = [{"name": "BlueBattery_"}]
    PAIRING_REQUIRED = False

    CHARACTERISTICS = [BCSec, BCLive, BCLog]
