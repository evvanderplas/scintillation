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

def time_plot(var, db, loc=None, svid=None, tstart=None, tend=None, plotdata=None, out='./', log=logging):
    '''
        Make a plot as a function of time of a variable var in the ismr database db
    '''

    try:
        os.makedirs(out)
    except OSError as e:
        log.warning('Output directory: {}'.format(e))

    if plotdata is None:
        plotdata = get_sqlite_data([var, 'timestamp'], db, svid=svid, tstart=tstart, tend=tend, log=log)

    allvardata = np.array([np.float(t[0]) for t in plotdata])
    log.debug('Shape of allvardata {}'.format(allvardata.shape))
    # nanvar = np.array(['nan' in allvar for allvar in allvardata], dtype='bool')
    nanvar = np.isnan(allvardata)
    vardata = allvardata[~nanvar]
    log.debug('Shape of vardata {}'.format(vardata.shape))

    # log.debug('Shape of plotdata without "nan": {}'.format(plotdata[~nanvar].shape))
    timestampdata = np.array([np.int(t[1]) for t in plotdata])[~nanvar]
    log.debug('Where are stupid time values: {}, {}'.format(timestampdata[timestampdata < 1.e6], np.argwhere(timestampdata < 1.e6)))

    timedata = np.array([dt.datetime.fromtimestamp(t[1]) for t in plotdata])[~nanvar]
    # timedata = timedata[~np.isnan(vardata)]

    fig, ax = plt.subplots()
    ax.plot(timedata, vardata, 'b.')
    ax.set_title('{} at {}, {}-{}'.format(var, loc,
        tstart.strftime('%Y%m%d%H%M%S'), tend.strftime('%Y%m%d%H%M%S')))
    fig.autofmt_xdate()

    tag = var
    if loc is not None:
        tag += '_{}'.format(loc)
    if svid is not None:
        if isinstance(svid, int):
            tag += '_{}'.format(str(svid).zfill(2))
        elif isinstance(svid, (tuple,list)):
            tag += '_ID{}-{}'.format(str(min(svid)).zfill(3),str(max(svid)).zfill(3))
    if tstart is not None and isinstance(tstart, dt.datetime):
        tag += '_{}-{}'.format(tstart.strftime('%Y%m%d%H%M%S'), tend.strftime('%Y%m%d%H%M%S'))

    figname = os.path.join(out, 'sql_time_{}.png'.format(tag))
    log.debug('Saving {}'.format(figname))
    fig.savefig(figname)

    return plotdata

def hist_plot(var, db, svid=None, tstart=None, tend=None, plotdata=None, out='./', loc='SABA', log=logging):
    '''
        Make a histogram plot of a variable var in the ismr database db
    '''

    try:
        os.makedirs(out)
    except OSError as e:
        log.warning('Output directory: {}'.format(e))

    if plotdata is None:
        plotdata = get_sqlite_data([var, 'timestamp'], db, svid=svid, tstart=tstart, tend=tend, log=log)

    allvardata = np.array([np.float(t[0]) for t in plotdata])
    # nanvar = np.array(['nan' in allvar for allvar in allvardata], dtype='bool')
    nanvar = np.isnan(allvardata)
    vardata = allvardata[~nanvar]
    log.debug('Size vardata: {}'.format(vardata.shape))
    timestampdata = np.array([t[1] for t in plotdata])[~nanvar]
    timedata = np.array([dt.datetime.fromtimestamp(t[1]) for t in plotdata])[~nanvar]

    tag = var
    if loc is not None:
        tag += '_{}'.format(loc)
    if svid is not None:
        if isinstance(svid, int):
            tag += '_{}'.format(str(svid).zfill(2))
        elif isinstance(svid, (tuple,list)):
            tag += '_ID{}-{}'.format(str(min(svid)).zfill(3),str(max(svid)).zfill(3))
    if tstart is not None and isinstance(tstart, dt.datetime):
        tag += '_{}-{}'.format(tstart.strftime('%Y%m%d%H%M%S'), tend.strftime('%Y%m%d%H%M%S'))

    # 1D histogram
    fig, ax = plt.subplots()
    n, bins, patches = ax.hist(vardata, bins=50, normed=1, facecolor='green', alpha=0.75)
    ax.set_xlabel('{} (binned)'.format(var))
    ax.set_title('Histogram of {} at {}'.format(var, loc))

    figname = os.path.join(out, 'sql_hist_{}_{}.png'.format(tag, loc))
    log.debug('Saving {}'.format(figname))
    fig.savefig(figname)

    # 2D histogram
    fig, ax = plt.subplots()

    ax.hist2d(timestampdata, vardata, bins=[150, 50], norm=LogNorm())
    ax.set_ylabel('{} (binned)'.format(var))

    xlocs = ax.get_xticks()
    ax.set_xticks(xlocs) # unnecessary?
    dtlabels = [dt.datetime.fromtimestamp(tlab) for tlab in xlocs]
    ax.set_xticklabels([dtlab.strftime('%Y-%m-%d') for dtlab in dtlabels])
    ax.set_xlabel('Time (binned)')

    # ax.hist2d(timedata, vardata, bins=[150, 50], norm=LogNorm())

    fig.autofmt_xdate()
    ax.set_title('Histogram as a function of time of {} at {}'.format(var, loc))

    figname = os.path.join(out, 'sql_hist2d_{}_{}.png'.format(tag,loc))
    log.debug('Saving {}'.format(figname))
    fig.savefig(figname)

    return plotdata

