from typing import Optional, Union
import logging

from . import frametypes
from .commands import BBFrame, BBFrameTypeSwitch


class BBCharacteristic:
    GATT_CHARACTERISTIC_UUID: str
    READ: Optional[Union[BBFrame, BBFrameTypeSwitch]] = None
    WRITE: Optional[BBFrame] = None

    characteristic = None
    callback = None

    def __init__(self, characteristic):
        self.characteristic = characteristic
        self.log = logging.getLogger(f"Characteristic {self.GATT_CHARACTERISTIC_UUID}")
        if self.READ:
            self.log.debug("Subscribing.")
            characteristic.enable_notifications()

    def process(self, value):
        frames = list(self.READ.process(self, value))
        if self.callback:
            self.log.debug("Calling callback.")
            cb = self.callback
            self.callback = None
            cb(self, frames)
        return frames

    def read(self, callback=None):
        self.callback = callback
        if not self.characteristic:
            raise Exception("Characteristic not discovered yet!")
        self.characteristic.read_value()


class BCSec(BBCharacteristic):
    """
    time of day in seconds, after power-up it starts with 0, needs to be set after initial connection to correct time.
    Log entry is generated when seconds reach 86400 (24 Hours) and seconds are reset to 0.
    """

    GATT_CHARACTERISTIC_UUID = "4b616901-40bd-428b-bf06-698e5e422cd9"
    READ = frametypes.SecFrame
    WRITE = frametypes.SecFrame


class BCLog(BBCharacteristic):
    """
    Each read access auto increments the day counter until current day is reach, then it wraps around.
    Reading starts at day first available day.
    First all type 0x00 entries are send, then all type 0x01 frames etc.
    Note: Reading "sec" characteristics resets read pointer to earliest available log entry.
    """

    GATT_CHARACTERISTIC_UUID = "4b616907-40bd-428b-bf06-698e5e422cd9"
    READ = BBFrameTypeSwitch(
        "36xB",  # 36th byte is the frame type indicator
        {
            (0x00,): frametypes.LogEntryDaysFrame,
            (0x01,): frametypes.LogEntryFrameOld,
            (0x02,): frametypes.LogEntryFrameNew,
        },
    )

    # Helper variable to reverse the day counter.
    max_days_observed = 0


class BCLive(BBCharacteristic):
    GATT_CHARACTERISTIC_UUID = "4b616912-40bd-428b-bf06-698e5e422cd9"
    READ = BBFrameTypeSwitch(
        "BB",  # first two bytes indicate frame type
        {
            # byte 0: type
            # byte 1: length
            (0x00, 0x07): frametypes.BCLiveMeasurementsFrame,
            (0x01, 0x09): frametypes.BCSolarChargerEBLFrame,
            (0x01, 0x0B): frametypes.BCSolarChargerStandardFrame,
            (0x01, 0x0C): frametypes.BCSolarChargerExtendedFrame,
            (0x02, 0x10): frametypes.BCBatteryComputer1Frame,
            (0x03, 0x0F): frametypes.BCBatteryComputer2Frame,
            (0x04, 0x01): frametypes.BCIntradayLogEntryFrame,
            (0x05, 0x0A): frametypes.BCBoosterDataFrame,
            (0x05, 0x04): frametypes.BCNoBoosterDataFrame,
        },
    )


ALL_CHARACTERISTICS = (BCLive, BCLog, BCSec)
