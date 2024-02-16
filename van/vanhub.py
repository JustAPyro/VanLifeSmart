import argparse


def get_gps_data():
    return 'hello'


parser = argparse.ArgumentParser()
parser.add_argument("action", help="Select a van action")
parser.add_argument("sensor", help="Get feedback from a van sensor.")
args = parser.parse_args()

if args.action == 'sensor':
    if args.sensor == 'gps':
        print(get_gps_data())
    elif args.sensor == 'tio':
        print('weather')
