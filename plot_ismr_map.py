#! /usr/bin/env python
'''
    Module that holds the code for plotting ISMR GPS data on a map
'''

import os
import numpy as np
# import cartopy

import cartopy.crs as ccrs
import matplotlib.pyplot as plt

topo = {
    'SABA': (17.62048, -63.24323),
    'SEUT': (17.47140, -62.97570)
}

def saba_map(var='TEC', outdir = './'):
    '''
        Plot the surroundings of Saba on a map.
    '''

    sphere = ccrs.PlateCarree(globe=ccrs.Globe(datum='WGS84',
                                               ellipse='sphere'))


    # fig, ax = plt.subplots(projection=ccrs.PlateCarree())
    ax = plt.axes(projection=ccrs.PlateCarree())

    extent = ( -66., -59., 13., 21.)
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.coastlines(resolution='50m', color='black', linewidth=1)
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
              linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    plt.show()
    return

    figfile =  os.path.join(outdir, 'saba_{}.png'.format(var))
    fig.savefig(figfile, dpi=400)
    plt.close(fig)

if __name__ == '__main__':
    print('Run test')
    saba_map()