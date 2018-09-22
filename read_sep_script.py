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
    data_location = '/Users/plas/Downloads/IONO'
    if os.path.isdir(data_location):
        for (dirname, dirs, files) in os.walk(data_location):
            # print('Walkdir: dirname: {} dirs: {}, files {}'.format(dirname, dirs, files))
            for file in files:
                

if __name__ == '__main__':
    main()
