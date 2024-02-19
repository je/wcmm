""" Total deposition. """

import shutil
import fiona
import geopandas
import pandas
import rasterio
import rasterio.mask
import statsmodels.api
from django.utils.text import slugify
from matplotlib import colors
from rasterio.features import shapes
from scipy import stats

from utils import *

max_iter = 9999

def tdep_stack(ns):
    years = list(range(2000, 2023))
    dd = "/2023-11-28/"
    file_list = []
    for year in years:
        fn = ("/Volumes/PATRIOT/cda_data/_tdep_"
        + ns
        + dd
        + ns
        + "_tw-"
        + str(year))
        shutil.unpack_archive(fn + '.zip', fn)
        tn = ("/Volumes/PATRIOT/cda_data/_tdep_"
        + ns
        + dd
        + ns
        + "_tw-"
        + str(year)
        + "/"
        + ns
        + "_tw-"
        + str(year))
        file_list.append(tn + ".tif")

    # Read metadata of first file
    with rasterio.open(file_list[0]) as src0:
        meta = src0.meta

    # Update meta to reflect the number of layers
    meta.update(count=len(file_list))

    # Read each layer and write it to stack
    with rasterio.open(cache_dir + ns + "-stacked.tif", "w", **meta) as dst:
        for id, layer in enumerate(file_list, start=1):
            with rasterio.open(layer) as src1:
                dst.write_band(id, src1.read(1))


def tdep2_awilderness_nwps(which_wilderness, ns):  # cut and stack rasters to shp
    tdep_national = cache_dir + ns + "-stacked.tif"
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    awilderness_file = slug_wilderness + "." + out_ext
    awilderness_n_5mi_file = slug_wilderness + "-n5-buffer." + out_ext

    empty_file_out = out_dir + slug_wilderness + "-" + ns + "tdep-empty.txt"
    if os.path.exists(empty_file_out):
        os.remove(empty_file_out)

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    awilderness_5mi = awilderness.copy()
    ras_epsg = "EPSG:5070"
    awilderness_5mi["geometry"] = awilderness_5mi.geometry.buffer(
        0.01609344 * 5
    )  # warns but ok
    awilderness_5mi = awilderness_5mi.to_crs(ras_epsg)
    awilderness_5mi.to_file(
        driver=out_driver, filename=out_dir + awilderness_n_5mi_file,
    )
    log(slug_wilderness, slug_agency, "GREEN", str(awilderness_n_5mi_file) + " created")

    with fiona.open(out_dir + awilderness_n_5mi_file, "r") as shapefile:
        shapefeatures = [feature["geometry"] for feature in shapefile]

    try:
        with rasterio.open(tdep_national) as src:
            out_image, out_transform = rasterio.mask.mask(src, shapefeatures, crop=True)
            out_meta = src.meta
        out_meta.update(
            {
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
            }
        )
        with rasterio.open(
            out_dir + slug_wilderness + "-" + ns + ".tif", "w", **out_meta
        ) as dest:
            dest.write(out_image)
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            str(slug_wilderness) + " " + ns + " tdep mask created",
        )

        tdep_years = [
            # "20230",
            "20220",
            "20210",
            "20200",
            "20190",
            "20180",
            "20170",
            "20160",
            "20150",
            "20140",
            "20130",
            "20120",
            "20110",
            "20100",
            "20090",
            "20080",
            "20070",
            "20060",
            "20050",
            "20040",
            "20030",
            "20020",
            "20010",
            "20000",
        ]  # 20 out
        first = 0
        for tdep_year in tdep_years:
            first = first + 1
            bandnum = int(tdep_year[:4]) - 1999
            with rasterio.open(out_dir + slug_wilderness + "-" + ns + ".tif") as rds:
                band = rds.read(bandnum)
                transform = rds.transform
                mask = None
                if first == 1:
                    colname = tdep_year[-5:]
                    print(
                        colorama.Fore.WHITE
                        + str(datetime.now().strftime("%Y%m%d_%H%M"))
                        + colorama.Style.BRIGHT
                        + " vectorizing "
                        + colname
                        + " grid"
                    )
                    results = (
                        {"properties": {"c": i, "raster_val": v}, "geometry": s}
                        for i, (s, v) in enumerate(
                            shapes(band, mask=mask, transform=transform)
                        )
                    )
                    geoms = list(results)
                    pd_raster = geopandas.GeoDataFrame.from_features(geoms)
                    pd_raster.crs = ras_epsg
                    pd_raster = pd_raster.rename(columns={"raster_val": colname})
                    pd_raster = pd_raster[["c", colname, "geometry"]]
                    tdep_stack = pd_raster
                    print(tdep_stack.head)
                else:
                    colname = tdep_year[-5:]
                    print(
                        colorama.Fore.WHITE
                        + str(datetime.now().strftime("%Y%m%d_%H%M"))
                        + colorama.Style.BRIGHT
                        + " indexing "
                        + colname
                        + " grid"
                    )
                    results = (
                        {"properties": {"c": i, "raster_val": v}, "geometry": s}
                        for i, (s, v) in enumerate(
                            shapes(band, mask=mask, transform=transform)
                        )
                    )
                    geoms = list(results)
                    pd_raster = geopandas.GeoDataFrame.from_features(geoms)
                    pd_raster = pd_raster.rename(columns={"raster_val": colname})
                    pd_raster = pd_raster[["c", colname, "geometry"]]
                    print(pd_raster.head)

                    points = pd_raster.copy()
                    points.crs = ras_epsg
                    theboth = geopandas.sjoin(
                        tdep_stack, points, how="left", predicate="contains"
                    )

                    tdep_stack = geopandas.GeoDataFrame(theboth, geometry="geometry")
                    extra_cols = [
                        e
                        for e in tdep_stack.columns
                        if e
                        not in [
                            "FID",
                            "20230",
                            "20220",
                            "20210",
                            "20200",
                            "20190",
                            "20180",
                            "20170",
                            "20160",
                            "20150",
                            "20140",
                            "20130",
                            "20120",
                            "20110",
                            "20100",
                            "20090",
                            "20080",
                            "20070",
                            "20060",
                            "20050",
                            "20040",
                            "20030",
                            "20020",
                            "20010",
                            "20000",
                            "geometry",
                        ]
                    ]
                    tdep_stack = tdep_stack.drop(columns=extra_cols)
                    tdep_stack.crs = ras_epsg

        tdep_stack["acres"] = tdep_stack["geometry"].area / 4046.856
        tdep_stack = tdep_stack[tdep_stack["acres"] <= 8000]  # more than one cell
        tdep_stack = tdep_stack.drop(columns=["acres"])

        tdep_stack.to_file(driver=out_driver, filename=out_dir + ns + "tdep-cut-stack.shp")
        print(
            colorama.Fore.GREEN
            + str(datetime.now().strftime("%Y%m%d_%H%M"))
            + colorama.Style.BRIGHT
            + " "
            + ns
            + " tdep-cut-stack.shp"
            + " created"
        )

    except:
        log(slug_wilderness, slug_agency, "WHITE", ns + "tdep empty")
        empty_file_out = out_dir + slug_wilderness + "-" + ns + "tdep-empty.txt"
        tdep_wgrid = None
        with uopen(empty_file_out, "a"):
            os.utime(empty_file_out, None)


