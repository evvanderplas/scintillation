#! /usr/bin/env python

'''
    Script that plots information from the Septentrio GPS receiver instrument
'''

import os, sys
import argparse
import yaml
import datetime as dt
import logging

import plot_ismr

def init_logger():
    '''
        Initialize a logger
    '''
    logger = logging.getLogger('plotting')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    return logger

def read_yaml(yamlfile):
    '''
        Read a YAML file into a dictionary
    '''

    with open(yamlfile, 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    return config

def read_confdate(dlist):
    '''
        Read the list of [Y, m, d, H, M, S] and turn it into a datetime
    '''

    if len(dlist) >= 6:
        readdate = dt.datetime(dlist[0], dlist[1], dlist[2], dlist[3], dlist[4], dlist[5])
    elif len(dlist) == 3:
        readdate = dt.datetime(dlist[0], dlist[1], dlist[2], 0, 0, 0)

    return readdate

if __name__ == '__main__':

    logger = init_logger()
    logger.info('Plotting data')

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="the configuration file on what to plot")
    args = parser.parse_args()
    logger.debug(args.infile)

    dbconfig = read_yaml('local.yaml')

    plotconfig = read_yaml(args.infile)
    ismrdb = os.path.join(dbconfig['ismrdb_path'],dbconfig['ismrdb_name'].format(plotconfig['location']))
    startdate = read_confdate(plotconfig['startdate'])
    enddate = read_confdate(plotconfig['enddate'])
    plot_var = plotconfig['plot_var']

    print('plot_var {}, {} - {}'.format(plot_var, startdate, enddate))

    if plotconfig['plot_type'] == 'az_el':
        plot_ismr.plot_az_el_multisat(plot_var, ismrdb, svid=plotconfig['satellites'],
            tstart=startdate, tend=enddate,
            loc=plotconfig['location'], out=plotconfig['outputdir'],
            cmap='hot_r', log=logger)
    elif plotconfig['plot_type'] == 'time':
        plot_ismr.time_plot(plot_var, ismrdb, svid=plotconfig['satellites'],
            tstart=startdate, tend=enddate,
            loc=plotconfig['location'], out=plotconfig['outputdir'], log=logger)