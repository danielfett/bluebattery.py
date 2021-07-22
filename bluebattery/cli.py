from bluebattery.frametypes import LogEntryDaysFrame, LogEntryFrameOld, LogEntryFrameNew
from bluebattery.device import BBDevice, BBDeviceManager
from bluebattery.characteristics import BCLog, BCSec
import argparse
import logging
import signal
import json


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
    return parser


def run(args, recv_callback, ready_callback=None):
    manager = BBDeviceManager(
        on_message=recv_callback,
        on_device_ready=ready_callback,
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

    def read_sec_cb(device: BBDevice):
        info = {
            'first_day_seen': None,
            'first_frametype_seen': None,
        }
        def read_log_cb(characteristic, frames):
            if not isinstance(characteristic, BCSec):
                for frametype, measurement, values in frames:
                    if not info['first_frametype_seen']:
                        info['first_frametype_seen'] = frametype
                        info['first_day_seen'] = values['day_counter']
                        
                    elif frametype == info['first_frametype_seen'] and values['day_counter'] == info['first_day_seen']:
                        print("Finished reading history values.")
                        return
            device.characteristics_by_class[BCLog].read(read_log_cb)

        device.characteristics_by_class[BCSec].read(read_log_cb)

    run(args, recv_callback, read_sec_cb)


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
        mqtt_client.publish(
            mktopic(measurement), json.dumps(dict(values), default=str)
        )

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
