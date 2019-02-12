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


def to_png(gdf, col, upper_bin_lims, title, out_dir, out_name, background, background_cells):

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

    plt.savefig(os.path.join(out_dir, out_name))
    plt.close


def diff_to_png(gdf, title, col, cats, background, background_cells, out_dir, out_name):
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

    legend_patches = []
    for cat, color in cats.items():
        legend_patches.append(mpatches.Patch(label=cat, edgecolor='black', facecolor=color))

    for cat, color in cats.items():
        gdf.loc[gdf[col] == cat, :].plot(ax=ax, column=col, linewidth=0, color=color)

    plt.legend(handles=legend_patches, loc='upper left', fontsize='small', frameon=False, title='Toe/Afname')
    plt.savefig(os.path.join(out_dir, out_name))
    plt.close





