from bluebattery.frametypes import LogEntryDaysFrame, LogEntryFrameOld, LogEntryFrameNew
from bluebattery.device import BBDevice, BBDeviceManager
from bluebattery.characteristics import BCLog, BCSec
import argparse
import logging
import signal
import json


from gi.repository import GObject


class ReaderLogic:
    TIMEOUT_LOG = 60 * 60 * 1000  # once every hour

    def __init__(self, read_log):
        self.read_log = read_log
        self.log_info = {
            "first_day_seen": None,
            "first_frametype_seen": None,
        }

    def ready_callback(self, device):
        self.device = device
        if self.read_log:
            GObject.timeout_add(self.TIMEOUT_LOG, self.start_read_log)
            self.start_read_log()

    def start_read_log(self):
        if BCSec not in self.device.characteristics_by_class:
            return True
        self.device.characteristics_by_class[BCSec].read(self.continue_read_log)
        return True

    def continue_read_log(self, characteristic, frames):
        if not isinstance(characteristic, BCSec):
            for frametype, measurement, values in frames:
                if not self.log_info["first_frametype_seen"]:
                    self.log_info["first_frametype_seen"] = frametype
                    self.log_info["first_day_seen"] = values["day_counter"]

                elif (
                    frametype == self.log_info["first_frametype_seen"]
                    and values["day_counter"] == self.log_info["first_day_seen"]
                ):
                    # finished reading log entries
                    return
        self.device.characteristics_by_class[BCLog].read(self.continue_read_log)


def default_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mac_address",
        help="Mac address of the BlueBattery device, format 'AA:BB:CC:DD:EE:FF'."
        "If no address is given, any suitable Bluebattery device will be used.",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "--device",
        help="Device name of bluetooth adapter.",
        default="hci0",
    )
    parser.add_argument(
        "--read-log",
        "-l",
        help="Read the log files of BB every hour.",
        action="store_true",
    )
    return parser


def run(args, recv_callback):
    reader_logic = ReaderLogic(args.read_log)
    manager = BBDeviceManager(
        on_message=recv_callback,
        on_device_ready=reader_logic.ready_callback,
        target_mac_address=args.mac_address,
        adapter_name=args.device,
    )

    def handler_stop_signals(signum, frame):
        try:
            manager.stop()
        except Exception as e:
            print(e)

    signal.signal(signal.SIGINT, handler_stop_signals)
    signal.signal(signal.SIGTERM, handler_stop_signals)

    manager.run()


def cli():
    parser = default_parser()

    parser.add_argument("-v", help="Enable verbose logging.", action="store_true")
    parser.add_argument("-vv", help="Enable debug logging.", action="store_true")

    args = parser.parse_args()

    if args.v:
        log_level = logging.INFO
    elif args.vv:
        log_level = logging.DEBUG
    else:
        log_level = logging.ERROR
    logging.basicConfig(level=log_level)
    logging.getLogger().info(f"Log level set to to {log_level}.")

    def recv_callback(characteristic, frametype, measurement, values):
        print(f"Received {measurement}:")
        for key, value in values.items():
            print(f"  {key:>30} | {value}")
        print()

    run(args, recv_callback)


def mqtt():
    import paho.mqtt.client as mqtt

    parser = default_parser()
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
    parser.add_argument(
        "--collect",
        "-c",
        help="Collect measurements into JSON objects.",
        action="store_true",
    )
    parser.add_argument("-v", help="Enable verbose logging.", action="store_true")
    parser.add_argument("-vv", help="Enable debug logging.", action="store_true")

    args = parser.parse_args()

    def mktopic(postfix):
        return args.prefix + "/" + postfix

    def on_connect(client, *args, **kwargs):
        client.publish(mktopic("online"), "1", retain=True)

    if args.v:
        log_level = logging.INFO
    elif args.vv:
        log_level = logging.DEBUG
    else:
        log_level = logging.ERROR
    logging.basicConfig(level=log_level)
    logging.getLogger().info(f"Log level set to to {log_level}.")

    log = logging.getLogger()

    mqtt_client = mqtt.Client()
    mqtt_client.enable_logger(log)
    mqtt_client.will_set(mktopic("online"), "0", retain=True)
    mqtt_client.on_connect = on_connect
    mqtt_client.connect_async(args.host, int(args.port))
    mqtt_client.loop_start()

    def recv_callback_collect(characteristic, frametype, measurement, values):
        mqtt_client.publish(mktopic(measurement), json.dumps(dict(values), default=str))

    def recv_callback_single(characteristic, frametype, measurement, values):
        for key, value in values.items():
            mqtt_client.publish(mktopic(measurement + "/" + key), str(value))

    cb = recv_callback_collect if args.collect else recv_callback_single

    run(args, cb)


def live():
    from rich.columns import Columns
    from rich.panel import Panel
    from rich.live import Live
    from rich.table import Table
    from rich import box

    parser = default_parser()

    args = parser.parse_args()
    log_level = logging.ERROR
    logging.basicConfig(level=log_level)
    logging.getLogger().info(f"Log level set to to {log_level}.")

    topic_panels = {}

    columns = Columns()

    def recv_callback(characteristic, frametype, measurement, values):
        content = Table(show_header=False, box=box.MINIMAL)
        content.add_column("Name", justify="right", no_wrap=True)
        content.add_column("Value", no_wrap=True)
        for key, value in values.items():
            if isinstance(value, float):
                value = f"{value:5.1f}"
            elif isinstance(value, int):
                value = f"{value:5.0f}"
            else:
                value = str(value)
            content.add_row(key, value)

        if measurement in topic_panels:
            topic_panels[measurement].renderable = content
        else:
            panel = Panel(content, title=measurement)
            topic_panels[measurement] = panel
            columns.add_renderable(panel)

    with Live(columns, refresh_per_second=4):
        run(args, recv_callback)