def tdep_awilderness_graphs_nwps(which_wilderness, ns):  # make goofy graphs
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    tdep_national_file = out_dir + ns + "tdep-cut-stack.shp"
    awilderness_file = slug_wilderness + "." + out_ext
    awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext
    awilderness_n_file = slug_wilderness + "-n." + out_ext
    awilderness_n_1mi_file = slug_wilderness + "-n-buffer." + out_ext
    tdep_wgrid_file = slug_wilderness + "-" + ns + "tdep-grid." + out_ext
    tdep_w_file = slug_wilderness + "-" + ns + "tdep." + out_ext
    empty_file_out = out_dir + slug_wilderness + "-" + ns + "tdep-empty.txt"

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    wilderness_designation_year = awilderness["dd"].iloc[0][0:4]

    if os.path.exists(empty_file_out):
        log(slug_wilderness, slug_agency, "WHITE", ns + "tdep empty")
    else:
        if ns == "n":
            nsname = "Nitrogen"
        elif ns == "s":
            nsname = "Sulfur"
        awilderness_n = awilderness.to_crs(ras_epsg)
        awilderness_n.to_file(driver=out_driver, filename=out_dir + awilderness_n_file)
        log(slug_wilderness, slug_agency, "GREEN", str(awilderness_n_file) + " created")

        awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
        awilderness_n_1mi = awilderness_1mi.to_crs(ras_epsg)
        awilderness_n_1mi.to_file(
            driver=out_driver, filename=out_dir + awilderness_n_1mi_file
        )
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            str(awilderness_n_1mi_file) + " created",
        )

        tdep_national = geopandas.read_file(tdep_national_file)
        log(slug_wilderness, slug_agency, "WHITE", "clipping grid to wilderness")
        tdep_national.crs = ras_epsg
        extra_cols = [e for e in awilderness_n.columns if e != "geometry"]
        awilderness_n = awilderness_n.drop(columns=extra_cols)

        try:
            tdep_wgrid = geopandas.overlay(
                tdep_national, awilderness_n, how="intersection"
            )
            tdep_wgrid = tdep_wgrid.fillna("0")
            tdep_wgrid.crs = awilderness_n.crs
        except KeyError:
            log(slug_wilderness, slug_agency, "WHITE", ns + "tdep clipped empty")
            empty_file_out = out_dir + slug_wilderness + "-" + ns + "tdep-empty.txt"
            tdep_wgrid = None
            with uopen(empty_file_out, "a"):
                os.utime(empty_file_out, None)

        if tdep_wgrid is not None:  # array of grid cells over wilderness
            xlist0 = ""
            tdep_wgrid["y0"] = ""
            for col in list(tdep_wgrid):
                if col not in (
                    "geometry",
                    "c",
                    "y",
                    "x",
                    "m",
                    "b",
                    "endy",
                    "p_value",
                    "trend_text",
                    "acres",
                    "y0",
                    "x0",
                    "m0",
                    "b0",
                    "endy0",
                    "p_value0",
                    "trend_text0",
                ):
                    coly = col[:-1]
                    xlist0 = xlist0 + coly + " "
                    tdep_wgrid["y0"] = (
                        tdep_wgrid["y0"] + tdep_wgrid[col].astype(str) + " "
                    )

            tdep_wgrid["x0"] = xlist0
            x_vals0 = [int(value) for value in xlist0.split()]
            xmin0 = min(x_vals0)
            xmax0 = max(x_vals0)

            xlist = ""
            tdep_wgrid["y"] = ""
            for col in list(tdep_wgrid):
                if col not in (
                    "geometry",
                    "c",
                    "y",
                    "x",
                    "m",
                    "b",
                    "endy",
                    "p_value",
                    "trend_text",
                    "acres",
                    "y0",
                    "x0",
                    "m0",
                    "b0",
                    "endy0",
                    "p_value0",
                    "trend_text0",
                ):
                    coly = col[:-1]
                    if int(coly) >= int(wilderness_designation_year):
                        xlist = xlist + coly + " "
                        tdep_wgrid["y"] = (
                            tdep_wgrid["y"] + tdep_wgrid[col].astype(str) + " "
                        )

            tdep_wgrid["x"] = xlist

            if xmax0 == int(wilderness_designation_year):
                log(slug_wilderness, slug_agency, "WHITE", ns + "tdep trend empty")
                empty_file_out = out_dir + slug_wilderness + "-" + ns + "tdep-empty.txt"
                tdep_wgrid = None
                with uopen(empty_file_out, "a"):
                    os.utime(empty_file_out, None)
            elif tdep_wgrid.empty:
                log(slug_wilderness, slug_agency, "WHITE", ns + "tdep clipped empty")
                empty_file_out = out_dir + slug_wilderness + "-" + ns + "tdep-empty.txt"
                tdep_wgrid = None
                with uopen(empty_file_out, "a"):
                    os.utime(empty_file_out, None)
            elif not xlist:
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    ns + "tdep period of record too short",
                )
                empty_file_out = out_dir + slug_wilderness + "-" + ns + "tdep-empty.txt"
                tdep_wgrid = None
                with uopen(empty_file_out, "a"):
                    os.utime(empty_file_out, None)
            else:
                fig1 = pyplot.gcf()
                width = 13
                fig1.set_size_inches(width, width / 1.618, forward=True)
                x_vals = [int(value) for value in xlist.split()]
                xmin = min(x_vals)
                xmax = max(x_vals)
                ticks = x_vals
                pyplot.suptitle(
                    which_wilderness[1]
                    + " "
                    + which_wilderness[2]
                    + "\nTotal "
                    + nsname
                    + " Deposition Trend from "
                    + year_formatter(xmin)
                    + " to "
                    + year_formatter(xmax)
                    + " by Grid Cell",
                    y=0.95,
                )
                if not tdep_wgrid["x0"].values[0] == tdep_wgrid["x"].values[0]:
                    tdep_wgrid[
                        ["m0", "b0", "endy0", "p_value0", "trend_text0", "cols0"]
                    ] = tdep_wgrid.apply(
                        lambda row: pandas.Series(
                            trend2(
                                row["x0"], row["y0"], ["tab:cyan", "tab:gray", 0.025]
                            )
                        ),
                        axis=1,
                    )
                    tdep_wgrid = tdep_wgrid.drop(columns="cols0")
                    trend_max = tdep_wgrid.loc[tdep_wgrid["m0"].idxmax()]
                    trend_min = tdep_wgrid.loc[tdep_wgrid["m0"].idxmin()]
                    x_list0 = [int(i) for i in trend_max["x0"].split()]

                    maxline_values = [
                        trend_max["m0"] * int(i) + trend_max["b0"] for i in x_list0
                    ]
                    minline_values = [
                        trend_min["m0"] * int(i) + trend_min["b0"] for i in x_list0
                    ]
                    pyplot.plot(
                        x_list0,
                        maxline_values,
                        color="tab:cyan",
                        alpha=0.5,
                        linewidth=2,
                        label=None,
                    )
                    pyplot.plot(
                        x_list0,
                        minline_values,
                        color="tab:cyan",
                        alpha=0.5,
                        linewidth=2,
                        label=None,
                    )
                    ticks = x_vals0
                    pyplot.suptitle(
                        which_wilderness[1]
                        + " "
                        + which_wilderness[2]
                        + "\nTotal "
                        + nsname
                        + " Deposition Trend from "
                        + year_formatter(xmin)
                        + " to "
                        + year_formatter(xmax)
                        + " by Grid Cell\nwith Total "
                        + nsname
                        + " Deposition Trend from "
                        + year_formatter(xmin0)
                        + " to "
                        + year_formatter(xmax0)
                        + " by Grid Cell",
                        y=0.95,
                    )

                tdep_wgrid[
                    ["m", "b", "endy", "p_value", "trend_text", "cols"]
                ] = tdep_wgrid.apply(
                    lambda row: pandas.Series(
                        trend2(row["x"], row["y"], ["tab:green", "tab:gray", 0.05])
                    ),
                    axis=1,
                )
                tdep_wgrid = tdep_wgrid.drop(columns="cols")
                trend_max = tdep_wgrid.loc[tdep_wgrid["m"].idxmax()]
                trend_min = tdep_wgrid.loc[tdep_wgrid["m"].idxmin()]
                x_list = [int(i) for i in trend_max["x"].split()]

                maxline_values = [
                    trend_max["m"] * int(i) + trend_max["b"] for i in x_list
                ]
                minline_values = [
                    trend_min["m"] * int(i) + trend_min["b"] for i in x_list
                ]
                pyplot.plot(
                    x_list,
                    maxline_values,
                    color="tab:green",
                    alpha=1,
                    linewidth=2,
                    label=None,
                )
                pyplot.plot(
                    x_list,
                    minline_values,
                    color="tab:green",
                    alpha=1,
                    linewidth=2,
                    label=None,
                )

                pyplot.xticks(ticks)
                pyplot.suptitle(
                    which_wilderness[1]
                    + " "
                    + which_wilderness[2]
                    + "\nTotal "
                    + nsname
                    + " Deposition Trend from "
                    + year_formatter(xmin)
                    + " to "
                    + year_formatter(xmax)
                    + " by Grid Cell\nwith Total "
                    + nsname
                    + " Deposition Trend from "
                    + year_formatter(xmin0)
                    + " to "
                    + year_formatter(xmax0)
                    + " by Grid Cell",
                    y=0.95,
                )
                pyplot.margins(0, 0)
                fig1.savefig(
                    out_dir
                    + slug_wilderness
                    + "-"
                    + ns
                    + "tdep-graph-extended-grid.png"
                )
                fig1.clf()
                pyplot.clf()
                pyplot.cla()
                pyplot.close()

                tdep_wgrid["acres"] = tdep_wgrid["geometry"].area / 4046.856

                tdep_wgrid.to_file(
                    driver=out_driver, filename=out_dir + tdep_wgrid_file
                )
                log(
                    slug_wilderness,
                    slug_agency,
                    "GREEN",
                    str(tdep_wgrid_file)
                    + " created with "
                    + str(len(tdep_wgrid.index))
                    + " tdep cells",
                )

                w_acres = tdep_wgrid["acres"].sum()

                if ns == "s":
                    pass
                    # tdep_wgrid = tdep_wgrid[tdep_wgrid.c != 454443] # TODO: select border by area
                elif ns == "n":
                    pass
                    # tdep_wgrid = tdep_wgrid[tdep_wgrid.c != 454467] # TODO: select border by area
                for col in list(tdep_wgrid):
                    if col not in (
                        "geometry",
                        "c",
                        "x",
                        "y",
                        "m",
                        "b",
                        "endy",
                        "p_value",
                        "trend_text",
                        "acres",
                        "c0",
                        "y0",
                        "x0",
                        "m0",
                        "b0",
                        "endy0",
                        "p_value0",
                        "trend_text0",
                        "acres0",
                    ):
                        tdep_wgrid[col] = pandas.to_numeric(
                            tdep_wgrid[col], errors="coerce"
                        )
                        tdep_wgrid[col[:-1] + "_sum"] = (
                            tdep_wgrid[col] * tdep_wgrid["acres"]
                        ) / w_acres
                        tdep_wgrid[col[:-1] + "_tdep"] = tdep_wgrid[
                            col[:-1] + "_sum"
                        ].sum()
                        tdep_wgrid = tdep_wgrid.drop(columns=[col, col[:-1] + "_sum"])

                extra_cols = [e for e in tdep_wgrid.columns if "_tdep" not in e]
                extra_cols = [
                    value
                    for value in extra_cols
                    if value
                    not in [
                        "geometry",
                        "w_acres",
                        "y",
                        "x",
                        "m",
                        "b",
                        "endy",
                        "p_value",
                        "trend_text",
                        "acres",
                        "y0",
                        "x0",
                        "m0",
                        "b0",
                        "endy0",
                        "p_value0",
                        "trend_text0",
                    ]
                ]
                tdep_wgrid = tdep_wgrid.drop(columns=extra_cols)
                tdep_w = tdep_wgrid.dissolve(by="x")  # cells dissolved to wilderness
                tdep_w["w_acres"] = w_acres

                xlist = ""
                tdep_w["y"] = ""
                for col in list(tdep_w):
                    if col not in (
                        "geometry",
                        "c",
                        "y0",
                        "x0",
                        "y",
                        "x",
                        "m0",
                        "b0",
                        "endy0",
                        "p_value0",
                        "trend_text0",
                        "m",
                        "b",
                        "endy",
                        "p_value",
                        "trend_text",
                        "acres",
                        "w_acres",
                    ):
                        coly = col[:-5]
                        if int(coly) >= int(wilderness_designation_year):
                            tdep_w["y"] = tdep_w["y"] + tdep_w[col].astype(str) + " "
                            xlist = xlist + coly + " "
                tdep_w["x"] = xlist

                xlist0 = ""
                tdep_w["y0"] = ""
                for col in list(tdep_w):
                    if col not in (
                        "geometry",
                        "c",
                        "y0",
                        "x0",
                        "y",
                        "m0",
                        "x",
                        "b0",
                        "endy0",
                        "p_value0",
                        "trend_text0",
                        "m",
                        "b",
                        "endy",
                        "p_value",
                        "trend_text",
                        "acres",
                        "w_acres",
                    ):
                        coly = col[:-5]
                        tdep_w["y0"] = tdep_w["y0"] + tdep_w[col].astype(str) + " "
                        xlist0 = xlist0 + coly + " "
                tdep_w["x0"] = xlist0

                if tdep_w.empty:
                    log(
                        slug_wilderness, slug_agency, "WHITE", ns + "tdep clipped empty"
                    )
                    empty_file_out = (
                        out_dir + slug_wilderness + "-" + ns + "tdep-empty.txt"
                    )
                    tdep_w = None
                    with uopen(empty_file_out, "a"):
                        os.utime(empty_file_out, None)
                else:
                    fig2 = pyplot.gcf()
                    width = 13
                    fig2.set_size_inches(width, width / 1.618, forward=True)
                    x_vals = [int(value) for value in xlist.split()]
                    ticks = x_vals
                    xmin = min(x_vals)
                    xmax = max(x_vals)
                    if (
                        not tdep_w["x0"].values[0] == tdep_w["x"].values[0]
                    ):  # check if extended period
                        tdep_w[
                            ["m0", "b0", "endy0", "p_value0", "trendtext0", "cols0"]
                        ] = tdep_w.apply(
                            lambda row: pandas.Series(
                                trend2(row["x0"], row["y0"], ["tab:blue", "black", 0.5])
                            ),
                            axis=1,
                        )
                        tdep_w = tdep_w.drop(columns="cols0")
                        ticks = x_vals0

                        tdep_w[
                            ["m", "b", "endy", "p_value", "trendtext", "cols"]
                        ] = tdep_w.apply(
                            lambda row: pandas.Series(
                                trend2(row["x"], row["y"], ["tab:red", "black", 1])
                            ),
                            axis=1,
                        )
                        tdep_w = tdep_w.drop(columns="cols").reset_index(drop=True)

                        tdep_w.to_file(
                            driver=out_driver, filename=out_dir + tdep_w_file
                        )

                        pyplot.xticks(ticks)
                        pyplot.suptitle(
                            which_wilderness[1]
                            + " "
                            + which_wilderness[2]
                            + "\nTotal "
                            + nsname
                            + " Deposition Trend from "
                            + year_formatter(xmin)
                            + " to "
                            + year_formatter(xmax)
                            + "\nwith Total "
                            + nsname
                            + " Deposition Trend from "
                            + year_formatter(xmin0)
                            + " to "
                            + year_formatter(xmax0),
                            y=0.95,
                        )
                        txt = (
                            ns
                            + "tdep trend = "
                            + tdep_w["trendtext"][0]
                            + "\n"
                            + ns
                            + "tdep trend slope  = "
                            + float_formatter(tdep_w["m"][0])
                            + "\n"
                            + ns
                            + "tdep trend p-value = "
                            + p_formatter(tdep_w["p_value"][0])
                        )
                        ax = pyplot.gca()
                        ax.annotate(
                            txt,
                            xy=(0.9, 0.9),
                            xytext=(-100, -0),
                            xycoords=("figure fraction", "figure fraction"),
                            textcoords="offset points",
                            bbox={
                                "facecolor": "white",
                                "edgecolor": "black",
                                "pad": 5.0,
                            },
                            size=8,
                            family="monospace",
                            ha="left",
                            va="bottom",
                        )
                        pyplot.margins(0, 0)
                        fig2.savefig(
                            out_dir
                            + slug_wilderness
                            + "-"
                            + ns
                            + "tdep-graph-extended.png"
                        )
                        fig2.clf()
                        fig2.clear()
                        pyplot.clf()
                        pyplot.cla()
                        pyplot.close()
                        pyplot.gcf().clear()

                    fig2 = pyplot.gcf()
                    width = 13
                    fig2.set_size_inches(width, width / 1.618, forward=True)
                    x_vals = [int(value) for value in xlist.split()]
                    ticks = x_vals
                    xmin = min(x_vals)
                    xmax = max(x_vals)

                    tdep_wgrid[
                        ["m", "b", "endy", "p_value", "trend_text", "cols"]
                    ] = tdep_wgrid.apply(
                        lambda row: pandas.Series(
                            trend2(row["x"], row["y"], ["tab:green", "tab:gray", 0.05])
                        ),
                        axis=1,
                    )
                    tdep_wgrid = tdep_wgrid.drop(columns="cols")

                    trend_max = tdep_wgrid.loc[tdep_wgrid["m"].idxmax()]
                    trend_min = tdep_wgrid.loc[tdep_wgrid["m"].idxmin()]
                    x_list = [int(i) for i in trend_max["x"].split()]

                    maxline_values = [
                        trend_max["m"] * int(i) + trend_max["b"] for i in x_list
                    ]
                    minline_values = [
                        trend_min["m"] * int(i) + trend_min["b"] for i in x_list
                    ]
                    pyplot.plot(
                        x_list,
                        maxline_values,
                        color="tab:green",
                        alpha=1,
                        linewidth=2,
                        label=None,
                    )
                    pyplot.plot(
                        x_list,
                        minline_values,
                        color="tab:green",
                        alpha=1,
                        linewidth=2,
                        label=None,
                    )

                    pyplot.xticks(ticks)

                    tdep_w[
                        ["m", "b", "endy", "p_value", "trend_text", "cols"]
                    ] = tdep_w.apply(
                        lambda row: pandas.Series(
                            trend2(row["x"], row["y"], ["tab:red", "black", 1])
                        ),
                        axis=1,
                    )
                    tdep_w = tdep_w.drop(columns="cols")
                    print("trend2>")
                    print(tdep_w["trend_text"][0])
                    print(tdep_w["p_value"][0])

                    nx = tdep_w["x"].str.split().values.tolist()[0]
                    ny = tdep_w["y"].str.split().values.tolist()[0]
                    dictny = {"years_x": nx, "observations_y": ny}
                    nxy = pandas.DataFrame.from_dict(dictny)
                    nxy["years_x"] = pandas.to_numeric(nxy["years_x"])
                    nxy["observations_y"] = pandas.to_numeric(nxy["observations_y"])
                    nx = nxy["years_x"]
                    ny = nxy["observations_y"]
                    (
                        m,
                        b,
                        endy,
                        p_value,
                        trend_text,
                        mkr_p_value,
                        mkr_trend_text,
                        cols,
                    ) = trender(nx, ny)
                    print("trender>")
                    print(trend_text)
                    print(p_value)
                    jsd = [
                        {
                            "yr_min": year_formatter(min(nx)),
                            "yr_max": year_formatter(max(nx)),
                            "endy": float_formatter(endy),
                            "m": float_formatter(m),
                            "trend": trend_text,
                            "p": p_formatter(p_value),
                        }
                    ]
                    jsc = "".join(str(v) for v in jsd).replace("'", '"')
                    with uopen(
                        out_dir + "index-" + ns + "tdep-new.json", "w"
                    ) as static_file:
                        static_file.write(jsc)
                    # cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                    cols = pandas.DataFrame(
                        {
                            "years_x": cols[:, 0],
                            "observations_y": cols[:, 1],
                            "l_predicted_y": cols[:, 2],
                        }
                    )
                    txt = (
                        str(min(nx))
                        + "-"
                        + str(max(nx))
                        + " : "
                        + trend_text
                        + " "
                        + "(p="
                        + p_formatter(p_value)
                        + ")"
                    )

                    tdep_w.to_csv(
                        out_dir + slug_wilderness + "-" + ns + "tdep-cols.csv",
                        index=False,
                    )
                    tdep_w.to_file(
                        driver=out_driver, filename=out_dir + tdep_w_file, index=False
                    )
                    tdep_csv = tdep_w.drop(
                        columns=[
                            "y0",
                            "x0",
                            "y",
                            "x",
                            "m",
                            "b",
                            "endy",
                            "p_value",
                            "trend_text",
                            "acres",
                            "w_acres",
                            "geometry",
                        ]
                    )
                    tdep_csv.columns = tdep_csv.columns.str.rstrip("_tdep")
                    tdep_csv = tdep_csv.melt(
                        id_vars=[], var_name="year", value_name=ns + "tdep"
                    )
                    tdep_csv.to_csv(
                        out_dir + slug_wilderness + "-" + ns + "tdep.csv", index=False
                    )

                    pyplot.xticks(ticks)
                    pyplot.suptitle(
                        which_wilderness[1]
                        + " "
                        + which_wilderness[2]
                        + "\nTotal "
                        + nsname
                        + " Deposition Trend from "
                        + year_formatter(xmin)
                        + " to "
                        + year_formatter(xmax),
                        y=0.95,
                    )
                    txt = (
                        ns
                        + "tdep trend = "
                        + tdep_w["trend_text"][0]
                        + "\n"
                        + ns
                        + "tdep trend slope  = "
                        + float_formatter(tdep_w["m"][0])
                        + "\n"
                        + ns
                        + "tdep trend p-value = "
                        + p_formatter(tdep_w["p_value"][0])
                    )
                    ax = pyplot.gca()
                    ax.annotate(
                        txt,
                        xy=(0.9, 0.9),
                        xytext=(-100, -0),
                        xycoords=("figure fraction", "figure fraction"),
                        textcoords="offset points",
                        bbox={"facecolor": "white", "edgecolor": "black", "pad": 5.0},
                        size=8,
                        family="monospace",
                        ha="left",
                        va="bottom",
                    )
                    pyplot.margins(0, 0)
                    fig2.savefig(
                        out_dir + slug_wilderness + "-" + ns + "tdep-graph-short.png"
                    )
                    fig2.clf()
                    fig2.clear()
                    pyplot.clf()
                    pyplot.cla()
                    pyplot.close()
                    pyplot.gcf().clear()
                    jsd = [
                        {
                            "yr_min": year_formatter(xmin),
                            "yr_max": year_formatter(xmax),
                            "endy": float_formatter(tdep_w["endy"][0]),
                            "m": float_formatter(tdep_w["m"][0]),
                            "trend": tdep_w["trend_text"][0],
                            "p": p_formatter(tdep_w["p_value"][0]),
                        }
                    ]
                    jsc = "".join(str(v) for v in jsd).replace("'", '"')
                    with uopen(
                        out_dir + "index-" + ns + "tdep.json", "w"
                    ) as static_file:
                        static_file.write(jsc)


