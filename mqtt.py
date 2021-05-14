from bluebattery.device import BBDevice  # , BBDeviceManager
import gatt
import argparse
import logging
import paho.mqtt.client as mqtt
import signal
import sys


parser = argparse.ArgumentParser()
parser.add_argument(
    "mac_address",
    help="Mac address of the BlueBattery device, format 'AA:BB:CC:DD:EE:FF'.",
)
parser.add_argument(
    "--device",
    help="Device name of bluetooth adapter.",
    default="hci0",
)
parser.add_argument(
    "--host",
    help="MQTT broker host.",
    default="localhost",
)
parser.add_argument(
    "--port",
    "-p",
    help="MQTT broker port.",
    default="1883",
)
parser.add_argument(
    "--prefix",
    help="Prefix for topics sent from this script.",
    default="service/bluebattery",
)

args = parser.parse_args()


def mktopic(postfix):
    return args.prefix + "/" + postfix


logging.basicConfig(level=logging.INFO)

log = logging.getLogger()

mqtt_client = mqtt.Client()
mqtt_client.enable_logger(log)
mqtt_client.will_set(mktopic("online"), "0", retain=True)
mqtt_client.connect_async(args.host, int(args.port))
mqtt_client.loop_start()


def recv_callback(measurement, values):
    for key, value in values.items():
        mqtt_client.publish(mktopic(measurement + "/" + key), str(value))


# manager = BBDeviceManager(adapter_name="hci0", mac_address=args.mac_address.lower())
# manager.start_discovery()
manager = gatt.DeviceManager(adapter_name=args.device)
device = BBDevice(
    mac_address=args.mac_address.lower(), manager=manager, recv_callback=recv_callback
)


def handler_stop_signals(signum, frame):
    try:
        device.disconnect()
        manager.stop()
        sys.exit(0)
    except Exception as e:
        print(e)


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)


device.connect()
manager.run()