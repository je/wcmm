""" Lichen. """

import itertools
import os
import json
from datetime import datetime

import geopandas
import matplotlib.colors as mcolors
import numpy
import pandas
import statsmodels.api as sm
from adjustText import adjust_text
from django.utils.text import slugify
from matplotlib import pyplot
from statsmodels.stats import weightstats as sms

from settings import (
    base_dir,
    data_dir,
    cache_dir,
    out_ext,
    year_formatter,
    float_formatter,
    p_formatter,
    slash,
)
from utils import cols_to_plot, log, try_add_basemap, trender, uopen

# lichen_xlsx = data_dir + '_lichen' + slash + 'MegaDbPLOT_2022.05.13.xlsx'
# lichen_xlsx = data_dir + "_lichen" + slash + "MegaDbPLOT_2022.10.06.xlsx"
lichen_xlsx = data_dir + "_lichen" + slash + "2024-01-03" + slash + "MegaDbPLOT_2023.10.07.xlsx"


def lichen_match():
    """ read LG xls, check missing airscore for match_to with data, write filled airscores.csv
    """
    lichen_xls = lichen_xlsx
    out_dir = base_dir
    stations = pandas.read_excel(open(lichen_xls, "rb"), sheet_name="Full PlotDB")
    extra_cols = [
        e
        for e in stations.columns
        if e
        not in [
            "plot",
            "match_to",
            "wilderns",
            "dataset1",
            "year",
            "roundno",
            "n_airscore",
            "s_airscore",
            "c",
            "longusedd",
            "latusedd",
        ]
    ]
    stations = stations.drop(columns=extra_cols)
    print(str(len(stations)) + " total observations")
    d = {"n_airscore": ["mean"], "s_airscore": ["mean"]}
    stations = stations[~stations["n_airscore"].isin(["undefined"])]
    print(str(len(stations)) + " with defined n_airscore")
    stations = stations[~stations["s_airscore"].isin(["undefined"])]
    print(str(len(stations)) + " with defined s_airscore")
    stations["n_airscore"] = pandas.to_numeric(stations["n_airscore"])
    stations["s_airscore"] = pandas.to_numeric(stations["s_airscore"])

    stations['longusedd'] = stations.apply(lambda r: r['longusedd'] if type(r['longusedd'])==float else numpy.nan, axis=1)
    stations['latusedd'] = stations.apply(lambda r: r['latusedd'] if type(r['latusedd'])==float else numpy.nan, axis=1)
    print(str(len(stations)) + " before coords")
    stations = stations[~stations["longusedd"].isna()]
    stations = stations[~stations["latusedd"].isna()]
    print(str(len(stations)) + " with coords")

    s = (
        stations.groupby(["roundno", "year", "plot", "match_to", "wilderns"])
        .agg(d)
        .reset_index()
    )
    # print(s.head)
    match_self = stations[stations["match_to"] == stations["plot"]]
    print(str(len(match_self)) + " with self as match_to")
    match_other = stations[stations["match_to"] != stations["plot"]]
    print(str(len(match_other)) + " with other as match_to")
    match_other = match_other[~match_other["wilderns"].isnull()]
    print(str(len(match_other)) + " ...and an identified wilderness")
    match_other_n = match_other[
        match_other["n_airscore"].isnull() & match_other["s_airscore"].isnull()
    ]
    print(str(len(match_other_n)) + " ...and with null airscores")
    matchable = stations.dropna(subset=["n_airscore", "s_airscore"])
    print(str(len(matchable)) + " matchable with numeric airscores")

    match_other_n2 = match_other_n.merge(
        matchable,
        left_on=["match_to", "year"],
        right_on=["plot", "year"],
        suffixes=["", "_match"],
        how="inner",
    )
    match_other_n2.rename(
        columns={
            "n_airscore": "n_airscore_nil",
            "n_airscore_match": "n_airscore",
            "s_airscore": "s_airscore_nil",
            "s_airscore_match": "s_airscore",
        },
        inplace=True,
    )
    extra_cols = [
        e
        for e in match_other_n2.columns
        if e
        not in [
            "plot",
            "match_to",
            # "wilderns",
            "dataset1",
            "year",
            # "roundno",
            "n_airscore",
            "s_airscore",
            "c",
            "longusedd",
            "latusedd",
        ]
    ]
    match_other_n2 = match_other_n2.drop(columns=extra_cols)
    airscores = pandas.concat([matchable, match_other_n2])

    # airscores['date'] = airscores['date'].astype(str)
    airscores["geometry"] = geopandas.points_from_xy(
        airscores.longusedd, airscores.latusedd
    )

    nwps_shp = data_dir + "_wilderness" + slash + "_nwps-2022-12-16.topojson"
    nwps = geopandas.read_file(nwps_shp)
    nwps.rename(columns={"name": "w"}, inplace=True)

    airscores = geopandas.GeoDataFrame(airscores, crs=nwps.crs)
    airscores = geopandas.sjoin(
        airscores, nwps[["a", "w", "geometry"]], how="left", predicate="intersects"
    )
    airscores = airscores.drop(columns=["roundno", "wilderns", "index_right"])
    within = airscores[airscores["w"].notnull()]
    within_g = within.drop(columns=["longusedd", "latusedd"])
    within_g.to_file(
        driver="GeoJSON", filename=out_dir + "lichen-airscores-nwps.json",
    )
    print(out_dir + "lichen-airscores-nwps.json")
    within_c = within.drop(columns=["geometry"])
    within_c.to_csv(out_dir + "lichen-airscores-nwps.csv", index=False)
    print(out_dir + "lichen-airscores-nwps.csv")
    # quit()


