#/usr/bin/env python
'''
Script to read ISMR files from septentrio scintillator sensor
'''

import os
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
# import calendar

def weeksecondstoutc(gpsweek,gpsseconds,leapseconds):
    '''
        Convert GPS week to UTC time
        source: https://gist.github.com/jeremiahajohnson/eca97484db88bcf6b124
    '''

    gps_start = dt.datetime(1980,1,6,0,0,0)
    if isinstance(gpsweek, np.ndarray):
        date_array = np.zeros_like(gpsweek, dtype=dt.datetime)
        print('gpsweek: {} => {}'.format(gpsweek.shape, date_array.shape))
        for i, week in enumerate(gpsweek):
            date_array[i] = gps_start + dt.timedelta(days=week*7, seconds=gpsseconds[i])

        return date_array

    else:
        date_array = gps_start + dt.timedelta(days=gpsweek*7, seconds=gpsseconds)

    return date_array

def read_ismr(infile):
    '''
        Open and read ISMR files
        return panda dataframe
    '''

    names = ['weeknumber', 'timeofweek', 'SVID', 'fieldblockvalue', 'azimuth', 'elevation',
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

    print('Nr of names: # {}'.format(len(names)))

    with open(infile, 'r') as ismr:
        df = pd.read_csv(ismr, header=None, names=names, na_values='nan')

    df['t'] = weeksecondstoutc(df.weeknumber.values, df.timeofweek.values, 0)
    print(df.head())

    return df

def plot_df(df, id, var):
    '''
        Plot a variable from the dataframe
    '''
    print('shape of df: {}'.format(df.shape))

    plotdata = df[df.SVID == id][var].values
    xdata = df[df.SVID == id]['t']


    fig, ax = plt.subplots()
    ax.plot(xdata, plotdata)
    # ax.plot(plotdata)
    out = 'testplot_{}_sat{}.png'.format(var,str(id).zfill(2))
    print('shape of plotdata: {}'.format(plotdata.shape))
    fig.savefig(out)
    plt.close(fig)

def plot_df_multivar(df, id, varlist, name='multi'):
    '''
        Plot a list of variables from the dataframe
    '''

    iddf = df[df.SVID == id]
    # print('shape of df for sat {}: {}, head: {}, {}'.format(id, iddf.shape, iddf.head(), varlist))
    xdata = iddf.t
    ydata = iddf[varlist].astype('float') # necessary


    fig, ax = plt.subplots()
    ydata.plot(x=xdata, ax=ax)

    out = 'testplot_{}_sat{}.png'.format(name, str(id).zfill(2))
    fig.savefig(out)
    plt.close(fig)

def azel_to_xy(df, id=None):
    '''
        Compute x,y from azimuth and elevation in dataframe
    '''

    if id is not None:
        iddf = df[df.SVID == id]
    else:
        iddf = df

    azdata = 2. * np.pi * (iddf['azimuth']/360.)
    eldata = 2. * np.pi * (iddf['elevation']/360.)

    x = np.cos(eldata) * np.sin(azdata)
    y = np.cos(eldata) * np.cos(azdata)

    return x,y

def plot_az_el(df, id, var, cmap='jet'):
    '''
        Plot a variable as function of azimuth and elevation angle
        following:
        x = cos e * cos phi
        y = sin e * sin phi

    '''

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

def plot_az_el_multisat(df, var, cmap='jet'):
    '''
        Plot a variable as function of azimuth and elevation angle
        following:
        x = cos e * cos phi
        y = sin e * sin phi

    '''

    fig, ax = plt.subplots()

    satellites = df['SVID'].unique()
    for sat in satellites:
        if sat < 37:
            iddf = df[df.SVID == sat]
            plotdata = iddf[var].values
            x, y = azel_to_xy(iddf) # (df, id)
            print('For sat {} we have {} - {} - {}'.format(sat, len(x), len(y), len(plotdata)))
            azel = ax.scatter(x, y, c=plotdata, cmap=plt.cm.get_cmap(cmap), label='sat {}'.format(sat))

    ax.set_xlabel('x = cos [ Elevation] sin [ Azimuth ]')
    ax.set_ylabel('y = cos [ Elevation ] cos [ Azimuth ]')
    # plt.colorbar(azel, ax=ax)
    fig.savefig('azelplot_{}_multisat.png'.format(var))
    plt.close(fig)

def main():
    '''
        Main script
    '''

    # weeksecondstoutc(1811,164196.732,16) ## --> '2014-09-22 21:36:52'

    teclist = ['sig1_TEC_m45', 'sig1_TEC_m30', 'sig1_TEC_m15', 'sig1_TEC']
    dteclist = ['sig1_dTEC_m60_m45', 'sig1_dTEC_m45_m30', 'sig1_dTEC_m30_m15', 'sig1_dTEC_m15_0']
    philist = ['sig1_phi01', 'sig1_phi03', 'sig1_phi10', 'sig1_phi30', 'sig1_phi60']
    sig4_list = ['sig1_S4', 'sig2_S4', 'sig3_S4']

    ismrfile = 'KNMI283M.17_.ismr'
    print('ISMR file; {}, available: {}'.format(ismrfile, os.path.isfile(ismrfile)))

    data = read_ismr(ismrfile)

    plot_az_el(data, 1, 'sig1_S4')
    plot_az_el_multisat(data, 'sig1_S4', cmap='RdBu_r')
    plot_az_el_multisat(data, 'sig1_TEC', cmap='hot')

    satellites = data['SVID'].unique()
    for sat in satellites:
        if sat < 37:
            plot_df_multivar(data, sat, teclist, name='multitec')
            plot_df_multivar(data, sat, dteclist, name='deltatec')
            plot_df_multivar(data, sat, philist, name='mphase')
            plot_df_multivar(data, sat, sig4_list, name='sigN')


    plot_df(data, 1, 'sig1_S4')
    plot_df(data, 1, 'sig1_TEC')

if __name__ == '__main__':
    main()
