import asyncio
import logging
import signal

import coloredlogs
from bleak import BleakScanner, exc

from .bbdevice import BlueBattery

# Set up logging with colored output
coloredlogs.install(level="DEBUG")

# Set bleak logger to INFO
logging.getLogger("bleak").setLevel(logging.INFO)


KNOWN_DEVICES = (
    # SmartSolar,
    BlueBattery,
)

# default logger
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)



class LogOutput:
    def __init__(self, log):
        self.log = log.getChild("output")

    def put(self, data):
        self.log.debug(data)

async def scan_and_connect(tasks, loop, output):
    device_list = []

    # scan for devices
    devices = await BleakScanner.discover(timeout=5.0, loop=loop)
    for device in devices:
        log.debug(device.metadata)
        for k in KNOWN_DEVICES:
            if k.filter(device):
                log.info(f"Found device: {device.name} ({device.address})")
                device_list.append((k, device))
                break
        else:
            log.info(f"Found other device: {device.name} ({device.address})")

    # ensure discovery has finished
    await asyncio.sleep(2.0)

    if not devices:
        return

    for cls, device in device_list:
        # check if any of the running tasks already covers this device
        if device.address in tasks:
            # if task is running, skip this device
            if not tasks[device.address].done():
                log.debug(f"Task for {device.address} is already running. Skipping.")
                continue
            # if task is done, remove it from the list
            else:
                del tasks[device.address]

        # else create a new task
        log.info(f"Connecting to {device.address}...")
        instance = cls(device, loop, output)
        try:
            device_task = asyncio.create_task(instance.run())
        except exc.BleakError as e:
            log.exception(f"Error connecting to {device.address}")
        else:
            tasks[device.address] = device_task


tasks = {}

output = LogOutput(log)

async def scanTask():
    loop = asyncio.get_running_loop()
    while True:
        log.info("Scanning for devices...")
        try:
            await scan_and_connect(tasks, loop, output)
        except exc.BleakError as e:
            log.exception("Error scanning for devices")
        await asyncio.sleep(10.0)


async def main():
    loop = asyncio.get_running_loop()
    loop.create_task(scanTask())

    # run until shutdown
    while True:
        await asyncio.sleep(1.0)


def shutdown(_, __):
    log.info("Shutting down...")
    for task in tasks.values():
        task.cancel()
    loop = asyncio.get_running_loop()
    loop.stop()


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

log.info("Started!")
asyncio.run(main())
