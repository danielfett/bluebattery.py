import logging
import asyncio
from bleak import BleakClient


class BLEDevice:
    CHARACTERISTICS = []
    FILTERS = []
    PAIRING_REQUIRED = True

    def __init__(self, device, loop, output):
        self.device = device
        self.loop = loop
        self.output = output
        self.log = logging.getLogger(f"Device {device.name}")
        self.log.setLevel(logging.DEBUG)

    @classmethod
    def filter(cls, device):
        for f in cls.FILTERS:
            if "name" in f:
                if device.name.startswith(f["name"]):
                    return True
            if "address" in f:
                if device.address.startswith(f["address"]):
                    return True
        return False

    async def run(self):
        self.log.info("Starting...")
        characteristics = []
        # connect to device
        async with BleakClient(self.device.address, loop=self.loop) as client:
            # read device name
            # name = await client.read_gatt_char("00002a00-0000-1000-8000-00805f9b34fb")
            # self.log.debug(f"Device name: {name.decode('utf-8')}")

            if self.PAIRING_REQUIRED:
                res = await client.pair(protection_level=3)
                self.log.debug(f"Pairing result: {res!r}")

            disconnected_event = asyncio.Event()

            def disconnect_callback(client):
                self.log.info(f"Disconnected!")
                self.loop.call_soon_threadsafe(disconnected_event.set)

            client.set_disconnected_callback(disconnect_callback)

            # read characteristics
            for service in client.services:
                self.log.debug(f"Service: {service.uuid}")
                for characteristic in service.characteristics:
                    self.log.debug(f"  Characteristic: {characteristic.uuid}")

                    # check if there exists a characteristic in the device configuration

                    for c in self.CHARACTERISTICS:
                        if c.UUID == characteristic.uuid:
                            # create characteristic
                            characteristics.append(c(client, self.log, self.output))
                            break

            # wait for all tasks of all characteristics to finish
            while True:
                await asyncio.sleep(1.0)
