#!/usr/bin/env python
import argparse
import json
import os

import requests
import serial
from dotenv import load_dotenv
from serial import SerialException

load_dotenv()


def has_gps():
    try:
        gps = serial.Serial('/dev/ttyACM0', baudrate=9600)
        return True
    except SerialException:
        return False


def get_gps_data():
    gps = serial.Serial('/dev/ttyACM0', baudrate=9600)
    formats = ['GPGGA', 'GPVTG']
    found = {format_type: False for format_type in formats}
    data = {}

    # Flush buffer
    gps.flushInput()
    gps.flushOutput()

    # Trash the first line because it might be malformed
    _ = gps.readline()
    while True:
        parsed = []
        sentence = gps.readline().decode('utf-8')
        formatting = sentence[1:6]
        values = sentence.split(',')
        if formatting == 'GPGGA':
            data['utc_time'] = float(values[1])

            # Process N/S/E/W into decimal lat/long
            latitude = float(values[2])
            if values[3] == 'W':
                latitude = latitude * -1
            longitude = float(values[4])
            if values[5] == 'S':
                longitude = longitude * -1
            data['latitude'] = latitude
            data['longitude'] = longitude

            # Fix quality processing
            fq = int(values[6])
            if fq == 0:
                fq = 'Not Fixed'
            elif fq == 1:
                fq = 'GPS Fix'
            elif fq == 2:
                fq = 'DGPS Fix'
            else:
                fq = f'Unknown Fix: {fq}'
            data['fix_quality'] = fq
            data['satellites_used'] = int(values[7])
            data['HDOP'] = float(values[8])
            data['altitude'] = float(values[9])
            found['GPGGA'] = True
        if formatting == 'GPVTG':
            data['true_track'] = None if values[1] == '' else float(values[1])
            data['magnetic_track'] = None if values[3] == '' else float(values[3])
            data['ground_speed'] = float(values[7])
            found['GPVTG'] = True
        if all(value == True for value in found.values()):
            return data


def get_tio_data(latitude: float = None, longitude: float = None, cmd_args=None):
    if has_gps():
        data = get_gps_data()
        latitude = data['latitude']
        longitude = data['longitude']

    if len(cmd_args.location) == 2:
        latitude = cmd_args.location[0]
        longitude = cmd_args.location[1]
    else:
        return {'Error': 'args.location should provide exactly 2 values.'}

    if latitude is None or longitude is None:
        return {'Error': 'Could not find latitude and longitude.'}

    data = {}
    response = requests.get('https://api.tomorrow.io/v4/weather/realtime'
                            f'?location={latitude},{longitude}'
                            f'&apikey={os.environ["TOMORROWAPI"]}')

    td = response.json()['data']['values']
    data['time'] = response.json()['data']['time']
    data['latitude'] = response.json()['location']['lat']
    data['longitude'] = response.json()['location']['lon']

    data['uv_index'] = td['uvIndex']
    data['humidity'] = td['humidity']
    data['wind_gust'] = td['windGust']
    data['dew_point'] = td['dewPoint']
    data['cloud_base'] = td['cloudBase']
    data['wind_speed'] = td['windSpeed']
    data['visibility'] = td['visibility']
    data['cloud_cover'] = td['cloudCover']
    data['temperature'] = td['temperature']
    data['weather_code'] = td['weatherCode']
    data['cloud_ceiling'] = td['cloudCeiling']
    data['rain_intensity'] = td['rainIntensity']
    data['snow_intensity'] = td['snowIntensity']
    data['wind_direction'] = td['windDirection']
    data['sleet_intensity'] = td['sleetIntensity']
    data['uv_health_concern'] = td['uvHealthConcern']
    data['temperature_apparent'] = td['temperatureApparent']
    data['pressure_surface_level'] = td['pressureSurfaceLevel']
    data['freezing_rain_intensity'] = td['freezingRainIntensity']
    data['precipitation_probability'] = td['precipitationProbability']
    return data


parser = argparse.ArgumentParser()
parser.add_argument("action", help="Select a van action")
parser.add_argument("sensor", help="Get feedback from a van sensor.")
parser.add_argument('--location', nargs='+', type=float)
args = parser.parse_args()

if args.action == 'sensor':
    if args.sensor == 'gps':
        print(json.dumps(get_gps_data(), indent=4))
    elif args.sensor == 'tio':
        print(json.dumps(get_tio_data(cmd_args=args), indent=4))
