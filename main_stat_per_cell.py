"""

Script for generating several tables of NDFF data
  number of observations per period
  number of unique species per cell per period, plus difference
  tally of differences
  number of cells per species per period

NDFF database can be restricted to observations meeting some criteria, or cells meeting some criteria.
Further restrictions can be applied to guarantee equal nr of observations per cell per protocol

The NDFF dabtasbase selection criteria are:
km or uurhok, minimum area, sampling protocol, include nulsoort, species group, beheertype

The cell selection criteria are:
onderzoeksvolledigheid per soortgroep voor periodes 1998-2007 and 2008-2018
areaal heide volgens LGN in 1900 en 2012
areaal SBB beheerd land

Hans Roelofsen, WEnR, 20 feb 2019
updates 21 august 2019

"""

import os
import datetime
import numpy as np
import pandas as pd

from nw import utils
from nw import export_shape

# =====================================================================================================================#
# Constraints on NDFF database
hok = 'kmhok'  # one of: uurhok, kmhok.
protocol_excl = []  # one or more observations protocols to exclude. If none, then use []
nulsoort = False  # include nulsoorten? True or False
groep = 'all'  # one of: 'broedvogel', 'dagvlinder', 'vaatplant', 'herpetofauna', 'all'
beheertypes = 'all'  #['snl_hoogveen', 'snl_vochtige_heide', 'snl_zuur_ven_of_hoogveenven', 'snl_droge_heide',
                     #'snl_zandverstuiving', 'snl_hoogveen', 'all']
periodes = [range(1998, 2004), range(2013, 2019)]  # list of ranges
labels = ['P1998-2003', 'P2013-2018']  # labels for each periode

# =====================================================================================================================#
# Contraints on cells
heide_periode_in = 2012  # reference year for heide presence in cells, either 1900 or 2012
heide_treshold_in = 0  # % of cell in year constaining heide. 0 if all values are ok
oz05_treshold_in = 75  # drempelwaarde voor onderzoeksvolledigheid periode 1998-2007. 0 if all values are ok
oz18_treshold_in = 75  # drempelwaarde voor onderzoeksvolledigheid periode 2008-2018. 0 if all values are ok
sbb_area_treshold = 0  # drempelwaarde voor SBB areaal in de cell. Evaluation is >=. 0 if all values are ok

# =====================================================================================================================#
# various processing and output options
equal_protocol_density_per_cell = False  # Harmonize observation count per cell, per protocol, between periods?
equal_obs_per_cell = False  # Harmonize observation count per cell, between periodes
equal_obs_per_period = True  # Harmonize observation count between periodes

if equal_protocol_density_per_cell and equal_obs_per_cell:
    raise Exception('This is not recommended')

print_tables = True  # write tables to file. See below for output directory
print_diff_maps = False  # write maps to file. See below for parameters

# =================================================================================================================#
# get requested cell type and narrow down
cells = utils.get_hok_gdf_simple(hok_type=hok)
cells_query = '{0}_oz05 >= {1} & {0}_oz18 >= {2} & heide{3} >= {4} & sbb_aream2 >= {5}'.format(
     utils.get_soortgroep_afkorting(groep), oz05_treshold_in, oz18_treshold_in, heide_periode_in, heide_treshold_in,
     sbb_area_treshold)
cells_sel = cells.query(cells_query)

if cells_sel.empty:
    raise Exception('No {0}-hokken found complying to query'.format(hok))
else:
    print('Found {0} {1}-hokken complying to query'.format(cells_sel.shape[0], hok))

# =================================================================================================================#
# get information dictionary on all species
sp_info = utils.get_sp_info()

# request full ndff database
ndff = utils.get_ndff_full()

'''
NDFF format is as follows:

nl_name|sci_name|datum waarneming|protocol|X|Y|oppervlakte|kmhokID|uurhokID|duplohokID|quartohokID|year

'''

# intersection of species complying to species tax group, beheertype and nulsoort queries
sp_sel = set(sp_info[groep]['sp_nm']) & set(sp_info[beheertypes]['sp_nm']) & \
         set(sp_info['nulsoort'][nulsoort]['sp_nm'])

# selection from the full NDFF
ndff_query = 'protocol not in {0} & area < {1} & nl_name in {2} & year ' \
             'in {3} & {4} in {5}'.format(protocol_excl,  # observation protocols to exclude, [] if none
                                          utils.minimum_area(hok),   # max. area of the observation
                                          list(sp_sel),  # the species of interest
                                          utils.ranges_to_years(periodes),   # observation made in selected year
                                          hok,  # [kmhok|uurhok|duplohok|quartohok]
                                          list(cells_sel['ID']))  # list of hok IDs complying to earlier query
