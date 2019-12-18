# Script to analyse the effect of increased visits to a km cell on the number of observed species
# Hans Roelofsen, WEnR, 19 feb 2019

import os
import matplotlib.pyplot as plt
import pandas as pd

from nw import utils
from nw import export_shape

# Constraints on NDFF observations
hok = 'kmhok'  # either uurhok, kmhok. TODO: Extent to duplohok, quartohok
min_area = {'kmhok':2500000, 'uurhok':1e9}[hok] # 2500000 for km hokken! 1e9 for uurhokken
protocol_excl = ['12.205 Monitoring Beoordeling Natuurkwaliteit EHS - N2000 (SNL-2014)'] # list of protocols, or empty list
nulsoort = False  # include nulsoorten: True or False
groep = 'all'  # one of following['broedvogel', 'dagvlinder', 'vaatplant', 'herpetofauna', 'all']
periodes = ['N1999-2012', 'N2013-2018']  # start-end year inclusive!
beheertype = 'all'   # either one of: 'snl_vochtige_heide' 'snl_zwakgebufferd_ven', 'snl_zuur_ven_of_hoogveenven',  'snl_droge_heide',
                    # 'snl_zandverstuiving', 'snl_hoogveen, 'all'

# shortlist of legible species
sp_sel = set(utils.get_sp_info()[groep]['sp_nm']) & set(utils.get_sp_info()[beheertype]['sp_nm']) & set(utils.get_sp_info()['nulsoort'][nulsoort]['sp_nm'])

# get raw ndff data and filter on observation specs, such as area, protocol.
# also narrow down to species from the selected species (ie. soortgroep, SNL subtype, nulsoort)
ndff = utils.get_ndff_full()
quer = 'protocol not in {0} & area < {1} & nl_name in {2}'.format(protocol_excl, min_area, list(sp_sel))
ndff.query(quer, inplace=True)

sp_info = utils.get_sp_info()
def get_tax(soort):
    return sp_info[soort]['tax_groep']
ndff['soortgroep'] = ndff['nl_name'].apply(get_tax)
ndff['cell_obs'] = 1

sp_count = pd.pivot_table(data=ndff, values='nl_name', columns='soortgroep', index=hok, aggfunc=lambda x: len(x.unique()))
sp_count.rename(columns=dict(zip(list(sp_count), ['{0}_sp'.format(x) for x in  list(sp_count)])), inplace=True)

obs_count = pd.pivot_table(data=ndff, values='cell_obs', columns='soortgroep', index=hok, aggfunc='sum')
obs_count.rename(columns=dict(zip(list(obs_count), ['{0}_obs'.format(x) for x in list(obs_count)])), inplace=True)

dat = pd.merge(left=sp_count, right=obs_count, how='outer', right_index=True, left_index=True)
dat['sp_all'] = dat[[x for x in list(dat) if 'sp' in x]].sum(axis=1)
dat['obs_all'] = dat[[x for x in list(dat) if 'obs' in x]].sum(axis=1)



# dat = pd.DataFrame(data={'sp_count':cell_sp_count, 'obs_count':cell_obs_count})

fig = plt.figure()
ax1 = fig.add_subplot(331)
ax1.set(title='broedvogels', ylabel='# unique species')
ax2 = fig.add_subplot(332)
ax2.set(title='dagvlinders', )
ax3 = fig.add_subplot(333)
ax3.set(title='vaatplant',)
ax4 = fig.add_subplot(334)
ax4.set(title='herpetofauna', ylabel='# unique species', xlabel='# observations')
ax5 = fig.add_subplot(335)
ax5.set(title='All', xlabel='# observations')
ax6 = fig.add_subplot(336)
ax6.set(title='All - zoom', xlabel='# observations', xlim=(0, 8000))

ax1.scatter(dat['broedvogel_obs'], dat['broedvogel_sp'])
ax2.scatter(dat['dagvlinder_obs'], dat['dagvlinder_sp'])
ax3.scatter(dat['vaatplant_obs'], dat['vaatplant_sp'])
ax4.scatter(dat['herpetofauna_obs'], dat['herpetofauna_sp'])
ax5.scatter(dat.obs_all, dat.sp_all)
ax6.scatter(dat.obs_all, dat.sp_all)

plt.show()

# print(dat.loc[dat['obs_count'] == 22458, :])
# plt.close()

