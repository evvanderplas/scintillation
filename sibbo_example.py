#! /usr/bin/env python

import read_ismr
import os
import sqlite3
import datetime as dt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import time
import logging

topo = {
    'SABA': (17.62048, -63.24323),
    'SEUT': (17.47140, -62.97570)
}

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
    elif isinstance(svid, (list, tuple)):
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

if __name__ == '__main__':

    ismrdb_path = '/data/storage/trop/users/plas/SW'
    # ismrdb_path = '/Users/plas/data/SW'
    loc = 'SABA'
    # loc = 'SEUT'
    ismrdb = os.path.join(ismrdb_path,'test_scint_{}.db'.format(loc))

    logger = logging.getLogger('plotting')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    startdate = dt.datetime(2018,5,4,0,0,0)
    enddate = dt.datetime(2018,5,7,0,0,0)
    # enddate = dt.datetime(2018,5,10,0,0,0)

    satellites = (38, 39, 40, 41)

    plotdata = get_sqlite_data(['sig1_TEC', 'SVID', 'timestamp', 'azimuth', 'elevation'], ismrdb, svid=satellites, tstart=startdate, tend=enddate, log=logger)
    allvardata = np.array([np.float(t[0]) for t in plotdata])
    sviddata = np.array([np.float(t[1]) for t in plotdata])
    svids = sorted(np.unique(sviddata))
    az = np.array([np.float(t[3]) for t in plotdata])
    el = np.array([np.float(t[4]) for t in plotdata])
    logger.debug('Shape of allvardata {}'.format(allvardata.shape))
    for a, e, v in zip(az[:10], el[:10], allvardata[:10]):
        logger.debug('Azimuth, elevation ({}, {}), value : {}'.format(a,e,v))
