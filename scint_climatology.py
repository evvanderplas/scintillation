#! /usr/bin/env python


import os
import tools
import scintplots

def main():
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



if __name__ == '__main__':

    logger = tools.init_logger()
    logger.info('Create a mean signal and its excursions')
