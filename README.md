# bluebattery.py

Software for interacting with the [BlueBattery](https://www.blue-battery.com/) line of battery computers for RVs.

Features:

- [x] Reading of periodically sent measurements
- [x] Publishes value to an MQTT broker
- [x] Auto-discovery of BB devices
- [x] Access to stored logs
- [ ] Modification of device settings
- [ ] Firmware update

## Changelog

2023-01-14: Moved to bleak library. This should make the software much more reliable. Multiple devices are now supported and the MQTT topic has changed to include the device address.

## Installation

```
sudo apt-get install python3-pip
# log out and in again to apply new environment variables 
pip3 install git+https://github.com/danielfett/bluebattery.py.git
```


## Reading values from the command line

```
$ bb_cli log
```

If you want to see more details of what is going on, use the debug flag:

```
$ bb_cli --log-level DEBUG log
```

## Publishing values to an MQTT server

If you want to use the MQTT features, start the MQTT publisher using

```
$ bb_cli mqtt
```

Append `--help` to see the configuration options.

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
