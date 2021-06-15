#! /usr/bin/env python

import os
import numpy as np
import datetime as dt
import logging

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

from lib import tools

# make a dict that contains necessary tags to make the plotting work if none are given
TAGDEF = {
    'satellites': 'unknown', # which satellites
    'location': 'also_unknown',
    'startdt': dt.datetime.now()- dt.timedelta(seconds=300),
    'enddt': dt.datetime.now(),
    'tag': 'sometag',
}

def checkdt(somedt):
    return

def scatterplot(xdata, ydata, xname, yname, colorby=None, colorname=None, cmap='hsv',
    tagdict={}, outdir = './', log=logging):
    '''
        make a scatterplot
    '''

    #xdata, ydata, xname, yname, colorby, colors = self._prepare_plotdata(xvar, yvar, colorby)
    if tagdict == {}:
        tagdict = TAGDEF

    fig, ax = plt.subplots()
    ax.axhline(y=0, color='r', alpha=0.4)
    if not colorby:
        ax.scatter(xdata, ydata, c=colors, edgecolors='none')
    else:
        ax.scatter(xdata, ydata, c=colorby, cmap=cmap, alpha=0.5, edgecolors='none')
    ax.set_xlabel(xname)
    ax.set_ylabel(yname)
    title = '{} vs {}'.format(yname, xname)
    if 'satellites' in tagdict and len(tagdict['satellites']) < 4:
        title += ' for satellites {}'.format(tagdict['satellites'])
    title += ' from {} - {}'.format(tagdict['startdt'].strftime('%Y-%m-%d'),
                                    tagdict['enddt'].strftime('%Y-%m-%d'))
    ax.set_title(title)

    plotfile = os.path.join(outdir,
                        'scatter_{}-{}_{}_{}-{}_sat_{}_{}.png'.format(xname, yname,
                                tagdict['location'],
                                tagdict['startdt'].strftime('%Y%m%d%H%M'),
                                tagdict['enddt'].strftime('%Y%m%d%H%M'),
                                tools._sats_for_figname(), tagdict['tag']))
    log.info('Plotted {}'.format(plotfile))
    fig.savefig(plotfile)
    plt.close(fig)

def hist2D_plot(xdata, xname, ydata, yname, xbins, ybins, xrange=None, yrange=None,
                tagdict={}, outdir= './', log=logging):
    '''

    '''
    x_is_time = False
    if tagdict == {}:
        tagdict = TAGDEF

    fig, ax = plt.subplots()

    # make sure the information passed on about the histograms is properly implemented
    histbins = [xbins, ybins]
    # houroftheday = np.array([t.hour for t in self.timedata])
    if 'time' in xname.lower(): #isinstance(xdata[0], dt.datetime):
        x_is_time = True

    hdata, _xedges, _yedges, _histhandle = ax.hist2d(xdata, ydata, bins=histbins, norm=LogNorm())
    ax.set_ylabel('{} (binned)'.format(yname))
    if yrange is not None:
        ymin, ymax = yrange
        ax.set_ylim(ymin, ymax)
    else:
        ax.set_ylim(np.nanmin([0., 1.8 * np.nanpercentile(ydata, 2.)]),
                    np.nanmax([1.8 * np.nanpercentile(ydata, 98.)]) )

    # draw a red line where the zero should be:
    ax.axhline(y=0, color='red', linestyle='-', alpha=0.4)
    ax.set_xlabel('{} (binned)'.format(xname))

    if x_is_time:
        xlocs = ax.get_xticks()
        ax.set_xticks(xlocs) # unnecessary?
        dtlabels = [dt.datetime.fromtimestamp(tlab) for tlab in xlocs]
        ax.set_xticklabels([dtlab.strftime('%Y-%m-%d') for dtlab in dtlabels])
        ax.set_xlabel('Time (binned)')

        fig.autofmt_xdate()

    ax.set_title('Histogram as a function of {} for {} at {}'.format(xname, yname, tagdict['location']))

    plotfile = os.path.join(outdir,
                            'hist2D_{}_{}_{}_{}-{}_sat_{}_{}.png'.format(xname, yname,
                                    tagdict['location'],
                                    tagdict['startdt'].strftime('%Y%m%d%H%M'),
                                    tagdict['enddt'].strftime('%Y%m%d%H%M'),
                                    tools._sats_for_figname(tagdict['satellites']), tagdict['tag']))
    log.debug('Saving {}'.format(plotfile))
    fig.savefig(plotfile)
    plt.close(fig)

    return hdata, histbins
