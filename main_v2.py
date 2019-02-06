'''Script to calculate species count per cell based on NDFF waarnemingen
Hans Roelofsen, WEnR, feb 2019'''

import os
import pandas as pd

from nw import utils
from nw import export_shape

# Constraints on NDFF observations
hok = 'kmhok'
min_area = 2500000 # 2500000 for km hokken! 1e9 for uurhokken
nulsoort = 0
groep = ['vaatplant']#['broedvogel', 'dagvlinder', 'vaatplant', 'herpetofauna']
periodes = ['N2003-2012', 'N2013-2018']
beheertype = 'snl_vochtige_heide'#, 'snl_zwakbuf_ven', 'snl_zuur_hoogven', 'snl_droge_heide', 'snl_zandstuif', 'snl_hoogveen]
beheertype_val = [0, 1]

# Contraints on cells
heide_periode_in = 2012
heide_treshold_in = 7.5  # 0 if all values are ok
oz_groep_in = utils.get_soortgroep_afkorting(groep[0])
oz05_treshold_in = 75  # 0 if all values are ok
oz18_treshold_in = 75  # 0 if all values are ok
plot_background = True


# out directory
out_base_dir = r'd:\NW_out_data\b_per_tax\20190206\part2b'

# get raw ndff data and filter
ndff = utils.get_ndff_full()
ndff = ndff.loc[(ndff['area'] < min_area) &
                (ndff['nulsoort'] == nulsoort) &
                (ndff['taxgroep'].isin(groep)) &
                (ndff[beheertype].isin(beheertype_val)), :]

# get requested cell type and narrow down
cells = utils.get_hok_gdf(hok_type=hok, oz_taxgroup=oz_groep_in, oz05_treshold=oz05_treshold_in,
                          oz18_treshold=oz18_treshold_in, heide_periode=heide_periode_in,
                          heide_treshold=heide_treshold_in)
# TODO (optioneel) heide1900 en heide 2012 treshold, ipv heide periode en heide treshold


for periode in periodes:
    # generate out file name with full info
    out_name = '{0}_{1}_{2}_heide{3}-{4}_' \
               'oz{5}05-{6}_oz{7}18-{8}_{9}-{10}'.format(hok, '-'.join(x for x in groep), periode, heide_periode_in,
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

    # save to shp
    merged.to_file(os.path.join(out_base_dir, 'shp', '{0}.shp'.format(out_name)))

    # save to image
    if len(groep) > 1:
        bin_groep = 'all'
    else:
        bin_groep = groep[0]
    title_neat= '{0}_{1}_{2}'.format(hok, bin_groep, periode)
    export_shape.to_png(gdf=merged, col='sp_count', upper_bin_lims=utils.get_bins(bin_groep),
                        title=title_neat, out_dir=os.path.join(out_base_dir, 'png'),
                        out_name='{0}.png'.format(out_name), background=plot_background, background_cells=cells)

    del ndff_sel
    del ndff_piv