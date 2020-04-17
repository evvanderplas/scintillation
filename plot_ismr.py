#! /usr/bin/env python

import os
import sqlite3
import time
import logging
import datetime as dt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# import read_ismr


topo = {
    'SABA': (17.62048, -63.24323),
    'SEUT': (17.47140, -62.97570)
}
R_earth = 6378.100   # m
HEIGHT = 20200 # altitude of GPS satellites in km

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

def time_plot(var, db, loc=None, svid=None, tstart=None, tend=None, plotdata=None, out='./', log=logging):
    '''
        Make a plot as a function of time of a variable var in the ismr database db
    '''

    try:
        os.makedirs(out)
    except OSError as errdir:
        log.warning('Output directory: {}'.format(errdir))

    if plotdata is None:
        plotdata = get_sqlite_data([var, 'SVID', 'timestamp'], db,
                                   svid=svid, tstart=tstart, tend=tend, log=log)

    allvardata = np.array([np.float(t[0]) for t in plotdata])
    sviddata = np.array([np.float(t[1]) for t in plotdata])
    svids = sorted(np.unique(sviddata))
    log.debug('Shape of allvardata {}'.format(allvardata.shape))
    # nanvar = np.array(['nan' in allvar for allvar in allvardata], dtype='bool')
    nanvar = np.isnan(allvardata)
    vardata = allvardata[~nanvar]
    sviddata = sviddata[~nanvar]
    log.debug('Shape of vardata {}'.format(vardata.shape))

    # log.debug('Shape of plotdata without "nan": {}'.format(plotdata[~nanvar].shape))
    timestampdata = np.array([np.int(t[2]) for t in plotdata])[~nanvar]
    log.debug('Where are stupid time values: {}, {}'\
            .format(timestampdata[timestampdata < 1.e6], np.argwhere(timestampdata < 1.e6)))

    timedata = np.array([dt.datetime.fromtimestamp(t[2]) for t in plotdata])[~nanvar]
    # timedata = timedata[~np.isnan(vardata)]

    colors = ['b', 'g', 'r', 'c', 'lime', 'k', 'orange']
    fig, ax = plt.subplots()
    for idx, sat_id in enumerate(svids):
        varsviddata = vardata[sviddata == sat_id]
        timesviddata = timedata[sviddata == sat_id]
        color = colors[idx % len(colors)]
        # print('Vardata for SVID {}: \n{} \n{}'.format(svid, varsviddata[0:20], timesviddata[0:20]))
        ax.plot(timesviddata, varsviddata, linestyle=':', color=color,
                label=('Sat {}'.format(sat_id)))
    ax.set_title('{} at {}, {}-{}'.format(var, loc,
                                          tstart.strftime('%Y%m%d, %H:%M:%S'),
                                          tend.strftime('%Y%m%d, %H:%M:%S')))
    ax.set_xlabel('Time')
    ax.set_ylabel('{}'.format(var))
    ax.legend(loc='best')
    fig.autofmt_xdate()

    tag = var
    if loc is not None:
        tag += '_{}'.format(loc)
    if svid is not None:
        if isinstance(svid, int):
            tag += '_{}'.format(str(svid).zfill(2))
        elif isinstance(svid, (tuple, list)):
            tag += '_ID{}-{}'.format(str(min(svid)).zfill(3), str(max(svid)).zfill(3))
    if tstart is not None and isinstance(tstart, dt.datetime):
        tag += '_{}-{}'.format(tstart.strftime('%Y%m%d%H%M%S'), tend.strftime('%Y%m%d%H%M%S'))

    figname = os.path.join(out, 'sql_time_{}.png'.format(tag))
    log.debug('Saving {}'.format(figname))
    fig.savefig(figname)

    return plotdata

def hist_plot_manual(var, db, svid=None, tstart=None, tend=None, plotdata=None,
              out='./', loc='SABA', log=logging):
    '''
        Make a histogram plot of a variable var in the ismr database db
    '''

    try:
        os.makedirs(out)
    except OSError as e:
        log.warning('Output directory: {}'.format(e))

    if plotdata is None:
        plotdata = get_sqlite_data([var, 'timestamp'], db, svid=svid,
                                   tstart=tstart, tend=tend, log=log)

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
        elif isinstance(svid, (tuple, list)):
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

def interpret_histogram_bins(config):
    '''
        See if in the configuration file the bins for the histogram have been
        specified, and if yes, how
    '''
    # the bins are configurable: if given [a, b] is amount of bins in x, y direction
    # or if a or b is array-like they represent the bins (edges) themselves
    if 'histbins' in config:
        histbins_conf = config['histbins']
        # check if it has a separate entry for bins in the x and y direction
        if len(histbins_conf) > 1:
            histbins_x, histbins_y = histbins_conf
            # check if it is a number or an attempt to define an array:
            for idx, histb in enumerate(histbins_conf): #(histbins_x, histbins_y):
                # print('Looking at histbins: {}'.format(histb))
                if idx > 1:
                    break # do not consider strangely formatted bins
                if not isinstance(histb, (list, tuple, np.ndarray)):
                    pass
                else:
                    if len(histb) == 2:
                        histbins_conf[idx] = np.arange(histb[0], histb[1])
                    elif len(histb) == 3:
                        histbins_conf[idx] = np.linspace(histb[0], histb[1], histb[2])
            histbins = histbins_conf
            # print('Were the histbins changed? {}'.format(histbins))
        else:
            histbins = [histbins_conf, histbins_conf]
    else:
        histbins = [150, 50]

    return histbins

