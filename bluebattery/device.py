import logging

import gatt

from .characteristics import ALL_CHARACTERISTICS


class BBDeviceManager(gatt.DeviceManager):
    ADVERTISED_SERVICE_ID = "AA021474-780D-439F-AF20-6B46446A610E"
    target_device = None

    def __init__(
        self, target_mac_address=None, on_message=None, on_device_ready=None, **kwargs
    ):
        self.on_message = on_message
        self.on_device_ready = on_device_ready

        self.log = logging.getLogger("Device Manager")
        super().__init__(**kwargs)
        if target_mac_address:
            self.log.debug(
                f"Creating target device with mac address {target_mac_address.lower()}"
            )
            self.target_device = BBDevice(
                on_message=self.on_message,
                on_ready=self.on_device_ready,
                mac_address=target_mac_address.lower(),
                manager=self,
            )

    def stop(self):
        if self.target_device:
            self.log.debug("Trying to disconnect target device.")
            try:
                self.target_device.disconnect()
            except Exception as e:
                print(e)
        self.stop_discovery()
        super().stop()

    def device_discovered(self, device):
        self.log.debug(f"Discovery found device: {device.mac_address}.")
        device.advertised()
        self.stop_discovery()
        device.connect()

    def make_device(self, mac_address):
        return BBDevice(
            on_message=self.on_message,
            on_ready=self.on_device_ready,
            mac_address=mac_address,
            manager=self,
        )

    def run(self):
        if self.target_device:
            self.log.debug("Trying to connect target device.")
            self.target_device.connect()
        else:
            self.log.debug("No target device given, starting discovery.")
            self.start_discovery([self.ADVERTISED_SERVICE_ID])
        super().run()


class BBDevice(gatt.Device):
    auto_reconnect = True

    def __init__(self, on_message=None, on_ready=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = logging.getLogger(f"Device {self.mac_address}")
        self.callbacks = {}
        self.characteristics = {}
        self.characteristics_by_uuid = {}
        self.characteristics_by_class = {}
        if on_message:
            self.callbacks["message"] = on_message
        if on_ready:
            self.callbacks["ready"] = on_ready

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
        if self.auto_reconnect:
            self.log.debug("Trying to reconnect")
            self.connect()

    def disconnect(self):
        self.auto_reconnect = False
        self.log.debug("Disconnect request received, auto_reconnect set to False")
        super().disconnect()

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        self.log.info("Disconnected")
        if self.auto_reconnect:
            self.log.debug("Trying to reconnect")
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
                        self.characteristics_by_class[
                            BBCharacteristicType
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
            for frametype, measurement, values in bbcharacteristic.process(value):
                self.callbacks["message"](
                    type(bbcharacteristic), frametype, measurement, values
                )
