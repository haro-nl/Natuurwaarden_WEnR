'''Script to calculate species count per cell based on NDFF waarnemingen
Hans Roelofsen, WEnR, feb 2019'''

import os
import pandas as pd

from nw import utils
from nw import export_shape

# Constraints on NDFF observations
hok = 'kmhok'  # either uurhok, kmhok. TODO: Extent to duplohok, quartohok
min_area = {'kmhok':2500000, 'uurhok':1e9}[hok] # 2500000 for km hokken! 1e9 for uurhokken
nulsoort = False # include nulsoorten: True or False
groep = 'vaatplant'  # one of following['broedvogel', 'dagvlinder', 'vaatplant', 'herpetofauna', 'all']
periodes = ['N2003-2012', 'N2013-2018']  # start-end year inclusive!
beheertype = 'all'    # either one of: 'snl_vochtige_heide' 'snl_zwakbuf_ven', 'snl_zuur_hoogven',
                                   # 'snl_droge_heide', 'snl_zandstuif', 'snl_hoogveen, 'all']

sp_sel = set(utils.get_sp_info()[groep]['sp_nm']) & set(utils.get_sp_info()[beheertype]['sp_nm']) & set(utils.get_sp_info()['nulsoort'][nulsoort]['sp_nm'])


# Contraints on cells
heide_periode_in = 2012  # reference year for heide presence in cells, either 1900 or 2012
heide_treshold_in = 1  # % of cell in year constaining heide. 0 if all values are ok
oz_groep_in = utils.get_soortgroep_afkorting(groep[0])
oz05_treshold_in = 75  # drempelwaarde voor onderzoeksvolledigheid periode 1998-2007. 0 if all values are ok
oz18_treshold_in = 75  # drempelwaarde voor onderzoeksvolledigheid periode 2008-2018. 0 if all values are ok
plot_background = False  # Boolean, plot cells in output graph
beheertype_in_titel = True


# out directory
out_base_dir = r'd:\NW_out_data\b_per_tax\20190207\p2b'

# get raw ndff data and filter
ndff = utils.get_ndff_full()
ndff = ndff.loc[(ndff['area'] < min_area) &
                (ndff['nl_name'].isin(sp_sel)), :]  #dit zou voldoende moeten zijn!!!!!11!!1112!@!!!@!!|214
                # (ndff['nulsoort'] == nulsoort) &
                # (ndff['taxgroep'].isin(groep)) &
                # (ndff[beheertype].isin(beheertype_val)), :]
        # TODO: nl_name.isin(alle soorten behorende bij groep or beheertype or nulsoort)

# get requested cell type and narrow down
cells = utils.get_hok_gdf(hok_type=hok, oz_taxgroup=oz_groep_in, oz05_treshold=oz05_treshold_in,
                          oz18_treshold=oz18_treshold_in, heide_periode=heide_periode_in,
                          heide_treshold=heide_treshold_in)
# TODO (optioneel) heide1900 en heide 2012 treshold, ipv heide periode en heide treshold


for periode in periodes:
    # generate out file name with full info
    if len(groep) > 1:
        bin_groep = 'all'
    else:
        bin_groep = groep[0]
    out_name = '{0}_{1}_{2}_heide{3}-{4}_' \
               'oz{5}05-{6}_oz{7}18-{8}_{9}-{10}'.format(hok, bin_groep, periode, heide_periode_in,
                                                         heide_treshold_in, oz_groep_in, oz05_treshold_in, oz_groep_in,
                                                         oz18_treshold_in, beheertype,
                                                         ''.join(str(val) for val in beheertype_val))

    # period coverage as integers
    periode_int = [j for j in range(int(periode[1:5]), int(periode[6:10])+1)]

    # reduce ndff data to requested period and pivot on requested cell type
    ndff_sel = ndff.loc[ndff['year'].isin(periode_int), :]
    ndff_piv = pd.DataFrame(pd.pivot_table(ndff_sel, values='nl_name', index=hok, aggfunc=lambda x: len(x.unique())))

    # merge with the cell geodataframe and rename column to standard name
    merged = pd.merge(cells, ndff_piv, how='inner', right_index=True, left_on='ID')
    merged.rename(columns={'nl_name':'sp_count'}, inplace=True)


    if not merged.empty:

        print('{0} cells will be written to file for periode {1}'.format(merged.shape[0], periode))

        # save to shp
        merged.to_file(os.path.join(out_base_dir, 'shp', '{0}.shp'.format(out_name)))

        # save to image
        title_neat= '{0}_{1}_{2}'.format(hok, bin_groep, periode)
        if beheertype_in_titel:
            title_neat += '_{0}'.format(beheertype)
        export_shape.to_png(gdf=merged, col='sp_count', upper_bin_lims=utils.get_bins(bin_groep),
                            title=title_neat, out_dir=os.path.join(out_base_dir, 'png'),
                            out_name='{0}.png'.format(out_name), background=plot_background, background_cells=cells)
    else:
        print('Empty dataframe produced for period {0}, bummer'.format(periode))
    # TODO: log file as output with full database query.

    del ndff_sel
    del ndff_piv