def hist_plot(config, log=logging):
    '''
        Make a histogram plot of a variable var in the ismr database db
    '''

    try:
        os.makedirs(config['outputdir'])
    except OSError as e:
        log.warning('Output directory: {}'.format(e))

    var = config['plot_var']
    tstart = config['startdt'] # the interpreted starttime in datetime format
    tend = config['enddt'] # the interpreted endtime in datetime format
    loc = config['location']
    scint_db = os.path.join(config['ismrdb_path'], config['ismrdb_name'].format(loc))
    tabname = config['tabname'].format(loc)
    if 'satellites' in config:
        svid = config['satellites']
    else:
        svid = None

    if ('plotdata' not in config) or config['plotdata'] is None:
        query_start = time.time()
        plotdata = get_sqlite_data([var, 'timestamp'], scint_db, table=tabname,
                                   svid=svid,
                                   tstart=tstart, tend=tend, log=log)
        query_end = time.time()
        print('Query took {:.3f} seconds'.format(query_end - query_start))

    else:
        plotdata = config['plotdata']

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
        elif isinstance(svid, (tuple, list)):
            tag += '_ID{}-{}'.format(str(min(svid)).zfill(3),str(max(svid)).zfill(3))
    if tstart is not None and isinstance(tstart, dt.datetime):
        tag += '_{}-{}'.format(tstart.strftime('%Y%m%d%H%M%S'), tend.strftime('%Y%m%d%H%M%S'))

    # 1D histogram
    fig, ax = plt.subplots()
    _nrbins, _bins, _patches = ax.hist(vardata, bins=50, normed=1, facecolor='green', alpha=0.75)
    ax.set_xlabel('{} (binned)'.format(var))
    ax.set_title('Histogram of {} at {}'.format(var, loc))

    figname = os.path.join(config['outputdir'], 'sql_hist_{}_{}.png'.format(tag, loc))
    log.debug('Saving {}'.format(figname))
    fig.savefig(figname)

    # 2D histogram
    fig, ax = plt.subplots()

    # make sure the information passed on about the hostograms is properly implemented
    histbins = interpret_histogram_bins(config)

    ax.hist2d(timestampdata, vardata, bins=histbins, norm=LogNorm())
    ax.set_ylabel('{} (binned)'.format(var))
    if 'yrange' in config:
        ymin, ymax = config['yrange']
        ax.set_ylim(ymin, ymax)

    # draw a red line where the zero should be:
    ax.axhline(y=0, color='red', linestyle='-', alpha=0.4)

    xlocs = ax.get_xticks()
    ax.set_xticks(xlocs) # unnecessary?
    dtlabels = [dt.datetime.fromtimestamp(tlab) for tlab in xlocs]
    ax.set_xticklabels([dtlab.strftime('%Y-%m-%d') for dtlab in dtlabels])
    ax.set_xlabel('Time (binned)')

    # ax.hist2d(timedata, vardata, bins=[150, 50], norm=LogNorm())

    fig.autofmt_xdate()
    ax.set_title('Histogram as a function of time of {} at {}'.format(var, loc))

    figname = os.path.join(config['outputdir'], 'sql_hist2d_{}_{}.png'.format(tag, loc))
    log.debug('Saving {}'.format(figname))
    fig.savefig(figname)

    return plotdata

def hist_plot_hourly(config, log):
    '''
        make a histogram using the hour (minute?) of the day as bins
    '''

    ####
    try:
        os.makedirs(config['outputdir'])
    except OSError as e:
        log.warning('Output directory: {}'.format(e))

    var = config['plot_var']
    tstart = config['startdt'] # the interpreted starttime in datetime format
    tend = config['enddt'] # the interpreted endtime in datetime format
    loc = config['location']
    scint_db = os.path.join(config['ismrdb_path'], config['ismrdb_name'].format(loc))
    tabname = config['tabname'].format(loc)
    if 'satellites' in config:
        svid = config['satellites']
    else:
        svid = None

    if ('plotdata' not in config) or config['plotdata'] is None:
        query_start = time.time()
        plotdata = get_sqlite_data([var, 'timestamp'], scint_db, table=tabname,
                                   svid=svid,
                                   tstart=tstart, tend=tend, log=log)
        query_end = time.time()
        print('Query took {:.3f} seconds'.format(query_end - query_start))

    else:
        plotdata = config['plotdata']

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
        elif isinstance(svid, (tuple, list)):
            tag += '_ID{}-{}'.format(str(min(svid)).zfill(3),str(max(svid)).zfill(3))
    if tstart is not None and isinstance(tstart, dt.datetime):
        tag += '_{}-{}'.format(tstart.strftime('%Y%m%d%H%M%S'), tend.strftime('%Y%m%d%H%M%S'))

    ####

    houroftheday = np.array([t.hour for t in timedata])
    #####
    histbins = interpret_histogram_bins(config)

    fig, ax = plt.subplots()
    _histdist, _xedges, _yedges, _img = ax.hist2d(houroftheday, vardata, bins=histbins, norm=LogNorm())
    ax.set_ylabel('{} (binned)'.format(var))
    if 'yrange' in config:
        ymin, ymax = config['yrange']
        ax.set_ylim(ymin, ymax)
    ax.set_xlabel('Hour of the day (binned)')
    ax.set_title('Histogram as a function of hour of day of {} at {}'.format(var, loc))

    figname = os.path.join(config['outputdir'], 'sql_hist2d_hourly_{}_{}.png'.format(tag, loc))
    log.debug('Saving {}'.format(figname))
    fig.savefig(figname)

    return plotdata
    #####