ndff_sel = ndff.query(ndff_query)

if ndff_sel.empty:
    print('\tNo NDFF records for {0} - {1}'.format(groep, beheertypes))
else:
    print('\t{0} out of {1} NDFF records complying to query.'.format(ndff_sel.shape[0], ndff.shape[0]))

# add the periode as a string-column based on the year of the observation
ndff_sel['periode'] = ndff_sel['year'].apply(utils.classifier, args=(periodes, labels))
ndff_sel['count'] = 1  # counter
print(ndff_sel.head())

#==================================================================================================================#
# store NDFF sample size
ndff_sel_size = ndff_sel.shape[0]

#==================================================================================================================#
# Dilute NDFF to equal obs per cell per protocol between periodes if requested
if equal_protocol_density_per_cell:
    indices_to_drop = utils.get_equal_protocol_density(ndff_database=ndff_sel, hok_type=hok, periode_labels=labels)
    ndff_sel.drop(indices_to_drop, axis=0, inplace=True)
    print('\tOutgoing: {0}'.format(ndff_sel.shape[0]))

#==================================================================================================================#
# Dilute NDFF to equal obs per cell between periodes, regardless of protocol, if requested
elif equal_obs_per_cell:
    indices_to_drop = utils.get_equal_obs_per_cell(ndff_database=ndff_sel, hok_type=hok, periode_labels=labels)
    ndff_sel.drop(indices_to_drop, axis=0, inplace=True)
    print('\tOutgoing: {0}'.format(ndff_sel.shape[0]))

#==================================================================================================================#
# Dilute NDFF to equal obs between periodes, regardless of protocol or count per cell, if requested
elif equal_obs_per_period:
    obs_count = pd.pivot_table(ndff_sel, index='periode', values='count', aggfunc='sum')  # nr of obs per periode
    surplus = np.abs(np.subtract(obs_count[labels[0]], obs_count[labels[1]]))  # surplus of observations

    if surplus > 0:
        surplus_periode = obs_count.loc[obs_count == obs_count.max()].index.tolist()[0]
        deficient_periode = obs_count.loc[obs_count == obs_count.min()].index.tolist()[0]

        print('Periode {0} has {1} obs, which is {2} more than periode {3} with {4}'.format(surplus_periode,
                                                                                            obs_count[surplus_periode],
                                                                                            surplus,
                                                                                            deficient_periode,
                                                                                            obs_count[deficient_periode]))

        indices_to_drop = np.random.choice(ndff_sel[ndff_sel['periode'] == surplus_periode].index, size=surplus,
                                           replace=False)
        ndff_sel.drop(indices_to_drop, axis=0, inplace=True)

        print('Removed {0} observations for equal obs between periodes, '.format(surplus))
    else:
        print('Equal observations between periodes already achieved.')

else:
    indices_to_drop = []

ndff_sel_post_size = ndff_sel.shape[0]

#==================================================================================================================#
# summarize results via several piv tables

# nr species per hok for each period
hok_piv = pd.pivot_table(ndff_sel, index=hok, columns='periode', values='nl_name', aggfunc=lambda x: len(x.unique()))

# nr obs per hok for each period
obs_piv = pd.pivot_table(ndff_sel, index=hok, columns='periode', values='count', aggfunc='sum')

# nr protocols per hok for each period
prt_piv = pd.pivot_table(ndff_sel, index=hok, columns='periode', values='protocol', aggfunc=lambda x: len(x.unique()))

# merge above 3 pivs into single df
tmp_df = pd.merge(left=hok_piv.rename(columns=dict(zip(labels, [label + '_sp_count' for label in labels]))),
                  right=obs_piv.rename(columns=dict(zip(labels, [label + '_obs_count' for label in labels]))),
                  how='left', left_index=True, right_index=True)
hok_df = pd.merge(left=tmp_df, how='left', left_index=True, right_index=True,
                  right=prt_piv.rename(columns=dict(zip(labels, [label+'_protocol_count' for label in labels]))))

# difference in species count per hok between two periods
hok_df['sp_count_diff'.format(hok)] = hok_df.apply(lambda row: np.subtract(row[labels[1]+'_sp_count'],
                                                                           row[labels[0]+'_sp_count']), axis=1)

