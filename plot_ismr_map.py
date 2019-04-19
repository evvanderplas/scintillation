#! /usr/bin/env python
'''
    Module that holds the code for plotting ISMR GPS data on a map
'''

import os
import numpy as np
import pandas as pd
# import cartopy

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from plot_ismr import get_sqlite_data, azel_to_latlon

topo = {
    'SABA': (17.62048, -63.24323),
    'SEUT': (17.47140, -62.97570)
}

def prepare_map_data(var, db, svid=12, tstart=None, tend=None, loc='SABA', out='./', cmap='jet', log=None):
    '''
        Get data to plot on a map
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

    _, _, df_ll = azel_to_latlon(df, point=topo[loc])
    plot_data_on_map(var, df_ll, topo[loc], outdir=out, cmap=cmap)

def plot_data_on_map(var, df, midpoint, outdir='./', cmap='jet'):
    '''
        make a map around a midpoint and plot data on it
    '''

    sphere = ccrs.PlateCarree(globe=ccrs.Globe(datum='WGS84',
                                               ellipse='sphere'))


    # fig, ax = plt.subplots(projection=ccrs.PlateCarree())
    fig = plt.figure()
    ax = plt.axes(projection=ccrs.PlateCarree())

    lon0, lat0 = midpoint
    # extent = ( lon0 -5., lon0 + 5., lat0 - 5., lat0 + 5.)
    extent = ( lat0 -5., lat0 + 5., lon0 - 5., lon0 + 5.)
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.coastlines(resolution='50m', color='black', linewidth=1)
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
              linewidth=0.5, color='gray', alpha=0.5, linestyle='--')

    minval = np.nanpercentile(df[var].astype('float'), 10.)
    maxval = np.nanpercentile(df[var].astype('float'), 95.)
    satellites = df['SVID'].unique()
    # print('Looping over satellites {}\n{}'.format(satellites, df['SVID']))
    for sat in satellites:
        if 1: # sat < 37:
            iddf = df[df.SVID == sat]
            plotdata = iddf[var].astype(float).values
            # x, y = azel_to_xy(iddf) # (df, id)
            lats = iddf['lat']
            lons = iddf['lon']
            # x, y = azel_to_latlon(iddf) # (df, id)
            # print('For sat {} we have {} - {} - {}'.format(sat, len(x), len(y), len(plotdata)))
            # print('Scale: {} - {}, min, max here {} - {}'.format(minval, maxval, np.nanmin(plotdata), np.nanmax(plotdata)))
            azel = ax.scatter(lons, lats, c=plotdata, vmin=minval, vmax=maxval,
                            cmap=plt.cm.get_cmap(cmap), linewidths=0, edgecolors=None,
                            # label='sat {}'.format(sat)
                            )
            # azel = ax.plot(lons, lats, 'b', marker='o')
            # for i, pt in enumerate(plotdata):
            #     ax.plot(lats[i], lons[i], 'b', marker='o')

    ax.set_title('Tracks: {}'.format(var))
    plt.colorbar(azel, ax=ax)
    outfig = os.path.join(outdir, 'azel_map_{}_multisat.png'.format(var))
    fig.savefig(outfig, dpi=400)
    plt.close(fig)
    print('Plotted {}'.format(outfig))

def saba_map(var='TEC', outdir = './'):
    '''
        Plot the surroundings of Saba on a map.
    '''

    sphere = ccrs.PlateCarree(globe=ccrs.Globe(datum='WGS84',
                                               ellipse='sphere'))


    # fig, ax = plt.subplots(projection=ccrs.PlateCarree())
    fig = plt.figure()
    ax = plt.axes(projection=ccrs.PlateCarree())

    extent = ( -66., -59., 13., 21.)
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.coastlines(resolution='50m', color='black', linewidth=1)
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
              linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    # plt.show()
    # return

    figfile =  os.path.join(outdir, 'saba_{}.png'.format(var))
    fig.savefig(figfile, dpi=400)
    plt.close(fig)

if __name__ == '__main__':
    print('Run test')
    saba_map()
