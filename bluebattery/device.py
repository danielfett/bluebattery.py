import logging

import gatt

from .characteristics import ALL_CHARACTERISTICS

# class BBDeviceManager(gatt.DeviceManager):
#    def __init__(self, mac_address, *args, **kwargs):
#        self.log = logging.getLogger("Device Manager")
#        self.log.info("Started")
#        self.target_mac_address = mac_address
#        super().__init__(*args, **kwargs)
#
#    def make_device(self, mac_address):
#        if self.target_mac_address != mac_address:
#            self.log.debug(f"Found other device: {mac_address} - no action")
#            return None
#
#        self.log.info(f"Found target device: {mac_address} - activating")
#        return BBDevice(mac_address=mac_address, manager=self)
#
#    def device_discovered(self, device):
#        self.log.info("Device discovered!")


class BBDevice(gatt.Device):
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

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        self.log.info("Disconnected")

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
