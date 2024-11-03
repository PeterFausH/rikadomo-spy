# Liest die API von Rika ein. Firenet-Stick wird benötigt.
# Grundidee von https://github.com/MoBOatGVA/Rika-Firenet
# Beim Befüllen Tagesbehälter Aufruf:
# python3 rika_fuellung.py settings.xml 30
# 30 wären dann 2 Sack mit je 15kg ohne Restmenge
# pf@nc-x.com, Peter Fürle, Schwarzwald
# V1.0 vom 23.11.2021
# wird der Behälter neu befüllt gehen 3 Säcke mit 45kg rein.

import sys
import time
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup # parse page
from influxdb import InfluxDBClient

# Configure InfluxDB connection variables
host = "127.0.0.1" 
port = 8086
user = "grafana"
password = "domo"
dbname = "rika"

# Influx Datenbank verbinden
influx_client = InfluxDBClient(host, port, user, password, dbname)

#mit dem Ofen in der Cloud verbinden
def connect(client, url_base, url_login, url_stove, user, pwd) :
  data = {
    'email':user,
    'password':pwd}
  r = client.post(url_base+url_login, data)
  #print(r.url)
  if ('Log out' in r.text) == True :
    print('Connected to Rika Firenet')
    soup = BeautifulSoup(r.content, "html.parser")
    text = soup.find("ul", {"id": "stoveList"})
    # print(text)
    if text is not None :
      stoveName = text.find('a').text
      a = text.find('a', href=True)
      stove = a['href'].replace(url_stove,'')
      #print("verbundener Ofen : {} [{}]".format(stoveName,stove))
      return stove
  return ""

#holt den ganzen JSON Datensatz ab
def get_stove_informations(client, url_base, url_api, stove) :
  r = client.get(url_base+url_api+stove+'/status?nocache=')
  return r.json()

# MAIN #
# settings.xml zur Authentifizierung einlesen
auth_tree = ET.parse(sys.argv[1])
auth_root = auth_tree.getroot()
for service in auth_root.findall('service') :
  if service.get("name") == "firenet" :
    user = service.find('user').text
    pwd = service.find('password').text
    url_base = service.find('url_base').text
    url_login = service.find('url_login').text
    url_stove = service.find('url_stove').text
    url_api = service.find('url_api').text  
client = requests.session()
stove = connect(client, url_base, url_login, url_stove, user, pwd)
if len(stove) == 0 :
  print("No stove found (connection failed ?)")
  sys.exit(1)


#Ofen-Informationen von der API einlesen
stove_infos = get_stove_informations(client, url_base, url_api, stove)

# wurden 2 Parameter mit angegeben ?
if len(sys.argv) == 3:
    # wieviel kg sind jetzt im Behälter (15,30,45)
    kilo=sys.argv[2]
    print(kilo)
else:
    print("bitte so aufrufen:")
    print("  python rika_fuellung.py settings.xml 45")
    print("die letzte Zahl gibt den Füllstand des Behälters an")
    print("war er leer und du kippst 2 Sack rein dann sinds 30")
    print("--> habe default 30kg eingetragen!")
    kilo=30

# jetzigen Tagesstand kg Pellets holen (1635)
fuellung_Tagesstand=stove_infos['sensors']['parameterFeedRateTotal']
print("Tagesstand gerade:",fuellung_Tagesstand)

#eintragen('info','fuellstand',kilo)
data=[{"measurement": "sensors","fields": {"pelletsAnfangsStand" : int(fuellung_Tagesstand)}}]
print(data)
influx_client.write_points(data)
data=[{"measurement": "sensors","fields": {"pelletsBehaelterKG" : int(kilo)}}]
print(data)
influx_client.write_points(data)

