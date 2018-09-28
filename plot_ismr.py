#! /usr/bin/env python

import read_ismr
import os
import sqlite3
import datetime as dt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging

def get_sqlite_data(varlist, db, table='sep_data', log=logging):
    '''
        Get data from SQLite database
    '''

    conn = sqlite3.connect(db)
    c = conn.cursor()

    checksql = 'PRAGMA table_info({})'.format(table)
    c.execute(checksql)
    cols = c.fetchall()
    log.debug('Columns: {}'.format(cols))

    sqlstat = 'SELECT {},{} FROM {}  WHERE SVID = 11'
    c.execute(sqlstat.format(','.join(var for var in varlist), 'timestamp', table))

    data = c.fetchall()
    log.debug('Shape of data; {}'.format(len(data))) # , data[0].shape))
    log.debug('Data: {}'.format(data[:20])) # , data[0].shape))

    return data

def time_plot(var, db, out='./', log=logging):
    '''
        Make a plot as a function of time of a variable var in the ismr database db
    '''

    try:
        os.makedirs(out)
    except OSError as e:
        log.warning('Output directory: {}'.format(e))

    plotdata = get_sqlite_data([var, 'timestamp'], db, log=log)
    vardata = np.array([t[0] for t in plotdata])
    timedata = np.array([dt.datetime.fromtimestamp(t[1]) for t in plotdata])
    fig, ax = plt.subplots()
    ax.plot(timedata, vardata, 'b.')

    figname = os.path.join(out, 'sql_time_{}.png'.format(var))
    log.debug('Saving {}'.format(figname))
    fig.savefig(figname)

if __name__ == '__main__':

    ismrdb_path = './'
    ismrdb_path = '/data/storage/trop/users/plas/SW'
    ismrdb = os.path.join(ismrdb_path,'test_scint_SABA.db')

    logger = logging.getLogger('plotting')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    time_plot('sig1_S4', ismrdb, out='plots', log=logger)
