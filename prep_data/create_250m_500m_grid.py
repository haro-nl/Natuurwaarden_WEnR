## Scratch file for generating 500 m and 250 m grids, based on the km hokken
# TODO: 20190110: Dit moet naar een nw directory, geen scratch
import os
from geopandas_master import geopandas as gp
import pandas as pd
from shapely import geometry

from nw import utils

def create_500m_hok(xy):
    # define X,Y coordinates of four squares (a, b, c, d) around point xy
    # a, b, c, d are positioned from top left, counter clockwise around xy
    # vertices of a, b, c, d are created starting bottom left, clockwise
    xcenter, ycenter = xy
    xmin, xmax = xcenter - 500, xcenter + 500
    ymin, ymax = ycenter - 500, ycenter + 500
    out = {}
    out['a'] = [(xmin, ycenter), (xcenter, ycenter), (xcenter, ymax), (xmin, ymax)]
    out['b'] = [(xcenter, ycenter), (xmax, ycenter), (xmax, ymax), (xcenter, ymax)]
    out['c'] = [(xcenter, ymin), (xmax, ymin), (xmax, ycenter), (xcenter, ycenter)]
    out['d'] = [(xmin, ymin), (xcenter, ymin), (xcenter, ycenter), (xmin, ycenter)]
    return out


def create_250m_hok(xy):
    # define X,Y coordinates of four squares (a, b, c, d) around point xy
    # a, b, c, d are positioned from top left, counter clockwise around xy
    # vertices of a, b, c, d are created starting bottom left, clockwise
    xcenter, ycenter = xy
    xmin, xmax = xcenter - 250, xcenter + 250
    ymin, ymax = ycenter - 250, ycenter + 250
    out = {}
    out['a'] = [(xmin, ycenter), (xcenter, ycenter), (xcenter, ymax), (xmin, ymax)]
    out['b'] = [(xcenter, ycenter), (xmax, ycenter), (xmax, ymax), (xcenter, ymax)]
    out['c'] = [(xcenter, ymin), (xmax, ymin), (xmax, ycenter), (xcenter, ycenter)]
    out['d'] = [(xmin, ymin), (xcenter, ymin), (xcenter, ycenter), (xmin, ycenter)]
    return out


## KILOMETERHOKKEN
kh_dir_in = r'd:\NW_src_data\subhokken'
kh_shp_in = 'duplos.shp'
kh_orig = gp.read_file(os.path.join(kh_dir_in, kh_shp_in))
kh = kh_orig.copy()

centroids = kh.centroid

ahok = gp.GeoDataFrame(crs = {"init": "epsg:28992"})
ahok['centerx'] = centroids.x
ahok['centery'] = centroids.y
ahok['geometry'] = ahok.apply(lambda row: geometry.Polygon(create_250m_hok((row['centerx'], row['centery']))['a']), axis=1)

bhok = gp.GeoDataFrame(crs = {"init": "epsg:28992"})
bhok['centerx'] = centroids.x
bhok['centery'] = centroids.y
bhok['geometry'] = bhok.apply(lambda row: geometry.Polygon(create_250m_hok((row['centerx'], row['centery']))['b']), axis=1)

chok = gp.GeoDataFrame(crs = {"init": "epsg:28992"})
chok['centerx'] = centroids.x
chok['centery'] = centroids.y
chok['geometry'] = chok.apply(lambda row: geometry.Polygon(create_250m_hok((row['centerx'], row['centery']))['c']), axis=1)

dhok = gp.GeoDataFrame(crs = {"init": "epsg:28992"})
dhok['centerx'] = centroids.x
dhok['centery'] = centroids.y
dhok['geometry'] = dhok.apply(lambda row: geometry.Polygon(create_250m_hok((row['centerx'], row['centery']))['d']), axis=1)

# concatenate
duplohok = pd.concat([ahok, bhok, chok, dhok])

# create new unique identifiers for all duplohokken
duplohok['centroid'] = duplohok.centroid
duplohok['ID'] = duplohok.apply(lambda row: nw.quartohok_id((row['centroid'].x, row['centroid'].y)), axis=1)

# drop confusing columns
duplohok = duplohok.drop(['centerx', 'centery', 'centroid'], 1)

# write to shapefile
duplohok.to_file(os.path.join(r'd:\NW_src_data\subhokken','quartohokken.shp'))


