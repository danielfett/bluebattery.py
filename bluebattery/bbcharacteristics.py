import asyncio
from concurrent.futures import CancelledError

from . import frametypes
from .commands import BBFrameTypeSwitch
from hummable.characteristics import ReadPeriodicCharacteristic


class BCLog(ReadPeriodicCharacteristic):
    """
    This characteristic is used to read the log entries from the battery computer.
    Each read access auto increments the day counter until current day is reach, then it wraps around.
    Reading starts at day first available day.
    First all type 0x00 entries are send, then all type 0x01 frames etc.
    Note: Reading "sec" characteristics resets read pointer to earliest available log entry.
    """

    UUID = "4b616907-40bd-428b-bf06-698e5e422cd9"
    PERIOD = 1
    WAIT_BETWEEN = 60 * 60  # once per hour
    MAX_LOG_FRAMES = 60 * 3  # 60 days, three types of log entries
    INITIAL_WAIT = 30

    async def read_periodically(self):
        self.log.debug(f"Starting periodic read of {self.UUID}")
        try:
            # wait some time so that sec has been read
            await asyncio.sleep(self.INITIAL_WAIT)
            while True:
                self.log.debug(f"Starting new readout of logs from {self.UUID}")
                self.reset_log_info()
                while True:
                    # read characteristic
                    data = await self.client.read_gatt_char(self.UUID)
                    self.log.debug(
                        f"Read {self.UUID}: {' '.join(f'{b:02x}' for b in data)}"
                    )

                    parsed = self.parse(data)

                    wrapped = False
                    for frame in parsed:
                        self.log.debug(f"Parsed frame: {frame}")
                        self.output_callback(frame)
                        if self.check_log_has_wrapped(frame):
                            wrapped = True
                            break

                    if wrapped:
                        self.log.debug("Log has wrapped, stopping readout")
                        break

                    # wait a second before continuing reading
                    await asyncio.sleep(self.PERIOD)
                await asyncio.sleep(self.WAIT_BETWEEN)
        except CancelledError:
            self.log.debug("Task cancelled")
        except Exception as e:
            self.log.exception("Error reading characteristic")

    def reset_log_info(self):
        self.log_info = {
            "first_day_seen": None,
            "first_frametype_seen": None,
            "frames_seen": 0,
        }

    def check_log_has_wrapped(self, frame):
        frametype, measurement, values = frame
        self.log_info["frames_seen"] += 1
        if self.log_info["frames_seen"] == self.MAX_LOG_FRAMES:
            return True

        if not self.log_info["first_frametype_seen"]:
            self.log_info["first_frametype_seen"] = frametype
            self.log_info["first_day_seen"] = values["day_counter"]

        elif (
            frametype == self.log_info["first_frametype_seen"]
            and values["day_counter"] == self.log_info["first_day_seen"]
        ):
            # finished reading log entries
            return True
        return False

    def parse(self, data):
        yield from BBFrameTypeSwitch(
            "36xB",  # 36th byte is the frame type indicator
            {
                (0x00,): frametypes.LogEntryDaysFrame,
                (0x01,): frametypes.LogEntryFrameOld,
                (0x02,): frametypes.LogEntryFrameNew,
                (0x03,): frametypes.LogEntryFrameLargeSolarCurrent,  ###KS
            },
        ).process(self, data)


class BCSec(ReadPeriodicCharacteristic):
    """
    time of day in seconds, after power-up it starts with 0, needs to be set after initial connection to correct time.
    Log entry is generated when seconds reach 86400 (24 Hours) and seconds are reset to 0.
    """

    UUID = "4b616901-40bd-428b-bf06-698e5e422cd9"
    PERIOD = 10 * 60  # once every 10 minutes

    def parse(self, data):
        yield from frametypes.SecFrame.process(self, data)


class BCLive(ReadPeriodicCharacteristic):
    UUID = "4b616912-40bd-428b-bf06-698e5e422cd9"
    PERIOD = 0.33

    def parse(self, data):
        yield from BBFrameTypeSwitch(
            "BB",  # first two bytes indicate frame type
            {
                # byte 0: type
                # byte 1: length
                (0x00, 0x07): frametypes.BCLiveMeasurementsFrame,
                (0x00, 0x09): frametypes.BCLiveMeasurementsFrameExtended,
                (0x00, 0x0A): frametypes.BCLiveMeasurementsFrameLargeSolarCurrent,
                (0x01, 0x09): frametypes.BCSolarChargerEBLFrame,
                (0x01, 0x0B): frametypes.BCSolarChargerStandardFrame,
                (0x01, 0x0C): frametypes.BCSolarChargerExtendedFrame,
                (0x01, 0x0F): frametypes.BCSolarChargerLargeSolarCurrent,
                (0x02, 0x10): frametypes.BCBatteryComputer1Frame,
                (0x02, 0x11): frametypes.BCBatteryComputer1Frame,
                (0x03, 0x0F): frametypes.BCBatteryComputer2Frame,
                (0x04, 0x01): frametypes.BCIntradayLogEntryFrame,
                (0x04, 0x02): frametypes.BCIntradayLogEntryFrameExtended,
                (0x05, 0x0A): frametypes.BCBoosterDataFrame,
                (0x05, 0x0C): frametypes.BCBoosterDataFrameExtended,
                (0x05, 0x10): frametypes.BCBoosterDataFrameExtendedBBX,
                (0x05, 0x04): frametypes.BCNoBoosterDataFrame,
            },
        ).process(self, data)
