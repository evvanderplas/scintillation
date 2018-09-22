#! /usr/bin/env python
'''
  Library with routines to read ISMR files and store the information in sqlite database
'''

import os
import datetime as dt
import sqlite3
import numpy as np
import pandas as pd
import calendar


NAMES = ['weeknumber', 'timeofweek', 'SVID', 'fieldblockvalue', 'azimuth', 'elevation',
         'sig1_CNO_avg_min', 'sig1_S4', 'sig1_S4_corr', 'sig1_phi01', 'sig1_phi03', 'sig1_phi10', 'sig1_phi30', 'sig1_phi60',
         'sig1_avgccd', 'sig1_sigmaccd',
         'sig1_TEC_m45', 'sig1_dTEC_m60_m45',
         'sig1_TEC_m30', 'sig1_dTEC_m45_m30',
         'sig1_TEC_m15', 'sig1_dTEC_m30_m15',
         'sig1_TEC', 'sig1_dTEC_m15_0',
         'sig1_locktime',
         'sbf2ismr_version',
         'sig2_locktime', 'sig2_avg',
         'sig1_SI', 'sig1_SI_nom', 'p_sig1',
         'sig2_CNO_avg_min', 'sig2_S4', 'sig2_S4_corr', 'sig2_phi01', 'sig2_phi03', 'sig2_phi10', 'sig2_phi30', 'sig2_phi60',
         'sig2_avgccd', 'sig2_sigmaccd',
         'sig2_locktime',
         'sig2_SI', 'sig2_SI_nom', 'p_sig2',
         'sig3_CNO_avg_min', 'sig3_S4', 'sig3_S4_corr', 'sig3_phi01', 'sig3_phi03', 'sig3_phi10', 'sig3_phi30', 'sig3_phi60',
         'sig3_avgccd', 'sig3_sigmaccd',
         'sig3_locktime',
         'sig3_SI', 'sig3_SI_nom', 'p_sig3',
         'sig1_T', 'sig2_T', 'sig3_T'
         ]

def dt2ts(dttime):
    """
        Converts a datetime object to UTC timestamp
        naive datetime will be considered UTC.
        https://stackoverflow.com/questions/5067218/get-utc-timestamp-in-python-with-datetime
    """

    # return calendar.timegm(dttime.utctimetuple())
    return pd.Series(dttime.view('int64'), dtype='float')

def init_db(cursor, tabname='sep_data'):
    '''
        Create table for all the SEPTENTRIO data
    '''

    namelist = ','.join('{} REAL'.format(name) for name in NAMES)
    namelist += ', time INTEGER'
    create_table_sql = '''CREATE TABLE IF NOT EXISTS {} (
        {}
    )
    '''.format(tabname, namelist)

    try:
        cursor.execute(create_table_sql)
    except Exception as e:
        print(e)

    return

def write_to_sqlite(df, dbname='scint.db', loc='SABA'):
    '''
        Write the data (in dataframe) from a ISMR file to an SQLite database
    '''
    conn = sqlite3.connect(dbname)
    c = conn.cursor()

    init_db(c, tabname='sep_data')
    df['timestamp'] = dt2ts(df.t)
    df.drop('t')
    df.to_sql('sep_data', c)

    return

def weeksecondstoutc(gpsweek,gpsseconds,leapseconds):
    '''
        Convert GPS week to UTC time
        source: https://gist.github.com/jeremiahajohnson/eca97484db88bcf6b124
    '''

    gps_start = dt.datetime(1980,1,6,0,0,0)
    if isinstance(gpsweek, np.ndarray):
        date_array = np.zeros_like(gpsweek, dtype=dt.datetime)
        print('gpsweek: {} => {}\n{} + {}'.format(gpsweek.shape, date_array.shape, gpsweek, gpsseconds))
        for i, week in enumerate(gpsweek):
            if np.isnan(week):
                continue
            date_array[i] = gps_start + dt.timedelta(days=week*7., seconds=gpsseconds[i])

        return date_array

    else:
        date_array = gps_start + dt.timedelta(days=gpsweek*7., seconds=gpsseconds)

    return date_array


def read_ismr(infile):
    '''
        Open and read ISMR files
        return panda dataframe
    '''


    with open(infile, 'r') as ismr:
        df = pd.read_csv(ismr, header=None, names=NAMES, na_values='nan')

    df['t'] = weeksecondstoutc(df.weeknumber.values, df.timeofweek.values, 0)
    print(df.head())

    return df
