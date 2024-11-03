## Name
RikaDomo-spy

## Description
monitor RIKA Domo pellet stove using firestick extension. Checks cloud communication and fetches JSON data. Data is sent to local influxdb. Grafana may present data as history or actual settings and switches. 

## Visuals
![rikadomo-spy basic info](/media/rikadomo-spy_basic_info.png "oven status")
![rikadomo-spy temperature history](/media/rikadomo-spy_temperatures.png "temperature history")
![rikadomo-spy consumption](/media/rikadomo-spy_consumption-overview.png "Pellet consumption overview" )
![rikadomo-spy ventilation](/media/rikadomo-spy_switches-motors.png "switches and motors")

## Installation
this is mentioned to run on RaspberryPi. 
Each Version is suitable, needs no powerful hardware.
You may use the prepared rika-spy-pishrinkV2.img for your SD-Card. 
This comes with activated SSH and the user pi with standard password. You have to modify `settings.xml` and give it your credentials for email and password.
Use the modified version of rika_iter.py and change default text in line 37 with your stoveID.

**You may also do it from scratch:**

- **Install influxdb** with `sudo apt install influxdb`. 
- `sudo apt install influxdb-client` for terminal support
- configure influxdb with user = "grafana",password = "domo" and dbname = "rika"

```
CREATE USER "grafana" WITH PASSWORD 'domo' WITH ALL PRIVILEGES
CREATE DATABASE "rika"
GRANT ALL ON "rika" TO "grafana"
```

- **Install Grafana** 
```
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install -y grafana
sudo /bin/systemctl enable grafana-server
sudo /bin/systemctl start grafana-server
```
- and setup data source influxdb. Import the Rika-Domo-xxx.json dashboard.
- enhance your python3.x installation with 

-- `pip3 install elementpath`

-- `pip3 install beautifulsoup4`

-- `sudo apt-get install python3-influxdb`

- Call rika_iter.py in `sudo nano /etc/crontab` every 3 minutes.
- Modify settings.xml with your credentials and save into same folder as rika*.py 

```
<?xml version="1.0"?>
<data>
  <service name="firenet">
    <user>YOUREMAIL</user>
    <password>PASSWORD</password>
    <url_base>https://www.rika-firenet.com</url_base>
    <url_login>/web/login</url_login>
    <url_stove>/web/stove/</url_stove>
    <url_api>/api/client/</url_api>
  </service>
</data>
```

- Fill your storage bin and call `python3 rika_fuellung.py settings.xml nn` where nn ist the amount of pellets in kg.

## Usage
just call `ip:3000` or `rikaspy:3000` to open grafana. Replace ip with ip of your computer. 
select + and import the dashboard json

## Backup
**to back up your influx database using usb-stick and crontab:**

`0 3   * * *  pi    /usr/bin/influxd backup -portable /media/tosh32/rikaspy_influxdb_'date +\%Y-\%m-\%d'/`

please replace ' with back tics `

This saves your influx databases in a folder including the date in its name.

**You may create an image of your installation and send it to your NAS like this:**
```
sudo mkdir /media/qnap
sudo mount 192.168.xx.xxx:/Public /media/qnap
sudo dd if=/dev/mmcblk0 of=/media/qnap/rikaspy.img bs=4M status=progress
```

## Support
pf@nc-x.com

## Roadmap


## Contributing
open to contributions

## Authors and acknowledgment
inspired by [iero](https://github.com/iero/Rika-Stove)
and [MoBOatGVA](https://github.com/MoBOatGVA/Rika-Firenet)

## License
MIT

## Project status
under development
