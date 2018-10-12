#! /usr/bin/env python
'''
  Script that reads csv files and puts data in database
'''

import read_ismr
import os

def main():
    '''
        Take the location of the files and parse them
    '''
    # data_location = '/Users/plas/Downloads/IONO'
    data_location = '/data/storage/trop/users/plas/SW/IONO'
    scint_locations = ['SABA','SEUT']

    instrument_location = 'SEUT'
    db_location = '/data/storage/trop/users/plas/SW/'
    ismrdb = os.path.join(db_location, 'test_scint_new_{}.db'.format(instrument_location))

    if os.path.isdir(data_location):
        for (dirname, dirs, files) in os.walk(data_location):
            print('Walkdir: dirname: {} dirs: {}, files {}'.format(dirname, dirs, files))
            for file in files:
                print('Reading dirname {} with file {}'.format(dirname, os.path.splitext(file)))
                if not os.path.splitext(file)[1] == '.ismr':
                    continue
                infile = os.path.join(dirname, file)
                if instrument_location in dirname:
                    df = read_ismr.read_ismr(infile)
                    if df.shape[0] == 0: continue
                    read_ismr.write_to_sqlite(df, dbname=ismrdb, loc=instrument_location)


if __name__ == '__main__':
    main()
