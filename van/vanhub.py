#!/usr/bin/env python
import argparse
import json
import os

import requests
import serial
from dotenv import load_dotenv
from requests.adapters import Retry

from van.sensors import get_gps_data, get_tio_data

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

# ABSTRACT- Step 5/6: A function that actually generates the data



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
