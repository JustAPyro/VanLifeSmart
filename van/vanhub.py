#!/usr/bin/env python
import argparse
import json
import os

import requests
import serial
from dotenv import load_dotenv

NO_ARG = 1
MISSING_ARG = 2
load_dotenv()


def get_van_hub():
    with open('vhs_cmd_config.json', 'r') as file:
        return json.load(file)['VAN_HUB_LOCATION']


def set_van_hub(van_hub_location: str):
    # TODO: Try polling the new location before setting it
    with open('vhs_cmd_config.json', 'r+') as file:
        data = json.load(file)
        data['VAN_HUB_LOCATION'] = van_hub_location
        file.seek(0)  # rewind
        json.dump(data, file)
        file.truncate()


def has_gps():
    try:
        gps = serial.Serial('/dev/ttyACM0', baudrate=9600)
        return True
    except (Exception,):
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
            latitude = float(values[2][0:2]) + (float(values[2][2:]) / 60)
            if values[3] == 'W':
                latitude = latitude * -1
            longitude = float(values[4][0:3]) + (float(values[4][3:]) / 60)
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
            data['hdop'] = float(values[8])
            data['altitude'] = float(values[9])
            found['GPGGA'] = True
        if formatting == 'GPVTG':
            data['true_track'] = None if values[1] == '' else float(values[1])
            data['magnetic_track'] = None if values[3] == '' else float(values[3])
            data['ground_speed'] = float(values[7])
            found['GPVTG'] = True
        if all(value == True for value in found.values()):
            return data


# ABSTRACT- Step 5/6: A function that actually generates the data
def get_tio_data(latitude: float = None, longitude: float = None, arguments=None):
    data = {}
    if has_gps():
        gps = get_gps_data()
        latitude = gps['latitude']
        longitude = gps['longitude']
        data['gps'] = gps
    else:
        data['gps'] = {'latitude': latitude, 'longitude': longitude}

    if arguments and arguments.location and len(arguments.location) == 2:
        latitude = arguments.location[0]
        longitude = arguments.location[1]
    elif arguments and arguments.location:
        return {'Error': 'args.location should provide exactly 2 values.'}

    if latitude is None or longitude is None:
        return {'Error': 'Could not find latitude and longitude.'}

    if not os.getenv('TOMORROWAPI'):
        return {}
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


def sensor_handler(arguments):
    if args.input == 'gps':
        print(json.dumps(get_gps_data(), indent=4))
    elif args.input == 'tio':
        print(json.dumps(get_tio_data(arguments), indent=4))
    else:
        print("{'error': 'Sensor input parameters not recognized.'}")


def schedule_handler(arguments):
    schedulers = requests.get(f'{get_van_hub()}/scheduler.json')
    if schedulers.status_code != 200:
        print(f'Error connecting to the local van hub. Make sure {get_van_hub()} is the correct address.')
    else:
        print(json.dumps(schedulers.json(), indent=4))


def config_handler(arguments):
    if arguments.set == NO_ARG:
        print(f'Currently targeting hub at: {get_van_hub()}. Use the -s or --set flag to change this.')
    elif arguments.set == MISSING_ARG:
        print(f'To use the -s flag please include a new target van hub. E.g. "vanhub hub -s https://127.0.0.1:8000"')
    else:
        set_van_hub(arguments.set)
        print(f'Updated target to van hub running at {arguments.set}')


def adjust_handler(arguments):
    #
    arg_dict = vars(arguments)
    time_args = ['seconds', 'minutes', 'hours', 'days', 'weeks']
    included_time_args = {targ: int(arg_dict.get(targ)) for targ in arg_dict
                          if arg_dict.get(targ) is not None and targ in time_args}
    # If the user is setting interval and didn't include time args we complain
    if arguments.trigger_type == 'interval' and not included_time_args:
        print('Error: Please include time arguments when using the interval trigger.')

    trigger = {
        'type': 'interval',
        'interval': included_time_args
    }

    r = requests.patch(f'{get_van_hub()}/scheduler/report.json', json={'trigger': trigger})
    if r.status_code != 200:
        print('Error setting time')
    else:
        print('Successfully requested van hub to change interval.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='vanhub')
    subparsers = parser.add_subparsers()

    parser_sensor = subparsers.add_parser('sensor', help='Get information from van hub sensors.')
    # ABSTRACT SENSOR ADDED HERE
    parser_sensor.add_argument("input", choices=['gps', 'tio'], help="Get feedback from this van sensor.")
    # parser.add_argument('--location', nargs='+', type=float)
    # parser.add_argument('--raw', action='store_false')
    parser_sensor.set_defaults(func=sensor_handler)

    # ---- Parser for the scheduling system ----
    schedule_parser = subparsers.add_parser('schedule',
                                            help='Get information or modify the schedule of van hub systems.')
    schedule_parser.set_defaults(func=schedule_handler)

    # ---- Parser for the config ----
    hub_parser = subparsers.add_parser('config',
                                       help='View and change config information for the van hub command line tool.')
    hub_parser.add_argument('-s', '--set', nargs='?', default=NO_ARG, const=MISSING_ARG)
    hub_parser.set_defaults(func=config_handler)

    # TODO :Refactor THIS!
    # ADD TO CHOICES HERE
    sched = subparsers.add_parser('adjust')
    sched.add_argument('scheduler', choices=['report', 'tio', 'gps'], help='Select the scheduler you want to change.')
    sched.add_argument('trigger_type', choices=['interval'],
                       help='The type of trigger you want to set on this scheduler.')

    trigger_time_group = sched.add_argument_group('Interval time',
                                                  'Flags used to select the amount of time between interval triggers.'
                                                  '\nPlease note that when using interval one or more of these must be '
                                                  'present.')
    trigger_time_group.add_argument('--seconds', type=int)
    trigger_time_group.add_argument('--minutes', type=int)
    trigger_time_group.add_argument('--hours', type=int)
    trigger_time_group.add_argument('--days', type=int)
    trigger_time_group.add_argument('--weeks', type=int)
    sched.set_defaults(func=adjust_handler)

    args = parser.parse_args()

    try:
        args.func(args)
    except (Exception,):
        parser.print_help()
