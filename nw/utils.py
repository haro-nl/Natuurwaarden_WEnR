"""Several helper functies voor het Natuurwaarden project. Hans Roelofsen, 04 december 2018 WEnR"""

"""script to make species list information available as a dictionary in the broadest sense of the terms
Hans Roelofsen"""

import sys
import os
import pandas as pd
import numpy as np

sys.path.extend(['D:\\projects_code\\NW_WEnR\\geopandas_master', 'D:/projects_code/NW_WEnR/geopandas_master'])
import geopandas as gp

def iftrue(x):
    if x == 1:
        return 1
    else:
        return 0


def get_sp_info():
    # Read csv file with information on species, return as dictionary
    splist = pd.read_csv(os.path.join(r'd:\NW_src_data', 'soorten_lijst.txt'), sep=';')

    # convert species names to lowercase just to be sure
    splist['sp_nm'] = splist['sp_nm'].str.lower()

    out = {}

    # species names and numbers for each taxonomic group
    tax_groups = splist['tax_groep'].unique().tolist()
    for group in tax_groups:
        out[group] = {'sp_nm': splist.loc[splist['tax_groep'] == group, 'sp_nm'].tolist(),
                      'sp_nr': splist.loc[splist['tax_groep'] == group, 'sp_nr'].tolist()}

    # species names and numbers for each subhabitat
    habtypes = [x for x in list(splist) if 'SNL_' in x]
    for hab in habtypes:
        out[hab] = {'sp_nm': splist.loc[splist[hab] == 1, 'sp_nm'].tolist(),
                    'sp_nr': splist.loc[splist[hab] == 1, 'sp_nr'].tolist()}

    # species names and numbers for NW, LPI, SNL
    for ding in ['NW', 'LPI', 'SNL', 'nulsoort']:
        out[ding] = {'sp_nm': splist.loc[splist[ding] == 1, 'sp_nm'].tolist(),
                     'sp_nr': splist.loc[splist[ding] == 1, 'sp_nr'].tolist()}

    # all specs per species name and species nummer
    row_iterator = splist.iterrows()
    for i, row in row_iterator:
        # sp nr:sp naam, tax_groep, NW, LPI, SNL membership
        out[splist.loc[i, 'sp_nr']] = {'sp_nm': splist.loc[i, 'sp_nm'],
                                       'tax_groep': splist.loc[i, 'tax_groep'],
                                       'NW': iftrue(splist.loc[i, 'NW']),
                                       'LPI': iftrue(splist.loc[i, 'LPI']),
                                       'SNL': iftrue(splist.loc[i, 'SNL'])}

        # sp naam:sp nr, tax_groep, NW, LPI, SNL membership
        out[splist.loc[i, 'sp_nm']] = {'sp_nr': splist.loc[i, 'sp_nr'],
                                       'tax_groep': splist.loc[i, 'tax_groep'],
                                       'NW': iftrue(splist.loc[i, 'NW']),
                                       'LPI': iftrue(splist.loc[i, 'LPI']),
                                       'SNL': iftrue(splist.loc[i, 'SNL'])}

    return out


def try_get_sp_info(sp_name, sp_char, default, sp_info):
    # try to get species information
    try:
        return sp_info[sp_name][sp_char]
    except KeyError:
        return default


def get_hab_cels(hab_type, cell_type, all):
    return all.loc[(all[hab_type] == 1) &
                   (all['nulsoort'] == 1), cell_type].unique().tolist()


def kh_id(xy):
    # identify km hok in which point (*rdx*,*rdy*) resides as XXXYYY where
    # XXX = X-coord rounded down to thousands
    # YYY = Y-coord rounded down to thousands
    # e.g. point(117500,582500) lies in km hok 117582
    rdx, rdy = xy
    if rdx < rdy:
        head = np.prod([np.divide(rdx, 1000).astype(np.int32), 1000])
        tail = np.divide(rdy, 1000).astype(np.int32)
        out = np.sum([head, tail])
    else:
        print('In RDNew, the X coordinate must be smaller than the Y coordinate.')
        out = 0
    return out


def uh_id(xy):
    # idem for uurhokken, which are 5.000 m
    rdx, rdy = xy
    head = np.prod([divmod(rdx, 5000)[0], 5000]).astype(np.int32)
    tail = np.prod([divmod(rdy, 5000)[0], 5]).astype(np.int32)
    return np.sum([head, tail])


def duplohok_id(xy):
    # returns identified for a 500 m block as xxxxyyyy
    # xxxx = first four digits of x coordinate of hok lower left vertex
    # yyyy = first four digits of y coordinate of hok lower left vertex
    xcoord, ycoord = xy
    head = np.prod([divmod(xcoord, 500)[0], 5], dtype=np.int32)
    tail = np.prod([divmod(ycoord, 500)[0], 5], dtype=np.int32)
    return "{0}{1}".format(head, tail)


def quartohok_id(xy):
    # returns identifier for a 250 m block as xxxxxyyyyy
    # xxxxx = first five digits of x coordinate of hok lower left vertex
    # yyyyy = first five digits of y coordinate of hok lower left vertex
    xcoord, ycoord = xy
    head = np.prod([divmod(xcoord, 250)[0], 25], dtype=np.int32)
    tail = np.prod([divmod(ycoord, 250)[0], 25], dtype=np.int32)
    return "{0}{1}".format(head, tail)


