#! /usr/bin/env python
'''
    Some tools for the management of GNSS scintillation measurement files in ISMR
    format
'''

import os
import sys
import logging
import yaml
import sqlite3

import datetime as dt
import numpy as np

from lib.constants import TOPO, R_earth

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

def test_logger():
    '''
        Test the logger
    '''
    try:
        logger = init_logger()
        logger.debug('Test message succeeded')
        return 1
    except err:
        print('Initialize logger failed: {}'.format(err))
        return 0

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

def get_sqlite_data(varlist, db, svid=12, tstart=None, tend=None, table='sep_data', log=logging):
    '''
        Get data from SQLite database
    '''

    log.debug('Connect to SQLite db {}'.format(db))
    conn = sqlite3.connect(db)
    c = conn.cursor()

    check_db = False
    if check_db:
        checksql = 'PRAGMA table_info({})'.format(table)
        c.execute(checksql)
        cols = c.fetchall()
        log.debug('Columns: {}'.format(cols))

    if (isinstance(tstart, dt.datetime) and (isinstance(tend, dt.datetime))):
        timestart, timeend = tstart.timestamp(), tend.timestamp()
    elif (isinstance(tstart, (int, float)) and (isinstance(tend, (int, float)))):
        timestart, timeend = tstart, tend

    sql_stat = 'SELECT {} FROM {}  WHERE ' # SVID = {}'
    sql_crit = []

    log.debug('Which satellites: {}'.format(svid))
    if svid is None:
        print('Use all satellite ID (SVID)')
    elif isinstance(svid, int):
        sql_crit.append('SVID = {}'.format(svid))
    elif isinstance(svid, (list, tuple, np.ndarray)):
        if len(svid) == 1:
            sql_crit.append('SVID = {}'.format(svid[0]))
        else:
            sql_crit.append('SVID IN {}'.format(tuple(svid)))

    if tstart is not None:
        sqltime = 'timestamp BETWEEN {} and {}'.format(timestart, timeend)
        sql_crit.append(sqltime)

    log.debug('Criteria: {}'.format(sql_crit))
    sql_stat += ' AND '.join(sql_crit)
    vars = ','.join(var for var in varlist)
    log.debug('Start reading: {}'.format(sql_stat.format(vars, table, svid)))
    c.execute(sql_stat.format(vars, table, svid))
    data = c.fetchall()
    log.debug('Shape of data; {}'.format(len(data))) # , data[0].shape))
    log.debug('Data: {}'.format(data[:20])) # , data[0].shape))

    return data

def deg_to_lon(angle):
    '''
        Return angle between -180 and 180 degrees
    '''
    return (angle + 180.) % 360 - 180

def azel_to_xy(azimuth, elevation, h=None):
    '''
        Compute x,y from azimuth and elevation in dataframe
        following:
        x = cos e * cos phi
        y = sin e * sin phi

    '''
    if h is None:
        h = 300 # km

    azdata = 2. * np.pi * (azimuth/360.)
    eldata = 2. * np.pi * (elevation/360.)

    x = h * np.cos(eldata) * np.sin(azdata)
    y = h * np.cos(eldata) * np.cos(azdata)

    return x,y

def azel_to_latlon(azimuth, elevation, point=TOPO['SABA'], height=300):
    '''
        Compute latitude longitude from azimuth and elevation angle
        and height in km

        First, distance north and east is computed using height, then from a
        distance from a certain latlon-point lat and lon.
    '''
    relx, rely = azel_to_xy(azimuth, elevation, h=height)
    lat_angle = point[0] + np.arctan2(rely, R_earth)
    lon_angle = point[1] + np.arctan2(relx, R_earth)
    # result_df['lat'] = lat_angle
    # result_df['lon'] = lon_angle

    return deg_to_lon(lon_angle), lat_angle

if __name__ == '__main__':

    print('tools')
    if test_logger():
        print('All fine')
