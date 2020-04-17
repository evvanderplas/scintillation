#! /usr/bin/env python
'''
    Some tools for the management of GNSS scintillation measurement files in ISMR
    format
'''

import os
import sys
import logging
import yaml
import datetime as dt

def init_logger():
    '''
        Initialize a logger
    '''
    logger = logging.getLogger('plotting')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    return logger

def test_logger():
    '''
        Test the logger
    '''
    try:
        logger = init_logger()
        logger.debug('Test message succeeded')
        return 1
    except err:
        print('Initialize logger failed: {}'.format(err))
        return 0

def read_yaml(yamlfile):
    '''
        Read a YAML file into a dictionary
    '''

    with open(yamlfile, 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    return config

def read_confdate(dlist):
    '''
        Read the list of [Y, m, d, H, M, S] and turn it into a datetime
    '''

    if len(dlist) >= 6:
        readdate = dt.datetime(dlist[0], dlist[1], dlist[2], dlist[3], dlist[4], dlist[5])
    elif len(dlist) == 3:
        readdate = dt.datetime(dlist[0], dlist[1], dlist[2], 0, 0, 0)

    return readdate

if __name__ == '__main__':

    print('tools')
    if test_logger():
        print('All fine')
