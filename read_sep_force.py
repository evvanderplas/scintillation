#! /usr/bin/env python
'''
    Script that is meant to repair the reading, by trying to force to
    read a number of files and not quit when it encounters ~resistance~
    a value that is already in the database.
'''
import os, sys
import datetime as dt
import argparse

# use read functionality:
import read_ismr
from lib.tools import init_logger, read_yaml, read_confdate

data_location = '/data/storage/trop/users/plas/SW/IONO'
scint_locations = ['SABA','SEUT']
db_location = '/data/storage/trop/users/plas/SW/'

def ingest_dir(readdir, instrument_location, target_db):
    '''
    '''

    exclude = set(['CAL'])
    for (dirname, dirs, files) in os.walk(readdir):
        dirs[:] = [d for d in dirs if d not in exclude]
        for file in sorted(files, reverse=True):
            print('Reading dirname {} with file {}'.format(dirname, os.path.splitext(file)))
            if not os.path.splitext(file)[1] == '.ismr':
                continue
            infile = os.path.join(dirname, file)
            if instrument_location in dirname:
                ismr_dataframe = read_ismr.read_reduced_ismr(infile)
                if ismr_dataframe.shape[0] == 0:
                    continue

                written = read_ismr.write_to_reduced_sqlite(ismr_dataframe, dbname=target_db,
                                                            loc=instrument_location)


def read_forced(indir, log, loc='all'):
    '''
        Read the actual data from the ISMR
    '''

    if loc == 'all':
        locations = scint_locations
    else:
        locations = loc

    for instrument_location in locations:
        data_dir = os.path.join(data_location, instrument_location)
        print('Walking directory tree {}'.format(data_dir))

        # # full database, not used
        # ismrdb = os.path.join(db_location, 'scint_new_{}.db'.format(instrument_location))
        # print('Writing to {}'.format(ismrdb))

        # NB TEMP!
        # # reduced database
        # ismr_red_db = os.path.join(db_location, 'scint_reduced_{}.db'.format(instrument_location))
        # print('Writing normal to reduced {}'.format(ismr_red_db))
        #
        # ismr_cal_db = os.path.join(db_location, 'scint_reduced_{}.db'.format(instrument_location))
        # print('Writing cal to reduced {}'.format(ismr_cal_db))

        # TODO: reduced database TEST!
        ismr_red_db = os.path.join(db_location, 'scint_reduced_{}_test.db'.format(instrument_location))
        print('Writing normal to reduced {}'.format(ismr_red_db))

        ismr_cal_db = os.path.join(db_location, 'scint_reduced_{}_test.db'.format(instrument_location))
        print('Writing cal to reduced {}'.format(ismr_cal_db))
        #  end todo

        readdir = os.path.join(data_location, instrument_location, indir)
        ingest_dir(readdir, instrument_location, ismr_red_db)

        readdir = os.path.join(data_location, instrument_location, 'CAL', indir)
        ingest_dir(readdir, instrument_location, ismr_cal_db)


def find_directory_for_date(indate, log):
    '''
        The ISMR files are located in directories that are named
        by year and day-of-year number
    '''
    try:
        indt = dt.datetime.strptime(str(indate), '%Y%m%d')
        doy = str(indt.timetuple().tm_yday)
        yy = str(indt.year)[-2:]
    except ValueError as verr:
        log.error('Does not match YYYYMMDD format: {}'.format(indate))
        return None
    log.debug('Date in YYYYMMDD {}, datetime: {}, dir: {} '.format(indate, indt, yy+doy))
    return '{}{}'.format(yy,doy)

def main():
    '''
        main section, read date from command line, and
        read all files for this date
    '''
    logger = init_logger()
    logger.info('Reading data')

    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="date for which reading into the db is forced, YYYYMMDD")
    # parser.add_argument("location", help="location of the instrument")
    parser.add_argument("-l", "--location", type=str, choices=['SABA', 'SEUT', 'all'],
                        default='all', help="optional: give location for the forced ingestion")

    args = parser.parse_args()
    logger.debug('Read date {}'.format(args.date))
    readdir = find_directory_for_date(args.date, logger)
    read_forced(readdir, logger, loc=args.location)

if __name__ == '__main__':
    main()
