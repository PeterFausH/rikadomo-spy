# Liest die API von Rika ein. Firenet-Stick wird benötigt.
# Iteriert durch (fast) alle JSON Datensätze
# Grundidee von https://github.com/MoBOatGVA/Rika-Firenet
# Aufruf: python3 rika_iter.py settings.xml
# pf@nc-x.com, Peter Fürle, Schwarzwald
# V1.3 vom 04.10.2022
# ATTENTION: put your stoveID in line 37!

import sys
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


# mit dem Ofen in der Cloud verbinden
# Zugangsdaten aus settings.xml holen
def connect(client, url_base, url_login, url_stove, user, pwd) :
  data = {
    'email':user,
    'password':pwd}
  r = client.post(url_base+url_login, data)
  #print(r.url)
  #put your stove ID here:
  if ('stoveID' in r.text) == True :
    print('Connected to Rika Firenet')
    soup = BeautifulSoup(r.content, "html.parser")
    text = soup.find("ul", {"id": "stoveList"})
    # print(text)
    if text is not None :
      stoveName = text.find('a').text
      a = text.find('a', href=True)
      stove = a['href'].replace(url_stove,'')
      print("verbundener Ofen : {} [{}]".format(stoveName,stove))
      return stove
  return ""


#holt den ganzen JSON Datensatz ab
def get_stove_informations(client, url_base, url_api, stove) :
  r = client.get(url_base+url_api+stove+'/status?nocache=')
  return r.json()


# Jeder Bereich bekommt sein eigenes measurement (info,control,sensor,...)
## [{'measurement': 'controls',       'fields': {'revision': 0}}]
def eintragen(measurement,bez,wert):
    data=[{"measurement": measurement,"fields": {bez : wert}}]
    influx_client.write_points(data, time_precision='m')
    return

# es kommen nicht alle Stammdaten an, hier nachbessern
def get_stammdaten(d,att):
  attribute=att
  w=d[att]
  eintragen("info",str(attribute),w)
  

#bereitet Ausgabe der JSON-Daten vor
def show_stove_informations(data) :
  get_stammdaten(data,"name")
  get_stammdaten(data,"stoveID")
  get_stammdaten(data,"lastSeenMinutes")
  get_stammdaten(data,"stoveType")
  get_stammdaten(data,"oem")

  # Betriebszustand Ofen vom Webinterface / Source
  if data['controls']['operatingMode'] == 0 :
    eintragen('info','operating','Manuell')
  elif data['controls']['operatingMode'] == 1 :
    eintragen('info','operating','Automatik')
  elif data['controls']['operatingMode'] == 2 :
    eintragen('info','operating','Komfort')
  if data['sensors']['statusMainState'] == 1 :
    if data['sensors']['statusSubState'] == 0 :
      eintragen('info','mode','AUS')
    elif data['sensors']['statusSubState'] == 1 or data['sensors']['statusSubState'] == 3:
      eintragen('info','mode','Standby..')
    elif data['sensors']['statusSubState'] == 2 :
      eintragen('info','mode','extern')
    else:
      eintragen('info','mode','unbekannt')
  elif data['sensors']['statusMainState'] == 2 :
    eintragen('info','mode','Aufwachen')
  elif data['sensors']['statusMainState'] == 3 :
    eintragen('info','mode','Starten')
  elif data['sensors']['statusMainState'] == 4 :
    eintragen('info','mode','Regelbetrieb')
  elif data['sensors']['statusMainState'] == 5 :
    if data['sensors']['statusSubState'] == 3 or data['sensors']['statusSubState'] == 4 :
      eintragen('info','mode','umf. Reinigung')
    else :
      eintragen('info','mode','Reinigung')
  elif data['sensors']['statusMainState'] == 6 :
    eintragen('info','mode','Ausbrand')
  else :
    eintragen('info','mode','unbekannt')


# prüfen ob Wert numerisch sein könnte, sonst String
def num(s):
    try:
        return float(s)
    except ValueError:
        return s


# durch alle Elemente des JSON-Outputs durchgehen, nachbereiten und diese an
# die Funktion zum Eintragen in die Datenbank weitergeben.
def iter_dict(data):
    for key in data:
        #print(key)
        if isinstance(data[key], dict):
            #print("Anzahl Paare: "+str(len(data[key])))
            bereich = key
            iter_dict(data[key])
            print(str(bereich))
            # Nachbereitung einzelner Werte
            for attribute, value in data[key].items():
                w = num(value)
                if "mode" in str(attribute):
                    w = int(w)
                if "Mode" in str(attribute):
                    w = int(w)
                if "status" in str(attribute):
                    w = int(w)
                elif "Level" in str(attribute):
                    w = int(w)
                elif "output" in str(attribute):
                    w = int(w)
                elif "input" in str(attribute):
                    w = int(w)
                elif "heatingTime" in str(attribute):
                    w = str(w)
                elif "stoveFeatures" in str(key):
                    w = int(w)
                elif "Active" in str(attribute):
                    w = int(w)
                elif "revision" in str(attribute):
                    w = 0
                elif str(attribute)=="L_state":
                    w = int(w)
                elif str(attribute)=="onOff":
                    w = int(w)
                eintragen(str(key),str(attribute),w)


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

#Stammaten holen
show_stove_informations(stove_infos)

# mit dirty trick durch alle Elemente gehen
iter_dict(stove_infos)

