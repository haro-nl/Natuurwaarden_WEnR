# script for plotting species count difference per cell per periode
# Hans Roelofsen, WEnR 6 feb 2019

import os
import pandas as pd

from nw import utils
from nw import export_shape

# Constraints on NDFF observations
hok = 'kmhok'  # either uurhok, kmhok. TODO: Extent to duplohok, quartohok
min_area = 2500000 # 2500000 for km hokken! 1e9 for uurhokken # TODO: autmoatic lookup depending on hoktype
nulsoort = 0  # either 0 (nulsoorten are ignored) or 1 (nulsoorten are accepted)
groep = ['vaatplant'] #['broedvogel', 'dagvlinder', 'vaatplant', 'herpetofauna']  # one of following['broedvogel', 'dagvlinder', 'vaatplant', 'herpetofauna']
periode_1 = 'N2003-2012'
periode_2 = 'N2013-2018'  # periode 2 should be more recent in time than periode 1
beheertype = 'snl_zwakbuf_ven'  # either one of: 'snl_vochtige_heide' 'snl_zwakbuf_ven', 'snl_zuur_hoogven',
                                   # 'snl_droge_heide', 'snl_zandstuif', 'snl_hoogveen]
beheertype_val = [1]  # either [0,1] (alle beheertypen) or [1] (restrict selection to just *beheertype*

# Contraints on cells
heide_periode_in = 2012  # reference year for heide presence in cells, either 1900 or 2012
heide_treshold_in = 1  # % of cell in year constaining heide. 0 if all values are ok
oz_groep_in = utils.get_soortgroep_afkorting(groep[0])
oz05_treshold_in = 75  # drempelwaarde voor onderzoeksvolledigheid periode 1998-2007. 0 if all values are ok
oz18_treshold_in = 75  # drempelwaarde voor onderzoeksvolledigheid periode 2008-2018. 0 if all values are ok
plot_background = False  # Boolean, plot cells in output graph
beheertype_in_titel = True

# margins for equality
lims = [-2,2]
labs = [-1,0,1]
def classifier(x, limits, labels):
    foo = [x < y for y in limits] + [True]
    return labels[foo.index(True)]

# out directory
out_base_dir = r'd:\NW_out_data\b_per_tax\20190207\p2b'



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

# NDFF subset for each period
ndff_p1 = ndff.loc[ndff['year'].isin([j for j in range(int(periode_1[1:5]), int(periode_1[6:10])+1)]), :]
ndff_p2 = ndff.loc[ndff['year'].isin([j for j in range(int(periode_2[1:5]), int(periode_2[6:10])+1)]), :]

# pivot table for each period
p1_piv = pd.DataFrame(pd.pivot_table(ndff_p1, values='nl_name', index=hok, aggfunc=lambda x: len(x.unique())))
p2_piv = pd.DataFrame(pd.pivot_table(ndff_p2, values='nl_name', index=hok, aggfunc=lambda x: len(x.unique())))

# merge into new table, retain only cells w observations in both periods!
diff = pd.merge(left=p1_piv.rename(columns={'nl_name':periode_1}), right=p2_piv.rename(columns={'nl_name':periode_2}),
                right_index=True, left_index=True, how='outer')
diff['diff'] = diff[periode_2] - diff[periode_1]
diff['diff_cat'] = diff['diff'].apply(classifier, args=(lims, labs))

# remerge to original cells dataframe
merged = pd.merge(cells, diff, left_on='ID', right_index=True, how='left')

title = 'Toe/Afname {0} in {1}, {2}-{3}'.format(groep[0], beheertype, periode_1, periode_2)
out_name = '{0}_{1}_{2}-{3}-diff_heide{4}-{5}_' \
           'oz{6}05-{7}_oz{8}18-{9}_{10}-{11}'.format(hok, groep[0], periode_1, periode_2, heide_periode_in,
                                                     heide_treshold_in, oz_groep_in, oz05_treshold_in, oz_groep_in,
                                                     oz18_treshold_in, beheertype,
                                                      ''.join(str(val) for val in beheertype_val))
merged.drop('geometry', axis=1).to_csv(os.path.join(out_base_dir, 'csv', out_name + '.csv'), sep=';', index=False)

# if not merged.empty:
#     print('{0} cells will be written to file for diff {1}-{2}'.format(merged.shape[0], periode_1, periode_2))
    # export_shape.diff_to_png(gdf=merged, col='diff_cat', cats= dict(zip(labs, ['red', 'white', 'green'])), title=title,
    #                          background=plot_background, background_cells=cells,
    #                          out_dir=os.path.join(out_base_dir, 'png'), out_name=out_name)
    # merged.to_file(os.path.join(out_base_dir, 'shp', '{0}.shp'.format(out_name)))
# else:
#     print('Empty dataframe produced for period {0}, bummer'.format(periode_1))