def tdep_wilderness_maps_nwps(which_wilderness, ns):  # make maps
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    tdep_national_file = out_dir + ns + "tdep-cut-stack.shp"
    awilderness_file = slug_wilderness + "." + out_ext
    awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext
    awilderness_n_file = slug_wilderness + "-n." + out_ext
    awilderness_n_1mi_file = slug_wilderness + "-n-buffer." + out_ext
    tdep_wgrid_file = slug_wilderness + "-" + ns + "tdep-grid." + out_ext
    tdep_w_file = slug_wilderness + "-" + ns + "tdep." + out_ext
    empty_file_out = out_dir + slug_wilderness + "-" + ns + "tdep-empty.txt"

    if os.path.exists(empty_file_out):
        log(slug_wilderness, slug_agency, "WHITE", ns + "tdep empty")
    else:
        awilderness = geopandas.read_file(out_dir + awilderness_file)
        wilderness_designation_year = awilderness["dd"].iloc[0][0:4]

        if ns == "n":
            nsname = "Nitrogen"
        elif ns == "s":
            nsname = "Sulfur"
        if os.path.exists(out_dir + awilderness_n_file):
            awilderness_n = geopandas.read_file(out_dir + awilderness_n_file)
            awilderness_n = awilderness_n.to_crs(ras_epsg)
            awilderness_n_1mi = geopandas.read_file(out_dir + awilderness_n_1mi_file)
            awilderness_n_1mi = awilderness_n_1mi.to_crs(ras_epsg)
        if os.path.exists(out_dir + tdep_wgrid_file):
            log(slug_wilderness, slug_agency, "WHITE", "reading " + tdep_wgrid_file)
            tdep_wgrid = geopandas.read_file(out_dir + tdep_wgrid_file)
        if os.path.exists(out_dir + tdep_w_file):
            log(slug_wilderness, slug_agency, "WHITE", "reading " + tdep_w_file)
            tdep_w = geopandas.read_file(out_dir + tdep_w_file)

        cmaps = [
            (
                "Perceptually Uniform Sequential",
                ["viridis", "plasma", "inferno", "magma", "cividis"],
            ),
            (
                "Sequential",
                [
                    "Greys",
                    "Purples",
                    "Blues",
                    "Greens",
                    "Oranges",
                    "Reds",
                    "YlOrBr",
                    "YlOrRd",
                    "OrRd",
                    "PuRd",
                    "RdPu",
                    "BuPu",
                    "GnBu",
                    "PuBu",
                    "YlGnBu",
                    "PuBuGn",
                    "BuGn",
                    "YlGn",
                ],
            ),
            (
                "Sequential (2)",
                [
                    "binary",
                    "gist_yarg",
                    "gist_gray",
                    "gray",
                    "bone",
                    "pink",
                    "spring",
                    "summer",
                    "autumn",
                    "winter",
                    "cool",
                    "Wistia",
                    "hot",
                    "afmhot",
                    "gist_heat",
                    "copper",
                ],
            ),
            (
                "Diverging",
                [
                    "PiYG",
                    "PRGn",
                    "BrBG",
                    "PuOr",
                    "RdGy",
                    "RdBu",
                    "RdYlBu",
                    "RdYlGn",
                    "Spectral",
                    "coolwarm",
                    "bwr",
                    "seismic",
                ],
            ),
            ("Cyclic", ["twilight", "twilight_shifted", "hsv"]),
            (
                "Qualitative",
                [
                    "Pastel1",
                    "Pastel2",
                    "Paired",
                    "Accent",
                    "Dark2",
                    "Set1",
                    "Set2",
                    "Set3",
                    "tab10",
                    "tab20",
                    "tab20b",
                    "tab20c",
                ],
            ),
            (
                "Miscellaneous",
                [
                    "flag",
                    "prism",
                    "ocean",
                    "gist_earth",
                    "terrain",
                    "gist_stern",
                    "gnuplot",
                    "gnuplot2",
                    "CMRmap",
                    "cubehelix",
                    "brg",
                    "gist_rainbow",
                    "rainbow",
                    "jet",
                    "turbo",
                    "nipy_spectral",
                    "gist_ncar",
                ],
            ),
        ]
        cmaps = [
            (
                "Diverging",
                [
                    "PiYG",
                    "PRGn",
                    "BrBG",
                    "PuOr",
                    "RdGy",
                    "RdBu",
                    "RdYlBu",
                    "RdYlGn",
                    "Spectral",
                    "coolwarm",
                    "bwr",
                    "seismic",
                ],
            )
        ]

        colors1 = pyplot.cm.Reds(numpy.linspace(0.0, 1, 128))
        colors2 = pyplot.cm.Greens_r(numpy.linspace(0, 1, 128))
        colors3 = numpy.vstack((colors1, colors2))
        mymap = colors.LinearSegmentedColormap.from_list("my_colormap", colors3)

        cmaps = [("Custom", ["mymap"])]

        pmax = tdep_wgrid["p_value"].max()
        pmin = pmax * -1
        # tdep_wgrid['drx'] = numpy.where((tdep_wgrid['trend_text'] == 'increasing'), tdep_wgrid['p_value']*-1, tdep_wgrid['p_value'])
        tdep_wgrid["drx"] = numpy.where(
            (tdep_wgrid["m"] >= 0), tdep_wgrid["p_value"] * -1, tdep_wgrid["p_value"]
        )
        tdep_wgrid["drx"] = numpy.where(
            (tdep_wgrid["trend_text"] == "flat"), 0, tdep_wgrid["drx"]
        )
        for cmap_category, cmap_list in cmaps:
            for cmap in cmap_list:
                width = 13
                hidth = width / 1.618
                fig, ax = pyplot.subplots(figsize=(width, hidth))
                # cax = fig.add_subplot(121)
                # tdep_wgrid.plot(ax=ax, column='drx', cmap=cmap, vmin=pmin, vmax=pmax, edgecolor='white', alpha=1)
                tdep_wgrid.plot(
                    ax=ax,
                    column="drx",
                    cmap=mymap,
                    vmin=pmin,
                    vmax=pmax,
                    edgecolor="white",
                    alpha=0.9,
                )
                flats = tdep_wgrid[tdep_wgrid["trend_text"].isin(["flat"])]
                flats.plot(ax=ax, color="white", edgecolor="white", alpha=0.9)
                awilderness_n.plot(ax=ax, facecolor="none", edgecolor="black")
                xlim = [
                    awilderness_n_1mi.total_bounds[0],
                    awilderness_n_1mi.total_bounds[2],
                ]
                ylim = [
                    awilderness_n_1mi.total_bounds[1],
                    awilderness_n_1mi.total_bounds[3],
                ]
                ax.set_xlim(xlim)
                ax.set_ylim(ylim)
                title = (
                    which_wilderness[1]
                    + " "
                    + which_wilderness[2]
                    + "\n"
                    + nsname
                    + " Total Deposition"
                )
                pyplot.suptitle(title)
                txt = (
                    ns
                    + "tdep trend = "
                    + tdep_w["trend_text"][0]
                    + "\n"
                    + ns
                    + "tdep trend slope  = "
                    + float_formatter(tdep_w["m"][0])
                    + "\n"
                    + ns
                    + "tdep trend p-value = "
                    + p_formatter(tdep_w["p_value"][0])
                )
                pyplot.axis("off")
                fig1 = pyplot.gcf()
                pyplot.subplots_adjust(
                    top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0
                )
                pyplot.margins(0, 0)
                stats = ax.annotate(
                    txt,
                    xy=(0.9, 0.9),
                    xytext=(-100, -0),
                    xycoords=("figure fraction", "figure fraction"),
                    textcoords="offset points",
                    bbox={"facecolor": "white", "edgecolor": "black", "pad": 5.0},
                    size=8,
                    family="monospace",
                    ha="left",
                    va="bottom",
                )

                tdep_national_file = out_dir + ns + "tdep-cut-stack.shp"
                tdep_national = geopandas.read_file(tdep_national_file)
                tdep_national.crs = ras_epsg
                tdep_wgrid_centers = tdep_wgrid.copy()
                tdep_wgrid_centers["geometry"] = tdep_wgrid_centers["geometry"].centroid
                grid_plots = tdep_national.sjoin(
                    tdep_wgrid_centers, how="inner", predicate="contains"
                )

                # grid_plots.plot(ax=ax, edgecolor='tab:red', alpha=1)
                # for index, cell in grid_plots.iterrows():
                #    ax.annotate(text=cell['trend_text'] + '\n' + p_formatter(cell['p_value']), size=4, family='monospace', xy=(cell.geometry.centroid.x, cell.geometry.centroid.y), ha='center')
                # tdep_wgrid.apply(lambda x: ax.annotate(text=tdep_wgrid['trend_text'][0] + '\n' + p_formatter(tdep_wgrid['p_value'][0]), xy=tdep_wgrid.geometry.centroid.coords, ha='center'), axis=1)

                fig1.savefig(out_dir + slug_wilderness + "-" + ns + "tdep-map.png")
                extent_df = tdep_national
                xd = abs(extent_df.total_bounds[0] - extent_df.total_bounds[2])
                yd = abs(extent_df.total_bounds[1] - extent_df.total_bounds[3])
                print(xd)
                print(yd)
                width = xd / 3320
                hidth = yd / 3320
                print(width)
                print(hidth)
                if width <= hidth * 1.1:
                    width = hidth * 1.1
                print(width)
                print(hidth)
                fig1.set_size_inches(width, hidth)
                xlim = [extent_df.total_bounds[0], extent_df.total_bounds[2]]
                ylim = [extent_df.total_bounds[1], extent_df.total_bounds[3]]
                ax.set_xlim(xlim)
                ax.set_ylim(ylim)
                for index, cell in grid_plots.iterrows():
                    ax.annotate(
                        text=cell["trend_text"] + "\n" + p_formatter(cell["p_value"]),
                        size=8,
                        family="monospace",
                        xy=(cell.geometry.centroid.x, cell.geometry.centroid.y),
                        ha="center",
                    )
                fig1.savefig(
                    out_dir + slug_wilderness + "-" + ns + "tdep-map-scaled.png"
                )


