#!/usr/bin/env python
import argparse
import json
import serial

gps = serial.Serial('/dev/ttyACM0', baudrate=9600)


def get_gps_data():
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
            data['time'] = values[1]
            data['latitude'] = (values[2], values[3])
            data['longitude'] = (values[4], values[5])
            data['fix_quality'] = values[6]
            data['satellites_used'] = values[7]
            data['HDOP'] = values[8]
            data['altitude'] = (values[9], values[10])
            found['GPGGA'] = True
        if formatting == 'GPVTG':
            data['true_track'] = values[1]
            data['magnetic_track'] = values[3]
            data['ground_speed'] = values[7]
            found['GPVTG'] = True
        if all(value == True for value in found.values()):
            return data


parser = argparse.ArgumentParser()
parser.add_argument("action", help="Select a van action")
parser.add_argument("sensor", help="Get feedback from a van sensor.")
args = parser.parse_args()

if args.action == 'sensor':
    if args.sensor == 'gps':
        print(json.dumps(get_gps_data(), indent=4))
    elif args.sensor == 'tio':
        print('weather')
