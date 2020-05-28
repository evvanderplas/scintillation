#! /usr/bin/env python

'''
    Make a (simple) class to plot scintillation measurement plots
'''

import os, sys
import time
import argparse

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt

from lib.tools import get_sqlite_data, init_logger, read_yaml, read_confdate
import lib.constants as constants

class ISMRplot():
    '''
        Class to plot ismr data, with functionality to get data from the database,
        interpret the configuration etc
    '''
    def __init__(self, configfile, log, tag):
        '''
            Initialise
        '''
        self.config = {}
        self.log = log
        self.tag = tag
        self._complete_config(configfile)

        self.vardata = None
        self.timedata = np.array([], dtype=np.float)
        self.timeofday = np.array([], dtype=np.float)

        if self.config['plot_type'] == 'scatter':
            self.scatterplot(colorby='timeofday')

            var1 = self.config['plot_var'][0]
            self.tag = 'extra_tod_{}'.format(var1)
            self.log.debug('Extra: xvar timeofday, yvar = {}'.format(var1))
            self.scatterplot(xvar='timeofday', yvar=var1)

            var2 = self.config['plot_var'][1]
            self.tag = 'extra_tod_{}'.format(var2)
            self.log.debug('Extra: xvar timeofday, yvar = {}'.format(var2))
            self.scatterplot(xvar='timeofday', yvar=var2)

    def _complete_config(self, configfile):
        '''
            Read some complementary stuff form a local.yaml file
            such as which database to use etc: not something you want for each plot
        '''

        # read where the database is
        dbconfig = read_yaml('local.yaml')

        # read what plot(s) to make
        self.config = read_yaml(configfile)
        self.ismrdb = os.path.join(dbconfig['ismrdb_path'], dbconfig['ismrdb_name'].format(self.config['location']))
        self.log.debug('Reading from database {}'.format(self.ismrdb))

        # make one dict with the settings to convey to plotting routine
        self.config['startdt'] = read_confdate(self.config['startdate'])
        self.config['enddt'] = read_confdate(self.config['enddate'])
        for item, setting in dbconfig.items():
            self.config[item] = setting

    def _prepare_data(self):
        '''
            Look in config which data to retrieve from the database
            and put in a numpy array.
        '''
        total_vars = constants.HEADER_NAMES + constants.NAMES

        tstart = self.config['startdt'] # the interpreted starttime in datetime format
        tend = self.config['enddt'] # the interpreted endtime in datetime format
        loc = self.config['location']
        # scint_db = os.path.join(self.config['ismrdb_path'], self.config['ismrdb_name'].format(loc))
        tabname = self.config['tabname'].format(loc)
        if 'satellites' in self.config:
            svid = self.config['satellites']
        else:
            svid = None

        if ('plotdata' not in self.config) or self.config['plotdata'] is None:
            query_start = time.time()
            vars = self.config['plot_var']

            if isinstance(vars, (list, tuple)):
                nrvars = len(vars)
                req_list = list(vars) + ['timestamp']
            else:
                req_list = [vars, 'timestamp']

            # if the variable by which you want to color the data is not
            # already in the list, add it
            if 'colorby' in self.config and self.config['colorby'] in total_vars \
                    and self.config['colorby'] not in vars:

                # we use the fact that time comes last:
                req_list.insert(-1, self.config['colorby'])
                vars.insert(-1, self.config['colorby'])
                nrvars += 1

            plotdata = get_sqlite_data(req_list, self.ismrdb, table=tabname,
                                       svid=svid,
                                       tstart=tstart, tend=tend, log=log)
            query_end = time.time()
            self.log.debug('Query took {:.3f} seconds'.format(query_end - query_start))

        else:
            plotdata = config['plotdata']

        if nrvars == 1:
            allvardata = np.array([np.float(t[0]) for t in plotdata])
            nanvar = np.isnan(allvardata)
            vardata = allvardata[~nanvar]
            log.debug('Size vardata: {}'.format(vardata.shape))
        else:
            vardata = {}
            timestampdata = np.array([t[-1] for t in plotdata])

            # make two rounds:
            # first to get all the nan-values, second to get the data:
            nanvar = np.zeros_like(timestampdata, dtype=bool)
            for idx_var, multivar in enumerate(vars):
                allvardata = np.array([np.float(t[idx_var]) for t in plotdata])
                nanvar = np.logical_and(np.isnan(allvardata), nanvar)

            # remember where the NaN's are:
            self.nanvar = nanvar

            # second round:
            # self.log.debug('Loop over vars: {}, but index over req_list: {}'.format(vars, req_list))
            for idx_var, multivar in enumerate(req_list):

                allvardata = np.array([np.float(t[idx_var]) for t in plotdata])
                vardata[multivar] = allvardata[~nanvar]
                log.debug('Size vardata {}: {}'.format(multivar, vardata[multivar].shape))

        # gamble that the not available data is the same for all vars in the list...
        timestampdata = np.array([t[-1] for t in plotdata])[~nanvar]
        self.timedata = np.array([dt.datetime.fromtimestamp(t[-1]) for t in plotdata])[~nanvar]
        self._add_hour_of_day()
        vardata['timeofday'] = self.timeofday

        # for a next plot(?)
        self.vardata = vardata

        return vardata

    def _add_hour_of_day(self):
        '''
            Get the time-of-day for each measurement
        '''
        tod = np.zeros_like(self.timedata)
        for mt_idx, mtime in enumerate(self.timedata):
            tod[mt_idx] = (mtime - dt.datetime(mtime.year, mtime.month, mtime.day, 0,0,0,0)).seconds/3600.
        self.timeofday = tod[~self.nanvar]

    def _sats_for_figname(self):
        '''
            Decide how to indicate for which sats the figure was made
        '''
        sats = self.config['satellites']
        if len(list(sats)) == 1:
            return str(list(sats)[0])
        elif len(list(sats)) < 4:
            return '_'.join([str(s) for s in list(sats)])
        else:
            smin, smax = np.min(list(sats)), np.max(list(sats))
            return '{}-{}'.format(smin, smax)

    def scatterplot(self, xvar=None, yvar=None, colorby=None):
        '''
            make a scatterplot
        '''

        if self.vardata is None:
            vardata = self._prepare_data()

        if 'colorby' in self.config:
            colorby = self.config['colorby']

        vars = self.config['plot_var']
        self.log.debug('First we have vars {}'.format(vars))
        if 'colorby' in self.config and self.config['colorby'] in vars:
            vars.remove(self.config['colorby'])
        if (len(vars) < 2) or (len(vars) > 2):
            self.log.error('Specify which variables to plot: {}'.format(vars))
        # self.log.debug('Now we have vars {}'.format(vars))
        # self.log.debug('Data from vars (dict keys) {}'.format(self.vardata.keys()))

        if xvar is None:
            xname = vars[0]
            # self.log.debug('X data: {}'.format(xname))
            xdata = self.vardata[xname]
        elif xvar == 'timeofday':
            xdata = self.timeofday
            xname = 'timeofday'
        if yvar is None:
            yname = vars[1]
            # self.log.debug('X data: {}'.format(yname))
            ydata = self.vardata[yname]
        else:
            try:
                ydata = self.vardata[yvar]
                yname = yvar
            except KeyError as kerr:
                self.log.error('Not an available variable: {} in {}'.format(yvar, self.vardata.keys()))
                sys.exit(0)
        if colorby is None:
            color = 'b'
        else:
            try:
                colors = self.vardata[colorby]
            except KeyError as kerr:
                self.log.error('Not an available variable: {}'.format(kerr))
                self.log.error('You want: {}, available: {}'.format(colorby, self.vardata.keys()))
                sys.exit(0)

        fig, ax = plt.subplots()
        ax.axhline(y=0, color='r', alpha=0.4)
        if not colorby:
            ax.scatter(xdata, ydata, c=color, edgecolors='none')
        else:
            ax.scatter(xdata, ydata, c=colors, cmap='hsv', alpha=0.7, edgecolors='none')
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        title = '{} vs {}'.format(yname, xname)
        if len(self.config['satellites']) < 4:
            title += ' for satellites {}'.format(self.config['satellites'])
        title += ' from {} - {}'.format(self.config['startdt'].strftime('%Y-%m-%d'),
                                        self.config['enddt'].strftime('%Y-%m-%d'))
        ax.set_title(title)


        plotfile = os.path.join(self.config['outputdir'],
                            'scatter_{}-{}_{}-{}_sat_{}_{}.png'.format(xname, yname,
                                    self.timedata[0].strftime('%Y%m%d%H%M'),
                                    self.timedata[-1].strftime('%Y%m%d%H%M'),
                                    self._sats_for_figname(), self.tag))
        self.log.info('Plotted {}'.format(plotfile))
        fig.savefig(plotfile)
        plt.close(fig)


if __name__ == '__main__':

    tag = 'test'
    print('Do test plot: tag="{}"'.format(tag))
    test_yaml_file = 'test_simple_TEC_scatter.yaml'
    log = init_logger()

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="the configuration file on what to plot",
                        default=test_yaml_file)
    args = parser.parse_args()
    log.debug('Plotting from {}'.format(args.infile))

    test_inst = ISMRplot(args.infile, log, tag)
