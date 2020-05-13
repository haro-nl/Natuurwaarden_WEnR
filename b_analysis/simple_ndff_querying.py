"""
Script for simple queries and plots from NDFF
Hans Roelofsen, mei 2020
"""

import os
import pandas as pd
import geopandas as gp
from shapely.geometry import Point
from shapely.geometry import Polygon
from nw import utils
from nw import export_shape

# read the full ndff
ndff = utils.get_ndff_full()

# define queries that isolate the data of interest
sp = 'zwarte specht'
queries = {'q1': ndff.loc[(ndff.year > 2010) & (ndff.year.notna())].index,
           'q2': ndff.loc[ndff.nl_name.isin([sp])].index,
           'q3': ndff.loc[ndff.area < 185400].index,
           'q4': ndff.loc[ndff.centrumx.notna()].index,
           'q5': ndff.loc[ndff.centrumy.notna()].index}
sel = set.intersection(*[set(queries[x]) for x in queries.keys()])  # for query in selected_queries
assert len(sel) > 0, 'no observations remaining'

# pnt Shapefile with centroids
pnt_gdf = gp.GeoDataFrame(data=ndff.loc[sel], crs={'init': 'epsg:28992'},
                          geometry=[Point(x, y) for (x, y) in list(zip(ndff.loc[sel, 'centrumx'],
                                                                       ndff.loc[sel, 'centrumy']))]).assign(present=1)
export_shape.to_png(gdf=pnt_gdf, col='present', title='{} presentie puntsgewijs '.format(sp), out_dir=r'.\z_out',
                    out_name='{0}__presentie.png'.format(sp))

# ply Shapefile with observations aggregated to 1000 meter sided squares
side = 1000
mapper = ndff.loc[sel].assign(hok=[utils.sq_vert(pnt, size=side, ll_string=True) for pnt in
                                   zip(ndff.loc[sel, 'centrumx'], ndff.loc[sel, 'centrumy'])])
pdf = pd.pivot_table(data=mapper, index='hok', values='nl_name', aggfunc='count').assign(present=1)
sq1 = gp.GeoDataFrame(data=pdf, crs={'init': 'epsg:28992'}, geometry=[Polygon(vertices) for vertices in
                                                                      [utils.sq_vert(xy, size=side, vertices=True)
                                                                       for xy in pdf.index.tolist()]])
export_shape.to_png(gdf=sq1, col='present', title='{} presentie @ {}m hokken'.format(sp, side), out_dir=r'.\z_out',
                    out_name='{0}_{1}m_presentie.png'.format(sp, side))

# ply Shapefile with observations aggregated to 5000 meter sided squares
side = 5000
mapper = ndff.loc[sel].assign(hok=[utils.sq_vert(pnt, size=side, ll_string=True) for pnt in
                                   zip(ndff.loc[sel, 'centrumx'], ndff.loc[sel, 'centrumy'])])
pdf = pd.pivot_table(data=mapper, index='hok', values='nl_name', aggfunc='count').assign(present=1)
sq2 = gp.GeoDataFrame(data=pdf, crs={'init': 'epsg:28992'}, geometry=[Polygon(vertices) for vertices in
                                                                      [utils.sq_vert(xy, size=side, vertices=True)
                                                                       for xy in pdf.index.tolist()]])
export_shape.to_png(gdf=sq2, col='present', title='{} presentie @ {}m hokken'.format(sp, side), out_dir=r'.\z_out',
                    out_name='{0}_{1}m_presentie.png'.format(sp, side))
