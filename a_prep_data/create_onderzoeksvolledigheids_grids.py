# short script to generate oz volledigheid shp for km hokken for four tax groups,
# based on D:\NW_src_data\ozvolledigheid\export ozvolledigheid 1000m.csv
# Hans Roelofsen, WEnR, 18-12-2018

import os
import pandas as pd
from geopandas_master import geopandas as gp
import numpy as np

from nw import utils

# input data voor vlinders @ 250 m
# oz_dir_in = r'd:\NW_src_data\ozvolledigheid\dagvlinders'
# oz_in = 'oz_volledigheid_dagvlinders_250m.shp'
# oz = gp.read_file(os.path.join(oz_dir_in, oz_in))
#
# oz['centroid'] = oz.centroid
# oz['quartohok'] = oz.apply(lambda row: nw.quartohok_id((row['centroid'].x, row['centroid'].y)), axis=1)
# oz.head()
# oz = oz.drop(labels= 'centroid', axis=1)
# oz.to_file(os.path.join(r'm:\a_Projects\Natuurwaarden\intermediate_data\oz_volledigheid\vlinders_250m',
#                         'vlinder_oz_250m.shp'))

# voor alle groepen @ 1000 m periode 2008-2018 (p1)
oz_p1_dir_in = r'd:\NW_src_data\ozvolledigheid'
oz_p1_in = 'export ozvolledigheid 1000m.csv'
oz_p1 = pd.read_csv(os.path.join(oz_p1_dir_in, oz_p1_in), sep=";", usecols=[1,2,3,6])

oz_p1['kmhok'] = oz_p1.apply(lambda row: nw.kh_id((row['x']+1, row['y']+1)), axis=1)
oz_p1_piv = pd.DataFrame(pd.pivot_table(oz_p1, values='completeness', columns='kortenaam', index='kmhok', aggfunc=np.mean))
oz_p1_piv['kmhok'] = oz_p1_piv.index

cols = ['broedvogels', 'dagvlinders', 'reptielen', 'vaatplanten']
new_cols = ['vog_oz18', 'vli_oz18', 'rep_oz18', 'plnt_oz18']
oz_p1_piv.rename(columns=dict(zip(cols, new_cols)), inplace=True)

# voor alle groepen @ 1000 m periode 1995-2005 (p2)
oz_p2_dir_in = r'm:\a_Projects\Natuurwaarden\intermediate_data\oz_volledigheid\all_kmhok_1995-2005'
oz_p2_in = 'natuurloket Query.txt'
oz_p2 = pd.read_csv(os.path.join(oz_p2_dir_in, oz_p2_in), sep=';')
# multiply completeness scores 1:25, 2:50, 3:75, 4:100 for compatability with p1 data
oz_p2['vog_vol'] = oz_p2.apply(lambda row: np.multiply(row['vog_vol'], 25), axis=1)
oz_p2['rep_vol'] = oz_p2.apply(lambda row: np.multiply(row['rep_vol'], 25), axis=1)
oz_p2['vli_vol'] = oz_p2.apply(lambda row: np.multiply(row['vli_vol'], 25), axis=1)
oz_p2['pla_vol'] = oz_p2.apply(lambda row: np.multiply(row['pla_vol'], 25), axis=1)

# add km hok identifiers
oz_p2['kmhok'] = oz_p2.apply(lambda row: nw.kh_id((row['XRD']+1, row['YRD']+1)), axis=1)

# rename columns
cols = ['vog_vol', 'rep_vol', 'vli_vol', 'pla_vol']
new_cols = ['vog_oz05', 'rep_oz05', 'vli_oz05', 'plnt_oz05']
oz_p2.rename(columns=dict(zip(cols, new_cols)), inplace=True)

# merge oz_p1_piv and oz_p2 based on shared kmhok ID. Type = outer
merged = pd.merge(oz_p1_piv, oz_p2, on='kmhok', how='outer')
merged.drop(['XRD', 'YRD', 'km_id'], axis=1, inplace=True)

# read empty km hokken file
## KILOMETERHOKKEN
kh_dir_in = r'd:\NW_src_data'
kh_shp_in = 'kmhok_prov.shp'
kh_orig = gp.read_file(os.path.join(kh_dir_in, kh_shp_in))
kh = kh_orig.copy()

# merge completeness data to geodataframe of kmhokken
out = pd.merge(kh, merged, left_on='ID', right_on='kmhok', how='inner')
out.drop(['Join_Count', 'TARGET_FID', 'AREA', 'PERIMETER', 'KMHOK_', 'KMHOK_ID', 'X_COöRD', 'Y_COöRD', 'PROVINCIE'],
         axis=1, inplace=True)
out.fillna(0, inplace= True)
out.to_file(os.path.join(r'm:\a_Projects\Natuurwaarden\intermediate_data\oz_volledigheid\all_kmhok_2008-2018',
                            'oz_all_kh.shp'))