def deg_to_lon(angle):
    '''
        Return angle between -180 and 180 degrees
    '''
    return (angle + 180.) % 360 - 180

def azel_to_latlon(result_df, point=topo['SABA'], id=None, height=300):
    '''
        Compute latitude longitude from azimuth and elevation angle

        First distance north and east is computed using height, then from a
        distance from a certain latlon-point lat and lon.
    '''
    relx, rely = azel_to_xy(result_df, id=id, h=height)
    lat_angle = point[0] + np.arctan2(rely, R_earth)
    lon_angle = point[1] + np.arctan2(relx, R_earth)
    result_df['lat'] = lat_angle
    result_df['lon'] = lon_angle

    return deg_to_lon(lon_angle), lat_angle, result_df

def azel_to_xy(df, id=None, h=HEIGHT):
    '''
        Compute x,y from azimuth and elevation in dataframe
        following:
        x = cos e * cos phi
        y = sin e * sin phi

    '''
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
    dbdata = get_sqlite_data(varlist, db, svid=svid, tstart=tstart, tend=tend,
                             table='sep_data', log=log)

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
    # print('Looping over satellites {}\n{}'.format(satellites, df['SVID']))
    for sat in satellites:
        if 1: # sat < 37:
            iddf = df[df.SVID == sat]
            plotdata = iddf[var].astype(float).values
            # x, y = azel_to_xy(iddf) # (df, id)
            x, y, _ = azel_to_latlon(iddf) # (df, id)
            # print('For sat {} we have {} - {} - {}'.format(sat, len(x), len(y), len(plotdata)))
            # print('Scale: {} - {}, min, max here {} - {}'.format(minval, maxval, np.nanmin(plotdata), np.nanmax(plotdata)))
            azel = ax.scatter(x, y, c=plotdata, vmin=minval, vmax=maxval,
                            cmap=plt.cm.get_cmap(cmap), linewidths=0, edgecolors=None,
                            # label='sat {}'.format(sat)
                            )
            print('Plotted sat {}'.format(sat))

    ax.set_xlabel(u'$x = \cos \ \epsilon \quad \sin \ \phi$')
    ax.set_ylabel(u'$y = \cos \ \epsilon \quad \cos \ \phi$')
    ax.set_title('Tracks: {}'.format(var))
    plt.colorbar(azel, ax=ax)
    outfig = os.path.join(out, 'azelplot_{}_multisat.png'.format(var))
    fig.savefig(outfig, dpi=400)
    plt.close(fig)
    print('Plotted {}'.format(outfig))

if __name__ == '__main__':

    ismrdb_path = './'
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

    # S4 = time_plot('sig1_S4', ismrdb, svid=tuple(range(1, 38)), tstart=startdate, tend=enddate, loc=loc, out='plots', log=logger)
    # TEC = time_plot('sig1_TEC', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, loc=loc, out='plots', log=logger)
    # hist_plot_manual('sig1_S4', ismrdb,  svid=tuple(range(1, 38)), tstart=startdate, tend=enddate, plotdata=S4, out='plots', loc=loc, log=logger)
    # hist_plot_manual('sig1_TEC', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, plotdata=TEC, out='plots', loc=loc, log=logger)
    # hist_plot_manual('sig1_S4', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, out='plots', loc=loc, log=logger)
    # hist_plot_manual('sig2_S4', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, out='plots', loc=loc, log=logger)
    # hist_plot_manual('sig1_phi01', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, out='plots', loc=loc, log=logger)
    # hist_plot_manual('sig2_phi01', ismrdb,  svid=tuple(range(38,62)), tstart=startdate, tend=enddate, out='plots', loc=loc, log=logger)

    plot_az_el_multisat('sig1_TEC', ismrdb, svid=satellites,
                        tstart=startdate, tend=enddate, loc=loc,
                        out='plots', cmap='hot_r', log=logger)