# tally of how frequent difference occurs
diff_piv = pd.pivot_table(hok_df, values=labels[0]+'_sp_count', index='sp_count_diff', aggfunc='count')

# nr hokken per species for each period
spe_piv = pd.pivot_table(ndff_sel, index='nl_name', columns='periode', values=hok, aggfunc=lambda x: len(x.unique()))
spe_piv['trend'] = spe_piv.apply(lambda row: np.divide(row[labels[1]], row[labels[0]]).astype(np.float16), axis=1)

# =================================================================================================================#
# Write output to file(s)
t0 = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
t0_brief = datetime.datetime.now().strftime("%y%m%d-%H%M")
out_base_dir = r'd:\NW_out_data'
base_name = '-{0}-{1}-{2}'.format(groep, beheertypes, '-'.join([label for label in labels]))

if print_tables:
    out_name = 'Table{0}_{1}_{2}.csv'.format(base_name, hok, t0_brief)
    with open(os.path.join(out_base_dir, out_name), 'w') as f:
        # header
        f.write('# Tabulated extract from NDFF database, by Hans Roelofsen, {0}, WEnR team B&B.\n'.format(t0))
        f.write('# Following query from NDFF database resulted in {0} records:\n'.format(ndff_sel_size))
        f.write('#  Species taxgroup: {0}\n'.format(sp_info['taxgroep'][groep]))
        f.write('#  SNL Habitattype: {0}\n'.format(sp_info['habitattypes'][beheertypes]))
        f.write('#  Nulsoorten: {0}\n'.format(nulsoort))
        f.write('#  area < {0}\n'.format(utils.minimum_area(hok)))
        f.write('#  year in {0}\n'.format(utils.ranges_to_years(periodes)))
        f.write('# NDFF observations restricted to {0} meeting the following query: {1}, r'
                'esulting in {2} hokken\n'.format(hok, cells_query, str(hok_df.shape[0])))
        if equal_protocol_density_per_cell:
            f.write('# {0} out of {1} observations were removed at random from NDDF to achieve equal observations per '
                    'protocol per cell between periodes.\n'.format(len(indices_to_drop), ndff_sel_size))
        if equal_obs_per_cell:
            f.write('# {0} out of {1} observations were removed at random from NDDF to achieve equal '
                    'bservations per cell between periodes.\n'.format(len(indices_to_drop), ndff_sel_size))
        if equal_obs_per_period:
            f.write('# {0} out of {1} NDFF observations were removed at random from periode {2} to achieve equal '
                    'observations between periodes.\n'.format(len(indices_to_drop), ndff_sel_size, surplus_periode))

        f.write('# n Obs {0}: {1}, {2}: {3}\n'.format(labels[0], np.sum(hok_df['{0}_obs_count'.format(labels[0])]),
                                                  labels[1], np.sum(hok_df['{0}_obs_count'.format(labels[0])])))


        # hok as index dataframe
        f.write(hok_df.fillna(9999).astype(np.int32).to_csv(sep=';', header=True, index=True))

        # empty line, then difference histogram
        f.write(';' * len(periodes) + '\n' + ';' * len(periodes) + '\n')
        f.write(diff_piv.rename(columns={labels[0]+'_sp_count', 'difference_count'}).to_csv(sep=';', header=True,
                                                                                            index=True))
        # empty line, then species histogram
        f.write(';' * len(periodes) + '\n' + ';' * len(periodes) + '\n')
        f.write(spe_piv.fillna(0).astype(np.int32).to_csv(sep=';', header=True, index=True))

if print_diff_maps:
    # categorize difference into categories
    cats = [range(-1000, -1), range(-1, 2), range(2, 1000)]
    labs = ['-2 of nog minder', '-1, 0 of 1', '2 of nog meer']
    hok_df['diff_cat'] = hok_df['sp_count_diff'].apply(utils.classifier, args=(cats, labs))
    hok_gdf = pd.merge(left=cells_sel, right=hok_df, how='inner', left_on='ID', right_index=True)

    title = 'Toe/Afname van {0} gedurende {1} - {2}'.format(groep, labels[0], labels[1])
    out_name = 'Map_{0}_{1}_{2}.png'.format(base_name, hok, t0_brief)
    export_shape.diff_to_png(gdf=hok_gdf, col='diff_cat', cats=dict(zip(labs, ['red', 'white', 'green'])),
                             title=title, comment='', background=False, background_cells=cells_sel,
                             out_dir=out_base_dir, out_name=out_name)