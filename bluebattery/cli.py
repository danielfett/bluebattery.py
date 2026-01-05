import logging
import signal
import argparse
import asyncio

import coloredlogs

from .bbdevice import BlueBattery
from .output.log import LogOutput
from .output.mqtt import MQTTOutput
from hummable.scanner import Scanner


KNOWN_DEVICES = (BlueBattery,)


async def run():
    # Parse command line arguments, use subparsers from log and mqtt.

    parser = argparse.ArgumentParser(description="BlueBattery Service")
    subparsers = parser.add_subparsers(dest="output", help="Output")
    LogOutput.add_subparser(subparsers)
    MQTTOutput.add_subparser(subparsers)

    # let user define the log level, default is INFO

    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    args = parser.parse_args()

    # set log level
    # Set up logging with colored output
    coloredlogs.install(level=args.log_level)

    # Set bleak logger to INFO
    logging.getLogger("bleak").setLevel(logging.INFO)

    # Create output depending on which subparser was used.
    if args.output == "log":
        output = LogOutput(args)
    elif args.output == "mqtt":
        output = MQTTOutput(args)
    else:
        raise ValueError("Please specify an output method.")

    scanner = Scanner(output.callback, KNOWN_DEVICES)

    # default logger
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    signal.signal(signal.SIGINT, scanner.shutdown)
    signal.signal(signal.SIGTERM, scanner.shutdown)

    log.info("Started!")

    await scanner.run()


if __name__ == "__main__":
    asyncio.run(run())
