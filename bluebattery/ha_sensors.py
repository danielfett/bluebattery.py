from dataclasses import dataclass, field
import re


def clean_string(raw: str) -> str:
    """
    MQTT Discovery protocol only allows [a-zA-Z0-9_-]
    """
    result = re.sub(r"[^A-Za-z0-9_-]", "-", raw)
    return result.strip("-")


@dataclass
class Device:
    service: object
    name: str
    model: str | None = None
    manufacturer: str | None = None
    sw_version: str | None = None
    hw_version: str | None = None
    identifiers: list[str] | str | None = None
    connections: list[tuple] | None = None
    suggested_area: str | None = None
    via_device: "Device | None" = None
    _extra_availability: dict = field(default_factory=dict)

    _unique_id: str | None = None

    __entities: list["Entity"] = field(default_factory=list)

    def __post_init__(self):
        self._unique_id = f"{self.service.SERVICE_NAME}_{clean_string(self.name)}"
        if self.identifiers is None:
            self.identifiers = [self._unique_id]
        else:
            if isinstance(self.identifiers, str):
                self.identifiers = [self.identifiers]
            if self._unique_id not in self.identifiers:
                self.identifiers.append(self._unique_id)

    @property
    def entities(self):
        return self.__entities

    def add_entity(self, entity):
        self.__entities.append(entity)

    def publish_discovery(self, prefix):
        device_payload = {
            k: v
            for k, v in self.__dict__.items()
            if v is not None and not k.startswith("_")
        }

        del device_payload["service"]

        if self.via_device is not None:
            device_payload["via_device"] = self.via_device._unique_id
        availability = [
            {
                "topic": self.service.willtopic,
                "payload_available": "1",
                "payload_not_available": "0",
            }
        ]
        if self._extra_availability:
            availability.append(self._extra_availability)

        payload = {
            "device": device_payload,
            "origin": {"name": f"Bluebattery service"},
            "availability": availability,
            "components": {},
        }

        for entity in self.__entities:
            payload["components"][entity.unique_id] = entity.get_discover_payload()
        topic = f"{prefix}/device/{self._unique_id}/config"
        self.service.publish_json(topic, payload, qos=1, retain=True)


@dataclass
class EntityWithoutStateTopic:
    device: Device
    name: str
    display_name: str | None = None
    device_class: str | None = None
    enabled_by_default: bool | None = None
    entity_category: str | None = None
    expire_after: int | None = None
    force_update: bool | None = None
    icon: str | None = None
    default_entity_id: str | None = None
    qos: int | None = None
    unique_id: str | None = None

    json_attributes_topic_postfix: str | None = None
    json_attributes_template: str | None = None

    def __post_init__(self):
        if self.default_entity_id is None:
            self.default_entity_id = f"{self._component}.{clean_string(self.name)}"
        if self.unique_id is None:
            self.unique_id = (
                f"{self.device._unique_id}__{self.default_entity_id.replace('.', '_')}"
            )

        self.device.add_entity(self)

    def get_discover_payload(self):
        payload = {
            k: v
            for k, v in self.__dict__.items()
            if v is not None and not k.startswith("_") and k != "device"
        }
        payload["platform"] = self._component

        for key, value in list(payload.items()):
            if key.endswith("_postfix"):
                full_key = key[:-8]
                payload[full_key] = f"{self.device.service.data_topic_prefix}{value}"
                del payload[key]

        return payload


@dataclass
class Entity(EntityWithoutStateTopic):
    state_topic_postfix: str = ""
    value_template: str | None = None

    def __post_init__(self):
        if self.state_topic_postfix == "":
            raise ValueError("state_topic_postfix must be set")
        if self.default_entity_id is None:
            self.default_entity_id = (
                f"{self._component}.{self.state_topic_postfix.replace('/', '_')}"
            )
        if self.unique_id is None:
            self.unique_id = (
                f"{self.device._unique_id}__{self.default_entity_id.replace('.', '_')}"
            )
        self.device.add_entity(self)


@dataclass
class Sensor(Entity):
    _component: str = "sensor"
    unit_of_measurement: str | None = None
    state_class: str | None = None
    last_reset_value_template: str | None = None
    suggested_display_precision: int | None = None
    options: list | None = None

    def __post_init__(self):
        super().__post_init__()

        if self.options is not None:
            self.device_class = "enum"
