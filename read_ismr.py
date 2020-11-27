#! /usr/bin/env python
'''
  Library with routines to read ISMR files and store the information in sqlite database
'''

import os
import datetime as dt
import pytz
import sqlite3
import numpy as np
import pandas as pd
import calendar

HEADER_NAMES = ['weeknumber', 'timeofweek', 'SVID', 'fieldblockvalue']
#NAMES = ['weeknumber', 'timeofweek', 'SVID', 'fieldblockvalue',
NAMES = ['azimuth', 'elevation',
         'sig1_CNO_avg_min', 'sig1_S4', 'sig1_S4_corr', 'sig1_phi01', 'sig1_phi03', 'sig1_phi10', 'sig1_phi30', 'sig1_phi60',
         'sig1_avgccd', 'sig1_sigmaccd',
         'sig1_TEC_m45', 'sig1_dTEC_m60_m45',
         'sig1_TEC_m30', 'sig1_dTEC_m45_m30',
         'sig1_TEC_m15', 'sig1_dTEC_m30_m15',
         'sig1_TEC', 'sig1_dTEC_m15_0',
         'sig1_locktime',
         'sbf2ismr_version',
         'sig1_f2_locktime', 'sig1_f2_avg',
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

REDUCED_NAMES = ['azimuth', 'elevation', 'sig1_TEC',
                 'sig1_S4', 'sig1_S4_corr',
                 'sig2_S4', 'sig2_S4_corr',
                 'sig3_S4', 'sig3_S4_corr',]

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

    # namelist = 'index INTEGER, '
    namelist = ', '.join('{} INTEGER'.format(name) for name in HEADER_NAMES)
    namelist += ', ' + ', '.join('{} REAL'.format(name) for name in NAMES)
    namelist += ', timestamp INTEGER'
    create_table_sql = '''CREATE TABLE IF NOT EXISTS {} (
        {}
    )
    '''.format(tabname, namelist)
    create_index = 'CREATE INDEX IF NOT EXISTS "idx_timestamp" ON {} ("timestamp")'.format("{}".format(tabname))

    try:
        # print('Create table using: {}'.format(create_table_sql))
        cursor.execute(create_table_sql)
        cursor.execute(create_index)
    except Exception as e:
        print(e)

    return cursor

def init_reduced_db(cursor, tabname='sep_data'):
    '''
        Create table for a reduced set of the the SEPTENTRIO data
    '''

    # namelist = 'index INTEGER, '
    namelist = ', '.join('{} INTEGER'.format(name) for name in HEADER_NAMES)
    namelist += ', ' + ', '.join('{} REAL'.format(name) for name in REDUCED_NAMES)
    namelist += ', timestamp INTEGER'
    create_table_sql = '''CREATE TABLE IF NOT EXISTS {} (
        {},
        PRIMARY KEY ('weeknumber', 'timeofweek', 'SVID')
    )
    '''.format(tabname, namelist)
    create_index = 'CREATE INDEX IF NOT EXISTS "idx_timestamp" ON {} ("timestamp")'.format("{}".format(tabname))

    try:
        # print('Create table using: {}'.format(create_table_sql))
        cursor.execute(create_table_sql)
        cursor.execute(create_index)
    except Exception as e:
        print(e)

    return cursor


def write_to_sqlite(df, dbname='scint.db', tabname='sep_data_{}', loc='SABA'):
    '''
        Write the data (in dataframe) from a ISMR file to an SQLite database
    '''

    # isolation_level = None should enable autocommit
    conn = sqlite3.connect(dbname) #, isolation_level=None)
    c = conn.cursor()

    init_db(c, tabname=tabname.format(loc))

    # #############
    # df_test = df[['weeknumber', 'timeofweek', 'SVID']]
    # print(df_test.head())
    # print(df_test.columns)
    # df_test.to_sql('test', conn, if_exists='append', index=False)
    # #################

    df.to_sql('sep_data_{}'.format(loc), conn, if_exists='append', index=False)
    # df.to_sql('other_data_{}'.format(loc), conn, if_exists='append')

    return

def write_to_reduced_sqlite(df, dbname='scint.db', tabname='sep_data_{}', loc='SABA'):
    '''
        Write the data (in dataframe) from a ISMR file to an SQLite database
    '''

    # isolation_level = None should enable autocommit
    conn = sqlite3.connect(dbname) #, isolation_level=None)
    c = conn.cursor()

    init_reduced_db(c, tabname=tabname.format(loc))
    success = False
    try:
        df.to_sql('sep_data_{}'.format(loc), conn, if_exists='append', index=False)
        success = True
    except sqlite3.IntegrityError as sqlerr:
        print('Already present in the database: {}, moving on'.format(sqlerr))

    return success


def weeksecondstoutc(gpsweek, gpsseconds, leapseconds):
    '''
        Convert GPS week to UTC time
        source: https://gist.github.com/jeremiahajohnson/eca97484db88bcf6b124
    '''

    gps_start = dt.datetime(1980,1,6,0,0,0)

    if isinstance(gpsweek, np.ndarray):
        date_array = np.zeros_like(gpsweek, dtype=dt.datetime)
        timestamp_array = np.zeros_like(gpsweek, dtype=np.float64)
        # print('gpsweek: {} => {}\n{} + {}'.format(gpsweek.shape, date_array.shape, gpsweek, gpsseconds))
        for i, week in enumerate(gpsweek):
            if np.isnan(week):
                continue
            # print('Time delta days = week : {},'.format(week))
            # print( 'seconds: {}'.format(gpsseconds[i]) )
            date_array[i] = gps_start + dt.timedelta(days=week*7., seconds=np.float(1.* gpsseconds[i]))
            timestamp_array[i] = date_array[i].timestamp()

        return date_array, timestamp_array

    else:
        date_array = gps_start + dt.timedelta(days=gpsweek*7., seconds=np.float64(1.* gpsseconds))
        timestamp_array = date_array.timestamp()

    return date_array, timestamp_array


def read_ismr(infile):
    '''
        Open and read ISMR files
        return panda dataframe
    '''

    print('Parsing {}'.format(infile))

    df_names = HEADER_NAMES + NAMES
    with open(infile, 'r') as ismr:
        df = pd.read_csv(ismr, header=None, names=df_names, na_values='nan')

    datetimes, df['timestamp'] = weeksecondstoutc(df.weeknumber.values, df.timeofweek.values, 0)

    return df

def read_reduced_ismr(infile):
    '''
        Open and read ISMR files
        return panda dataframe
    '''

    print('Parsing {}'.format(infile))

    df_names = HEADER_NAMES + NAMES
    with open(infile, 'r') as ismr:
        df = pd.read_csv(ismr, header=None, names=df_names, na_values='nan')

    df_reduced = df[HEADER_NAMES + REDUCED_NAMES]
    # print(df_reduced.head())
    datetimes, df_reduced['timestamp'] = weeksecondstoutc(df.weeknumber.values, df.timeofweek.values, 0)

    return df_reduced
