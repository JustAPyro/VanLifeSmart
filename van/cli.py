#!/usr/bin/env python

import argparse

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

sensor_parser = subparsers.add_parser('sensor')

parser.parse_args()
