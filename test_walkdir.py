#! /usr/bin/env python
import os, sys


archdir = '/data/storage/trop/users/plas/SW/IONO'

if __name__ == '__main__':

    data_dir = os.path.join(archdir, 'SEUT')
    print('Test vanuit {}'.format(data_dir))
    nrofdirs = 0

    exclude = set(['CAL'])
    for (dirname, dirs, files) in os.walk(data_dir, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude]
        dirs.sort(reverse=True)
        print('='*20)
        print('Walkdir: dirname: {} dirs: {}, files {}'.format(dirname, dirs, files))
        nrofdirs += 1
        if nrofdirs > 5:
            sys.exit(0)
