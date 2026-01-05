# bluebattery.py

Software for interacting with the [BlueBattery](https://www.blue-battery.com/) line of battery computers for RVs.

Features:

- [x] Reading of periodically sent measurements
- [x] Publishes value to an MQTT broker
- [x] Auto-discovery of BB devices
- [x] Access to stored logs
- [x] Homeassistant support
- [ ] Modification of device settings
- [ ] Firmware update

## Changelog

2026-01-05: Support for Homeassistant
2023-01-14: Moved to bleak library. This should make the software much more reliable. Multiple devices are now supported and the MQTT topic has changed to include the device address.

## Installation

To install the latest published version:

```
sudo apt-get install python3-pip
# log out and in again to apply new environment variables 
pip3 install bluebattery-py
```

To install the latest version from this git repository:

```
sudo apt-get install python3-pip
# log out and in again to apply new environment variables 
pip3 install git+https://github.com/danielfett/bluebattery.py.git
```


## Setting up a Systemd Service

See the [systemd service](assets/bb.service) file for details.


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

This is an example of the values published to the MQTT broker:

```
service/bluebattery/FC:45:C3:CA:FF:EE/live/solar_charger_ext/max_solar_current_day_A 0.0
service/bluebattery/FC:45:C3:CA:FF:EE/live/solar_charger_ext/max_solar_watt_day_W 0.0
service/bluebattery/FC:45:C3:CA:FF:EE/live/solar_charger_ext/solar_charge_day_Ah 0.0
service/bluebattery/FC:45:C3:CA:FF:EE/live/solar_charger_ext/solar_energy_day_Wh 0
service/bluebattery/FC:45:C3:CA:FF:EE/live/solar_charger_ext/solar_charger_status 1
service/bluebattery/FC:45:C3:CA:FF:EE/live/solar_charger_ext/solar_module_voltage_V 0.0
service/bluebattery/FC:45:C3:CA:FF:EE/live/solar_charger_ext/relay_status RelayStatus()
service/bluebattery/FC:45:C3:CA:FF:EE/live/battery_comp_1/battery_charge_Ah 158.48
service/bluebattery/FC:45:C3:CA:FF:EE/live/battery_comp_1/state_of_charge_percent 83.4
service/bluebattery/FC:45:C3:CA:FF:EE/live/battery_comp_1/max_battery_current_day_A 0.0
service/bluebattery/FC:45:C3:CA:FF:EE/live/battery_comp_1/min_battery_current_day_A -1.1
service/bluebattery/FC:45:C3:CA:FF:EE/live/battery_comp_1/max_battery_charge_day_Ah 16.16
service/bluebattery/FC:45:C3:CA:FF:EE/live/battery_comp_1/min_battery_charge_day_Ah 15.84
service/bluebattery/FC:45:C3:CA:FF:EE/live/battery_comp_1/max_battery_voltage_day_V 12.54
service/bluebattery/FC:45:C3:CA:FF:EE/live/battery_comp_1/min_battery_voltage_day_V 12.5
service/bluebattery/FC:45:C3:CA:FF:EE/live/info/battery_voltage_V 12.61
service/bluebattery/FC:45:C3:CA:FF:EE/live/info/starter_battery_voltage_V 12.43
```


Use `--prefix BBX` to pass a specific device name. In this example, `BBX`.

For using the bb_mqtt as daemon [see here](DAEMON.md).

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
