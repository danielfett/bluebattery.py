from bluebattery.device import BBDeviceManager
import argparse
import logging
import signal
import json


def default_parser():
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
    return parser


def run(args, recv_callback):
    manager = BBDeviceManager(target_mac_address=args.mac_address, adapter_name=args.device)
    manager.target_device.on_message(recv_callback)

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

    def recv_callback(_, measurement, values):
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
        "--collect", "-c", help="Collect measurements into JSON objects."
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

    def recv_callback_collect(_, measurement, values):
        mqtt_client.publish(mktopic(measurement), json.dumps(dict(values)))

    def recv_callback_single(_, measurement, values):
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

    def recv_callback(_, measurement, values):
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
