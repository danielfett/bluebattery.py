import asyncio


class Characteristic:
    UUID = ""

    def __init__(self, client, log, output):
        self.client = client
        # create sub-logger for this characteristic
        self.log = log.getChild(self.UUID)
        self.output = output


class ReadPeriodicCharacteristic(Characteristic):
    PERIOD = 10

    def __init__(self, client, log, output):
        super().__init__(client, log, output)
        # create periodic task to read characteristic
        self.task = asyncio.create_task(self.read_periodically())

    async def read_periodically(self):
        self.log.debug(f"Starting periodic read of {self.UUID}")
        while True:
            # read characteristic
            data = await self.client.read_gatt_char(self.UUID)
            self.log.debug(f"Read {self.UUID}: {' '.join(f'{b:02x}' for b in data)}")

            parsed = self.parse(data)

            for frame in parsed:
                self.log.debug(f"Parsed frame: {frame}")
                self.output.put(frame)

            # wait for 5 seconds
            await asyncio.sleep(self.PERIOD)

    def parse(self, data):
        yield {
            "raw": data,
        }


class NotifiedCharacteristic(Characteristic):
    def __init__(self, client, log, output):
        super().__init__(client, log, output)

        # create task to handle notifications
        self.task = asyncio.create_task(self.handle_notifications())

    async def handle_notifications(self):
        self.log.debug(f"Subscribing to notifications of {self.UUID}")
        # subscribe to notifications
        try:
            await self.client.start_notify(self.UUID, self.notify_callback)
        except Exception as e:
            self.log.exception("Error subscribing to notifications")

        while True:
            await asyncio.sleep(1.0)

    async def notify_callback(self, sender, data):
        self.log.debug(f"Received notification from {sender}: {data}")

        parsed = self.parse(data)

        for frame in parsed:
            self.log.debug(f"Parsed frame: {frame}")
            self.output.put(frame)

    def parse(self, data):
        yield {
            "raw": data,
        }
