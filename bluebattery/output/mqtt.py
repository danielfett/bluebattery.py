"""
An MQTT output plugin to publish data to an MQTT broker.
"""

import asyncio
import logging
import json

import paho.mqtt.client as mqtt

from bluebattery.frametypes import ALL_FRAME_TYPES
from bluebattery.ha_sensors import Device, Sensor, clean_string


class MQTTOutput:
    SERVICE_NAME = "bluebattery_py"

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
            default="service/bluebattery/",
            help="MQTT topic to publish to will be extended by the device UUID. (default: service/bluebattery)",
        )
        mqtt_parser.add_argument(
            "--client-id",
            default="bluebattery",
            help="MQTT client ID (default: bluebattery)",
        )

    def __init__(self, args):
        self.log = logging.getLogger("output.mqtt")
        self.ha_devices = {}
        self.data_topic_prefix = args.topic
        self.willtopic = f"{self.data_topic_prefix}online"
        self.client = mqtt.Client(args.client_id)
        if args.username:
            self.client.username_pw_set(args.username, args.password)
        self.client.connect(args.host, args.port)
        self.client.loop_start()

        # publish to the "online" topic as last will
        self.client.will_set(self.willtopic, "0", retain=True)
        self.client.publish(self.willtopic, "1", retain=True)

    def callback(self, device, data):
        frame, output_id, output_data = data

        if not device.address in self.ha_devices:
            self.log.info(f"Creating Home Assistant device for {device.address}")
            self.create_ha_device(device)

        for key, value in output_data.items():
            topic = f"{self.data_topic_prefix}{device.address}/{output_id}/{key}"
            if type(value) not in (str, int, float):
                value = str(value)
            self.log.debug(f"Publishing {topic} = {value}")
            self.client.publish(topic, value, retain=False)

    def publish_json(self, topic, payload, qos=0, retain=False):
        self.log.debug(f"Publishing JSON to {topic}: {payload}")
        self.client.publish(topic, json.dumps(payload), qos=qos, retain=retain)

    def create_ha_device(self, device):
        ha_device = Device(
            service=self,
            name=f"{device.name} ({device.address})",
            identifiers=[device.address],
            manufacturer="BlueBattery",
            model="Unknown",
            _extra_availability={
                "topic": f"{self.data_topic_prefix}{device.address}/status/connected",
                "payload_available": "1",
                "payload_not_available": "0",
            },
        )
        self.ha_devices[device.address] = ha_device

        # iterate through all frame types and their commands to create sensors

        for frame_type in ALL_FRAME_TYPES:
            for value in frame_type.fields:
                if not value.ha_details:
                    continue
                if value.ha_details.get("platform") != "sensor":
                    raise NotImplementedError(
                        "Only sensor platform is implemented yet."
                    )
                sensor = Sensor(
                    device=ha_device,
                    name=value.ha_details["name"],
                    device_class=value.ha_details.get("device_class"),
                    unit_of_measurement=value.ha_details.get("unit_of_measurement"),
                    suggested_display_precision=value.ha_details.get(
                        "suggested_display_precision"
                    ),
                    state_topic_postfix=f"{device.address}/{frame_type.output_id}/{value.output_id}",
                    default_entity_id=f"sensor.{clean_string(ha_device.name)}_{clean_string(frame_type.output_id)}_{clean_string(value.output_id)}",
                    unique_id=f"{clean_string(ha_device.name)}__sensor_{clean_string(frame_type.output_id)}_{clean_string(value.output_id)}",
                    enabled_by_default=value.ha_details.get("enabled_by_default", True),
                    state_class=value.ha_details.get("state_class", None),
                )

        ha_device.publish_discovery("homeassistant")
