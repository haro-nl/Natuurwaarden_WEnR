""""Script to read a mesh shapefile (e.g. uurhokken) and add as attribute:
Species count per cell given certain conditions.

Script for set B: per soortgroepen voor periodes voor uur en km hokken

Hans Roelofsen, 18 december 2018 WEnR"""


import os
import datetime
import pandas as pd
import sys
# sys.path.extend(['M:\\B_aux\\geopandas', 'M:/B_aux/geopandas'])
import geopandas as gp

from nw import utils
from nw import export_shape

# read NDFF observations
ndff = pd.read_csv(os.path.join(r'm:\a_Projects\Natuurwaarden\intermediate_data', 'ndff_b2_all.csv'))

## UURHOKKEN
uh_dir_in = r'd:\NW_src_data'
uh_shp_in = 'uurhok_prov.shp'
uh_orig = gp.read_file(os.path.join(uh_dir_in, uh_shp_in))

## KILOMETERHOKKEN
kh_dir_in = r'd:\NW_src_data'
kh_shp_in = 'kmhok_prov.shp'
kh_orig = gp.read_file(os.path.join(kh_dir_in, kh_shp_in))

# define periodes here! The dictionary key will be the attribute name!
periodes = {'N1935-1948': [j for j in range(1935, 1949)],
            'N1949-1962': [j for j in range(1949, 1963)],
            'N1963-1976': [j for j in range(1963, 1977)],
            'N1977-1990': [j for j in range(1977, 1991)],
            'N1991-2004': [j for j in range(1991, 2005)],
            'N2005-2018': [j for j in range(2005, 2019)],
            'N1987-1994': [j for j in range(1987, 1995)],
            'N1995-2002': [j for j in range(1995, 2003)],
            'N2003-2010': [j for j in range(2003, 2011)],
            'N2011-2018': [j for j in range(2011, 2019)]}

tax_groepen = ['vaatplant', 'broedvogel', 'dagvlinder', 'vaatplant', 'herpetofauna', 'all']

out_dir = r'd:\NW_out_data\b_per_tax\20190202\1a'

for k, v in periodes.items():
    for groep in tax_groepen:
        if groep == 'all':
            groep_list = ['vaatplant', 'broedvogel', 'dagvlinder', 'vaatplant', 'herpetofauna']
        else:
            groep_list = [groep]

        print("Periode {0} in progress at {1}".format(k, datetime.datetime.now().strftime("%Y%m%d_%H%M")))

        # ==uurhokken==
        ndff_sel = ndff.loc[(ndff['year'].isin(v)) &
                            (ndff['nulsoort'] == 0) &
                            (ndff['taxgroep'].isin(groep_list)), :]  # Additional selections here!

        # pivot table to make uurhok IDs the rownames, values are lenght of uniques of 'soort_ned'
        ndff_piv = pd.DataFrame(pd.pivot_table(ndff_sel, values = 'nl_name', index='uurhok', aggfunc=lambda x:len(x.unique())))

        # copy uurhokken shp and join on the uurhok ID, retaining only matching uurhok IDs
        uh = uh_orig.copy()
        merged = pd.merge(uh, ndff_piv, how='inner', right_index=True, left_on='ID')
        # merged.rename(columns={'nl_name':k}, inplace=True)

        # write to file
        if not merged.empty:
            uh_out_name = 'UH_{0}_{1}_{2}'.format(groep, k, datetime.datetime.now().strftime("%Y%m%d-%H%M"))

            merged.to_file(os.path.join(out_dir, '{0}.shp'.format(uh_out_name)))
            # export_shape.to_png(gdf=merged, col=k, upper_bin_lims=utils.get_bins(groep, max(merged[k])), title=uh_out_name.replace('_', ' '),
            #               out_dir=out_dir, out_name='{0}.png'.format(uh_out_name), heide=False, oz_volledigheid=False,
            #               vlinder_oz_volledigheid=False)

        del ndff_piv, ndff_sel, merged, uh


        # ==kmhokken==
        ndff_sel = ndff.loc[(ndff['year'].isin(v)) &
                            (ndff['area'] < 2500000) &
                            (ndff['nulsoort'] == 0) &
                            (ndff['taxgroep'] == groep), :]

        # pivot table to make kmhok IDs the rownames, values are lenght of uniques of 'soort_ned'
        ndff_piv = pd.DataFrame(pd.pivot_table(ndff_sel, values = 'nl_name', index='kmhok', aggfunc=lambda x:len(x.unique())))

        # copy kmhokken shp and join on the kmhok ID
        kh = kh_orig.copy()
        merged = pd.merge(kh, ndff_piv, how='inner', right_index=True, left_on='ID')
        merged.rename(columns={'nl_name':k}, inplace=True)

        # write to file
        if not merged.empty:
            kh_out_name = 'KH_{0}_{1}_{2}'.format(groep, k, datetime.datetime.now().strftime("%Y%m%d-%H%M"))

            # merged.to_file(os.path.join(out_dir, '{0}.shp'.format(kh_out_name)))
            # export.to_png(gdf=merged, col=k, upper_bin_lims=nw.get_bins(groep, max(merged[k])), title=kh_out_name,
            #               out_dir=out_dir, out_name='{0}.png'.format(kh_out_name), heide=False, oz_volledigheid=False,
            #               vlinder_oz_volledigheid=False)


