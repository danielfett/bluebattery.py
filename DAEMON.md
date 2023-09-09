## bb_mqtt as Daemon

If you want to send the BlueBattery Data to another server via MQTT it's helpful to start the bb_mqtt as a daemon.

Here a example with Systemctl based on Debian Linux systems like Bullseye for the Raspberry Pi.

At first we need a file in /lib/systemd/system/

`sudo nano /lib/ststemd/system/bluebattery.service`

This file we fill with the follow _code_ and save this file `ctrl`&`x`

````
[Unit]

Description=Bluebattery Service

After=multi-user.target
 
[Service]

ExecStart=/usr/bin/python3 /usr/local/bin/bb_mqtt aa:bb:cc:dd:ee:ff #Mac is optional!
 
[Install]

WantedBy=multi-user.target
````

At the next stepp we have to make this file executable for root and readable for users

`sudo chmod 644 /lib/systemd/system/bluebattery.service`

Now it's possible to start/stop the daemon with

`sudo systemctl start bluebattery`

If you have any trouble you can see the status of the daemon with

`sudo systemctl status bluebattery`

if you want to start the service at system boot, you can turn it on like this

`sudo systemctl enable bluebattery`
