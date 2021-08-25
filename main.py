#!/usr/bin/env python3
import pprint
import asyncio
import logging
import inspect
import time
import sys
import os
from aiohttp import ClientSession
from datetime import date, datetime
import requests
import csv
import configparser
import argparse

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

try:
    from skodaconnect import Connection
except ModuleNotFoundError:
    print("Unable to import library")
    sys.exit(1)

config = configparser.ConfigParser()

parser = argparse.ArgumentParser(
    description=
"""This program allows polling of information from the Skoda Enyaq iV car.
The program will look for a config.ini file with configuration options, however all
options can be overridden by using command arguments listed below
""")
parser.add_argument("-u","--username", help="Username for SkodaConnect")
parser.add_argument("-p","--password", type=str, help="Password for SkodaConnect. Note that if the password include specail characters, it should be encloused by \" characters.")
parser.add_argument("-i","--interval", type=int, help="Polling Interval for SkodaConnect")
parser.add_argument("-ife", action="store_true", help="Enable Influx")
parser.add_argument("-ifhost","--influx_host", help="Influx Host url")
parser.add_argument("-ifdb","--influx_database", help="Influx Database")
parser.add_argument("-ifp","--influx_precision", help="Influx Precision")
parser.add_argument("-ce", action="store_true", help="Enable csv logging")
parser.add_argument("-cf","--csv_folder", help="Folder to use for csv logging")

config.read("config.ini")
args = parser.parse_args()
# override config with args
if args.username!=None:
    config["SkodaConnect"]["Username"] = args.username
if args.password!=None:
    config["SkodaConnect"]["Password"] = args.password
if args.interval!=None:
    config["SkodaConnect"]["PollInterval"] = str(args.interval)

if args.ife==True:
    config["InfluxDb"]["Enabled"] = "yes"
if args.influx_host!=None:
    config["InfluxDb"]["Host"] = args.influx_host
if args.influx_database!=None:
    config["InfluxDb"]["Database"] = args.influx_database
if args.influx_precision!=None:
    config["InfluxDb"]["Precision"] = args.influx_precision

if args.ce==True:
    config["CSV"]["Enabled"] = "yes"

if args.csv_folder!=None:
    config["CSV"]["Folder"] = args.csv_folder


logging.basicConfig(level=logging.DEBUG)


PRINTRESPONSE = True

USERNAME = config.get("SkodaConnect","Username",fallback=None)
PASSWORD = config.get("SkodaConnect","Password",fallback=None)

INTERVAL = int(config.get("SkodaConnect","PollInterval",fallback=60))

InfluxDb_Enabled = config.get("InfluxDb","Enabled",fallback=False)
InfluxDb_Host = config.get("InfluxDb","Host",fallback=None)
InfluxDb_Database = config.get("InfluxDb","Database",fallback="sampledb")
InfluxDb_Precision = config.get("InfluxDb","Precision",fallback="m")

csv_Enabled = config.get("CSV","Enabled",fallback=True)
csv_Folder = config.get("CSV","Folder",fallback="logs")

for key,item in config.items():
    print(key)
    for k,v in item.items():
        print(k,v)


if csv_Enabled and csv_Folder!=None:
    try:
        os.mkdir(csv_Folder)
    except:
        pass

InfluxDb_Url = "{}/write?db={}&precision={}".format(InfluxDb_Host,InfluxDb_Database,InfluxDb_Precision)






COMPONENTS = {
    'sensor': 'sensor',
    'binary_sensor': 'binary_sensor',
    'lock': 'lock',
    'device_tracker': 'device_tracker',
    'switch': 'switch',
}

RESOURCES = [
		"adblue_level",
		"auxiliary_climatisation",
		"battery_level",
		"charge_max_ampere",
		"charger_action_status",
		"charging",
                "charge_rate",
                "charging_power",
		"charging_cable_connected",
		"charging_cable_locked",
		"charging_time_left",
		"climater_action_status",
		"climatisation_target_temperature",
		"climatisation_without_external_power",
		"combined_range",
		"combustion_range",
                "departure1",
                "departure2",
                "departure3",
		"distance",
		"door_closed_left_back",
		"door_closed_left_front",
		"door_closed_right_back",
		"door_closed_right_front",
		"door_locked",
		"electric_climatisation",
		"electric_range",
		"energy_flow",
		"external_power",
		"fuel_level",
		"hood_closed",
		"last_connected",
		"lock_action_status",
		"oil_inspection",
		"oil_inspection_distance",
		"outside_temperature",
		"parking_light",
		"parking_time",
		"pheater_heating",
		"pheater_status",
		"pheater_ventilation",
		"position",
		"refresh_action_status",
		"refresh_data",
		"request_in_progress",
		"request_results",
		"requests_remaining",
		"service_inspection",
		"service_inspection_distance",
		"sunroof_closed",
		"trip_last_average_auxillary_consumption",
		"trip_last_average_electric_consumption",
		"trip_last_average_fuel_consumption",
		"trip_last_average_speed",
		"trip_last_duration",
		"trip_last_entry",
		"trip_last_length",
		"trip_last_recuperation",
		"trip_last_total_electric_consumption",
		"trunk_closed",
		"trunk_locked",
		"vehicle_moving",
		"window_closed_left_back",
		"window_closed_left_front",
		"window_closed_right_back",
		"window_closed_right_front",
		"window_heater",
		"windows_closed"
]

