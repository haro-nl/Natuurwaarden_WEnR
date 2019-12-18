# script for plotting species count difference per cell per periode
# Hans Roelofsen, WEnR 6 feb 2019

import os
import pandas as pd

from nw import utils
from nw import export_shape

# Constraints on NDFF observations
hok = 'kmhok'  # either uurhok, kmhok. TODO: Extent to duplohok, quartohok
min_area = {'kmhok':2500000, 'uurhok':1e9}[hok] # 2500000 for km hokken! 1e9 for uurhokken
protocol_excl = ['12.205 Monitoring Beoordeling Natuurkwaliteit EHS - N2000 (SNL-2014)']
nulsoort = False # include nulsoorten: True or False
groep = 'vaatplant'  # one of following['broedvogel', 'dagvlinder', 'vaatplant', 'herpetofauna', 'all']
periode_1 = 'N2003-2012'  # start-end year inclusive!
periode_2 = 'N2013-2018'  # start-end year inclusive!
beheertype = 'snl_hoogveen'  # either one of: 'snl_vochtige_heide' 'snl_zwakgebufferd_ven', 'snl_zuur_ven_of_hoogveenven',  'snl_droge_heide',
                    # 'snl_zandverstuiving', 'snl_hoogveen, 'all'

sp_info = utils.get_sp_info()
sp_sel = set(sp_info[groep]['sp_nm']) & set(sp_info[beheertype]['sp_nm']) & set(sp_info['nulsoort'][nulsoort]['sp_nm'])

# get raw ndff data and filter on observation specs, such as area, protocol.
# also narrow down to species from the selected species (ie. soortgroep, SNL subtype, nulsoort)
ndff = utils.get_ndff_full()
quer = 'protocol not in {0} & area < {1} & nl_name in {2}'.format(protocol_excl, min_area, list(sp_sel))
ndff.query(quer, inplace=True)

# Contraints on cells
heide_periode_in = 2012  # reference year for heide presence in cells, either 1900 or 2012
heide_treshold_in = 1  # % of cell in year constaining heide. 0 if all values are ok
oz_groep_in = utils.get_soortgroep_afkorting(groep)
oz05_treshold_in = 75  # drempelwaarde voor onderzoeksvolledigheid periode 1998-2007. 0 if all values are ok
oz18_treshold_in = 75  # drempelwaarde voor onderzoeksvolledigheid periode 2008-2018. 0 if all values are ok
plot_background = False  # Boolean, plot cells in output graph
beheertype_in_titel = True
comment_text = 'exclusief protocols' + ', '.join([protocol for protocol in protocol_excl])

# margins for equality
# cats = {'<0':range(-1000, 0), '0':range(0,1), '>0':range(1, 1000)}
cats= [range(-1000, -1), range(-1,2), range(2,1000)]
labs= ['-2 of nog minder', 'tussen -1 en 1', '2 of meer']
def classifier(x, categories, labels):
    # cats = [v for k,v in categories.items()]
    # labs = [k for k,v in categories.items()]
    try:
        return labs[[x in range for range in cats].index(True)]
    except ValueError:
        raise Exception('Sorry, requested value {0} is not found in any of the ranges.'.format(x))

# out directory
out_base_dir = r'd:\NW_out_data\20190218\minus_12-205'


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
                right_index=True, left_index=True, how='inner')
diff['diff'] = diff[periode_2] - diff[periode_1]
diff['diff_cat'] = diff['diff'].apply(classifier, args=(cats, labs))

# remerge to original cells dataframe
merged = pd.merge(cells, diff, left_on='ID', right_index=True, how='inner')

title = 'Toe/Afname {0} in {1}, {2}-{3}'.format(groep, beheertype, periode_1, periode_2)
out_name = '{0}_{1}_{2}-{3}-diff_heide{4}-{5}_' \
           'oz{6}05-{7}_oz{8}18-{9}_{10}'.format(hok, groep, periode_1, periode_2, heide_periode_in,
                                                     heide_treshold_in, oz_groep_in, oz05_treshold_in, oz_groep_in,
                                                     oz18_treshold_in, beheertype)

# merged.drop('geometry', axis=1).to_csv(os.path.join(out_base_dir, 'csv', out_name + '.csv'), sep=';', index=False)

if not merged.empty:
    print('{0} cells will be written to file for diff {1}-{2}'.format(merged.shape[0], periode_1, periode_2))
    export_shape.diff_to_png(gdf=merged, col='diff_cat', cats= dict(zip(labs, ['red', 'white', 'green'])), title=title,
                             comment=comment_text, background=plot_background, background_cells=cells,
                             out_dir=os.path.join(out_base_dir, 'png'), out_name=out_name)
    merged.to_file(os.path.join(out_base_dir, 'shp', '{0}.shp'.format(out_name)))
else:
    print('Empty dataframe produced for period {0}, bummer'.format(periode_1))