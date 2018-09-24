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
    if os.path.isdir(data_location):
        for (dirname, dirs, files) in os.walk(data_location):
            print('Walkdir: dirname: {} dirs: {}, files {}'.format(dirname, dirs, files))
            for file in files:
                print('Reading dirname {} with file {}'.format(dirname, os.path.splitext(file)))
                if not os.path.splitext(file)[1] == '.ismr':
                    continue
                infile = os.path.join(dirname, file)
                if 'SABA' in dirname:
                    df = read_ismr.read_ismr(infile)
                    if df.shape[0] == 0: continue
                    read_ismr.write_to_sqlite(df, dbname='test_scint.db', loc='SABA')


if __name__ == '__main__':
    main()