def is_enabled(attr):
    """Return true if the user has enabled the resource."""
    return attr in RESOURCES

async def main():
    """Main method."""
    async with ClientSession(headers={'Connection': 'keep-alive'}) as session:
        print('')
        print('########################################')
        print('#      Logging on to Skoda Connect     #')
        print('########################################')
        print(f"Initiating new session to Skoda Connect with {USERNAME} as username")
        connection = Connection(session, USERNAME, PASSWORD, PRINTRESPONSE)
        print("Attempting to login to the Skoda Connect service")
        print(datetime.now())
        if await connection.doLogin():
            print('Login success!')
            logintime = datetime.now()
            print(logintime)

        else:
            print("Login Failed, exiting...")
            return False

        # Output all instruments and states

        print('')
        print('----------------------------------------')
        print('#      Eppa                            #')
        print('----------------------------------------')
        for vehicle in connection.vehicles:
            firstLine = True
            if csv_Enabled:
                csv_file = csv_Folder+"/"+logintime.strftime("%Y%m%d-%H%M%S")+".csv"
                csvfile = open(csv_file, 'w')
            
            timesincelogin = datetime.now()-logintime
            while timesincelogin<datetime.timedelta(minutes=5):
            #while True:

                #print(dashboard.instruments)
                
                #print(dashboard.instruments)
                print(vehicle._states)
                print(vehicle._states["plug"]["connectionState"])

                #tags:
                tags = "connectionState={connectionState},state={state},chargingType={chargingType},chargeMode={chargeMode},maxChargeCurrentAc={maxChargeCurrentAc},autoUnlockPlugWhenCharged={autoUnlockPlugWhenCharged},lockState={lockState}".format(
                    connectionState=                    vehicle._states["plug"]["connectionState"],
                    state=                              vehicle._states["charging"]["state"],
                    chargingType=                       vehicle._states["charging"]["chargingType"],
                    chargeMode=                         vehicle._states["charging"]["chargeMode"],
                    maxChargeCurrentAc=                 vehicle._states["chargerSettings"]["maxChargeCurrentAc"],
                    autoUnlockPlugWhenCharged=          vehicle._states["chargerSettings"]["autoUnlockPlugWhenCharged"],
                    lockState=                          vehicle._states["plug"]["lockState"]
                )
                print(tags)

                fields = "chargingPowerInWatts={chargingPowerInWatts},remainingToCompleteInSeconds={remainingToCompleteInSeconds},stateOfChargeInPercent={stateOfChargeInPercent},targetStateOfChargeInPercent={targetStateOfChargeInPercent},cruisingRangeElectricInMeters={cruisingRangeElectricInMeters}".format(
                chargingPowerInWatts=                vehicle._states["charging"]["chargingPowerInWatts"],
                remainingToCompleteInSeconds=        vehicle._states["charging"]["remainingToCompleteInSeconds"],
                stateOfChargeInPercent=              vehicle._states["battery"]["stateOfChargeInPercent"],
                targetStateOfChargeInPercent=        vehicle._states["chargerSettings"]["targetStateOfChargeInPercent"],
                cruisingRangeElectricInMeters=       vehicle._states["battery"]["cruisingRangeElectricInMeters"]
                )
                print(fields)
                print(InfluxDb_Url)

                row = {}
                csv_columns = []
                csv_columns.append("Time")
                row["Time"] = datetime.now().isoformat()
                for category,measurements in vehicle._states.items():
                    for measurement_name,value in measurements.items():
                        key = "{}_{}".format(category,measurement_name)
                        row[key]=value
                        csv_columns.append(key)
                
                
                print(row)
                if csv_Enabled:
                    if firstLine:
                        firstLine=False
                        writer = csv.DictWriter(csvfile,fieldnames=csv_columns)
                        writer.writeheader()
                    writer.writerow(row)
                    csvfile.flush()

                time.sleep(INTERVAL-5)
                if await connection.update():
                    print("Success!")
                else:
                    print("Failed")
                

                if InfluxDb_Enabled:
                    r = requests.post(InfluxDb_Url, data = "{},{} {}".format("charging",tags,fields))
                time.sleep(5)
                timesincelogin = datetime.now()-logintime

            try:
                csv_file.close()
            except:
                pass




if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