def lichen_plot_map(which_wilderness):
    lichen_xls = lichen_xlsx  # todo: use airscores.csv from lichen_match instead

    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    awilderness_file = slug_wilderness + "." + out_ext
    awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext
    plots_file = slug_wilderness + "-lichen-plots." + out_ext
    plots_1mi_file = slug_wilderness + "-lichen-plots-buffer." + out_ext
    empty_file_out = out_dir + slug_wilderness + "-lichen-empty.txt"

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    wilderness_designation_year = awilderness["dd"].iloc[0][0:4]

    airscores = pandas.read_excel(open(lichen_xls, "rb"), sheet_name="Full PlotDB")
    #print(airscores.head)
    airscores = airscores.dropna(subset=["longusedd", "latusedd"])
    #print(airscores.head)
    airscores = airscores[~(airscores["longusedd"].isin([" ", ]) | airscores["latusedd"].isin([" ", ]))]
    #airscores = airscores[(airscores["longusedd"].isin([" ", ]) | airscores["latusedd"].isin([" ", ]))]
    #airscores = airscores[~airscores["longusedd"] == (" ")].copy(deep=True)
    #print(airscores.head)
    #quit()

    dbcols = [
        "plot",
        "geometry",
        "s_airscore",
        "s_airscore_clim_adj",
        "n_airscore",
        "n_airscore_clim_adj",
        "id",
        "megadbid",
        "plot_use",
        "plot",
        "match_to",
        "HexID_or_FIAdb",
        "visitno",
        "year",
        "roundno",
        "date",
        "nfs_reg",
        "nfsregad",
        "fia_reg",
        "dataset1",
        "dataset2",
        "wilderns",
        "class",
        "InWilderness",
        "WithinHalfMile",
        "Within1Mile",
        "latusedd",
        "longusedd",
        "latuseNAD83",
        "longuseNAD83",
        "progspon",
        "protocol",
        "publicat",
        "fia_prot",
        "plottype",
        "devsop",
        "project",
    ]
    extra_cols = [e for e in airscores.columns if e not in dbcols]
    airscores = airscores.drop(columns=extra_cols)
    airscores["date"] = airscores["date"].astype(str)
    airscores["geometry"] = geopandas.points_from_xy(
        airscores.longusedd, airscores.latusedd
    )  #

    # w_airscores = airscores[airscores["wilderns"] == (which_wilderness[1] + " Wilderness")].copy(deep=True)

    # airscores["geometry"] = geopandas.points_from_xy(airscores.longuseNAD83, airscores.latuseNAD83)  #
    airscores = geopandas.GeoDataFrame(airscores, crs=awilderness_1mi.crs)  #
    airscores = geopandas.sjoin(
        airscores, awilderness_1mi[["name", "geometry"]], how="left", predicate="within"
    )

    within = airscores["name"].notnull()
    tagged = airscores["wilderns"] == (which_wilderness[2] + " Wilderness")
    scores = airscores[within | tagged]
    print(scores.head)

    stations = pandas.read_excel(open(lichen_xls, "rb"), sheet_name="Full PlotDB")
    station = scores.copy(deep=True)
    extra_cols = [
        e
        for e in station.columns
        if e
        not in [
            "wilderns",
            "dataset1",
            "year",
            "roundno",
            "n_airscore",
            "s_airscore",
            "c",
            "longuseNAD83",
            "latuseNAD83",
        ]
    ]
    station = station.drop(columns=extra_cols)
    station.to_csv(out_dir + slug_wilderness + "-lichen-plots-a.csv")
    log(
        slug_wilderness,
        slug_agency,
        "CYAN",
        slug_wilderness + " lichen plots a: " + str(len(station)),
    )

    station = station.dropna(axis=0)
    station["plot_id"] = station["latuseNAD83"].astype(str) + station[
        "longuseNAD83"
    ].astype(str)
    station["hash"] = station.plot_id.map(hash)
    station["plot_id"] = pandas.factorize(station["plot_id"])[0]
    station.to_csv(out_dir + slug_wilderness + "-lichen-plots-b.csv")
    log(
        slug_wilderness,
        slug_agency,
        "CYAN",
        slug_wilderness + " lichen plots b: " + str(len(station)),
    )
    extra_cols = [
        e
        for e in station.columns
        if e not in ["roundno", "plot_id", "n_airscore", "s_airscore"]
    ]
    #station_ = station.drop(columns=extra_cols)
    #print(station_.head)
    #s = station_.groupby(["roundno", "plot_id",]).mean().add_suffix("_avg").reset_index()
    d = {"n_airscore": ["mean"], "s_airscore": ["mean"]}
    station["n_airscore"] = pandas.to_numeric(station["n_airscore"])
    station["s_airscore"] = pandas.to_numeric(station["s_airscore"])
    s = (
        station.groupby(["roundno", "plot_id", "latuseNAD83", "longuseNAD83"])
        .agg(d)
        .reset_index()
    )
    s.columns = ["_".join(col) for col in s.columns.values]

    station["geometry"] = geopandas.points_from_xy(
        station.longuseNAD83, station.latuseNAD83
    )
    # plots = geopandas.GeoDataFrame(station, crs='EPSG:4326')
    plots = geopandas.GeoDataFrame(station, geometry="geometry", crs=awilderness.crs)
    log(
        slug_wilderness,
        slug_agency,
        "CYAN",
        slug_wilderness + " mapped plots: " + str(len(plots)),
    )

    if not plots.empty:
        plots.to_file(
            driver="GeoJSON", filename=out_dir + slug_wilderness + "-lichen-plots.json"
        )
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            out_dir + slug_wilderness + "-lichen-plots.json created",
        )

        plots_1mi = plots.copy()
        plots_1mi.dataset1 = plots_1mi.dataset1.str[0:3]
        plots_1mi["bd"] = 0.0001
        plots_1mi.loc[plots_1mi["dataset1"] == "FIA", "bd"] = 0.01609344
        # print(plots_1mi.columns)
        # quit()
        plots_fia = geopandas.GeoDataFrame(
            plots_1mi, geometry="geometry", crs=plots_1mi.crs
        ).reindex(columns=plots_1mi.columns)
        # print(plots_fia.head)
        # quit()
        # print(plots_fia.crs)
        for index, plot in plots_1mi.iterrows():
            plot_df = plots_1mi.loc[plots_1mi["plot_id"] == plot.plot_id]
            cust_epsg = (
                "+proj=aeqd +lat_0="
                + str(plot.latuseNAD83)
                + " +lon_0="
                + str(plot.longuseNAD83)
                + " +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
            )
            plot_df = plot_df.to_crs(cust_epsg)
            # print(plot_df.head)
            # print(plot_df.bd)
            # print(plot_df.crs.axis_info[0].unit_name)
            # quit()
            plot_df["geometry"] = plot_df.geometry.buffer(
                1609.34 / 2
            )  # 1609.34 m in mi
            plot_df = plot_df.to_crs(plots_fia.crs)
            plots_fia = pandas.concat([plots_fia, plot_df])
        # print(plots_fia.head)
        # plots_1mi = plots_1mi.to_crs(cust_epsg)
        # quit()
        # plots_1mi['geometry'] = plots_1mi.geometry.buffer(plots_1mi.bd)

        aw_center = awilderness.geometry.unary_union.centroid
        # tepsg = '+proj=tpers +h=500000000 +lat_0=' + aw_center.lat + ' +lon_0=' + aw_center.lon + ' +x_0=0 +y_0=0 +a=6371000 +b=6371000 +units=m +tilt=10 +azi=10'
        # tepsg = '+proj=tpers +h=500000000 +lat_0=' + aw_center.y + ' +lon_0=' + aw_center.x + ' +x_0=0 +y_0=0 +units=m +tilt=10 +azi=10'
        # awilderness = awilderness.to_crs(plots.crs) # 4326, WGS 84
        # awilderness_1mi = awilderness_1mi.to_crs(plots.crs) # 4326, WGS 84
        # tepsg = {'proj': 'tpers', 'h': 1500000, 'tilt': 10, 'azi': 10, 'lat_0': aw_center.y, 'lon_0': aw_center.x, 'datum': 'WGS84', 'units': 'm',}
        # awilderness = awilderness.to_crs(tepsg)
        # print(awilderness.crs)

        width = 13
        axis = awilderness.plot(
            color="none",
            edgecolor="black",
            linewidth=2.0,
            alpha=0.9,
            figsize=(width, width / 1.618),
        )
        awilderness_1mi.plot(ax=axis, color="black", edgecolor="black", alpha=0.05)
        plots_fia.plot(ax=axis, color="tab:cyan", edgecolor="tab:cyan", alpha=0.2)
        plots.plot(ax=axis, color="tab:cyan", edgecolor="tab:cyan", alpha=1)
        xlim = [awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]]
        ylim = [awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]]
        pyplot.suptitle("Lichen plot locations near " + which_wilderness[2])
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        pyplot.axis("off")
        fig1 = pyplot.gcf()
        pyplot.subplots_adjust(top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0)
        pyplot.margins(0, 0)
        fig1.savefig(out_dir + slug_wilderness + "-lichen-plots.png")
        log(
            slug_wilderness, slug_agency, "GREEN", slug_wilderness + "-lichen-plots.png"
        )
        awilderness_box = awilderness_1mi.copy()
        print(awilderness_box.crs)
        awilderness_box["geometry"] = awilderness_box.geometry.buffer(0.1609344)
        xlim2 = [awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]]
        ylim2 = [awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]]
        axis.set_xlim(xlim2)
        axis.set_ylim(ylim2)
        # print(awilderness.crs)
        # print(plots_fia.crs)
        # pyplot.show()
        # quit()
        # print(awilderness.crs) # 4269
        # quit()
        # contextily.add_basemap(axis, crs=awilderness.crs.to_string())
        # contextily.add_basemap(axis, crs='EPSG:4269')
        # contextily.add_basemap(axis, crs='EPSG:4326')
        # contextily.add_basemap(axis, crs=awilderness.crs.to_string(), zoom=10, source=contextily.providers.Stamen.TonerLite)
        # try_add_basemap(slug_wilderness, axis, awilderness.crs)
        try_add_basemap(awilderness_box.total_bounds, slug_wilderness, slug_agency, axis, awilderness.crs.to_string())
        awilderness.plot(
            ax=axis, color="none", edgecolor="black", linewidth=1.0, alpha=0.9
        )
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        fig1.savefig(out_dir + slug_wilderness + "-lichen-plots-base.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            slug_wilderness + "-lichen-plots-base.png",
        )

        fig1.clf()
        pyplot.clf()
        pyplot.cla()
        pyplot.close()