def tdep_do_nwps(which_wilderness, ns):
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    awilderness_file = slug_wilderness + "." + out_ext
    awilderness = geopandas.read_file(out_dir + awilderness_file)
    wilderness_designation_year = awilderness["dd"].iloc[0][0:4]
    awilderness_csv_file = slug_wilderness + "-" + ns + "tdep.csv"
    empty_file_out = out_dir + slug_wilderness + "-" + ns + "tdep-empty.txt"

    if os.path.exists(empty_file_out):
        log(
            slug_wilderness,
            slug_agency,
            "WHITE",
            which_wilderness[1] + " " + which_wilderness[2] + " " + ns + " tdep empty",
        )
    else:
        x_list, y_list = csv_to_lists(out_dir + awilderness_csv_file)
        trend_tdep(which_wilderness, ns, wilderness_designation_year, x_list, y_list)


def filter_rows_by_values(df, col, values):
    return df[~df[col].isin(values)]


def csv_to_lists(csv_pathname):
    csv_file = csv_pathname
    df = pandas.read_csv(csv_file)
    df = filter_rows_by_values(
        df,
        "year",
        ["m0", "b0", "endy0", "p_value0", "trend_text0", "trendtext0", "trendtex"],
    ).reindex()
    df = df.rename(columns={df.columns[1]: "tdep"})
    # df = df.rename(index=str, columns={'ntdep': 'tdep'})
    x_list = df.year.tolist()
    y_list = df.tdep.tolist()
    x_list = [int(i) for i in x_list]
    y_list = [float(i) for i in y_list]
    return (x_list, y_list)


