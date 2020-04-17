#! /usr/bin/env python

'''
    Make a (simple) class to plot scintillation measurement plots
'''

import os
import time
import numpy as np

from lib.tools import get_sqlite_data, init_logger

class ISMRplot():
    '''
        Class to plot ismr data, with functionality to get data from the database,
        interpret the configuration etc
    '''
    def __init__(self, config, log):
        '''
            Initialise
        '''
        self.config = config
        self.log = log

    def _prepare_data(self):
        '''
            Look in config which data to retrieve from the database
            and put in a numpy array.
        '''
        tstart = self.config['startdt'] # the interpreted starttime in datetime format
        tend = self.config['enddt'] # the interpreted endtime in datetime format
        loc = self.config['location']
        scint_db = os.path.join(config['ismrdb_path'], config['ismrdb_name'].format(loc))
        tabname = self.config['tabname'].format(loc)
        if 'satellites' in config:
            svid = self.config['satellites']
        else:
            svid = None

        if ('plotdata' not in self.config) or self.config['plotdata'] is None:
            query_start = time.time()
            var = self.config['plot_var']
            if istype(var, (list, tuple)):
                nrvars = len(var)
                req_list = list(vars) + ['timestamp']
            else:
                req_list = [var, 'timestamp']
            plotdata = get_sqlite_data(req_list, scint_db, table=tabname,
                                       svid=svid,
                                       tstart=tstart, tend=tend, log=log)
            query_end = time.time()
            print('Query took {:.3f} seconds'.format(query_end - query_start))

        else:
            plotdata = config['plotdata']

        if nrvars == 1:
            allvardata = np.array([np.float(t[0]) for t in plotdata])
            nanvar = np.isnan(allvardata)
            vardata = allvardata[~nanvar]
            log.debug('Size vardata: {}'.format(vardata.shape))
        else:
            vardata = {}
            for idx_var, multivar in enumerate(var):
                allvardata = np.array([np.float(t[idx_var]) for t in plotdata])
                nanvar = np.isnan(allvardata)
                vardata[multivar] = allvardata[~nanvar]
                log.debug('Size vardata {}: {}'.format(multivar, vardata[multivar].shape))

        # gamble that the not available data is the same for all vars in the list...
        timestampdata = np.array([t[-1] for t in plotdata])[~nanvar]
        timedata = np.array([dt.datetime.fromtimestamp(t[-1]) for t in plotdata])[~nanvar]

        return timedata, vardata

    def scatterplot(self):
        '''
            make a scatterplot
        '''

        timedata, vardata = self._prepare_data()
        vars = self.config['plot_var']

if __name__ == '__main__':

    print('Do test plot')
    test_yaml_file = ''
    conf = read_yaml(test_yaml_file)
    log = init_logger()

    test_inst = ISMRplot(conf, log)