def lichen_rounds(which_wilderness):
    """ read airscores.csv, make trend plots """
    lichen_xls = lichen_xlsx  # todo: use airscores.csv from lichen_match instead

    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    awilderness_file = slug_wilderness + "." + out_ext
    awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext
    plots_csv = slug_wilderness + "-lichen-plots.csv"
    matrix_csv = slug_wilderness + "-lichen-matrix.csv"
    empty_file_out = out_dir + slug_wilderness + "-lichen-empty.txt"

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    wilderness_designation_year = awilderness["dd"].iloc[0][0:4]

    airscores = pandas.read_excel(open(lichen_xls, "rb"), sheet_name="Full PlotDB")
    #print(airscores.head)
    airscores = airscores.dropna(subset=["longusedd", "latusedd"])
    #print(airscores.head)
    airscores = airscores[~(airscores["longusedd"].isin([" ", ]) | airscores["latusedd"].isin([" ", ]))]
    #airscores = airscores[(airscores["longusedd"].isin([" ", ]) | airscores["latusedd"].isin([" ", ]))]
    #airscores = airscores[~airscores["longusedd"] == (" ")].copy(deep=True)
    #print(airscores.head)
    #quit()

    dbcols = [
        "plot",
        "geometry",
        "s_airscore",
        "s_airscore_clim_adj",
        "n_airscore",
        "n_airscore_clim_adj",
        "id",
        "megadbid",
        "plot_use",
        "plot",
        "match_to",
        "HexID_or_FIAdb",
        "visitno",
        "year",
        "roundno",
        "date",
        "nfs_reg",
        "nfsregad",
        "fia_reg",
        "dataset1",
        "dataset2",
        "wilderns",
        "class",
        "InWilderness",
        "WithinHalfMile",
        "Within1Mile",
        "latusedd",
        "longusedd",
        "latuseNAD83",
        "longuseNAD83",
        "progspon",
        "protocol",
        "publicat",
        "fia_prot",
        "plottype",
        "devsop",
        "project",
    ]
    extra_cols = [e for e in airscores.columns if e not in dbcols]
    airscores = airscores.drop(columns=extra_cols)
    airscores["date"] = airscores["date"].astype(str)
    airscores["geometry"] = geopandas.points_from_xy(
        airscores.longusedd, airscores.latusedd
    )  #

    # w_airscores = airscores[airscores["wilderns"] == (which_wilderness[1] + " Wilderness")].copy(deep=True)

    # airscores["geometry"] = geopandas.points_from_xy(airscores.longuseNAD83, airscores.latuseNAD83)  #
    airscores = geopandas.GeoDataFrame(airscores, crs=awilderness_1mi.crs)  #
    airscores = geopandas.sjoin(
        airscores, awilderness_1mi[["name", "geometry"]], how="left", predicate="within"
    )

    within = airscores["name"].notnull()
    tagged = airscores["wilderns"] == (which_wilderness[2] + " Wilderness")
    scores = airscores[within | tagged]
    print(scores.head)

    scores.to_csv(out_dir + slug_wilderness + "-lichen.csv")
    scores.to_file(
        driver="GeoJSON", filename=out_dir + slug_wilderness + "-lichen.json",
    )
    #quit()

    # plots = pandas.read_excel(open(lichen_xls, 'rb'), sheet_name='Full PlotDB')
    # w_plots = plots[plots['wilderns'] == which_wilderness].copy(deep=True)
    # extra_cols = [e for e in w_plots.columns if e not in ['plot', 'match_to', 'wilderns',
    #    'dataset1', 'year', 'roundno', 'n_airscore', 's_airscore', 'c',
    #    'longuseNAD83','latuseNAD83']]
    # w_plots = w_plots.drop(columns=extra_cols)

    d = {"n_airscore": ["mean"], "s_airscore": ["mean"]}
    df = scores.groupby(["plot", "roundno", "year"]).agg(d).reset_index()
    df.columns = df.columns.map(lambda x: "_".join(a for a in x if len(a) > 0))

    if df.empty:
        log(slug_wilderness, slug_agency, "CYAN", slug_wilderness + " lichen empty")
        with uopen(empty_file_out, "a"):
            os.utime(empty_file_out, None)
    else:
        df.to_csv(out_dir + plots_csv)
        df["roundy"] = df.year.astype(str).str[:3]
        # print(df.head) # because pivot fails with dups in round
        # round_matrix = df.pivot(index=['plot'], columns=['roundno'], values=['n_airscore_mean','s_airscore_mean'])
        # round_matrix.to_csv(out_dir + matrix_csv)

        for ns in ["n", "s"]:
            if ns == "n":
                nsname = "nitrogen"
            elif ns == "s":
                nsname = "sulfur"
            # pyplot.clf()
            # pyplot.cla()
            # pyplot.close()

            dfns = df.copy()
            dfns = dfns[dfns["year"] > int(wilderness_designation_year)]
            keeps = ["plot", "roundno", "year", ns + "_airscore_mean", "roundy"]
            dfns = dfns[keeps]
            dfns = dfns[~dfns[ns + "_airscore_mean"].isnull()]
            print(dfns.head)

            if dfns.empty:
                log(
                    slug_wilderness,
                    slug_agency,
                    "CYAN",
                    slug_wilderness + " airscores empty",
                )
                with uopen(empty_file_out, "a"):
                    os.utime(empty_file_out, None)
            else:
                year_matrix = dfns.pivot(
                    index=["plot"], columns=["year"], values=[ns + "_airscore_mean"],
                )

                width = 13
                fig1, ax = pyplot.subplots(nrows=1, figsize=(width, width / 1.618))
                pyplot.text(
                    x=0.5,
                    y=0.96,
                    s=which_wilderness[2],
                    fontsize=10,
                    ha="center",
                    transform=fig1.transFigure,
                )
                pyplot.text(
                    x=0.5,
                    y=0.92,
                    s="Plotwise " + nsname + " airscores",
                    fontsize=12,
                    ha="center",
                    transform=fig1.transFigure,
                )
                pyplot.axvline(x=1980, color="k", alpha=0.1, linestyle="--")
                pyplot.axvline(x=1990, color="k", alpha=0.1, linestyle="--")
                pyplot.axvline(x=2000, color="k", alpha=0.1, linestyle="--")
                pyplot.axvline(x=2010, color="k", alpha=0.1, linestyle="--")
                pyplot.axvline(x=2020, color="k", alpha=0.1, linestyle="--")
                plot_matrix = dfns.pivot(
                    index=["year"], columns=["plot"], values=[ns + "_airscore_mean"]
                )
                # print(slug_wilderness)
                # print('year_matrix.head')
                # print(year_matrix.head)
                # [row[~numpy.isnan(row)] for row in year_matrix]
                # year_matrix = year_matrix[~numpy.isnan(year_matrix)]
                # print(year_matrix.head)

                n = len(numpy.unique(year_matrix.index))
                norm = mcolors.Normalize(vmin=1, vmax=n)
                colors = (
                    pyplot.cm.RdYlGn(numpy.linspace(0, 1, len(year_matrix)))
                    .ravel()
                    .tolist()
                )
                cmap = "viridis"
                t = df["year"].tolist() + [1980, 1990, 2000, 2010, 2020]
                t = sorted(list(set(t)))
                plot_matrix.plot(
                    xticks=t,
                    ylabel=ns + " airscore",
                    cmap=cmap,
                    marker=".",
                    legend=False,
                    ax=ax,
                )
                pyplot.xticks(fontsize=10, rotation=90)
                fig1 = pyplot.gcf()
                fig1.savefig(out_dir + slug_wilderness + "-lichen-" + ns + "-plots.png")

                list_of_years = dfns["year"].tolist()
                list_of_airscores = dfns[ns + "_airscore_mean"].tolist()
                list_of_plots = dfns["plot"].tolist()
                texts = []
                for x, y, s in zip(list_of_years, list_of_airscores, list_of_plots):
                    texts.append(pyplot.text(x, y, s, fontsize="xx-small"))
                adjust_text(texts)
                fig1.savefig(
                    out_dir + slug_wilderness + "-lichen-" + ns + "-plots-labels.png"
                )
                fig1.clf()
                pyplot.clf()
                pyplot.cla()
                pyplot.close()

                width = 13
                fig1, ax = pyplot.subplots(nrows=1, figsize=(width, width / 1.618))
                pyplot.text(
                    x=0.5,
                    y=0.96,
                    s=which_wilderness[2],
                    fontsize=10,
                    ha="center",
                    transform=fig1.transFigure,
                )
                pyplot.text(
                    x=0.5,
                    y=0.92,
                    s="Plotwise " + nsname + " airscores",
                    fontsize=12,
                    ha="center",
                    transform=fig1.transFigure,
                )
                pyplot.axvline(x=1980, color="k", alpha=0.1, linestyle="--")
                pyplot.axvline(x=1990, color="k", alpha=0.1, linestyle="--")
                pyplot.axvline(x=2000, color="k", alpha=0.1, linestyle="--")
                pyplot.axvline(x=2010, color="k", alpha=0.1, linestyle="--")
                pyplot.axvline(x=2020, color="k", alpha=0.1, linestyle="--")
                plot_matrix = dfns.pivot(
                    index=["year"], columns=["plot"], values=[ns + "_airscore_mean"]
                )
                n = len(numpy.unique(year_matrix.index))
                norm = mcolors.Normalize(vmin=1, vmax=n)
                colors = (
                    pyplot.cm.RdYlGn(numpy.linspace(0, 1, len(year_matrix)))
                    .ravel()
                    .tolist()
                )
                cmap = "viridis"
                t = df["year"].tolist() + [1980, 1990, 2000, 2010, 2020]
                t = sorted(list(set(t)))
                plot_matrix.plot(
                    xticks=t,
                    ylabel=ns + " airscore",
                    cmap=cmap,
                    marker=".",
                    legend=False,
                    ax=ax,
                )
                pyplot.xticks(fontsize=10, rotation=90)

                dfl = dfns.groupby("plot")
                i = 0
                list_of_years = []
                list_of_airscores = []
                list_of_plots = []
                for key, item in dfl:
                    key = dfl.get_group(key)
                    ax.plot(
                        key["year"],
                        key[ns + "_airscore_mean"],
                        color=pyplot.cm.viridis(norm(i)),
                    )
                    i = i + 1
                    kl = len(numpy.unique(key.index))
                    if kl >= 2:
                        list_of_years.extend(key["year"].tolist())
                        list_of_airscores.extend(key[ns + "_airscore_mean"].tolist())
                        list_of_plots.extend(key["plot"].tolist())
                fig1.savefig(
                    out_dir + slug_wilderness + "-lichen-" + ns + "-plotwise.png"
                )

                texts = []
                for x, y, s in zip(list_of_years, list_of_airscores, list_of_plots):
                    texts.append(pyplot.text(x, y, s, fontsize="xx-small"))
                adjust_text(texts)
                fig1.savefig(
                    out_dir + slug_wilderness + "-lichen-" + ns + "-plotwise-labels.png"
                )
                fig1.clf()
                pyplot.clf()
                pyplot.cla()
                pyplot.close()

                rounds_list = dfns["roundy"].drop_duplicates().sort_values().tolist()
                width = 13
                fig, ax = pyplot.subplots(nrows=1, figsize=(width, width / 1.618))
                n = len(rounds_list)
                colors = pyplot.cm.Spectral(numpy.arange(n) / numpy.arange(n).max())
                # texts = []
                for i, r in enumerate(rounds_list):
                    c = colors[i]
                    dfr = dfns.loc[dfns["roundy"].isin([r])]
                    dfmean = dfr[ns + "_airscore_mean"].mean()
                    pyplot.axhline(y=dfmean, color=c, alpha=0.9, linestyle="-")
                    ax.annotate(
                        r + "0s",
                        xy=(1, dfmean),
                        xytext=(6, 0),
                        color=c,
                        xycoords=ax.get_yaxis_transform(),
                        textcoords="offset points",
                        size=9,
                        ha="left",
                    )
                    # texts.append(pyplot.text(0, dfmean, r, fontsize='xx-small'))
                    pp = sm.ProbPlot(dfr[ns + "_airscore_mean"])
                    qq = pp.qqplot(
                        marker=".",
                        markerfacecolor=c,
                        markeredgecolor=c,
                        markersize=12,
                        line=None,
                        alpha=0.9,
                        ax=ax,
                    )
                # adjust_text(texts)
                fig1 = pyplot.gcf()
                pyplot.text(
                    x=0.5,
                    y=0.96,
                    s=which_wilderness[2],
                    fontsize=10,
                    ha="center",
                    transform=fig1.transFigure,
                )
                pyplot.text(
                    x=0.5,
                    y=0.92,
                    s="Quantiles by sampling round using all " + nsname + " airscores",
                    fontsize=12,
                    ha="center",
                    transform=fig1.transFigure,
                )

                fig1.savefig(
                    out_dir + slug_wilderness + "-lichen-" + ns + "-qq-all.png"
                )

                fig1.clf()
                pyplot.clf()
                pyplot.cla()
                pyplot.close()

                dfns = df.copy()
                dfns = dfns[dfns["year"] > int(wilderness_designation_year)]
                keeps = ["plot", "roundno", "year", ns + "_airscore_mean", "roundy"]
                dfns = dfns[keeps]
                dfns = dfns[~dfns[ns + "_airscore_mean"].isnull()]
                print(dfns.head)

                width = 13
                fig, ax = pyplot.subplots(nrows=1, figsize=(width, width / 1.618))
                # texts = []
                for i, r in enumerate(rounds_list):
                    c = colors[i]
                    dfr = dfns.loc[dfns["roundy"].isin([r])]
                    dfmean = dfr[ns + "_airscore_mean"].mean()
                    pyplot.axhline(y=dfmean, color=c, alpha=0.9, linestyle="-")
                    ax.annotate(
                        r + "0s",
                        xy=(1, dfmean),
                        xytext=(6, 0),
                        color=c,
                        xycoords=ax.get_yaxis_transform(),
                        textcoords="offset points",
                        size=9,
                        ha="left",
                    )
                    # texts.append(pyplot.text(0, dfmean, r, fontsize='xx-small'))
                    pp = sm.ProbPlot(dfr[ns + "_airscore_mean"])
                    qq = pp.qqplot(
                        marker=".",
                        markerfacecolor=c,
                        markeredgecolor=c,
                        markersize=12,
                        line=None,
                        alpha=0.9,
                        ax=ax,
                    )
                # adjust_text(texts)
                fig1 = pyplot.gcf()
                pyplot.text(
                    x=0.5,
                    y=0.96,
                    s=which_wilderness[2],
                    fontsize=10,
                    ha="center",
                    transform=fig1.transFigure,
                )
                pyplot.text(
                    x=0.5,
                    y=0.92,
                    s="Quantiles by sampling round using "
                    + nsname
                    + " airscores after "
                    + wilderness_designation_year
                    + " designation",
                    fontsize=12,
                    ha="center",
                    transform=fig1.transFigure,
                )
                fig1.savefig(
                    out_dir
                    + slug_wilderness
                    + "-lichen-"
                    + ns
                    + "-qq-d"
                    + wilderness_designation_year
                    + ".png"
                )

                fig1.clf()
                pyplot.clf()
                pyplot.cla()
                pyplot.close()

                dfns = df.copy()
                dfns = dfns[dfns["year"] > int(wilderness_designation_year)]
                keeps = ["plot", "roundno", "year", ns + "_airscore_mean", "roundy"]
                dfns = dfns[keeps]
                dfns = dfns[~dfns[ns + "_airscore_mean"].isnull()]
                print(dfns.head)

                pair_list = list(itertools.combinations(rounds_list, 2))
                with uopen(out_dir + slug_wilderness + "-lichen-" + ns + ".txt", "w"):
                    os.utime(out_dir + slug_wilderness + "-lichen-" + ns + ".txt", None)
                with uopen(out_dir + slug_wilderness + "-lichen-" + ns + ".json", "w"):
                    os.utime(out_dir + slug_wilderness + "-lichen-" + ns + ".json", None)
                jscd = []
                for pair in pair_list:
                    first_round = pair[0]
                    last_round = pair[1]

                    dfns.rename(columns={"plot": "plot_id"}, inplace=True)
                    dfr = dfns.copy()
                    dfr = dfr.loc[dfr["roundy"].isin([first_round, last_round])]
                    df1 = dfr.loc[dfr["roundy"].isin([first_round])]
                    df2 = dfr.loc[dfr["roundy"].isin([last_round])]

                    plot_list1 = df1.plot_id.tolist()
                    plot_list2 = df2.plot_id.tolist()
                    plot_list = [x for x in plot_list1 if x in plot_list2]
                    dfr = dfr.loc[dfr["plot_id"].isin(plot_list)].sort_values(
                        ["year", "plot_id"]
                    )
                    if dfr.empty:
                        pass
                    else:
                        por = first_round + "0s vs " + last_round + "0s"
                        df1a = dfr.loc[dfr["roundy"].isin([first_round])]
                        df2a = dfr.loc[dfr["roundy"].isin([last_round])]
                        df1a = (
                            df1a.groupby(["plot_id", "roundno", "roundy"])
                            .mean()
                            .reset_index()
                        )
                        df2a = (
                            df2a.groupby(["plot_id", "roundno", "roundy"])
                            .mean()
                            .reset_index()
                        )
                        print(df1a.head)
                        print(df2a.head)
                        if ns == "n":
                            a_list = df1a.n_airscore_mean.tolist()
                            b_list = df2a.n_airscore_mean.tolist()
                        elif ns == "s":
                            a_list = df1a.s_airscore_mean.tolist()
                            b_list = df2a.s_airscore_mean.tolist()
                        with uopen(
                            out_dir + slug_wilderness + "-lichen-" + ns + ".txt", "a"
                        ) as static_file:
                            static_file.write(
                                first_round
                                + "0s "
                                + ns
                                + "-airscore values: "
                                + str(a_list)
                                + "\n"
                            )
                            static_file.write(
                                last_round
                                + "0s "
                                + ns
                                + "-airscore values: "
                                + str(b_list)
                                + "\n"
                            )
                        ns, trend, p_value = trend_round(
                            which_wilderness[2],
                            ns,
                            por,
                            wilderness_designation_year,
                            a_list,
                            b_list,
                        )
                        txt = (
                            nsname
                            + " airscore "
                            + trend
                            + " (signifigance: p="
                            + p_formatter(p_value)
                            + ") from "
                            + por
                        )
                        with uopen(
                            out_dir + slug_wilderness + "-lichen-" + ns + ".txt", "a"
                        ) as text_file:
                            print(f"{txt}", file=text_file)

                        jsd = [
                            {
                                "airscore": ns,
                                "first_round": first_round,
                                "first_scores": a_list,
                                "last_round": last_round,
                                "last_scores": b_list,
                                "trend": trend,
                                "p": p_formatter(p_value),
                            }
                        ]
                        jsc = "".join(str(v) for v in jsd).replace("'", '"')

                        jscd = jscd + jsd

                        width = 13
                        fig, ax = pyplot.subplots(
                            nrows=1, figsize=(width, width / 1.618)
                        )
                        drounds_list = (
                            dfr["roundy"].drop_duplicates().sort_values().tolist()
                        )
                        n = len(drounds_list)
                        colors = pyplot.cm.Spectral(
                            numpy.arange(n) / numpy.arange(n).max()
                        )
                        # texts = []
                        for i, r in enumerate(drounds_list):
                            c = colors[i]
                            dfrp = dfr.loc[dfr["roundy"].isin([r])]

                            dfmean = dfrp[ns + "_airscore_mean"].mean()
                            pyplot.axhline(y=dfmean, color=c, alpha=0.9, linestyle="-")
                            ax.annotate(
                                r + "0s",
                                xy=(1, dfmean),
                                xytext=(6, 0),
                                color=c,
                                xycoords=ax.get_yaxis_transform(),
                                textcoords="offset points",
                                size=9,
                                ha="left",
                            )
                            # texts.append(pyplot.text(0, dfmean, r, fontsize='xx-small'))
                            pp = sm.ProbPlot(dfrp[ns + "_airscore_mean"])
                            qq = pp.qqplot(
                                marker=".",
                                markerfacecolor=c,
                                markeredgecolor=c,
                                markersize=12,
                                line=None,
                                alpha=0.9,
                                ax=ax,
                            )
                        # adjust_text(texts)
                        fig1 = pyplot.gcf()
                        pyplot.text(
                            x=0.5,
                            y=0.96,
                            s=which_wilderness[2],
                            fontsize=10,
                            ha="center",
                            transform=fig1.transFigure,
                        )
                        pyplot.text(
                            x=0.5,
                            y=0.92,
                            s="Quantiles for "
                            + first_round
                            + "0s vs "
                            + last_round
                            + "0s by sampling round using matched "
                            + nsname
                            + " airscores after "
                            + wilderness_designation_year
                            + " designation",
                            fontsize=12,
                            ha="center",
                            transform=fig1.transFigure,
                        )
                        pyplot.text(
                            x=0.5,
                            y=0.02,
                            s=txt,
                            fontsize=11,
                            ha="center",
                            transform=fig1.transFigure,
                            bbox=dict(
                                boxstyle="square,pad=.6",
                                facecolor="tab:olive",
                                edgecolor="tab:gray",
                                alpha=0.1,
                            ),
                        )

                        fig1.savefig(
                            out_dir
                            + slug_wilderness
                            + "-lichen-"
                            + ns
                            + "-qq-d"
                            + wilderness_designation_year
                            + "-"
                            + first_round
                            + "0s-"
                            + last_round
                            + "0s.png"
                        )

                        fig1.clf()
                        pyplot.clf()
                        pyplot.cla()
                        pyplot.close()

                print(jscd)
                #jscc = "".join(str(v) for v in jscd).replace("'", '"')
                jscc = json.dumps(jscd)
                with uopen(out_dir + slug_wilderness + "-lichen-" + ns + ".json", "a") as static_file:
                    static_file.write(jscc)


def trend_round(which_wilderness, ns, por, wilderness_designation_year, a_list, b_list):
    """ t-test round vs round """
    slug_wilderness = slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + slash
    if ns == "n":
        nsname = "Nitrogen"
    elif ns == "s":
        nsname = "Sulfur"

    a = numpy.array(a_list)
    b = numpy.array(b_list)
    # a = numpy.array([-0.2678, -0.244, -1.154])
    # b = numpy.array([-0.4108, -0.5537, 0.0884])
    print(a)
    print(b)

    d = sms.DescrStatsW(a - b)
    ttm = d.ttest_mean()
    tcm = d.tconfint_mean()
    # print(ttm)
    # print(tcm)
    p_value = ttm[1]

    slope = "what"
    a_mean = numpy.mean(a_list)
    b_mean = numpy.mean(b_list)

    if numpy.isnan(p_value):
        trend = "undetermined"
    elif p_value <= 0.05:
        if a_mean < b_mean:
            trend = "increasing"
        elif a_mean > b_mean:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "stable"

    return (ns, trend, p_value)
