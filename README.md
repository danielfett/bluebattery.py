# bluebattery.py

Software for interacting with the [BlueBattery](https://www.blue-battery.com/) line of battery computers for RVs.

Features:

- [x] Reading of periodically sent measurements
- [x] Publishes value to an MQTT broker
- [x] Auto-discovery of BB devices
- [ ] Persisting previously discovered BB device
- [x] Access to stored logs
- [ ] Modification of device settings
- [ ] Firmware update

## Installation

```
sudo apt-get install python3-pip
# log out and in again to apply new environment variables 
pip3 install git+https://github.com/danielfett/bluebattery.py.git
```


## Reading values from the command line

```
$ bb_cli 
```

(If you run into troubles connecting to the device, or if there are multiple BB devices nearby, provide the MAC address of the device. It can be found in the BB app. E.g.: `$ bb_cli AA:BB:CC:DD:EE:FF`)

For an updating live view, first run

```
$ pip3 install rich
```

and then

```
$ bb_live 
```

![live view interface](assets/live_interface.png?raw=true)

## Publishing values to an MQTT server

If you want to use the MQTT features, first run

```
pip3 install paho-mqtt
```

The start the MQTT publisher using

```
$ bb_mqtt --host my-mqtt.server.example
```

Use `--collect` to get a more concise MQTT output using JSON objects.

Use `--prefix BBX` to pass a specific device name. Here in example BBX

For using the bb_mqtt as daemon [described here](asDaemon.md)

## Troubleshooting

Depending on your environment, you may need to enable BLE first or to set up your linux user to allow using BLE:

### Enabling Bluetooth LE

If the above command does not work out-of-the-box, you might have to enable Bluetooth Low-Energy. 

On Ubuntu, add the following two lines at the bottom of `/etc/bluetooth/main.conf`:

```
EnableLE=true
AttributeServer=true
```

Then restart bluetooth: `sudo service bluetooth restart`

### On the Raspberry Pi

This software works on a Raspberry Pi and was tested with the built-in bluetooth device. To use the software as the user `pi` (recommended!), you need to make the dbus policy changes [described here](https://www.raspberrypi.org/forums/viewtopic.php?t=108581#p746917).
