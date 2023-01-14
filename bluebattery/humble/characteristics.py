import asyncio
from concurrent.futures import CancelledError


class Characteristic:
    UUID = ""

    def __init__(self, client, log, output_callback):
        self.client = client
        # create sub-logger for this characteristic
        self.log = log.getChild(self.UUID)
        self.output_callback = output_callback


class ReadPeriodicCharacteristic(Characteristic):
    PERIOD = 10

    def __init__(self, client, log, output_callback):
        super().__init__(client, log, output_callback)
        # create periodic task to read characteristic
        self.task = asyncio.create_task(self.read_periodically())

    async def read_periodically(self):
        self.log.debug(f"Starting periodic read of {self.UUID}")
        try:
            while True:
                # read characteristic
                data = await self.client.read_gatt_char(self.UUID)
                self.log.debug(
                    f"Read {self.UUID}: {' '.join(f'{b:02x}' for b in data)}"
                )

                parsed = self.parse(data)

                for frame in parsed:
                    self.log.debug(f"Parsed frame: {frame}")
                    self.output_callback(frame)

                # wait for 5 seconds
                await asyncio.sleep(self.PERIOD)

        except CancelledError:
            self.log.debug("Task cancelled")

        except Exception as e:
            self.log.exception("Error reading characteristic")

    def parse(self, data):
        yield {
            "raw": data,
        }


class NotifiedCharacteristic(Characteristic):
    def __init__(self, client, log, output_callback):
        super().__init__(client, log, output_callback)

        # create task to handle notifications
        self.task = asyncio.create_task(self.handle_notifications())

    async def handle_notifications(self):
        self.log.debug(f"Subscribing to notifications of {self.UUID}")
        # subscribe to notifications
        try:
            await self.client.start_notify(self.UUID, self.notify_callback)
        except Exception as e:
            self.log.exception("Error subscribing to notifications")

        try:
            while True:
                await asyncio.sleep(1.0)
        except CancelledError:
            self.log.debug("Task cancelled")
            await self.client.stop_notify(self.UUID)

    async def notify_callback(self, sender, data):
        self.log.debug(f"Received notification from {sender}: {data}")

        parsed = self.parse(data)

        for frame in parsed:
            self.log.debug(f"Parsed frame: {frame}")
            self.output_callback(frame)

    def parse(self, data):
        yield {
            "raw": data,
        }
