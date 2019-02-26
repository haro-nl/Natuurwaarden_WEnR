#======================================================================================================================#
# script for generating several tables of NDFF data
#   number of observations per period
#   number of unique species per cell per period, plus difference
#   tally of differences
#   number of cells per species per period
#
# Table content can be can restricted to NDFF observations meeting some criteria, or cells meeting some criteria.
#
# Observation selection criteria
# km or uurhok, minimum area, sampling protocol, include nulsoort, species group, beheertype
#
# cell selection criteria
# onderzoeksvolledigheid per soortgroep voor periodes 1998-2007 and 2008-2018
# areaal heide volgens LGN in 1900 en 2012
# areaal SBB beheerd land
#
# Hans Roelofsen, WEnR, 20 feb 2019
#======================================================================================================================#

import os
import datetime
import numpy as np
import pandas as pd

from nw import utils

#======================================================================================================================#
# Constraints on NDFF observations
hok = 'kmhok'        # one of: uurhok, kmhok.
min_area = {'kmhok': 2500000, 'uurhok': 1e9}[hok]
protocol_excl = []
nulsoort = False     # include nulsoorten: True or False
groep = 'vaatplant' # one of: 'broedvogel', 'dagvlinder', 'vaatplant', 'herpetofauna', 'all'
beheertypes = ['snl_vochtige_heide', 'snl_zwakgebufferd_ven', 'snl_zuur_ven_of_hoogveenven',  'snl_droge_heide',
               'snl_zandverstuiving', 'snl_hoogveen', 'all']
periodes = [range(2007, 2013), range(2013, 2019)]
labels = ['N2007-2012', 'N2013-2018']

#======================================================================================================================#
# Contraints on cells
heide_periode_in = 2012   # reference year for heide presence in cells, either 1900 or 2012
heide_treshold_in = 7.5   # % of cell in year constaining heide. 0 if all values are ok
oz05_treshold_in = 75     # drempelwaarde voor onderzoeksvolledigheid periode 1998-2007. 0 if all values are ok
oz18_treshold_in = 75     # drempelwaarde voor onderzoeksvolledigheid periode 2008-2018. 0 if all values are ok
sbb_area_treshold = 0   # drempelwaarde voor SBB areaal in de cell. Evaluation is <=. 100 if all values are ok

#======================================================================================================================#
# Harmonize observation count per cell between periods
equal_protocol_density = True

