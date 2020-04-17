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

    print('tools')
    if test_logger():
        print('All fine')
