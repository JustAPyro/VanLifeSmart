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
            fq = values[6]
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
            data['HDOP'] = values[8]
            data['altitude'] = float(values[9])
            found['GPGGA'] = True
        if formatting == 'GPVTG':
            data['true_track'] = values[1]
            data['magnetic_track'] = values[3]
            data['ground_speed'] = float(values[7])
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