#======================================================================================================================#
# Create table for selection, per beheertype
for beheertype in beheertypes:

    #==================================================================================================================#
    # get requested cell type and narrow down
    cells = utils.get_hok_gdf_simple(hok_type=hok)
    cells_quer = '{0}_oz05 >= {1} & {0}_oz18 >= {2} & heide{3} >= {4} & sbb_aream2 <= {5}'.format(utils.get_soortgroep_afkorting(groep),
                                                                                                  oz05_treshold_in,
                                                                                                  oz18_treshold_in,
                                                                                                  heide_periode_in,
                                                                                                  heide_treshold_in,
                                                                                                  sbb_area_treshold)
    cells_sel = cells.query(cells_quer)

    #==================================================================================================================#
    # Get full NDFF, filter down and add periode column showing periode label based on observation year
    sp_info = utils.get_sp_info()
    ndff = utils.get_ndff_full()

    sp_sel = set(sp_info[groep]['sp_nm']) & set(sp_info[beheertype]['sp_nm']) & set(sp_info['nulsoort'][nulsoort]['sp_nm'])

    ndff_quer = 'protocol not in {0} & area < {1} & nl_name in {2} & year in {3} & {4} in {5}'.format(protocol_excl,
                                                                                                      min_area,
                                                                                                      list(sp_sel),
                                                                                                      utils.ranges_to_years(periodes),
                                                                                                      hok,
                                                                                                      list(cells_sel['ID']))
    ndff_sel = ndff.query(ndff_quer)
    ndff_sel['periode'] = ndff_sel['year'].apply(utils.classifier, args=(periodes, labels))
    ndff_sel['count'] = 1

    #==================================================================================================================#
    # create piv tables and calculate trends if table is not empty

    def sample_ndff(row):
        # returns *obs_diff* indices from ndff_sel of observations corresponding to certain period, protocol and hok ID
        periode_to_trim = utils.classifier(row.obs_diff, [range(1, 100000), range(-100000, 0)], labels)
        subset = ndff_sel.loc[(ndff_sel[hok] == row.kmhok_id) &
                              (ndff_sel['periode'] == periode_to_trim) &
                              (ndff_sel['protocol'] == row.protocol), :]
        if subset.shape[0] > np.abs(row.obs_diff):
            return subset.sample(np.abs(row.obs_diff), replace=False).index.tolist()
        else:
            raise Exception('Requested sample size {0} exceeds ndff records '
                            'complying to query: {1}.'.format(row.obs_diff, subset.shape[0]))

    if equal_protocol_density:
        # trim NDFF observations to ensure equal nr of obs for each protocol in each hok

        # Piv tab of protocl counts per periode (columns) for each hok (index)
        prt_piv = pd.pivot_table(ndff_sel, values='count', index=hok, columns= ['periode', 'protocol'], aggfunc='sum')

        # Subtract two periods to calc diff in nr of observations per hok (index) per protocol (columns)
        prt_diff = prt_piv.loc[:, labels[0]].subtract(prt_piv.loc[:, labels[1]]) # <0 means more obs in P2
        prt_diff['kmhok_id'] = prt_diff.index

        # Do the magic to create df with cols: kmhok_id, protocol, diff_obs. Note repetition in cols[:1]
        prt_df = pd.melt(prt_diff, id_vars=['kmhok_id'], var_name='protocol', value_name='obs_diff')  # FUCK YEAH!
        prt_df.drop(prt_df.loc[(prt_df['obs_diff'] == 0) | (prt_df['obs_diff'].isnull())].index, inplace=True, axis=0)

        # sample ndff_sel for X indices to drop for each cell/protocol combination
        indices_to_drop = [item for sublist in prt_df.apply(sample_ndff, axis=1).tolist() for item in sublist]
        if len(indices_to_drop) > len(set(indices_to_drop)):
            raise Exception('List of {0} IDs nominated for removal contains duplicates. Should not be!'.format(hok))

        # drop all selected indices from ndff_sel
        ndff_sel.drop(indices_to_drop, axis=0, inplace=True)

        # TODO: report on difference before and after drop!

    hok_piv = pd.pivot_table(ndff_sel, values='nl_name', index=hok, columns='periode', aggfunc=lambda x: len(x.unique()))
    obs_piv = pd.pivot_table(ndff_sel, values='count', index='periode', aggfunc='sum')
    spe_piv = pd.pivot_table(ndff_sel, values=hok, index='nl_name', columns='periode', aggfunc=lambda x: len(x.unique()))

    if not obs_piv.empty:
        hok_piv['{0}_count_difference'.format(hok)] = hok_piv.apply(lambda row: np.subtract(row[labels[1]],
                                                                                            row[labels[0]]), axis=1)
        diff_piv = pd.pivot_table(hok_piv, values=labels[0], index='{0}_count_difference'.format(hok), aggfunc='count')
        spe_piv['trend'] = spe_piv.apply(lambda row: np.divide(row[labels[1]], row[labels[0]]), axis=1)

    #==================================================================================================================#
    # Write tables to file
    t0 = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_base_dir = r'd:\NW_out_data\tabs_per_kmhok\excl_sbb_incl_snl'
    base_name = 'Tabel-{0}-{1}-{2}_'.format(groep, beheertype, '-'.join([label for label in labels]))

    with open(os.path.join(out_base_dir, base_name+hok+'.csv'), 'w') as f:
        f.write('# Tabulated extract from NDFF database, by Hans Roelofsen, {0}, WEnR team B&B.\n'.format(t0))
        f.write('# Query from NDFF database was: {0}\n'.format(ndff_quer[:ndff_quer.index(hok)]))
        f.write('# Plus NDFF observations restricted to {0} meeting the following query: {1}\n'.format(hok, cells_quer))
        if not obs_piv.empty:
            f.write(hok+';'+';'.join(col for col in list(hok_piv))+'\n')
            f.write('obs_count;'+';'.join([str(obs_piv[label]) for label in labels])+'\n')
            f.write(hok_piv.fillna(9999).astype(np.int32).to_csv(sep=';', header=False, index=True))
            f.write(';' * len(periodes) + '\n' + ';' * len(periodes) + '\n')
            f.write(diff_piv.rename(columns={labels[0], 'difference_count'}).to_csv(sep=';', header=True, index=True))
            f.write(';' * len(periodes) + '\n' + ';' * len(periodes)+'\n')
            f.write(spe_piv.fillna(0).astype(np.int32).to_csv(sep=';', header=True, index=True))
        else:
            f.write(hok + ';' + ';'.join(label for label in labels) + '\n')
            f.write('obs_count;'+';'.join([str(0)]*len(periodes))+'\n')