#! /usr/bin/env python

import os
import numpy
import matplotlib.pyplot as plt
import logging

import tools

# make a dict that contains necessary tags to make the plotting work if none are given
TAGDEF = {
    'satellites': 'unknown', # which satellites
    'location': 'also_unknown'
    'startdt': dt.datetime.now()- dt.timedelta(seconds=300),
    'enddt': dt.datetime.now(),
    'tag': 'sometag'
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
