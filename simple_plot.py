#! /usr/bin/env python

'''
    Make a (simple) class to plot scintillation measurement plots
'''

import os
import time
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt

from lib.tools import get_sqlite_data, init_logger, read_yaml, read_confdate

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
            self.tag = 'extra_tod_TEC'
            self.scatterplot(xvar='timeofday', yvar='sig1_TEC')
            self.tag = 'extra_tod_S4'
            self.scatterplot(xvar='timeofday', yvar='sig1_S4')

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

            # remeber where the NaN's are:
            self.nanvar = nanvar

            # second round:
            for idx_var, multivar in enumerate(vars):
                allvardata = np.array([np.float(t[idx_var]) for t in plotdata])
                # nanvar = np.logical_and(np.isnan(allvardata), nan_before)
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
            Get the time-of-day for each measurment
        '''
        tod = np.zeros_like(self.timedata)
        for mt_idx, mtime in enumerate(self.timedata):
            tod[mt_idx] = (mtime - dt.datetime(mtime.year, mtime.month, mtime.day, 0,0,0,0)).seconds/3600.
        self.timeofday = tod[~self.nanvar]

    def scatterplot(self, xvar=None, yvar=None, colorby=None):
        '''
            make a scatterplot
        '''

        if self.vardata is None:
            vardata = self._prepare_data()

        vars = self.config['plot_var']
        if len(vars) > 2:
            self.log.error('Specify which variables to plot: {}'.format(vars))

        if xvar is None:
            xname = vars[0]
            xdata = self.vardata[xname]
        elif xvar == 'timeofday':
            xdata = self.timeofday
            xname = 'timeofday'
        if yvar is None:
            yname = vars[1]
            ydata = self.vardata[yname]
        else:
            try:
                ydata = self.vardata[yvar]
                yname = yvar
            except KeyError as kerr:
                print('Not an available variable: {}'.format(kerr))
                sys.exit(0)
        if colorby is None:
            color = 'b'
        else:
            try:
                colors = self.vardata[colorby]
            except KeyError:
                print('Not an available variable: {}'.format(kerr))
                sys.exit(0)

        fig, ax = plt.subplots()
        ax.axhline(y=0, color='r', alpha=0.4)
        if not colorby:
            ax.scatter(xdata, ydata, c=color)
        else:
            ax.scatter(xdata, ydata, c=colors, cmap='hsv')
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        title = '{} vs {}'.format(yname, xname)
        if len(self.config['satellites']) < 4:
            title += ' for satellites {}'.format(self.config['satellites'])
        title += ' from {} - {}'.format(self.config['startdt'].strftime('%Y-%m-%d'),
                                        self.config['enddt'].strftime('%Y-%m-%d'))
        ax.set_title(title)


        plotfile = os.path.join(self.config['outputdir'],
                            'scatter_{}-{}_{}-{}_{}.png'.format(xname, yname,
                                    self.timedata[0].strftime('%Y%m%d%H%M'),
                                    self.timedata[-1].strftime('%Y%m%d%H%M'), self.tag))
        self.log.info('Plotted {}'.format(plotfile))
        fig.savefig(plotfile)
        plt.close(fig)


if __name__ == '__main__':

    tag = 'test'
    print('Do test plot: tag="{}"'.format(tag))
    test_yaml_file = 'test_simple_TEC_scatter.yaml'
    log = init_logger()

    test_inst = ISMRplot(test_yaml_file, log, tag)
