#! /usr/bin/env python

import os
import numpy
import datetime as dt
import matplotlib.pyplot as plt
import logging

import tools

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
    if len(self.config['satellites']) < 4:
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
    if tagdict == {}:
        tagdict = TAGDEF

    fig, ax = plt.subplots()

    # make sure the information passed on about the histograms is properly implemented
    histbins = [xbins, ybins]
    houroftheday = np.array([t.hour for t in self.timedata])
    ax.hist2d(xdata, ydata, bins=histbins, norm=LogNorm())
    ax.set_ylabel('{} (binned)'.format(yname))
    if 'yrange' in self.config:
        ymin, ymax = self.config['yrange']
        ax.set_ylim(ymin, ymax)
    else:
        ax.set_ylim(np.nanmin([0., np.nanpercentile(self.vardata[var], 2.)]),
                    np.nanmax([1.3 * np.nanpercentile(self.vardata[var], 98.)]) )

    # draw a red line where the zero should be:
    ax.axhline(y=0, color='red', linestyle='-', alpha=0.4)

    ax.set_xlabel('{} (binned)'.format(xname))
    fig.autofmt_xdate()
    ax.set_title('Histogram as a function of {} for {} at {}'.format(xname, yname, location))

    plotfile = os.path.join(self.config['outputdir'],
                            'hist2D_{}_{}_{}_{}-{}_sat_{}_{}.png'.format(xname, yname,
                                    tagdict['location'],
                                    tagdict['startdt'].strftime('%Y%m%d%H%M'),
                                    tagdict['enddt'].strftime('%Y%m%d%H%M'),
                                    tools._sats_for_figname(), tagdict['tag']))
    log.debug('Saving {}'.format(plotfile))
    fig.savefig(plotfile)
    plt.close(fig)

    return
