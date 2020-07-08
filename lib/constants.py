#! /usr/bin/env python
'''
    Some constants to be used by different scripts
'''



HEADER_NAMES = ['weeknumber', 'timeofweek', 'SVID', 'fieldblockvalue']
#NAMES = ['weeknumber', 'timeofweek', 'SVID', 'fieldblockvalue',
NAMES = ['azimuth', 'elevation',
         'sig1_CNO_avg_min', 'sig1_S4', 'sig1_S4_corr', 'sig1_phi01', 'sig1_phi03', 'sig1_phi10', 'sig1_phi30', 'sig1_phi60',
         'sig1_avgccd', 'sig1_sigmaccd',
         'sig1_TEC_m45', 'sig1_dTEC_m60_m45',
         'sig1_TEC_m30', 'sig1_dTEC_m45_m30',
         'sig1_TEC_m15', 'sig1_dTEC_m30_m15',
         'sig1_TEC', 'sig1_dTEC_m15_0',
         'sig1_locktime',
         'sbf2ismr_version',
         'sig1_f2_locktime', 'sig1_f2_avg',
         'sig1_SI', 'sig1_SI_nom', 'p_sig1',
         'sig2_CNO_avg_min', 'sig2_S4', 'sig2_S4_corr', 'sig2_phi01', 'sig2_phi03', 'sig2_phi10', 'sig2_phi30', 'sig2_phi60',
         'sig2_avgccd', 'sig2_sigmaccd',
         'sig2_locktime',
         'sig2_SI', 'sig2_SI_nom', 'p_sig2',
         'sig3_CNO_avg_min', 'sig3_S4', 'sig3_S4_corr', 'sig3_phi01', 'sig3_phi03', 'sig3_phi10', 'sig3_phi30', 'sig3_phi60',
         'sig3_avgccd', 'sig3_sigmaccd',
         'sig3_locktime',
         'sig3_SI', 'sig3_SI_nom', 'p_sig3',
         'sig1_T', 'sig2_T', 'sig3_T'
         ]

REDUCED_NAMES = ['azimuth', 'elevation', 'sig1_TEC',
                 'sig1_S4', 'sig1_S4_corr',
                 'sig2_S4', 'sig2_S4_corr',
                 'sig3_S4', 'sig3_S4_corr',]

TOPO = {
        'SABA': (17.62048, -63.24323),
        'SEUT': (17.47140, -62.97570),
        }
R_earth = 6378.100   # km
