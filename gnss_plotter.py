#! /usr/bin/env python

'''
    Script that plots information from the Septentrio GPS receiver instrument
'''

import os, sys
import argparse

if __name__ == '__main__':

    print('Plotting data')

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="the configuration file on what to plot")
    args = parser.parse_args()
    print(args.infile)

    import yaml

    with open("local.yaml", 'r') as stream:
        try:
            dbconfig = yaml.load(stream))
        except yaml.YAMLError as exc:
            print(exc)

    print(dbconfig)
