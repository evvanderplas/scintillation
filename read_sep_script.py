#! /usr/bin/env python
'''
  Script that reads csv files and puts data in database
'''

import os, sys
import time

# use read functionality:
import read_ismr

def main():
    '''
        Take the location of the files and parse them
    '''
    # data_location = '/Users/plas/Downloads/IONO'
    data_location = '/data/storage/trop/users/plas/SW/IONO'
    scint_locations = ['SABA','SEUT']
    db_location = '/data/storage/trop/users/plas/SW/'
    # db_location = '/data/WNhome/plas/septentrio/'

    for location in scint_locations:
        print('One day: loop over location: {}'.format(location))

    # instrument_location = 'SABA'
    # instrument_location = 'SEUT'
    for instrument_location in scint_locations:
        data_dir = os.path.join(data_location, instrument_location)
        print('Walking directory tree {}'.format(data_dir))
        ismrdb = os.path.join(db_location, 'scint_new_{}.db'.format(instrument_location))
        print('Writing to {}'.format(ismrdb))

        ismr_red_db = os.path.join(db_location, 'scint_reduced_{}.db'.format(instrument_location))
        print('Writing to {}'.format(ismr_red_db))

        # start the time
        t_start = time.time()

        files_are_new = True
        latest_files_only = True # switch to stop reading if you reach files that you have already read
        if os.path.isdir(data_dir):
            # walk through all the .ismr files you can find in this directory:
            # Added reverse: do the new directories first!
            for (dirname, dirs, files) in os.walk(data_dir, topdown=True):
                dirs.sort(reverse=True)
                print('Walkdir: dirname: {} dirs: {}, files {}'.format(dirname, dirs, files))
                for file in sorted(files, reverse=True):
                    print('Reading dirname {} with file {}'.format(dirname, os.path.splitext(file)))
                    if not os.path.splitext(file)[1] == '.ismr':
                        continue
                    infile = os.path.join(dirname, file)
                    if instrument_location in dirname:
                        # ismr_dataframe = read_ismr.read_ismr(infile)
                        # if ismr_dataframe.shape[0] == 0:
                        #     continue
                        # read_ismr.write_to_sqlite(ismr_dataframe, dbname=ismrdb,
                        #                           loc=instrument_location)

                        ismr_dataframe = read_ismr.read_reduced_ismr(infile)
                        if ismr_dataframe.shape[0] == 0:
                            continue

                        written = read_ismr.write_to_reduced_sqlite(ismr_dataframe, dbname=ismr_red_db,
                                                            loc=instrument_location)
                        if written == False: # made distinction between output of routine and files_are_new
                            print('Reached end of new files: break')
                            files_are_new = False
                            break

                        # TEST reduced reading
                        # sys.exit(0)

                # keep track of time
                print('Elapsed: {} s'.format(time.time() - t_start))
                print('Wrote {}'.format(ismr_red_db))
                if latest_files_only and not files_are_new:
                    break

if __name__ == '__main__':
    main()
