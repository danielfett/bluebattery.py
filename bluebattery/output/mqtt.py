"""
An MQTT output plugin to publish data to an MQTT broker.
"""

import logging

import paho.mqtt.client as mqtt


class MQTTOutput:
    @staticmethod
    def add_subparser(parser):
        mqtt_parser = parser.add_parser("mqtt", help="MQTT output")
        mqtt_parser.add_argument(
            "--host",
            default="localhost",
            help="MQTT broker hostname (default: localhost)",
        )
        mqtt_parser.add_argument(
            "--port", default=1883, type=int, help="MQTT broker port (default: 1883)"
        )
        mqtt_parser.add_argument(
            "--username", default=None, help="MQTT broker username (default: None)"
        )
        mqtt_parser.add_argument(
            "--password", default=None, help="MQTT broker password (default: None)"
        )
        mqtt_parser.add_argument(
            "--topic",
            default="service/bluebattery",
            help="MQTT topic to publish to will be extended by the device UUID. (default: service/bluebattery)",
        )
        mqtt_parser.add_argument(
            "--client-id",
            default="bluebattery",
            help="MQTT client ID (default: bluebattery)",
        )

    def __init__(self, args):
        self.log = logging.getLogger("output.mqtt")
        self.topic = args.topic
        self.client = mqtt.Client(args.client_id)
        if args.username:
            self.client.username_pw_set(args.username, args.password)
        self.client.connect(args.host, args.port)
        self.client.loop_start()

        # publish to the "online" topic as last will
        self.client.will_set(f"{self.topic}/online", "0", retain=True)
        self.client.publish(f"{self.topic}/online", "1", retain=True)

    def callback(self, device, data):
        frame, output_id, output_data = data
        topic = self.topic.format(device=device)
        for key, value in output_data.items():
            topic = f"{self.topic}/{device.address}/{output_id}/{key}"
            if type(value) not in (str, int, float):
                value = str(value)
            self.log.debug(f"Publishing {topic} = {value}")
            self.client.publish(topic, value, retain=False)
