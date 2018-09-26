#! /usr/bin/env python

import read_ismr
import os
import datetime as dt
import logging

def get_sqlite_data(varlist, db, log=logging):
    '''
        Get data from SQLite database
    '''

    conn = sqlite3.connect(db)
    c = conn.cursor()
    sqlstat = 'SELECT {},{} FROM sep_data' #  WHERE SVID = 11'

    c.execute(sqlstat)

    data = c.fetchall()
    log.debug('Shape of data; {}'.format(data.shape))

    return data

def time_plot(var, db, out='./', log=logging):
    '''
        Make a plot as a function of time of a variable var in the ismr database db
    '''

    plotdata = get_sqlite_data([var, 'time'], db, log=log)
    timedata = np.array([dt.datetime.fromtimestamp(t) for t in plotdata[1]])
    fig, ax = plt.subplots()
    ax.plot(timedata, plotdata[0], 'b.')

    figname = os.path.join(out, 'sql_time_{}.png'.format(var))
    log.debug('Saving {}'.format(figname))
    fig.savefig(figname)

if __name__ == '__main__':

    ismrdb_path = './'
    ismrdb = os.path.join(ismrdb_path,'test_scint.db')

    logger = logging.getLogger('plotting')
    logger.setLevel(logging.DEBUG)

    time_plot('S4', out='plots', log=logger)
