import logging

import gatt

from .characteristics import ALL_CHARACTERISTICS


class BBDeviceManager(gatt.DeviceManager):
    target_device = None

    def __init__(self, target_mac_address=None, **kwargs):
        super().__init__(**kwargs)
        self.log = logging.getLogger("Device Manager")
        if target_mac_address:
            self.target_device = BBDevice(
                mac_address=target_mac_address.lower(),
                manager=self,
            )

    def stop(self):
        if self.target_device:
            try:
                self.target_device.disconnect()
            except Exception as e:
                print(e)
        super().stop()

    def run(self):
        if self.target_device:
            self.target_device.connect()
        super().run()


class BBDevice(gatt.Device):
    auto_reconnect = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = logging.getLogger(f"Device {self.mac_address}")
        self.callbacks = {}
        self.characteristics = {}
        self.characteristics_by_uuid = {}

    def on_message(self, callback):
        self.callbacks["message"] = callback

    def on_ready(self, callback):
        self.callbacks["ready"] = callback

    def connect_succeeded(self):
        super().connect_succeeded()
        self.log.info("Connected")

    def connect_failed(self, error):
        super().connect_failed(error)
        self.log.info("Connection failed")

    def disconnect(self):
        self.auto_reconnect = False
        super().disconnect()

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        self.log.info("Disconnected")
        if self.auto_reconnect:
            self.connect()

    def services_resolved(self):
        super().services_resolved()

        self.log.debug("Services resolved")

        for service in self.services:
            for characteristic in service.characteristics:
                for BBCharacteristicType in ALL_CHARACTERISTICS:
                    if (
                        BBCharacteristicType.GATT_CHARACTERISTIC_UUID
                        == characteristic.uuid
                    ):
                        # Instantiate a characteristic, passing the GATT object
                        new_characteristic = BBCharacteristicType(characteristic)
                        self.characteristics[BBCharacteristicType] = new_characteristic
                        self.characteristics_by_uuid[
                            characteristic.uuid
                        ] = new_characteristic
                        break
                else:
                    self.log.debug(
                        f"No matching characteristic found for {characteristic.uuid}."
                    )

        if self.callbacks.get("ready", None):
            self.callbacks["ready"](self)

    def characteristic_value_updated(self, characteristic, value):
        bbcharacteristic = self.characteristics_by_uuid[characteristic.uuid]
        self.log.debug(f"Received value for {characteristic.uuid} ({len(value)} bytes)")
        if self.callbacks.get("message", None):
            self.callbacks["message"](
                type(bbcharacteristic), *bbcharacteristic.process(value)
            )
