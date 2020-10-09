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

def last_downloaded_file(locpath, archpath=TROPDATAPATH):
    '''
        Check what the lastest file is that has been downloaded
    '''

    datapath = os.path.join(archpath, 'IONO', locpath)
    if not os.path.isdir(datapath):
        return 0

    dirs = sorted([os.path.split(yyw[0])[-1] for yyw in os.walk(datapath)
                   if os.path.split(yyw[0])[-1].isdigit()])
    # print('{}: {}'.format(site, dirs))
    last_dir = dirs[-1]
    print('Latest dir already ingested ({}): {}'.format(locpath, last_dir))

    return last_dir

def parse_daily_dirs(parent_dir, dest_dir, latestdirs, ftp_handle,verb=True):
    '''
        Parse the directories created by the Septentrio instrument per day of year
        For each instrument (location)  a parent directory exists in which they are
        stored at the FTP server.
        NB also the calibrated files are stored in a separate directory, that can be
        parsed by this function.
    '''
    ftp_handle.cwd(parent_dir)
    avail_dirs = sorted([item for item in ftp_handle.nlst() if item.isdigit()])
    print(avail_dirs)

    # for now
    for dailydir in avail_dirs:
        # lastdir = avail_dirs[-1]
        if int(dailydir) < int(latestdirs):
            print('Should have been ingested already: {} < {}'.format(dailydir, latestdirs))
            continue # TODO: new, check carefully if no files are forgotten!
        ftp_handle.cwd(dailydir)
        # localdir = os.path.join(archpath, 'IONO', site, dailydir)
        localdir = os.path.join(dest_dir, dailydir)
        if os.path.isdir(localdir):
            if verb:
                print('>>>>> Already a directory! {}'.format(localdir))
        try:
            os.makedirs(localdir)
            print('Made {}'.format(localdir))
        except FileExistsError as ferr:
            print('No need to create {} ({})'.format(localdir, ferr))
        # ftplisting = ftph.nlst()
        # for item in ftplisting:
        #     print('{}: {}'.format(item, os.path.splitext(item)))
        ismrfiles = sorted([item for item in ftp_handle.nlst()
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
                ftp_handle.retrbinary('RETR {}'.format(ismrf), localf.write)
                localf.close()
        ftp_handle.cwd('..')

    # back to level where function was started
    path_items = parent_dir.split(os.sep)
    ftp_handle.cwd(os.sep.join('..' for p in path_items))



def get_dir(remotedirs, archpath=TROPDATAPATH, verb=False):
    '''
        Get a directory via FTP
    '''

    ftph = ftplib.FTP(host=FTPHOST, user=FTPUSER, passwd=FTPWW)
    ftph.cwd('../IONO')
    for site in SITES:

        localdestdir = os.path.join(archpath, 'IONO', site)
        latestdir = last_downloaded_file(site, archpath=TROPDATAPATH)
        parse_daily_dirs(site, localdestdir, latestdir, ftph, verb=verb)

        # By now, we also have calibrated files:
        #ftph.cwd(site)
        localdestdir = os.path.join(archpath, 'IONO', site, 'CAL')
        calpath = '{}/CAL'.format(site)
        latestdir = last_downloaded_file(calpath, archpath=TROPDATAPATH)
        parse_daily_dirs(calpath, localdestdir, 0, ftph, verb=verb)
        #ftph.cwd('..')

        # if 1: # try:
        #     ftph.cwd(site)
        #     avail_dirs = sorted([item for item in ftph.nlst() if item.isdigit()])
        #     print(avail_dirs)
        #
        #     # for now
        #     for dailydir in avail_dirs:
        #         # lastdir = avail_dirs[-1]
        #         if int(dailydir) < int(localdirs[site]):
        #             print('Should have been ingested already: {} < {}'.format(dailydir, localdirs[site]))
        #             continue # TODO: new, check carefully if no files are forgotten!
        #         ftph.cwd(dailydir)
        #         localdir = os.path.join(archpath, 'IONO', site, dailydir)
        #         if os.path.isdir(localdir):
        #             if verb:
        #                 print('>>>>> Already a directory! {}'.format(localdir))
        #         try:
        #             os.makedirs(localdir)
        #             print('Made {}'.format(localdir))
        #         except FileExistsError as ferr:
        #             print('No need to create {} ({})'.format(localdir, ferr))
        #         # ftplisting = ftph.nlst()
        #         # for item in ftplisting:
        #         #     print('{}: {}'.format(item, os.path.splitext(item)))
        #         ismrfiles = sorted([item for item in ftph.nlst()
        #                             if os.path.splitext(item)[-1] == '.ismr'])
        #         for ismrf in ismrfiles:
        #             if verb:
        #                 print('getting {}'.format(ismrf))
        #             localfile = os.path.join(localdir, ismrf)
        #             if os.path.isfile(localfile):
        #                 if verb:
        #                     print('>>>>> Already a file: {}! Continuing...'.format(localfile))
        #             else:
        #                 localf = open(localfile, 'wb')
        #                 ftph.retrbinary('RETR {}'.format(ismrf), localf.write)
        #                 localf.close()
        #         ftph.cwd('..')
        #
        # else: # except: # ftperr
        #     print('Problem')

        # ftph.cwd('..')
    # close the connection
    ftph.quit()

    return 'Done'

if __name__ == '__main__':
    print('fetch stick')
    get_dir([], archpath=TROPDATAPATH)
