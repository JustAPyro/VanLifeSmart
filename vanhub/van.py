import argparse
parser = argparse.ArgumentParser()
parser.add_argument("action", help="Select a van action")
parser.add_argument("sensor", help="Get feedback from a van sensor.")
args = parser.parse_args()

if args.action == 'sensor':
    if args.sensor == 'gps':
        print('gps data!')