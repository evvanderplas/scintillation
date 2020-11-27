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

def interpret_svid(satellites):
    '''
        allow for easier selection of GNSS satellites
    '''
    SATRANGE = {
        'gps': np.arange(1,38),
        'glonass': np.arange(38,62),
        'galileo': np.arange(71, 103),
        'sbas': np.arange(120,141),
        'compass': np.arange(141, 173),
        'qzss': np.arange(180,188)
    }

    # self.log.debug('Interpreting: {}: {}'.format(self.config['satellites'], SATRANGE[self.config['satellites'].lower()]))
    if isinstance(satellites, str):
        if satellites.lower() in SATRANGE.keys():
            return SATRANGE[satellites.lower()]
    elif isinstance(satellites, (tuple, list, np.array)):
        return satellites
    elif '-' in satellites:
        print('Divination of a range')
        s1, sl = satellites.split('-')
        return np.arange(int(s1), int(sl))

def add_hour_of_day(timedata):
    '''
        Get the time-of-day for each measurement
    '''
    tod = np.zeros_like(timedata)
    for mt_idx, mtime in enumerate(timedata):
        tod[mt_idx] = (mtime - dt.datetime(mtime.year, mtime.month, mtime.day, 0,0,0,0)).seconds/3600.
    # timeofday = tod
    return tod

def get_sqlite_data(varlist, db, svid=12, tstart=None, tend=None,
                    restrict_crit=None, table='sep_data', log=logging):
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

    if restrict_crit is not None:
        sql_crit.extend(restrict_crit)

    log.debug('Criteria: {}'.format(sql_crit))
    sql_stat += ' AND '.join(sql_crit)
    vars = ','.join(var for var in varlist)
    log.debug('Start reading: {}'.format(sql_stat.format(vars, table, svid)))
    c.execute(sql_stat.format(vars, table, svid))
    data = c.fetchall()
    log.debug('Shape of data; {}'.format(len(data))) # , data[0].shape))
    log.debug('Data: {}'.format(data[:20])) # , data[0].shape))

    return data

def nice_data(plotdata, vars, nrvars=None, log=logging):
    '''
        Make sure that the data does not contain NaN or so
        output
    '''
    if nrvars is None:
        nrvars = len(vars)

    if not isinstance(nrvars, int) or nrvars != len(plotdata[0]):
        print('The number of variables in the data from the database should be an integer, not {}'.format(nrvars))
        sys.exit(0)

    if nrvars == 1:
        allvardata = np.array([np.float(t[0]) for t in plotdata])
        nanvar = np.isnan(allvardata)
        vardata = allvardata[~nanvar]
        log.debug('Size vardata: {}'.format(vardata.shape))
    else:
        vardata = {}
        timestampdata = np.array([t[-1] for t in plotdata])

        # make two rounds:
        # first to get all the nan-values, second to get the data:
        nanvar = np.zeros_like(timestampdata, dtype=bool)
        for idx_var, multivar in enumerate(vars):
            allvardata = np.ones(len(plotdata), dtype=np.float)
            try:
                # allvardata = np.array([np.float(t[idx_var]) for t in plotdata if not None in t else None])
                for idx_t, t in enumerate(plotdata):
                    if None in t or str(t[idx_var]).isalpha():
                        allvardata[idx_t] = None
                    else:
                        allvardata[idx_t] = np.float(t[idx_var])
            except TypeError as terr:
                for t in plotdata:
                    if t[idx_var] is None:
                        print('{}, idx {}: {} allvars = {}'.format(t, idx_var, multivar, vars))
                log.error('what went wrong? var {} in {}?: {}'.format(multivar, vars, t))
                log.error('up to now: {}'.format(allvardata))
            log.debug('Round {}: # of nans: {}, total {}'.format(idx_var,
                        np.sum(np.isnan(allvardata)), np.sum(nanvar)))
            nanvar = np.logical_or(np.isnan(allvardata), nanvar)

        # remember where the NaN's are:
        nanvar_first = nanvar
        log.debug('How many nan? {}'.format(np.sum(nanvar_first)))

        # second round:
        # self.log.debug('Loop over vars: {}, but index over req_list: {}'.format(vars, req_list))
        for idx_var, multivar in enumerate(vars):

            # allvardata = np.array([np.float(t[idx_var]) for t in plotdata])
            for idx_t, t in enumerate(plotdata):
                if None in t or str(t[idx_var]).isalpha():
                    allvardata[idx_t] = None
                else:
                    allvardata[idx_t] = np.float(t[idx_var])

            vardata[multivar] = allvardata[~nanvar]
            log.debug('Size vardata {}: {}'.format(multivar, vardata[multivar].shape))

    # gamble that the not available data is the same for all vars in the list...
    timestampdata = np.array([t[-1] for t in plotdata])[~nanvar]
    timedata = np.array([dt.datetime.fromtimestamp(t[-1]) for t in plotdata])[~nanvar]
    vardata['timeofday'] = add_hour_of_day(timedata)

    # for a next plot(?)
    # self.vardata = vardata
    log.debug('Vars: {}, vardata: {}'.format(vars, vardata.keys()))
    for var in vars:
        log.debug('Var {}: {}'.format(var, np.sum(np.isnan(vardata[var]))))
    return vardata

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

def azel_to_latlon(azimuth, elevation, point=TOPO['SABA'], height=300.e3):
    '''
        Compute latitude longitude from azimuth and elevation angle
        and height in km

        First, distance north and east is computed using height, then from a
        distance from a certain latlon-point lat and lon.
    '''
    relx, rely = azel_to_xy(azimuth, elevation, h=height)
    lat_angle = point[0] + (360./2*np.pi) * np.arctan2(rely, 1.e0 * R_earth)
    lon_angle = point[1] + (360./2*np.pi) * np.arctan2(relx, 1.e0 * R_earth)
    # result_df['lat'] = lat_angle
    # result_df['lon'] = lon_angle

    return deg_to_lon(lon_angle), lat_angle

def _sats_for_figname(sats, log=logging):
    '''
        Decide how to indicate for which sats the figure was made
    '''
    self.log.debug('For figname: satellites: {}'.format(sats))
    if isinstance(sats, str): # not str(sats).isdigit(): # might contain "unknown" or something
        return sats
    elif len(list(sats)) == 1: # only one
        return str(list(sats)[0])
    elif str(sats).isalpha(): # it is a shortcut for a range of satellites
        return str(sats)
    elif len(list(sats)) < 4: # a few numbers:
        return '_'.join([str(s) for s in list(sats)])
    else: # a long list of numbers
        smin, smax = np.min(list(sats)), np.max(list(sats))
        return '{}-{}'.format(smin, smax)


if __name__ == '__main__':

    print('tools')
    if test_logger():
        print('All fine')
