import logging

import gatt
from gi.repository import GObject

from .commands import SUBSCRIBE_CHARACTERISTICS


#class BBDeviceManager(gatt.DeviceManager):
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
    def __init__(self, recv_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = logging.getLogger(f"Device {self.mac_address}")
        self.recv_callback = recv_callback

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
                for command in SUBSCRIBE_CHARACTERISTICS:
                    if command.GATT_CHARACTERISTIC == characteristic.uuid:
                        self.log.debug(f"Subscribing to {command.GATT_CHARACTERISTIC}")
                        characteristic.enable_notifications()
                    else:
                        self.log.debug(f"Not subscribing to {characteristic.uuid}.")

    def characteristic_value_updated(self, characteristic, value):
        for command in SUBSCRIBE_CHARACTERISTICS:
            if command.GATT_CHARACTERISTIC == characteristic.uuid:
                self.log.debug(f"Received value for {command.GATT_CHARACTERISTIC} ({len(value)} bytes)")
                self.recv_callback(*command.process(value))
