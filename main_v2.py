'''Script to calculate species count per cell based on NDFF waarnemingen
Hans Roelofsen, WEnR, feb 2019'''

import os
import pandas as pd

from nw import utils
from nw import export_shape

# Constraints on NDFF observations
hok = 'kmhok'  # either uurhok, kmhok. TODO: Extent to duplohok, quartohok
min_area = {'kmhok':2500000, 'uurhok':1e9}[hok] # 2500000 for km hokken! 1e9 for uurhokken
protocol_excl = ['12.205 Monitoring Beoordeling Natuurkwaliteit EHS - N2000 (SNL-2014)'] # list of protocols, or empty list
nulsoort = False  # include nulsoorten: True or False
groep = 'vaatplant'  # one of following['broedvogel', 'dagvlinder', 'vaatplant', 'herpetofauna', 'all']
periodes = ['N2003-2012', 'N2013-2018']  # start-end year inclusive!
beheertype = 'snl_hoogveen'   # either one of: 'snl_vochtige_heide' 'snl_zwakgebufferd_ven', 'snl_zuur_ven_of_hoogveenven',  'snl_droge_heide',
                    # 'snl_zandverstuiving', 'snl_hoogveen, 'all'

# shortlist of legible species
sp_sel = set(utils.get_sp_info()[groep]['sp_nm']) & set(utils.get_sp_info()[beheertype]['sp_nm']) & set(utils.get_sp_info()['nulsoort'][nulsoort]['sp_nm'])

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
sbb_area_treshold = 0  # drempelwaarde voor sbb areaal in de cell
plot_background = True # Boolean, plot cells in output graph
beheertype_in_titel = True

# out directory
out_base_dir = r'd:\NW_out_data\20190218\minus_12-205'


# get requested cell type and narrow down
cells = utils.get_hok_gdf(hok_type=hok, oz_taxgroup=oz_groep_in, oz05_treshold=oz05_treshold_in,
                          oz18_treshold=oz18_treshold_in, heide_periode=heide_periode_in,
                          heide_treshold=heide_treshold_in)
# TODO (optioneel) heide1900 en heide 2012 treshold, ipv heide periode en heide treshold

comment_text = 'exclusief protocols' + ', '.join([protocol for protocol in protocol_excl])

for periode in periodes:
    # generate out file name with full info
    out_name = '{0}_{1}_{2}_heide{3}-{4}_' \
               'oz{5}05-{6}_oz{7}18-{8}_{9}'.format(hok, groep, periode, heide_periode_in, heide_treshold_in,
                                                    oz_groep_in, oz05_treshold_in, oz_groep_in, oz18_treshold_in,
                                                    beheertype)


    # period coverage as integers
    periode_int = [j for j in range(int(periode[1:5]), int(periode[6:10])+1)]

    # reduce ndff data to requested period and pivot on requested cell type
    ndff_sel = ndff.loc[ndff['year'].isin(periode_int), :]
    ndff_piv = pd.DataFrame(pd.pivot_table(ndff_sel, values='nl_name', index=hok, aggfunc=lambda x: len(x.unique())))

    # merge with the cell geodataframe and rename column to standard name
    merged = pd.merge(cells, ndff_piv, how='inner', right_index=True, left_on='ID')
    merged.rename(columns={'nl_name':'sp_count'}, inplace=True)


    if not merged.empty:

        print('{0} cells will be written to file for periode {1}'.format(merged.shape[0], periode))

        # save to shp
        merged.to_file(os.path.join(out_base_dir, 'shp', '{0}.shp'.format(out_name)))

        # save to image
        title_neat= '{0}_{1}_{2}'.format(hok, groep, periode)
        if beheertype_in_titel:
            title_neat += '_{0}'.format(beheertype)
        export_shape.to_png(gdf=merged, col='sp_count', upper_bin_lims=utils.get_bins(groep),
                            title=title_neat, comment=comment_text, out_dir=os.path.join(out_base_dir, 'png'),
                            out_name='{0}.png'.format(out_name), background=plot_background, background_cells=cells)
    else:
        print('Empty dataframe produced for period {0}, bummer'.format(periode))
    # TODO: log file as output with full database query.

    del ndff_sel
    del ndff_piv