import asyncio
import logging

from bleak import BleakScanner, exc
from concurrent.futures import CancelledError

"""
This class searches for compatible devices and connects to them.
"""


class Scanner:
    SCAN_INTERVAL = 20.0

    def __init__(self, output, known_devices):
        self.tasks = {}
        self.output = output
        self.known_devices = known_devices
        self.log = logging.getLogger("Scanner")

    async def scan_and_connect(self, loop):
        device_list = []

        # scan for devices
        devices = await BleakScanner.discover(timeout=5.0, loop=loop)
        for device in devices:
            self.log.debug(device.metadata)
            for k in self.known_devices:
                if k.filter(device):
                    self.log.info(f"Found device: {device.name} ({device.address})")
                    device_list.append((k, device))
                    break
            else:
                self.log.info(f"Found other device: {device.name} ({device.address})")

        # ensure discovery has finished
        await asyncio.sleep(2.0)

        if not devices:
            return

        for cls, device in device_list:
            # check if any of the running tasks already covers this device
            if device.address in self.tasks:
                # if task is running, skip this device
                if not self.tasks[device.address].done():
                    self.log.debug(
                        f"Task for {device.address} is already running. Skipping."
                    )
                    continue
                # if task is done, remove it from the list
                else:
                    del self.tasks[device.address]

            # else create a new task
            self.log.info(f"Connecting to {device.address}...")
            instance = cls(device, loop, self.output)
            try:
                device_task = asyncio.create_task(instance.run())
            except exc.BleakError as e:
                self.log.exception(f"Error connecting to {device.address}")
            else:
                self.tasks[device.address] = device_task

    async def run(self):
        loop = asyncio.get_running_loop()
        try:
            while True:
                self.log.info("Scanning for devices...")
                try:
                    await self.scan_and_connect(loop)
                except exc.BleakError as e:
                    self.log.exception("Error scanning for devices")
                await asyncio.sleep(self.SCAN_INTERVAL)
        except CancelledError:
            self.log.info("Stopping scan.")
            for task in self.tasks.values():
                task.cancel()

    def shutdown(self, _, __):
        self.log.info("Shutting down...")
        for task in asyncio.Task.all_tasks():
            task.cancel()
        loop = asyncio.get_running_loop()
        loop.stop()
