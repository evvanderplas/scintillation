#! /usr/bin/env python

'''
    Make a (simple) class to plot scintillation measurement plots
'''

import os, sys
import time
import argparse

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import cartopy.crs as ccrs

import lib.tools
from lib.tools import get_sqlite_data, init_logger, read_yaml, read_confdate
import lib.constants as constants


class ISMRplot():
    '''
        Class to plot ismr data, with functionality to get data from the database,
        interpret the configuration etc
    '''
    def __init__(self, configfile, log, tag):
        '''
            Initialise
        '''
        self.config = {}
        self.log = log
        self.tag = tag
        self.location = None
        self._complete_config(configfile)

        self.vardata = None
        self.nanvar = None
        self.timedata = np.array([], dtype=np.float)
        self.timeofday = np.array([], dtype=np.float)

        if self.config['plot_type'] == 'scatter':
            self.scatterplot(colorby='timeofday')

            var1 = self.config['plot_var'][0]
            self.tag = 'extra_tod_{}'.format(var1)
            self.log.debug('Extra: xvar timeofday, yvar = {}'.format(var1))
            self.scatterplot(xvar='timeofday', yvar=var1)

            var2 = self.config['plot_var'][1]
            self.tag = 'extra_tod_{}'.format(var2)
            self.log.debug('Extra: xvar timeofday, yvar = {}'.format(var2))
            self.scatterplot(xvar='timeofday', yvar=var2)

        elif self.config['plot_type'] == 'map':

            for mapvar in self.config['plot_var']:
                self.log.debug('Map: Plot: {}'.format(mapvar))
            self.log.debug('From {} till {}'.format(self.config['startdt'], self.config['enddt']))
            # return

            for mapvar in self.config['plot_var']:
                if mapvar in ('azimuth', 'elevation'):
                    pass
                else:
                    self.geo_plot(mapvar)

        if 'histogram' in self.config and self.config['histogram']:

            for mapvar in self.config['plot_var']:
                self.log.debug('Histogram: Plot: {}'.format(mapvar))
            self.log.debug('From {} till {}'.format(self.config['startdt'], self.config['enddt']))
            # return

            for var in self.config['plot_var']:
                self.tag = self.config['tag']
                self.log.debug('Histogram of {}'.format(var))
                self.hist_plot(var)

    def _complete_config(self, configfile):
        '''
            Read some complementary stuff from a local.yaml file
            such as which database to use etc: not something you want for each plot
        '''

        # read where the database is
        dbconfig = read_yaml('local.yaml')

        # read what plot(s) to make
        self.config = read_yaml(configfile)

        # override local.yaml if the database is set in the specific yaml
        if 'ismrdb_path' in self.config:
            dbconfig['ismrdb_path'] = self.config['ismrdb_path']
        if 'ismrdb_name' in self.config:
            dbconfig['ismrdb_name'] = self.config['ismrdb_name']

        self.ismrdb = os.path.join(dbconfig['ismrdb_path'], dbconfig['ismrdb_name'].format(self.config['location']))
        self.log.debug('Reading from database {}'.format(self.ismrdb))

        # make one dict with the settings to convey to plotting routine
        self.config['startdt'] = read_confdate(self.config['startdate'])
        self.config['enddt'] = read_confdate(self.config['enddate'])
        for item, setting in dbconfig.items():
            self.config[item] = setting

        if 'colormap' in self.config:
            self.cmap = self.config['colormap']
        else:
            self.cmap = 'hot_r'

        # prepare to output in the output directory
        os.makedirs(self.config['outputdir'], exist_ok=True)

    def _interpret_svid(self):
        '''
            allow for easier selection of GNSS satellites
        '''
        SATRANGE = {
            'gps': np.arange(1,38),
            'glonass': np.arange(38,62),
            'galileo': np.arange(71, 103),
            'sbas': np.arange(120,141),
            'compass': np.arange(141, 173),
            'qzss': np.arange(180,188)
        }

        # self.log.debug('Interpreting: {}: {}'.format(self.config['satellites'], SATRANGE[self.config['satellites'].lower()]))
        if isinstance(self.config['satellites'], str):
            if self.config['satellites'].lower() in SATRANGE.keys():
                return SATRANGE[self.config['satellites'].lower()]
        elif isinstance(self.config['satellites'], (tuple, list, np.array)):
            return self.config['satellites']
        elif '-' in self.config['satellites']:
            print('Divination of a range')
            s1, sl = self.config['satellites'].split('-')
            return np.arange(int(s1), int(sl))

    def _prepare_data(self):
        '''
            Look in config which data to retrieve from the database
            and put in a numpy array.
        '''
        total_vars = constants.HEADER_NAMES + constants.NAMES

        tstart = self.config['startdt'] # the interpreted starttime in datetime format
        tend = self.config['enddt'] # the interpreted endtime in datetime format
        loc = self.config['location']
        # scint_db = os.path.join(self.config['ismrdb_path'], self.config['ismrdb_name'].format(loc))
        tabname = self.config['tabname'].format(loc)
        if 'satellites' in self.config:
            svid = self._interpret_svid() # self.config['satellites']
        else:
            svid = None

        # make a list of the possible data you might need:
        if ('plotdata' not in self.config) or self.config['plotdata'] is None:
            query_start = time.time()
            vars = self.config['plot_var']

            if isinstance(vars, (list, tuple)):
                nrvars = len(vars)
                req_list = list(vars) + ['timestamp']
            else:
                req_list = [vars, 'timestamp']

            # if the variable by which you want to color the data is not
            # already in the list, add it
            if 'colorby' in self.config and self.config['colorby'] in total_vars \
                    and self.config['colorby'] not in vars:

                # we use the fact that time comes last:
                req_list.insert(-1, self.config['colorby'])
                vars.insert(-1, self.config['colorby'])
                nrvars += 1

            for geovar in ('azimuth', 'elevation'):
                if 'map' in self.config['plot_type'] and geovar not in vars:
                    # we use the fact that time comes last:
                    req_list.insert(-1, geovar)
                    vars.insert(-1, geovar)
                    nrvars += 1

            # see if the query should be restricted somehow:
            # idea is that a variable can be given with a min and a max
            # more advanced queries: maybe later:
            restrict_list = []
            if 'restrictions' in self.config:
                for rvar in self.config['restrictions']:
                    if rvar in total_vars:
                        if 'min' in self.config['restrictions'][rvar]:
                            rmin = self.config['restrictions'][rvar]['min']
                            if rmin == 'None':
                                pass
                            else:
                                restrict_list.append('{} > {}'.format(rvar, rmin))
                        else:
                            rmin = None
                        if 'max' in self.config['restrictions'][rvar]:
                            rmax = self.config['restrictions'][rvar]['max']
                            if rmax == 'None':
                                pass
                            else:
                                restrict_list.append('{} < {}'.format(rvar, rmax))
                        else:
                            rmax = None
            if restrict_list == []:
                restrict_list = None

            plotdata = get_sqlite_data(req_list, self.ismrdb, table=tabname,
                                       svid=svid, tstart=tstart, tend=tend,
                                       restrict_crit=restrict_list, log=log)
            query_end = time.time()
            self.log.debug('Query took {:.3f} seconds'.format(query_end - query_start))

        else:
            plotdata = config['plotdata']

        if nrvars == 1:
            allvardata = np.array([np.float(t[0]) for t in plotdata])
            nanvar = np.isnan(allvardata)
            vardata = allvardata[~nanvar]
            log.debug('Size vardata: {}'.format(vardata.shape))
        else:
            vardata = {}
            timestampdata = np.array([t[-1] for t in plotdata])

            # make two rounds:
            # first to get all the nan-values, second to get the data:
            nanvar = np.zeros_like(timestampdata, dtype=bool)
            for idx_var, multivar in enumerate(vars):
                allvardata = np.ones(len(plotdata), dtype=np.float)
                try:
                    # allvardata = np.array([np.float(t[idx_var]) for t in plotdata if not None in t else None])
                    for idx_t, t in enumerate(plotdata):
                        if None in t or str(t[idx_var]).isalpha():
                            allvardata[idx_t] = None
                        else:
                            allvardata[idx_t] = np.float(t[idx_var])
                except TypeError as terr:
                    for t in plotdata:
                        if t[idx_var] is None:
                            print('{}, idx {}: {} allvars = {}'.format(t, idx_var, multivar, vars))
                    self.log.error('what went wrong? var {} in {} or {}?: {}'.format(multivar, vars, req_list, t))
                    self.log.error('up to now: {}'.format(allvardata))
                self.log.debug('Round {}: # of nans: {}, total {}'.format(idx_var,
                            np.sum(np.isnan(allvardata)), np.sum(nanvar)))
                nanvar = np.logical_or(np.isnan(allvardata), nanvar)

            # remember where the NaN's are:
            self.nanvar = nanvar
            self.log.debug('How many nan? {}'.format(np.sum(self.nanvar)))

            # second round:
            # self.log.debug('Loop over vars: {}, but index over req_list: {}'.format(vars, req_list))
            for idx_var, multivar in enumerate(req_list):

                # allvardata = np.array([np.float(t[idx_var]) for t in plotdata])
                for idx_t, t in enumerate(plotdata):
                    if None in t or str(t[idx_var]).isalpha():
                        allvardata[idx_t] = None
                    else:
                        allvardata[idx_t] = np.float(t[idx_var])

                vardata[multivar] = allvardata[~nanvar]
                self.log.debug('Size vardata {}: {}'.format(multivar, vardata[multivar].shape))

        # gamble that the not available data is the same for all vars in the list...
        timestampdata = np.array([t[-1] for t in plotdata])[~nanvar]
        self.timedata = np.array([dt.datetime.fromtimestamp(t[-1]) for t in plotdata])[~nanvar]
        self._add_hour_of_day()
        vardata['timeofday'] = self.timeofday

        # for a next plot(?)
        self.vardata = vardata
        self.log.debug('Vars: {}, vardata: {}'.format(vars, vardata.keys()))
        for var in vars:
            self.log.debug('Var {}: {}'.format(var, np.sum(np.isnan(vardata[var]))))

        # sys.exit(0)
        return vardata

    def _add_hour_of_day(self):
        '''
            Get the time-of-day for each measurement
        '''
        tod = np.zeros_like(self.timedata)
        for mt_idx, mtime in enumerate(self.timedata):
            tod[mt_idx] = (mtime - dt.datetime(mtime.year, mtime.month, mtime.day, 0,0,0,0)).seconds/3600.
        self.timeofday = tod

    def _sats_for_figname(self):
        '''
            Decide how to indicate for which sats the figure was made
        '''
        sats = self.config['satellites']
        self.log.debug('For figname: satellites: {}'.format(sats))
        if len(list(sats)) == 1: # only one
            return str(list(sats)[0])
        elif str(sats).isalpha(): # it is a shortcut for a range of satellites
            return str(sats)
        elif len(list(sats)) < 4: # a few numbers:
            return '_'.join([str(s) for s in list(sats)])
        else: # a long list of numbers
            smin, smax = np.min(list(sats)), np.max(list(sats))
            return '{}-{}'.format(smin, smax)

    def _prepare_plotdata(self, xvar, yvar, colorby):
        '''
            Decide which data makes it in the plot
        '''

        if self.vardata is None:
            vardata = self._prepare_data()

        if 'colorby' in self.config:
            colorby = self.config['colorby']

        vars = self.config['plot_var']
        self.log.debug('First we have vars {}'.format(vars))
        if 'colorby' in self.config and self.config['colorby'] in vars:
            vars.remove(self.config['colorby'])
        if (len(vars) < 2) or (len(vars) > 2):
            self.log.error('Specify which variables to plot: {}'.format(vars))
        # self.log.debug('Now we have vars {}'.format(vars))
        # self.log.debug('Data from vars (dict keys) {}'.format(self.vardata.keys()))

        if xvar is None:
            xname = vars[0]
            xdata = self.vardata[xname]
        elif xvar == 'timeofday':
            xdata = self.timeofday
            xname = 'timeofday'
        if yvar is None:
            yname = vars[1]
            ydata = self.vardata[yname]
        else:
            try:
                ydata = self.vardata[yvar]
                yname = yvar
            except KeyError as kerr:
                self.log.error('Not an available variable: {} in {}'.format(yvar, self.vardata.keys()))
                sys.exit(0)
        if colorby is None:
            colors = 'b'
        else:
            try:
                colors = self.vardata[colorby]
            except KeyError as kerr:
                self.log.error('Not an available variable: {}'.format(kerr))
                self.log.error('You want: {}, available: {}'.format(colorby, self.vardata.keys()))
                sys.exit(0)

        return xdata, ydata, xname, yname, colorby, colors

    def _interpret_histogram_bins(self, var):
        '''
            See if in the configuration file the bins for the histogram have been
            specified, and if yes, how
        '''
        # the bins are configurable: if given [a, b] is amount of bins in x, y direction
        # or if a or b is array-like they represent the bins (edges) themselves
        if 'histbins' in self.config:
            histbins_conf = self.config['histbins']
            # check if it has a separate entry for bins in the x and y direction
            if len(histbins_conf) > 1:
                histbins_x, histbins_y = histbins_conf
                # check if it is a number or an attempt to define an array:
                for idx, histb in enumerate(histbins_conf): #(histbins_x, histbins_y):
                    if idx > 1:
                        break # do not consider strangely formatted bins
                    if not isinstance(histb, (list, tuple, np.ndarray)):
                        pass
                    else:
                        if len(histb) == 2:
                            histbins_conf[idx] = np.arange(histb[0], histb[1])
                        elif len(histb) == 3:
                            histbins_conf[idx] = np.linspace(histb[0], histb[1], histb[2])
                histbins = histbins_conf

            else:
                histbins = [histbins_conf, histbins_conf]
        else:
            if self.vardata:
                min_var = np.nanmin([-0.2 * np.nanpercentile(self.vardata[var], 2.),
                                     0.8 * np.nanpercentile(self.vardata[var], 2.),
                                     1.2 * np.nanpercentile(self.vardata[var], 2.)])
                max_var = 1.3 * np.nanpercentile(self.vardata[var], 98.)
                histbins = [200, np.linspace(min_var, max_var, 300)]
            else: # if all else fails: try useful TEC bins:
                histbins = [150, 50]

        return histbins


    def scatterplot(self, xvar=None, yvar=None, colorby=None, cmap='hsv'):
        '''
            make a scatterplot
        '''

        xdata, ydata, xname, yname, colorby, colors = self._prepare_plotdata(xvar, yvar, colorby)

        fig, ax = plt.subplots()
        ax.axhline(y=0, color='r', alpha=0.4)
        if not colorby:
            ax.scatter(xdata, ydata, c=colors, edgecolors='none')
        else:
            ax.scatter(xdata, ydata, c=colors, cmap=cmap, alpha=0.5, edgecolors='none')
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        title = '{} vs {}'.format(yname, xname)
        if len(self.config['satellites']) < 4:
            title += ' for satellites {}'.format(self.config['satellites'])
        title += ' from {} - {}'.format(self.config['startdt'].strftime('%Y-%m-%d'),
                                        self.config['enddt'].strftime('%Y-%m-%d'))
        ax.set_title(title)

        plotfile = os.path.join(self.config['outputdir'],
                            'scatter_{}-{}_{}_{}-{}_sat_{}_{}.png'.format(xname, yname,
                                    self.config['location'],
                                    self.timedata[0].strftime('%Y%m%d%H%M'),
                                    self.timedata[-1].strftime('%Y%m%d%H%M'),
                                    self._sats_for_figname(), self.tag))
        self.log.info('Plotted {}'.format(plotfile))
        fig.savefig(plotfile)
        plt.close(fig)

    def hist_plot(self, var):
        '''
            Make a histogram plot of a variable var in the ismr database db
        '''

        if self.vardata is None:
            vardata = self._prepare_data()

        for checkvar in self.vardata.keys():
            self.log.debug('Var {}: {} or {}'.format(checkvar, self.vardata[checkvar].shape,
                                self.nanvar.shape))

        self.log.debug('Hist data min, max: {} - {}'.format(np.min(self.vardata[var]), np.max(self.vardata[var])))

        # ================================
        # 1D histogram
        fig, ax = plt.subplots()
        _nrbins, _bins, _patches = ax.hist(self.vardata[var], bins=50, normed=1, facecolor='green', alpha=0.75)
        ax.set_xlabel('{} (binned)'.format(var))
        ax.set_title('Histogram of {} at {}'.format(var, self.config['location']))

        # figname = os.path.join(self.config['outputdir'], 'sql_hist_{}_{}.png'.format(tag, loc))
        plotfile = os.path.join(self.config['outputdir'],
                                'hist_{}_{}_{}-{}_sat_{}_{}.png'.format(var,
                                            self.config['location'],
                                            self.timedata[0].strftime('%Y%m%d%H%M'),
                                            self.timedata[-1].strftime('%Y%m%d%H%M'),
                                            self._sats_for_figname(), self.tag))
        self.log.debug('Saving {}'.format(plotfile))
        fig.savefig(plotfile)
        plt.close(fig)

        # ================================
        # 2D histogram
        fig, ax = plt.subplots()

        # make sure the information passed on about the histograms is properly implemented
        histbins = self._interpret_histogram_bins(var)
        # self.log.debug('Bins for 2D histogram: {}'.format(histbins))

        ax.hist2d(self.vardata['timestamp'], self.vardata[var], bins=histbins, norm=LogNorm())
        ax.set_ylabel('{} (binned)'.format(var))
        if 'yrange' in self.config:
            ymin, ymax = self.config['yrange']
            ax.set_ylim(ymin, ymax)
        else:
            ax.set_ylim(np.nanmin([0., np.nanpercentile(self.vardata[var], 2.)]),
                        np.nanmax([1.3 * np.nanpercentile(self.vardata[var], 98.)]) )

        # draw a red line where the zero should be:
        ax.axhline(y=0, color='red', linestyle='-', alpha=0.4)

        xlocs = ax.get_xticks()
        ax.set_xticks(xlocs) # unnecessary?
        dtlabels = [dt.datetime.fromtimestamp(tlab) for tlab in xlocs]
        ax.set_xticklabels([dtlab.strftime('%Y-%m-%d') for dtlab in dtlabels])
        ax.set_xlabel('Time (binned)')

        fig.autofmt_xdate()
        ax.set_title('Histogram as a function of time of {} at {}'.format(var, self.config['location']))

        plotfile = os.path.join(self.config['outputdir'],
                                'hist2D_{}_{}_{}-{}_sat_{}_{}.png'.format(var,
                                            self.config['location'],
                                            self.timedata[0].strftime('%Y%m%d%H%M'),
                                            self.timedata[-1].strftime('%Y%m%d%H%M'),
                                            self._sats_for_figname(), self.tag))
        self.log.debug('Saving {}'.format(plotfile))
        fig.savefig(plotfile)
        plt.close(fig)

        # ================================
        # 2D histogram time_of_day
        fig, ax = plt.subplots()

        # make sure the information passed on about the histograms is properly implemented
        histbins_tod = [24, histbins[1]]
        houroftheday = np.array([t.hour for t in self.timedata])
        ax.hist2d(houroftheday, self.vardata[var], bins=histbins_tod, norm=LogNorm())
        ax.set_ylabel('{} (binned)'.format(var))
        if 'yrange' in self.config:
            ymin, ymax = self.config['yrange']
            ax.set_ylim(ymin, ymax)
        else:
            ax.set_ylim(np.nanmin([0., np.nanpercentile(self.vardata[var], 2.)]),
                        np.nanmax([1.3 * np.nanpercentile(self.vardata[var], 98.)]) )

        # draw a red line where the zero should be:
        ax.axhline(y=0, color='red', linestyle='-', alpha=0.4)

        ax.set_xlabel('Time of day (binned)')
        fig.autofmt_xdate()
        ax.set_title('Histogram as a function of time of day for {} at {}'.format(var, self.config['location']))

        plotfile = os.path.join(self.config['outputdir'],
                                'hist2D_TOD_{}_{}_{}-{}_sat_{}_{}.png'.format(var,
                                                self.config['location'],
                                                self.timedata[0].strftime('%Y%m%d%H%M'),
                                                self.timedata[-1].strftime('%Y%m%d%H%M'),
                                                self._sats_for_figname(), self.tag))
        self.log.debug('Saving {}'.format(plotfile))
        fig.savefig(plotfile)
        plt.close(fig)

        return

    def geo_plot(self, var):
        '''
            Plot the GNSS data on a map
        '''
        if self.vardata is None:
            vardata = self._prepare_data()

        sphere = ccrs.PlateCarree(globe=ccrs.Globe(datum='WGS84',
                                                   ellipse='sphere'))

        midpoint = constants.TOPO[self.config['location']] # (17.62048, -63.24323),
        fig = plt.figure()

        # choose a projection
        ax = plt.axes(projection=ccrs.PlateCarree())

        # cut out the right part of the map:
        lat0, lon0 = midpoint
        extent = ( lon0 -25., lon0 + 25., lat0 - 20., lat0 + 20.)
        self.log.debug('Extent of axes: {}'.format(extent))
        ax.set_extent(extent, crs=ccrs.PlateCarree())
        ax.coastlines(resolution='50m', color='black', linewidth=1)
        gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                  linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        gl.xlabels_top = False
        gl.ylabels_right = False

        # the plotheight is a measure of where one would estimate the scintillation to
        # occur. The signal is measured at the earth's surface, the satellites are at
        # approximately 20.000 km height (Medium Earth Orbit, MEO).
        plotheight = 200. # km
        lons, lats = lib.tools.azel_to_latlon(self.vardata['azimuth'], self.vardata['elevation'],
                                              point=midpoint, height=plotheight)
        self.log.debug('Lats: {}-{}, \nLons: {}-{}'.format(np.nanmin(lats), np.nanmax(lats),
                                                            np.nanmin(lons), np.nanmax(lons)))
        plotdata = self.vardata[var]
        minval = np.nanpercentile(plotdata, 10.)
        maxval = np.nanpercentile(plotdata, 95.)
        self.log.debug('Plotdata {}: plot {} to {} \n{}'.format(var, minval, maxval, plotdata[:30]))

        # indicate the receiver station
        ax.scatter(lon0, lat0, s=130, c='r', marker='*')

        # the actual plotting:
        azel = ax.scatter(lons, lats, s=30, c=plotdata, vmin=minval, vmax=maxval,
                        cmap=plt.cm.get_cmap(self.cmap), alpha=0.7, linewidths=0, edgecolors=None,
                        )

        ax.set_xlabel('Longitude [deg]')
        ax.set_ylabel('Latitude [deg]')
        ax.set_title('Tracks: {} for satellites {} at {:.1f} km, \nperiod {} - {}'.format(var, self._sats_for_figname(),
                                plotheight, self.timedata[0].strftime('%Y%m%d%H%M'), self.timedata[-1].strftime('%Y%m%d%H%M')))
        cb = fig.colorbar(azel, ax=ax)
        cb.set_label('{} [units]'.format(var))
        outfig = os.path.join(self.config['outputdir'],
                'azel_map_{}_{}_{}-{}_sat_{}_{}.png'.format(var,
                                self.config['location'],
                                self.timedata[0].strftime('%Y%m%d%H%M'),
                                self.timedata[-1].strftime('%Y%m%d%H%M'),
                                self._sats_for_figname(), self.tag))
        fig.savefig(outfig, dpi=100)
        plt.close(fig)
        self.log.debug('Plotted {}'.format(outfig))



if __name__ == '__main__':

    tag = 'test'
    print('Do test plot: tag="{}"'.format(tag))
    test_yaml_file = 'test_simple_TEC_scatter.yaml'
    log = init_logger()

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="the configuration file on what to plot",
                        default=test_yaml_file)
    args = parser.parse_args()
    log.debug('Plotting from {}'.format(args.infile))

    test_inst = ISMRplot(args.infile, log, tag)
