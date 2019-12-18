"""Script to read NDFF data, add relevant attributes and store as csv
Hans Roelofsen, 3 December 2018"""

import os
import datetime
import pickle
import pandas as pd
import sys

sys.path.extend(['M:\\b_aux\\python\\clones\\geopandas_master', 'M:/b_aux/python/clones/geopandas_master'])
import geopandas as gp

from nw import utils

ndff_dir_in = r'd:\NW_src_data'


def date_to_year(date_in):
    date = datetime.datetime.strptime(date_in[:10], '%Y-%m-%d')
    return date.strftime('%Y')


def thing_is_in_group(thing, group):
    if thing in group:
        return 1
    else:
        return 0

def process_ndff(dir_in, shp_in):

    # read ndfff file
    ndff = gp.read_file(os.path.join(dir_in, shp_in), encoding='UTF-8')

    # check if centrumx and centrumy attributes are present, if not, create
    if not all([x in list(ndff) for x in ['centrumx', 'centrumy']]):
        # calculate centroid coordinates and area if not already present
        ndff['centroid'] = ndff.centroid
        ndff['centrumx'] = ndff.apply(lambda row: row['centroid'].x, axis=1)
        ndff['centrumy'] = ndff.apply(lambda row: row['centroid'].y, axis=1)
        ndff['area'] = ndff.area

    # drop columns
    ndff = ndff.drop([field for field in list(ndff) if field not in ['nl_name', 'sci_name', 'centrumx', 'centrumy',
                                                                     'area', 'loc_type', 'periodstop', 'broedcode',
                                                                     'protocol', 'broedcode']], 1)

    # convert species names to lowercase just to be sure
    ndff['nl_name'] = ndff['nl_name'].str.lower()

    # Add bunch of attributes
    ndff['kmhok'] = ndff.apply(lambda row: utils.kh_id((row['centrumx'], row['centrumy'])), axis=1)
    ndff['uurhok'] = ndff.apply(lambda row: utils.uh_id((row['centrumx'], row['centrumy'])), axis=1)
    ndff['duplohok'] = ndff.apply(lambda row: utils.duplohok_id((row['centrumx'], row['centrumy'])), axis=1)
    ndff['quartohok'] = ndff.apply(lambda row: utils.quartohok_id((row['centrumx'], row['centrumy'])), axis=1)
    ndff['year'] = ndff.apply(lambda row: date_to_year(row['periodstop']), axis=1)

    '''
    This is no longer needed, as these specs are filtered via the species list. 
    ndff['lpi'] = ndff.apply(lambda row: utils.try_get_sp_info(row['nl_name'], 'LPI', 0, sp_info),axis=1)
    ndff['snl'] = ndff.apply(lambda row: utils.try_get_sp_info(row['nl_name'], 'SNL', 0, sp_info),axis=1)
    ndff['taxgroep'] = ndff.apply(lambda row: utils.try_get_sp_info(row['nl_name'], 'tax_groep', 'unknown', sp_info),axis=1)
    ndff['snl_hoogveen'] = ndff.apply(lambda row: thing_is_in_group(row['nl_name'], sp_info['SNL_Hoogveen']['sp_nm']), axis=1)
    ndff['snl_vochtige_heide'] = ndff.apply(lambda row: thing_is_in_group(row['nl_name'], sp_info['SNL_Vochtige_heide']['sp_nm']), axis=1)
    ndff['snl_zwakbuf_ven'] = ndff.apply(lambda row: thing_is_in_group(row['nl_name'], sp_info['SNL_Zwakgebufferd_ven']['sp_nm']), axis=1)
    ndff['snl_zuur_hoogven'] = ndff.apply(lambda row: thing_is_in_group(row['nl_name'], sp_info['SNL_Zuur_ven_of_hoogveenven']['sp_nm']), axis=1)
    ndff['snl_droge_heide'] = ndff.apply(lambda row: thing_is_in_group(row['nl_name'], sp_info['SNL_Droge_heide']['sp_nm']), axis=1)
    ndff['snl_zandstuif'] = ndff.apply(lambda row: thing_is_in_group(row['nl_name'], sp_info['SNL_Zandverstuiving']['sp_nm']), axis=1)
    ndff['nulsoort'] = ndff.apply(lambda row: thing_is_in_group(row['nl_name'], sp_info['nulsoort']['sp_nm']), axis=1)
    '''
    return ndff


if __name__ == "__main__":

    shp_list = ['def_planten.shp', 'def_broedvogels.shp', 'def_dagvlinders.shp', 'def_reptielen.shp']

    pkl_dir = r'd:\temppickle'
    for shp in shp_list:
        out_temp = process_ndff(r'd:\NW_src_data\b2', shp)
        pickle_name = os.path.splitext(shp)[0] + datetime.datetime.now().strftime("%Y%m%d_%H%M") + '.pkl'
        with open(os.path.join(pkl_dir, pickle_name), 'wb') as handle:
            pickle.dump(out_temp, handle, protocol=pickle.HIGHEST_PROTOCOL)

    pkl_list = ['def_reptielen20190214_1057.pkl', 'def_dagvlinders20190214_1055.pkl', 'def_broedvogels20190214_1051.pkl',
                'def_planten20190214_1044.pkl']

    ndff_holder = []
    for pkl in pkl_list:
        with open(os.path.join(pkl_dir, pkl), 'rb') as handle:
            pikl = pickle.load(handle)
            ndff_holder.append(pikl)

    ndff_out = pd.concat([ndff for ndff in ndff_holder])
    ndff_out.to_csv(os.path.join(r'm:\a_Projects\Natuurwaarden\intermediate_data', 'ndff_all.csv'), index=False)