def trend_tdep(which_wilderness, ns, wilderness_designation_year, x_list, y_list):
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash
    if ns == "n":
        nsname = "Nitrogen"
    elif ns == "s":
        nsname = "Sulfur"

    # x_list = [2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006]
    # y_list = [0.4921320393, 0.4485062093, 0.4785704492, 0.5799515845, 0.4318211788, 0.5892534651, 0.5541802599, 0.4207925377, 0.4470462941, 0.4843444263, 0.3555758837, 0.4735326792, 0.4311118409, 0.4865506047, 0.4254581905]

    # x_list = [5, 23, 25, 48, 17, 8, 4, 26, 11, 19, 14, 35, 29, 4, 23]
    # y_list = [80, 78, 60, 53, 85, 84, 73, 79, 81, 75, 68, 72, 58, 92, 65]

    dictionary = dict(zip(x_list, y_list))

    dictionary = dict(
        kv for kv in dictionary.items() if kv[0] >= int(wilderness_designation_year)
    )
    print(dictionary)

    x_list = list(dictionary.keys())
    y_list = list(dictionary.values())

    x = numpy.asarray(x_list)
    y = numpy.asarray(y_list)
    X = statsmodels.api.add_constant(x, prepend=False)

    mod = statsmodels.api.OLS(y, X)
    res = mod.fit()
    print(res.summary())
    p_values = res.summary2().tables[1]["P>|t|"]
    txt1 = p_values.x1
    xmin = min(x_list)
    xmax = max(x_list)

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    txt2 = p_value
    print(slope)
    if txt1 > 0.05:
        trend = "stable"
    elif slope > 0:
        trend = "increasing"
    elif slope < 0:
        trend = "decreasing"
    txt = trend + " trend (signifigance: p=" + p_formatter(txt1) + ")"

    pred_ols = res.get_prediction()

    mean = pred_ols.summary_frame()["mean"]
    mean_l = pred_ols.summary_frame()["mean_ci_lower"]  # confidence
    mean_u = pred_ols.summary_frame()["mean_ci_upper"]
    iv_l = pred_ols.summary_frame()["obs_ci_lower"]  # prediction
    iv_u = pred_ols.summary_frame()["obs_ci_upper"]
    beta = [0, 1]

    jsd = [
        {
            "yr_min": year_formatter(xmin),
            "yr_max": year_formatter(xmax),
            "endy": float_formatter(intercept),
            "m": float_formatter(slope),
            "trend": trend,
            "p": p_formatter(p_value),
        }
    ]
    jsc = "".join(str(v) for v in jsd).replace("'", '"')
    with uopen(out_dir + "index-" + ns + "tdep.json", "w") as static_file:
        static_file.write(jsc)

    width = 13
    fig, ax = pyplot.subplots(figsize=(width, width / 1.618))
    fig.set_size_inches(width, width / 1.618, forward=True)

    ax.plot(
        x,
        y,
        color="black",
        linestyle="none",
        marker="o",
        markerfacecolor="black",
        label="observed",
    )
    # ax.plot(x, mean, "b--.", label="true")
    ax.plot(x, res.fittedvalues, c="tab:red", ls="dotted", label="OLS trend")
    ax.plot(x, iv_u, c="tab:blue", alpha=0.2, ls="dotted")
    ax.plot(x, iv_l, c="tab:blue", alpha=0.2, ls="dotted")
    # ax.fill_between(x, iv_u, mean_u, color='tab:green', alpha=0.2)
    # ax.fill_between(x, mean_l, iv_l, color='tab:green', alpha=0.2)
    # ax.plot(x, mean_u, c="tab:blue", ls="--")
    # ax.plot(x, mean_l, c="tab:blue", ls="--")
    ax.fill_between(x, mean_u, mean_l, color="tab:blue", edgecolor=None, alpha=0.2)
    ax.legend(loc="best")
    ax.annotate(
        txt,
        xy=(0.9, 0.9),
        xytext=(-200, -0),
        xycoords=("figure fraction", "figure fraction"),
        textcoords="offset points",
        bbox={"facecolor": "white", "edgecolor": "black", "pad": 5.0},
        size=8,
        family="monospace",
        ha="left",
        va="bottom",
    )

    pyplot.xticks(x)

    pyplot.suptitle(
        which_wilderness[1]
        + " "
        + which_wilderness[2]
        + "\nTotal "
        + nsname
        + " Deposition Trend from "
        + year_formatter(xmin)
        + " to "
        + year_formatter(xmax)
        + "",
        y=0.95,
    )

    fig.savefig(out_dir + slug_wilderness + "-" + ns + "tdep-graph.png")
    pyplot.clf()
    pyplot.close("all")
    # pyplot.gcf().clear()
