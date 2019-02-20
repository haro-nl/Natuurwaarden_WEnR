# short script to add SBB owned areas as attribute to km and uurhokken
# Hans Roelofsen, WEnR, 19 feb 2019


import sys
import os
import pandas as pd
import numpy as np

sys.path.extend(['M:\\b_aux\\python\\clones\\geopandas_master', 'M:/b_aux/python/clones/geopandas_master'])
import geopandas as gp


sbb = gp.read_file(r'd:\NW_src_data\sbb\sbb_terreinen_2019.shp')
kh = gp.read_file(r'm:\a_Projects\Natuurwaarden\intermediate_data\uh_kh_compleet\kmhok_compleet.shp')
uh = gp.read_file(r'm:\a_Projects\Natuurwaarden\intermediate_data\uh_kh_compleet\uurhok_compleet.shp')


kh['all_oz18'] = kh.apply(lambda row: min(row['vog_oz18'],  row['vli_oz18'], row['rep_oz18'], row['plnt_oz18']), axis=1)
kh['all_oz05'] = kh.apply(lambda row: min(row['vog_oz05'],  row['vli_oz05'], row['rep_oz05'], row['plnt_oz05']), axis=1)
uh['all_oz18'] = uh.apply(lambda row: min(row['vog_oz18'],  row['vli_oz18'], row['rep_oz18'], row['plnt_oz18']), axis=1)
uh['all_oz05'] = uh.apply(lambda row: min(row['vog_oz05'],  row['vli_oz05'], row['rep_oz05'], row['plnt_oz05']), axis=1)
kh.to_file(r'm:\a_Projects\Natuurwaarden\intermediate_data\uh_kh_compleet\kmhok_compleet.shp')
uh.to_file(r'm:\a_Projects\Natuurwaarden\intermediate_data\uh_kh_compleet\uurhok_compleet.shp')

# intersect = gp.overlay(kh, sbb.loc[sbb.area > 1], how='intersection')
# intersect.drop([lab for lab in list(intersect) if lab not in ['ID', 'geometry']], inplace=True, axis=1)
# intersect['sbb_aream2'] = intersect.area
# intersect_diss = intersect.dissolve(by='ID', aggfunc='sum')
# out = pd.merge(left=kh, right=intersect_diss.drop('geometry', axis=1), left_on='ID', right_index=True, how='left')
# print(out.head())
# print(out.shape)
# print(uh.shape)
# kh.sbb_aream2.fillna(0, inplace=True)
# kh.to_file(r'm:\\a_Projects\Natuurwaarden\intermediate_data\uh_kh_compleet\kmhok_compleet_2.shp')