def azel_to_xy(df, id=None):
    '''
        Compute x,y from azimuth and elevation in dataframe
        following:
        x = cos e * cos phi
        y = sin e * sin phi

    '''

    HEIGHT = 20200 # altitude of GPS satellites in km

    if id is not None:
        iddf = df[df.SVID == id]
    else:
        iddf = df

    azdata = 2. * np.pi * (iddf['azimuth']/360.)
    eldata = 2. * np.pi * (iddf['elevation']/360.)

    x = HEIGHT * np.cos(eldata) * np.sin(azdata)
    y = HEIGHT * np.cos(eldata) * np.cos(azdata)

    return x,y

def plot_az_el(df, var, cmap='jet'):
    '''
        Plot a variable as function of azimuth and elevation angle
        takes a pd.DataFrame containing var, azimuth and elevation
    '''

    # get_sqlite_data(varlist, db, svid=12, tstart=None, tend=None, table='sep_data', log=logging)
    plotdata = df[df.SVID == id][var].values
    x, y = azel_to_xy(df, id)

    print('AZ/EL: shape of plotdata: ({}, {}): {}'.format(len(x), len(y), plotdata.shape))

    fig, ax = plt.subplots()
    azel = ax.scatter(y, x, c=plotdata, cmap=plt.cm.get_cmap(cmap))
    # ax.plot(plotdata)
    ax.set_xlabel('x = cos [ Elevation] sin [ Azimuth ]')
    ax.set_ylabel('y = cos [ Elevation ] cos [ Azimuth ]')
    plt.colorbar(azel, ax=ax)
    fig.savefig('azelplot_{}_sat{}.png'.format(var, str(id).zfill(2)))
    plt.close(fig)

def plot_az_el_multisat(var, db, svid=None, tstart=None, tend=None, loc='SABA', out='./', cmap='jet', log=None):
    '''
        Plot a variable as function of azimuth and elevation angle
        following:
        x = cos e * cos phi
        y = sin e * sin phi

    '''

    varlist = list([var])
    varlist.extend(['azimuth', 'elevation', 'SVID'])
    print(varlist)
    dbdata = get_sqlite_data(varlist, db, svid=svid, tstart=tstart, tend=tend, table='sep_data', log=log)

    tempdata = dbdata[0:5]
    print('From database: {}'.format(dbdata[0:5]))
    for t in tempdata:
        print('{}'.format(t))
    allvardata = np.array([np.float(t[0]) for t in dbdata])
    azdata = np.array([np.float(t[1]) for t in dbdata])
    eldata = np.array([np.float(t[2]) for t in dbdata])
    sviddata = np.array([np.float(t[3]) for t in dbdata])

    nanvar = np.isnan(allvardata)
    vardata = allvardata[~nanvar]
    azdata = azdata[~nanvar]
    eldata = eldata[~nanvar]
    sviddata = sviddata[~nanvar]
    df = pd.DataFrame({var: vardata, 'azimuth':azdata, 'elevation':eldata, 'SVID': sviddata})
    log.debug('Size vardata: {}'.format(vardata.shape))

    fig, ax = plt.subplots()

    # take the minimum and maximum value within the dataframe and use it to
    # make sure that colors mean the same thing for different
    # satellite tracks
    # minval, maxval = np.nanmin(df[var]), np.nanmax(df[var])
    minval = np.nanpercentile(df[var].astype('float'), 10.)
    maxval = np.nanpercentile(df[var].astype('float'), 95.)
    satellites = df['SVID'].unique()
    for sat in satellites:
        if 1: # sat < 37:
            iddf = df[df.SVID == sat]
            plotdata = iddf[var].astype(float).values
            x, y = azel_to_xy(iddf) # (df, id)
            # print('For sat {} we have {} - {} - {}'.format(sat, len(x), len(y), len(plotdata)))
            print('Scale: {} - {}, min, max here {} - {}'.format(minval, maxval, np.nanmin(plotdata), np.nanmax(plotdata)))
            azel = ax.scatter(x, y, c=plotdata, vmin=minval, vmax=maxval,
                            cmap=plt.cm.get_cmap(cmap), linewidths=0, edgecolors=None,
                            # label='sat {}'.format(sat)
                            )

    ax.set_xlabel('$x = \cos \ \epsilon \quad \sin \ \phi$')
    ax.set_ylabel('$y = \cos \ \epsilon \quad \cos \ \phi$')
    ax.set_title('Tracks: {}'.format(var))
    plt.colorbar(azel, ax=ax)
    outfig = os.path.join(out, 'azelplot_{}_multisat.png'.format(var))
    fig.savefig(outfig, dpi=400)
    plt.close(fig)


if __name__ == '__main__':

    ismrdb_path = './'
    ismrdb_path = '/data/storage/trop/users/plas/SW'
    ismrdb_path = '/Users/plas/data/SW'
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

    # S4 = time_plot('sig1_S4', ismrdb, svid=tuple(range(1, 38)), tstart=startdate, tend=enddate, loc=loc, out='plots', log=logger)
    # TEC = time_plot('sig1_TEC', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, loc=loc, out='plots', log=logger)
    # hist_plot('sig1_S4', ismrdb,  svid=tuple(range(1, 38)), tstart=startdate, tend=enddate, plotdata=S4, out='plots', loc=loc, log=logger)
    # hist_plot('sig1_TEC', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, plotdata=TEC, out='plots', loc=loc, log=logger)
    # hist_plot('sig1_S4', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, out='plots', loc=loc, log=logger)
    # hist_plot('sig2_S4', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, out='plots', loc=loc, log=logger)
    # hist_plot('sig1_phi01', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, out='plots', loc=loc, log=logger)
    # hist_plot('sig2_phi01', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, out='plots', loc=loc, log=logger)

    plot_az_el_multisat('sig1_TEC', ismrdb, svid=satellites,
        tstart=startdate, tend=enddate, loc=loc,
        out='plots', cmap='hot_r', log=logger)
