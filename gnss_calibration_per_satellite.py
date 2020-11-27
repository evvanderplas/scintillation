#! /usr/bin/env python
'''
    A small module designed to see if a specific satellite may give negative
    total electron content measurments.
    Generates for a certain period a histogram as function of time.
'''


import os #, sys
import argparse
import datetime as dt
import logging
import time

import yaml

import plot_ismr
import plot_ismr_map
from lib.tools import init_logger, read_yaml, read_confdate

def main():
    '''
        Main section of the calibration script
    '''
    print('Put main script in here')

if __name__ == '__main__':

    main()
    logger = init_logger()
    logger.info('Plotting data')

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="the configuration file on what to plot")
    args = parser.parse_args()
    logger.debug(args.infile)

    # read where the database is
    dbconfig = read_yaml('local.yaml')

    # read what plot(s) to make
    plotconfig = read_yaml(args.infile)
    ismrdb = os.path.join(dbconfig['ismrdb_path'], dbconfig['ismrdb_name'].format(plotconfig['location']))
    startdate = read_confdate(plotconfig['startdate'])
    enddate = read_confdate(plotconfig['enddate'])
    plot_var = plotconfig['plot_var']

    # make one dict with the settings to convey to plotting routine
    plotconfig['startdt'] = read_confdate(plotconfig['startdate'])
    plotconfig['enddt'] = read_confdate(plotconfig['enddate'])
    for item, setting in dbconfig.items():
        plotconfig[item] = setting

    print('plot_var {}, {} - {}'.format(plot_var, startdate, enddate))
    tstart = time.time()

    for sat in range(1,137):
        plotconfig['satellites'] = sat
        plot_ismr.hist_plot(plotconfig, log=logger)

        tend = time.time()
        print('Satellite: {}, Time elapsed = {} s'.format(sat, tend-tstart))
