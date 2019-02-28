# Script for automatic export of a shapefile to png.
# Hans Roelofsen, WEnR team B&B february 2019


import pysal.esda.mapclassify as mc
import os
import sys
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from nw import utils

sys.path.extend(['M:\\b_aux\\python\\clones\\geopandas_master', 'M:/b_aux/python/clones/geopandas_master'])
import geopandas as gp

# prov = gp.read_file(os.path.join(r'm:\a_Projects\Natuurwaarden\agpro\natuurwaarden\shp', 'provincies.shp'))
#
# fig = plt.figure(figsize=(8, 10))
# ax = fig.add_subplot(111)
# ax.set_aspect('equal')
# plt.tick_params(axis='both', labelbottom=False, labeltop=False, labelleft=False, labelright=False)
# ax.set(title='testing')
# ax.set(xlim=[0, 300000], ylim=[300000, 650000])
# prov.plot(ax=ax,  linewidth=0, color='#FFEBBE')
# plt.show()
#
# plt.close()


def to_png(gdf, col, upper_bin_lims, title, comment, out_dir, out_name, background, background_cells):

    # background images of Provincies - hardcoded.
    prov = gp.read_file(os.path.join(r'm:\a_Projects\Natuurwaarden\agpro\natuurwaarden\shp', 'provincies.shp'))

    fig = plt.figure(figsize=(8,10))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    plt.tick_params(axis='both', labelbottom=False, labeltop=False, labelleft=False, labelright=False)
    ax.set(title=title)

    ax.set(xlim=[0, 300000], ylim=[300000, 650000])

    prov.plot(ax=ax, color='lightgrey')

    if background:
        background_cells.plot(ax=ax, color='#15b01a', linewidth=0)

    gdf.plot(ax=ax, scheme='User_Defined', cmap='OrRd', column=col, legend=True, linewidth=0,
             legend_kwds={'loc':'upper left', 'fontsize':'small', 'frameon':False, 'title':'# soorten per hok'},
             classification_kwds={'bins':upper_bin_lims})

    ax.text(1000, 301000, comment, ha='left', va='center', size=6)

    plt.savefig(os.path.join(out_dir, out_name))
    plt.close


def diff_to_png(gdf, title, comment, col, cats, background, background_cells, out_dir, out_name):
    # background images of Provincies - hardcoded.
    prov = gp.read_file(os.path.join(r'm:\a_Projects\Natuurwaarden\agpro\natuurwaarden\shp', 'provincies.shp'))

    fig = plt.figure(figsize=(8,10))
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    plt.tick_params(axis='both', labelbottom=False, labeltop=False, labelleft=False, labelright=False)
    ax.set(title=title)
    ax.set(xlim=[0, 300000], ylim=[300000, 650000])

    prov.plot(ax=ax, color='lightgrey')

    if background:
        background_cells.plot(ax=ax, color='orange', linewidth=0)

    legend_patches = []
    for cat, color in cats.items():
        legend_patches.append(mpatches.Patch(label=cat, edgecolor='black', facecolor=color))

    for cat, colour in cats.items():
        sel = gdf.loc[gdf[col] == cat, :]
        print('{0} df nrow: {1}'.format(cat, sel.shape[0]))
        sel.plot(ax=ax, linewidth=0, color=colour)

    ax.text(1000, 301000, comment, ha='left', va='center', size=6)

    plt.legend(handles=legend_patches, loc='upper left', fontsize='small', frameon=False, title='Toe/Afname')
    plt.savefig(os.path.join(out_dir, out_name))
    plt.close


def plot_protocol_pies(pre_data, post_data, out_dir, out_name):
    # function to plot pie-charts showing distribution of NDFF observation protocols (rows in *data*) for two periodes
    # (cols in *data*) before (*pre-*) and after (*-post*) applying equal protocol density processing
    periode1, periode2 = list(pre_data)

    if pre_data.index.tolist() != post_data.index.tolist():
        raise Exception('Different protocols found for pre and post data')

    protocols = pre_data.index.tolist()

    fig = plt.figure()
    ax1 = fig.add_subplot(221)
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)

    ax1.pie(x=pre_data[periode1].fillna(0), startangle=90)
    ax2.pie(x=post_data[periode1].fillna(0), startangle=90)
    ax3.pie(x=pre_data[periode2].fillna(0), startangle=90)
    ax4.pie(x=post_data[periode2].fillna(0), startangle=90)

    ax1.set(title='{0}-before'.format(periode1))
    ax2.set(title='{0}-after'.format(periode1))
    ax3.set(title='{0}-before'.format(periode2))
    ax4.set(title='{0}-after'.format(periode2))

    out_name_full = out_name + 'protocols.png'
    plt.savefig(os.path.join(out_dir, out_name_full))
    plt.close()

