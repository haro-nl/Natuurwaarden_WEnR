import os
import numpy as np
from geopandas_master import geopandas as gp
import rasterstats

from nw import utils

# quick and not so nice script to extract heide and zandverstuiving cell counts from Historisch Grond Gebruik NL (HGN)
# and associate with uurhokken and km hokken
# Hans Roelofsen, 13 december 2018
# WEnR

# uurhokken empty shp in
uh_dir_in = r'd:\NW_src_data'
uh_shp_in = 'uurhok_prov.shp'
uh_orig = gp.read_file(os.path.join(uh_dir_in, uh_shp_in))
uh = uh_orig.copy()

# km hokken empty shp in
kh_dir_in = r'd:\NW_src_data'
kh_shp_in = 'kmhok_prov.shp'
kh_orig = gp.read_file(os.path.join(kh_dir_in, kh_shp_in))
kh = kh_orig.copy()

# directory and tiff of land use rasters
hgn_dir = r'd:\NW_src_data\hgn'
hgn1900 = 'HGN_1900.tif'
hgn2012 = 'LGN7.tif'

# list of uurhok and km hok IDs
uh_ids = uh.ID.tolist()
kh_ids = kh.ID.tolist()


def get_heide_perc(zonal_stat, cats):
    # gets heide as % of all raster cells within a hok, based on zonal statistics categories
    if len(zonal_stat) > 0:
        tot = np.sum([v for k,v in zonal_stat.items()])
        heide = np.sum([v for k,v in zonal_stat.items() if k in cats])
        out = np.prod([np.divide(heide, tot), 100], dtype=np.float32)
    else:
        out = 0
    return out


def get_heide(dat, cell_id):
    # function to get the heide value, used in the 'apply' function
    try:
        return dat[cell_id]['heide_hdr']
    except KeyError:
        return 0

# Land Use categories for HGN1900 and LGN7
cmap_hgn = {3:'heide_hoogveen', 9:'stuifduinen',1:'grasland',2:'akkers_kale_grond', 4:'loofbos', 6:'bebouwing',
        7:'water', 8:'rietmoeras', 12:'bebouwd_gebied', 13:'kassen', 0:'no_data'}

cmap_lgn = {35:'stuifzand',
            36:'heide',
            37:'matig_vergraste_heide',
            38:'sterk_vergraste_heide',
            39:'hoogveen',
            41:'overige moerasvegetatie'}

# the land use categories that we believe contain heide, ie the relevant categories
heide_cats = [cmap_hgn[3], cmap_hgn[9], ] + [v for k,v in cmap_lgn.items()]

# uurhokken - heide in 1900
uh_heide_1900 = rasterstats.zonal_stats(uh.geometry, os.path.join(hgn_dir, hgn1900), categorical=True,
                                       category_map=cmap_hgn)
for stat in uh_heide_1900:
    stat['heide_hdr'] = get_heide_perc(stat, heide_cats)
uh_heide_1900 = dict(zip(uh_ids, uh_heide_1900))

# kmhok - heide in 1900
kh_heide_1900 = rasterstats.zonal_stats(kh.geometry, os.path.join(hgn_dir, hgn1900), categorical=True,
                                       category_map=cmap_hgn)
for stat in kh_heide_1900:
    stat['heide_hdr'] = get_heide_perc(stat, heide_cats)
kh_heide_1900 = dict(zip(kh_ids, kh_heide_1900))

# uurhok - heide in 2010 (LGN7)
uh_heide_2012 = rasterstats.zonal_stats(uh.geometry, os.path.join(hgn_dir, hgn2012), categorical=True,
                                       category_map=cmap_lgn)
for stat in uh_heide_2012:
    stat['heide_hdr'] = get_heide_perc(stat, heide_cats)
uh_heide_2012 = dict(zip(uh_ids, uh_heide_2012))

# kmhok - heide in 2012
kh_heide_2012 = rasterstats.zonal_stats(kh.geometry, os.path.join(hgn_dir, hgn2012), categorical=True,
                                       category_map=cmap_lgn)
for stat in kh_heide_2012:
    stat['heide_hdr'] = get_heide_perc(stat, heide_cats)
kh_heide_2012 = dict(zip(kh_ids, kh_heide_2012))


# append to empty uurhok file
uh['heide1900'] = uh.apply(lambda row: get_heide(uh_heide_1900, row['ID']), axis=1)
uh['heide2012'] = uh.apply(lambda row: get_heide(uh_heide_2012, row['ID']), axis=1)
uh.to_file(r'm:\a_Projects\Natuurwaarden\intermediate_data\hgn_heide\uurhok_heide.shp')

kh['heide1900'] = kh.apply(lambda row: get_heide(kh_heide_1900, row['ID']), axis=1)
kh['heide2012'] = kh.apply(lambda row: get_heide(kh_heide_2012, row['ID']), axis=1)
kh.to_file(r'm:\a_Projects\Natuurwaarden\intermediate_data\hgn_heide\kmhok_heide.shp')


