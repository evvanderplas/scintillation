#! /usr/bin/env python


import os
import time
import argparse
import numpy as np

# local imports
import lib.tools as tools
import lib.scintplots
import lib.constants as constants


def main(configfile):
    '''
        perform a number of steps:
        - logger
        - read configfile
        - create a baseline
        -- read baseline data
        -- determine histogram
        - see how other data relates
        -- read other data
        -- subtract baseline signal
    '''

    log = tools.init_logger()
    log.info('Read config')
    config = tools.read_yaml(configfile)
    dbconfig = tools.read_yaml('local.yaml')
    for key, val in dbconfig.items():
        if key not in config.keys():
            config[key] = val
    # make db filename
    loc = config['location']
    tabname = config['tabname'].format(loc)
    config['ismrdb'] = os.path.join(config['ismrdb_path'], config['ismrdb_name'].format(loc))

    config['startdt'] = tools.read_confdate(config['startdate'])
    config['enddt'] = tools.read_confdate(config['enddate'])
    config['clim']['startdt'] = tools.read_confdate(config['startdate'])
    config['clim']['enddt'] = tools.read_confdate(config['enddate'])
    svid = tools.interpret_svid(config['satellites'])

    log.debug('Read config: {}'.format(config))

    # Here, take the header, the S4 and TEC and the timestamp:
    req_list = constants.HEADER_NAMES + ['sig1_S4', 'sig1_TEC', 'timestamp']
    query_start = time.time()
    rawdata = tools.get_sqlite_data(req_list, config['ismrdb'], table=tabname,
                               svid=svid, tstart=config['clim']['startdt'],
                               tend=config['clim']['enddt'],
                               restrict_crit=None, log=log)
    query_end = time.time()
    log.debug('Query took {:.3f} seconds'.format(query_end - query_start))
    log.debug('Got {}, {}'.format(len(rawdata), np.asarray(rawdata).shape, rawdata))
    nonandata = tools.nice_data(rawdata, req_list, log=log)
    fulldata = tools.add_timedata(nonandata)
    log.debug('first 20 times {}'.format(fulldata['time'][:20]))
    log.debug('first 20 hours {} ({})'.format(fulldata['timeofday'][:20], [t.hour for t in fulldata['time'][:20]]))
    # sys.exit(0)

    log.info('Create a mean signal and its excursions')
    pdict = {
        'satellites': svid, # which satellites
        'location': loc,
        'startdt': config['startdt'],
        'enddt': config['enddt'],
        'tag': 'first_test_hist',
    }

    # pdict['histbins'] =
    lib.scintplots.hist2D_plot(fulldata['timestamp'], 'time', fulldata['sig1_TEC'], 'TEC',
                               300, 150, xrange=None, yrange=None,
                               tagdict=pdict, outdir= './plots/clim', log=log)

    # houroftheday = np.array([t.hour for t in fulldata['time']])
    # secondoftheday = np.array([tools.second_of_day(t) for t in fulldata['time']])
    # print(fulldata['time'])
    # print(secondoftheday)
    lib.scintplots.hist2D_plot(fulldata['timeofday'], 'hour_of_day', fulldata['sig1_TEC'], 'TEC',
                               24, 200, xrange=None, yrange=None,
                               tagdict=pdict, outdir= './plots/clim', log=log)
    lib.scintplots.hist2D_plot(fulldata['secondofday'], 'second_of_day', fulldata['sig1_TEC'], 'TEC',
                               96, 200, xrange=None, yrange=None,
                               tagdict=pdict, outdir= './plots/clim', log=log)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="the configuration file on what to plot",
                        default=None)
    args = parser.parse_args()

    main(args.infile)
