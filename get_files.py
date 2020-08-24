#! /usr/bin/env python

'''
    Routine that pulls ISMR files from the FTP-pro server at KNMI
'''
import os
import ftplib
from lib.tools import init_logger

FTPHOST = 'ftppro-236.knmi.nl'
FTPUSER = 'spaceweather'
FTPWW = 'sp33sW'

TROPDATAPATH = '/data/storage/trop/users/plas/SW'
SITES = ('SABA', 'SEUT')

def last_downloaded_file(archpath=TROPDATAPATH):
    '''
        Check what the lastest file is that has been downloaded
    '''

    last_dir = {}
    for site in SITES:
        datapath = os.path.join(archpath, 'IONO', site)
        dirs = sorted([os.path.split(yyw[0])[-1] for yyw in os.walk(datapath)
                       if os.path.split(yyw[0])[-1].isdigit()])
        print('{}: {}'.format(site, dirs))
        last_dir[site] = dirs[-1]

    return last_dir

def get_dir(localdirs, remotedirs, archpath=TROPDATAPATH, verb=False):
    '''
        Get a directory via FTP
    '''

    ftph = ftplib.FTP(host=FTPHOST, user=FTPUSER, passwd=FTPWW)
    ftph.cwd('../IONO')
    for site in SITES:
        if 1: # try:
            ftph.cwd(site)
            avail_dirs = sorted([item for item in ftph.nlst() if item.isdigit()])
            print(avail_dirs)

            # for now
            for dailydir in avail_dirs:
                # lastdir = avail_dirs[-1]
                ftph.cwd(dailydir)
                localdir = os.path.join(archpath, 'IONO', site, dailydir)
                if os.path.isdir(localdir):
                    if verb:
                        print('>>>>> Already a directory! {}'.format(localdir))
                try:
                    os.makedirs(localdir)
                except FileExistsError as ferr:
                    print('No need to create {} ({})'.format(localdir, ferr))
                print('Made {}'.format(localdir))
                # ftplisting = ftph.nlst()
                # for item in ftplisting:
                #     print('{}: {}'.format(item, os.path.splitext(item)))
                ismrfiles = sorted([item for item in ftph.nlst()
                                    if os.path.splitext(item)[-1] == '.ismr'])
                for ismrf in ismrfiles:
                    if verb:
                        print('getting {}'.format(ismrf))
                    localfile = os.path.join(localdir, ismrf)
                    if os.path.isfile(localfile):
                        if verb:
                            print('>>>>> Already a file: {}! Continuing...'.format(localfile))

                    else:
                        localf = open(localfile, 'wb')
                        ftph.retrbinary('RETR {}'.format(ismrf), localf.write)
                        localf.close()
                ftph.cwd('..')

        else: # except: # ftperr
            print('Problem')

        ftph.cwd('..')
    # close the connection
    ftph.quit()

    return 'Done'

if __name__ == '__main__':
    print('fetch stick')
    lastdir = last_downloaded_file(archpath=TROPDATAPATH)
    get_dir(lastdir, [], archpath=TROPDATAPATH)
