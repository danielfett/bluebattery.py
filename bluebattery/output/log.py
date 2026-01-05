import logging


class LogOutput:
    @staticmethod
    def add_subparser(parser):
        parser.add_parser("log", help="Log output")

    def __init__(self, args):
        self.log = logging.getLogger("output.log")

    def callback_device_connected(self, device):
        self.log.info(f"Device connected: {device.address}")

    def callback(self, device, data):
        frame, output_id, output_data = data
        self.log.info(f"{device.address} | {output_id}: {output_data}")