def get_uh_heide_ids(year, treshold):
    # returns list of uh IDs where heide coveregage exceeds *treshold* in *year*
    if year in (1900, 2012):
        dat = gp.read_file(r'm:\a_Projects\Natuurwaarden\intermediate_data\hgn_heide\uurhok_heide.shp')
        return dat.loc[dat['heide{0}'.format(year)] > treshold, 'ID'].tolist()
    else:
        return []


def get_kh_heide_ids(year, treshold):
    # returns list of uh IDs where heide coveregage exceeds *treshold* in *year*
    if year in (1900, 2012):
        dat = gp.read_file(r'm:\a_Projects\Natuurwaarden\intermediate_data\hgn_heide\kmhok_heide.shp')
        return dat.loc[dat['heide{0}'.format(year)] > treshold, 'ID'].tolist()
    else:
        return []


def get_heide_gdf(hok, year, treshold):
    # return geodataframe of either km or uurhok where heide presence exceeds treshold
    # assumes location of source shapefiles.
    # Hans Roelofsen, 09 january 2019
    #
    # Retired 5 feb 2019
    if hok in ['uur', 'km']:
        dat = gp.read_file(r'm:\a_Projects\Natuurwaarden\intermediate_data\hgn_heide\{0}hok_heide.shp'.format(hok))
        return dat.loc[dat['heide{0}'.format(year)] > treshold, :]
    else:
        raise Exception('Give either uur or km hok, not {0}'.format(hok))


def get_uh_gdf(heide_periode, heide_treshold):
    dat = gp.read_file(r'm:\a_Projects\Natuurwaarden\intermediate_data\hgn_heide\uurhok_heide.shp')
    return dat.loc[dat['heide{0}'.format(heide_periode)] > heide_treshold, :]


def get_hok_gdf(hok_type, oz_taxgroup, oz05_treshold, oz18_treshold, heide_periode, heide_treshold):
    # return geodataframe of kh cells where completeness > treshold for period and tax group
    # period must be in: ['05', '18']
    # taxgroup must be in: ['vog', 'vli', 'plnt', 'rep']
    # treshold must be in: [0, 25, 50, 100]
    # assumes location of data

    if hok_type not in['uurhok', 'kmhok']:
        raise Exception('Hoktype must be in [uur, km], not {0}'.format(hok_type))
    if oz_taxgroup not in ['vog', 'vli', 'plnt', 'rep']:
        raise Exception('Taxgroup must be in [vog, vli, plnt, rep], not {0}'.format(oz_taxgroup))
    if any([x not in [0, 25, 50, 75, 100] for x in [oz05_treshold, oz18_treshold]]):
        raise Exception('Valid tresholds are 25, 50, 75 and 100, not {0} or {1}'.format(oz05_treshold, oz18_treshold))
    # TODO, check heide arguments for validity
    dat = gp.read_file(
        os.path.join(r'm:\a_Projects\Natuurwaarden\intermediate_data\uh_kh_compleet', '{0}_compleet.shp'.format(hok_type)))
    oz05_att = '{0}_oz05'.format(oz_taxgroup)
    oz18_att = '{0}_oz18'.format(oz_taxgroup)
    heide_att = 'heide{0}'.format(heide_periode)
    return dat.loc[(dat[oz05_att] >= oz05_treshold) &
                   (dat[oz18_att] >= oz18_treshold) &
                   (dat[heide_att] >= heide_treshold), :]


def get_vlinder_250m_completeness(treshold):
    # return onderzoekscompleetheid data voor vlinders voor 250 m hokken waar onderzoekscompleetheid >= treshold
    dat = gp.read_file(os.path.join(r'm:\a_Projects\Natuurwaarden\intermediate_data\oz_volledigheid\vlinders_250m',
                                    'vlinder_oz_250m.shp'))
    return dat.loc[dat['val'] >= treshold, :]


def get_bins(soortgroep):
    # return upper bin limits for choropleth mapping of tax groups
    bins = {'broedvogel': [2, 5, 10, 1000],
            'dagvlinder': [2, 5, 8, 1000],
            'herpetofauna': [2, 1000],
            'vaatplant': [5, 10, 20, 40, 1000],
            'all': [10, 20, 50, 1000],
            'single_sp': [1]}

    try:
        dat = bins[soortgroep]
    except KeyError:
        raise Exception('{0} is not a valid species groep, please select from: '.format(soortgroep) +
                        ', '.join(str(k) for k, v in bins.items()))
    # while max_val < dat[-1]:
        # make sure that the highest value is never contained in the bins, but generated to cap the last class
        # dat = dat[:-1]
    return dat


def get_ndff_full():
    return pd.read_csv(os.path.join(r'm:\a_Projects\Natuurwaarden\intermediate_data', 'ndff_b2_all.csv'))


def get_soortgroep_afkorting(soortgroep):
    dict = {'vaatplant': 'plnt', 'broedvogel': 'vog', 'dagvlinder': 'vli', 'herpetofauna': 'rep'}
    try:
        return dict[soortgroep]
    except KeyError:
        raise Exception('Thats numberwang')
