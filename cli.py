from bluebattery.device import BBDevice  # , BBDeviceManager
import gatt
import argparse
import logging


parser = argparse.ArgumentParser()
parser.add_argument(
    "mac_address",
    help="Mac address of the BlueBattery device, format 'AA:BB:CC:DD:EE:FF'.",
)
parser.add_argument("-v", help="Enable verbose logging.", action="store_true")
parser.add_argument("-vv", help="Enable debug logging.", action="store_true")
parser.add_argument(
    "--device",
    help="Device name of bluetooth adapter.",
    default="hci0",
)

args = parser.parse_args()


if args.v:
    log_level = logging.INFO
elif args.vv:
    log_level = logging.DEBUG
else:
    log_level = logging.ERROR
logging.basicConfig(level=log_level)
logging.getLogger().info(f"Log level set to to {log_level}.")


def recv_callback(measurement, values):
    print(f"Received {measurement}:")
    for key, value in values.items():
        print(f"  {key:>30} | {value}")
    print()

# manager = BBDeviceManager(adapter_name="hci0", mac_address=args.mac_address.lower())
# manager.start_discovery()
manager = gatt.DeviceManager(adapter_name=args.device)
device = BBDevice(
    mac_address=args.mac_address.lower(), manager=manager, recv_callback=recv_callback
)
device.connect()
manager.run()