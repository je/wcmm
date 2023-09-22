""" Water. """

import json
import shutil

import geopandas
import pandas
import requests
import esri2gpd_ as esri2gpdx
from arcgis2geojson import arcgis2geojson
from django.utils.text import slugify
from matplotlib import colors, lines
from pytopojson import topology

import web
from utils import *

epa303d_gdb = water_dir + "rad_303d_20150501.gdb"  # TODO: update name with year
epa305b_gdb = water_dir + "rad_assd305b_20150618.gdb"  # TODO: update name with year


def watershed_conditions_nwps(water_list):
    """ clips wcc layer to wilderness, calc areas, makes map """
    # wcc = geopandas.read_file(wcc_gdb, layer='WatershedConditionClass')
    rev_date = str(datetime.now().strftime("%Y-%m-%d"))
    wcc = geopandas.read_file(
        web.get_gdb_rev("S_USA.WatershedConditionClass.gdb.zip", rev_date)
    )
    # wcc = geopandas.read_file(water_dir + 'S_USA.WatershedConditionClass.gdb.zip') # legacy clip

    extra_cols = [
        e
        for e in wcc.columns
        if e
        not in [
            "FOREST_NAME",
            "WATERSHED_CODE",
            "WATERSHED_NAME",
            "WATERSHED_CONDITION_FS_AREA",
            "geometry",
            "acres",
        ]
    ]
    wcc = wcc.drop(columns=extra_cols)
    for which_wilderness in water_list:
        slug_wilderness = slugify(which_wilderness[2])
        slug_agency = slugify(which_wilderness[1])
        out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

        awilderness_cea_file = slug_wilderness + "-cea." + out_ext
        awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext
        wcc_file = slug_wilderness + "-wcc." + out_ext
        wcc_full_file = slug_wilderness + "-wcc-full." + out_ext

        awilderness = geopandas.read_file(out_dir + awilderness_cea_file)
        awilderness = awilderness.to_crs(wcc.crs)
        try:
            wcc_inside = geopandas.overlay(wcc, awilderness, how="intersection")
            wcc_full = wcc[wcc["WATERSHED_CODE"].isin(wcc_inside["WATERSHED_CODE"])]
            if not wcc_full.empty:
                wcc_full.to_file(
                    driver=out_driver,
                    encoding="utf-8",
                    filename=out_dir + wcc_full_file,
                )
                log(
                    slug_wilderness,
                    slug_agency,
                    "GREEN",
                    str(wcc_full_file) + " created",
                )
                wcc_inside = wcc_inside.to_crs({"proj": "cea"})
                wcc_inside["acres"] = wcc_inside["geometry"].area / 4046.856
                wcc_inside = wcc_inside.to_crs(awilderness.crs)
                wcc_inside.to_file(
                    driver=out_driver, encoding="utf-8", filename=out_dir + wcc_file
                )
                log(slug_wilderness, slug_agency, "GREEN", str(wcc_file) + " created")

                w_ac = awilderness["acres"].sum()
                ia_ac = wcc_inside.loc[
                    wcc_inside["WATERSHED_CONDITION_FS_AREA"] == "Functioning Properly",
                    "acres",
                ].sum()
                ib_ac = wcc_inside.loc[
                    wcc_inside["WATERSHED_CONDITION_FS_AREA"] == "Functioning at Risk",
                    "acres",
                ].sum()
                ic_ac = wcc_inside.loc[
                    wcc_inside["WATERSHED_CONDITION_FS_AREA"] == "Impaired Function",
                    "acres",
                ].sum()
                ia_pct = "{0:.0f}".format((ia_ac / w_ac) * 100)
                ib_pct = "{0:.0f}".format((ib_ac / w_ac) * 100)
                ic_pct = "{0:.0f}".format((ic_ac / w_ac) * 100)
                w_ac = "{0:.2f}".format(w_ac)
                ia_ac = "{0:.2f}".format(ia_ac)
                ib_ac = "{0:.2f}".format(ib_ac)
                ic_ac = "{0:.2f}".format(ic_ac)
                zeros = len(str(int(float(w_ac)))) - len(str(int(float(ia_ac))))
                if zeros > 0:
                    space = ""
                    space += " " * zeros
                    ia_ac = space + ia_ac
                zeros = len(str(int(float(w_ac)))) - len(str(int(float(ib_ac))))
                if zeros > 0:
                    space = ""
                    space += " " * zeros
                    ib_ac = space + ib_ac
                zeros = len(str(int(float(w_ac)))) - len(str(int(float(ic_ac))))
                if zeros > 0:
                    space = ""
                    space += " " * zeros
                    ic_ac = space + ic_ac
                mxp = max(
                    len(str(int(float(ia_pct)))),
                    len(str(int(float(ib_pct)))),
                    len(str(int(float(ic_pct)))),
                )
                zeros = mxp - len(str(int(float(ia_pct))))
                if zeros > 0:
                    space = ""
                    space += " " * zeros
                    ia_pct = space + ia_pct
                zeros = mxp - len(str(int(float(ib_pct))))
                if zeros > 0:
                    space = ""
                    space += " " * zeros
                    ib_pct = space + ib_pct
                zeros = mxp - len(str(int(float(ic_pct))))
                if zeros > 0:
                    space = ""
                    space += " " * zeros
                    ic_pct = space + ic_pct
                width = 13

                jsd = [
                    {
                        "w_ac": w_ac,
                        "ia_ac": ia_ac,
                        "ib_ac": ib_ac,
                        "ic_ac": ic_ac,
                        "ia_pct": ia_pct,
                        "ib_pct": ib_pct,
                        "ic_pct": ic_pct,
                    }
                ]
                jsc = "".join(str(v) for v in jsd).replace("'", '"')
                with uopen(out_dir + "index-wcc.json", "w") as static_file:
                    static_file.write(jsc)

                awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
                wcc_fullc = wcc_full.copy()
                wcc_insidec = wcc_inside.copy()
                wcc_colors = {
                    "Functioning Properly": "green",
                    "Functioning at Risk": "orange",
                    "Impaired Function": "red",
                }

                extra_cols = [
                    e
                    for e in wcc_insidec.columns
                    if e
                    not in [
                        "WATERSHED_CODE",
                        "WATERSHED_NAME",
                        "WATERSHED_CONDITION_FS_AREA",
                        "acres",
                    ]
                ]
                wcccv = wcc_insidec.drop(columns=extra_cols).rename(
                    index=str, columns={"acres": "acres_inside_wilderness",}
                )
                wcccv.to_csv(out_dir + slug_wilderness + "-wcc.csv")
                axis = wcc_fullc.plot(
                    color=[
                        wcc_colors[i]
                        for i in wcc_insidec["WATERSHED_CONDITION_FS_AREA"]
                    ],
                    edgecolor="white",
                    alpha=0.2,
                    figsize=(width, width / 1.618),
                )
                wcc_green = wcc_insidec[
                    wcc_insidec["WATERSHED_CONDITION_FS_AREA"] == "Functioning Properly"
                ]
                wcc_orange = wcc_insidec[
                    wcc_insidec["WATERSHED_CONDITION_FS_AREA"] == "Functioning at Risk"
                ]
                wcc_red = wcc_insidec[
                    wcc_insidec["WATERSHED_CONDITION_FS_AREA"] == "Impaired Function"
                ]
                if not wcc_green.empty:
                    wcc_green.plot(
                        ax=axis,
                        color="green",
                        edgecolor="white",
                        alpha=0.8,
                        legend=False,
                    )
                if not wcc_orange.empty:
                    wcc_orange.plot(
                        ax=axis,
                        color="orange",
                        edgecolor="white",
                        alpha=0.8,
                        legend=False,
                    )
                if not wcc_red.empty:
                    wcc_red.plot(
                        ax=axis, color="red", edgecolor="white", alpha=0.8, legend=False
                    )
                awilderness.plot(ax=axis, color="none", edgecolor="black", alpha=1)

                xlim = [
                    awilderness_1mi.total_bounds[0],
                    awilderness_1mi.total_bounds[2],
                ]
                ylim = [
                    awilderness_1mi.total_bounds[1],
                    awilderness_1mi.total_bounds[3],
                ]
                pyplot.suptitle(
                    "Watershed condition class in "
                    + slug_agency
                    + " "
                    + slug_wilderness
                )
                txt = (
                    str(w_ac)
                    + " acres total wilderness area"
                    + "\n"
                    + str(ia_ac)
                    + " acres 'functioning properly' ("
                    + str(ia_pct)
                    + "%)"
                    + "\n"
                    + str(ib_ac)
                    + " acres 'functioning at risk'  ("
                    + str(ib_pct)
                    + "%)"
                    + "\n"
                    + str(ic_ac)
                    + " acres 'impaired function'    ("
                    + str(ic_pct)
                    + "%)"
                )
                axis.annotate(
                    txt,
                    xy=(1, 1),
                    xytext=(-20, -10),
                    xycoords=("figure fraction", "axes fraction"),
                    textcoords="offset points",
                    bbox={"facecolor": "white", "edgecolor": "black", "pad": 5.0},
                    size=8,
                    family="monospace",
                    ha="right",
                    va="top",
                )
                axis.set_xlim(xlim)
                axis.set_ylim(ylim)
                pyplot.axis("off")
                fig1 = pyplot.gcf()
                pyplot.subplots_adjust(
                    top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0
                )
                pyplot.margins(0, 0)
                fig1.savefig(out_dir + slug_wilderness + "-wcc.png")

                awilderness_box = awilderness_1mi.copy()
                awilderness_box = awilderness_1mi.to_crs({"proj": "cea"})
                awilderness_box["geometry"] = awilderness_box.geometry.buffer(0.1609344)
                awilderness_box = awilderness_box.to_crs(awilderness_1mi.crs)
                xlim2 = [
                    awilderness_box.total_bounds[0],
                    awilderness_box.total_bounds[2],
                ]
                ylim2 = [
                    awilderness_box.total_bounds[1],
                    awilderness_box.total_bounds[3],
                ]
                awilderness_box["geometry"] = awilderness_box.geometry.envelope
                fill = colors.colorConverter.to_rgba("tab:brown", alpha=0.1)
                try_add_basemap(
                    slug_wilderness, slug_agency, axis, awilderness.crs.to_string()
                )
                awilderness.plot(
                    ax=axis, color="none", edgecolor="black", linewidth=1.0, alpha=0.9
                )
                axis.set_xlim(xlim)
                axis.set_ylim(ylim)
                fig1.savefig(out_dir + slug_wilderness + "-wcc-base.png")
                own_blm_file = slug_wilderness + "-own-blm." + out_ext
                own_usfs_file = slug_wilderness + "-own-usfs." + out_ext
                if os.path.exists(out_dir + own_blm_file):
                    blm_inside = geopandas.read_file(out_dir + own_blm_file)
                if os.path.exists(out_dir + own_usfs_file):
                    usfs_inside = geopandas.read_file(out_dir + own_usfs_file)
                bfill = colors.colorConverter.to_rgba("tab:brown", alpha=0.2)
                ufill = colors.colorConverter.to_rgba("tab:green", alpha=0.2)
                try:
                    usfs_inside.plot(
                        ax=axis, color=ufill, edgecolor="white", linewidth=2.0,
                    )
                except:
                    pass
                try:
                    blm_inside.plot(
                        ax=axis, color=bfill, edgecolor="white", linewidth=2.0,
                    )
                except:
                    pass
                fig1.savefig(out_dir + slug_wilderness + "-wcc-base-own.png")
                fig1.clf()
                pyplot.clf()
                pyplot.cla()
                pyplot.close()
            else:
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    slug_wilderness + " wcc clipped empty",
                )
                empty_file_out = out_dir + slug_wilderness + "-wcc-empty.txt"
                with uopen(empty_file_out, "a"):
                    os.utime(empty_file_out, None)

        except KeyError:
            log(
                slug_wilderness,
                slug_agency,
                "WHITE",
                slug_wilderness + " wcc clipped empty",
            )
            empty_file_out = out_dir + slug_wilderness + "-wcc-empty.txt"
            with uopen(empty_file_out, "a"):
                os.utime(empty_file_out, None)


def poly_to_esripoly(poly):
    """ shapely polygon to esripoly polygon """
    boundary_geom = poly["geometry"][0]
    if boundary_geom.geom_type == "MultiPolygon":
        geoms = boundary_geom.geoms
        boundary_ext_coords = []
        for b in geoms:
            b = b.simplify(
                0.001, preserve_topology=False
            )  # maybe not, close enough for bufffering tho
            b_ext_coords = list(b.exterior.coords)
            b_ext_coords = [list(i) for i in b_ext_coords]
            b_ext_coords = numpy.round(b_ext_coords, 3).tolist()
            boundary_ext_coords.extend(b_ext_coords)
    else:
        boundary_geom = boundary_geom.simplify(0.001, preserve_topology=False)
        boundary_ext_coords = list(boundary_geom.exterior.coords)
        boundary_ext_coords = [list(i) for i in boundary_ext_coords]
        boundary_ext_coords = numpy.round(boundary_ext_coords, 3).tolist()
    esri_json_geom = str(
        {"rings": [boundary_ext_coords], "spatialReference": {"wkid": 4326}}
    )
    esri_json_geom = esri_json_geom.replace(" ", "").replace("'", '"')
    return esri_json_geom


def attains_geoms_to_local_nwps(wilderness_list, rev_date):
    """ 1: pull waterbody geoms from epa attains services """
    all_wilderness_list = []
    for which_wilderness in wilderness_list:
        print(which_wilderness)
        slug_wilderness = slugify(which_wilderness[2])
        slug_agency = slugify(which_wilderness[1])
        out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

        awilderness_file = slug_wilderness + "." + out_ext
        awilderness_cea_file = slug_wilderness + "-cea." + out_ext
        awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext
        awilderness = geopandas.read_file(out_dir + awilderness_file)
        awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
        awilderness_1mi["geometry"] = awilderness_1mi.unary_union.convex_hull

        awilderness_1mi_ep = poly_to_esripoly(awilderness_1mi)
        url_pt = "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/0"
        url_ln = "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/1"
        url_pl = "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/2"
        url_ca = "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/3"

        url_list = []
        url_list.append(
            [
                "_ty",
                "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/9",
            ]
        )  # water types
        url_list.append(
            [
                "_su",
                "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/4",
            ]
        )  # attribute summary
        # url_list.append(['_co', "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/5"]) # control
        url_list.append(
            [
                "_ct",
                "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/6",
            ]
        )  # catchment
        url_list.append(
            [
                "_hu",
                "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/7",
            ]
        )  # huc12
        url_list.append(
            [
                "_ap",
                "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer/8",
            ]
        )  # parameters

        # rev_date = str(datetime.now().strftime('%Y-%m-%d'))
        if not os.path.exists(water_dir + rev_date + slash):
            os.makedirs(water_dir + rev_date + slash)
            print("creating folder " + rev_date)
        if not os.path.exists(water_dir + rev_date + slash + slug_agency + slash):
            os.makedirs(water_dir + rev_date + slash + slug_agency + slash)
            print("creating folder " + rev_date + slash + slug_agency + slash)
        if awilderness_1mi.geometry[0].geom_type == "MultiPolygon":
            exploded = awilderness_1mi.explode()
            row = exploded.itertuples()
            my_dict = {}
            gdf = geopandas.GeoDataFrame()
            for row in exploded.itertuples():
                poly = pandas.DataFrame(
                    [list(row)[1:]], columns=exploded.columns, index=[row[0]]
                )
                poly_ep = poly_to_esripoly(poly)
                gdf = esri2gpdx.get(url_pl, geometry=awilderness_1mi_ep, inSR=54034)
                gdf = gdf.append(gdf)

        gdf = esri2gpdx.get(url_pl, geometry=awilderness_1mi_ep, inSR=54034)
        if not gdf.empty:
            log(
                None,
                None,
                "CYAN",
                "writing "
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pl.json",
            )
            assmnt_joinkey_list_pl = gdf.assmnt_joinkey.tolist()
            gdf.to_file(
                driver="GeoJSON",
                filename=water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pl.json",
            )
        else:
            assmnt_joinkey_list_pl = []
            with uopen(
                water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pl.txt",
                "a",
            ):
                os.utime(
                    water_dir
                    + rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + "_pl.txt",
                    None,
                )
            log(
                None,
                None,
                "WHITE",
                "empty "
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pl.json",
            )
        gdf = esri2gpdx.get(url_pt, geometry=awilderness_1mi_ep, inSR=54034)
        if not gdf.empty:
            log(
                None,
                None,
                "CYAN",
                "writing "
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pt.json",
            )
            assmnt_joinkey_list_pt = gdf.assmnt_joinkey.tolist()
            gdf.to_file(
                driver="GeoJSON",
                filename=water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pt.json",
            )
        else:
            assmnt_joinkey_list_pt = []
            with uopen(
                water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pt.txt",
                "a",
            ):
                os.utime(
                    water_dir
                    + rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + "_pt.txt",
                    None,
                )
            log(
                None,
                None,
                "WHITE",
                "empty "
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pt.json",
            )
        gdf = esri2gpdx.get(url_ln, geometry=awilderness_1mi_ep, inSR=54034)
        if not gdf.empty:
            assmnt_joinkey_list_ln = gdf.assmnt_joinkey.tolist()
            log(
                None,
                None,
                "CYAN",
                "writing "
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ln.json",
            )
            gdf.to_file(
                driver="GeoJSON",
                filename=water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ln.json",
            )
        else:
            assmnt_joinkey_list_ln = []
            with uopen(
                water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ln.txt",
                "a",
            ):
                os.utime(
                    water_dir
                    + rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + "_ln.txt",
                    None,
                )
            log(
                None,
                None,
                "WHITE",
                "empty "
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ln.json",
            )
        gdf = esri2gpdx.get(url_ca, geometry=awilderness_1mi_ep, inSR=54034)
        if not gdf.empty:
            log(
                None,
                None,
                "CYAN",
                "writing "
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ca.json",
            )
            gdf.to_file(
                driver="GeoJSON",
                filename=water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ca.json",
            )
        else:
            with uopen(
                water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ca.txt",
                "a",
            ):
                os.utime(
                    water_dir
                    + rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + "_ca.txt",
                    None,
                )
            log(
                None,
                None,
                "WHITE",
                "empty "
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ca.json",
            )

        assmnt_joinkey_list = list(
            set(
                assmnt_joinkey_list_pl + assmnt_joinkey_list_pt + assmnt_joinkey_list_ln
            )
        )
        for url in url_list:
            if assmnt_joinkey_list:
                # print(len(assmnt_joinkey_list))
                lists_ = [
                    assmnt_joinkey_list[i : i + 100]
                    for i in range(0, len(assmnt_joinkey_list), 100)
                ]
                gdf = geopandas.GeoDataFrame()
                for list_ in lists_:
                    assmnt_joinkey_sql = "assmnt_joinkey IN " + str(list_).replace(
                        "[", "("
                    ).replace("]", ")")
                    gdf_ = esri2gpdx.get(url[1], where=assmnt_joinkey_sql)
                    # gdf = gdf.append(gdf_) # deprec for below
                    gdf = geopandas.GeoDataFrame(
                        pandas.concat([gdf, gdf_], ignore_index=True)
                    )  # , crs=gdf_.crs)
            else:
                gdf = geopandas.GeoDataFrame()
            if not gdf.empty:
                log(
                    None,
                    None,
                    "CYAN",
                    "writing "
                    + rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + url[0]
                    + ".json",
                )
                gdf.to_file(
                    driver="GeoJSON",
                    filename=water_dir
                    + rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + url[0]
                    + ".json",
                )
            else:
                with uopen(
                    water_dir
                    + rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + url[0]
                    + ".txt",
                    "a",
                ):
                    os.utime(
                        water_dir
                        + rev_date
                        + slash
                        + slug_agency
                        + slash
                        + slug_wilderness
                        + url[0]
                        + ".txt",
                        None,
                    )
                log(
                    None,
                    None,
                    "WHITE",
                    "empty "
                    + rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + url[0]
                    + ".json",
                )


def get_file_rev_nwps(slug_agency, gdb_name, rev_date):
    """ get latest rev """
    gdb_name = gdb_name
    rev_datetime = datetime.strptime(rev_date, "%Y-%m-%d")
    short_txt = gdb_name.split(".")[-2] + ".txt"
    dfs = [
        os.path.join(root, name)
        for root, dirs, files in os.walk(
            water_dir + rev_date + slash + slug_agency + slash
        )
        for name in files
        if name in (gdb_name, short_txt)
    ]
    df = pandas.DataFrame({"path": dfs})
    df["folder"] = df["path"].str.replace(gdb_name, "", regex=False)
    df["agency"] = df["folder"].str.split(slash).str[-2]
    df["parent"] = df["folder"].str.split(slash).str[-3]
    df["date"] = pandas.to_datetime(df["parent"])
    youngest = max(dt for dt in df["date"] if dt <= rev_datetime)
    dfn = df[df["date"] == youngest]["path"]
    path = dfn.values[0]
    return path


def attains_waters_nwps(water_list, rev_date):
    """ 5: local latest attains to waterbody maps """
    not_waterbody = [
        "BEACH",
        "COASTAL & BAY SHORELINE",
        "COASTAL",
        "GREAT LAKES BEACH",
        "GREAT LAKES SHORELINE",
        "INLAND LAKE SHORELINE",
        "SPRING",
        "SPRINGSHED",
        "WATERSHED",
        "WETLAND",
        "WETLANDS, FRESHWATER",
        "WETLANDS, TIDAL",
    ]
    not_lake_or_stream = [
        "BAY",
        "ESTUARY",
        "GREAT LAKES BAYS AND HARBORS",
        "GREAT LAKES OPEN WATER",
        "IMPOUNDMENT",
        "LAGOON",
        "OCEAN",
        "OCEAN/NEAR COASTAL",
        "SOUND",
    ]
    def_lake = [
        "LAKE",
        "LAKE, FRESHWATER",
        "LAKE, PLAYA",
        "LAKE, SALINE",
        "LAKE, SPRINGS",
        "LAKE, WILD RICE",
        "LAKE/RESERVOIR/POND",
        "POND",
        "RESERVOIR EMBAYMENT",
        "RESERVOIR",
    ]
    def_stream = [
        "CONNECTING CHANNEL",
        "CREEK",
        "DITCH OR CANAL",
        "RIVER",
        "STREAM",
        "STREAM, COASTAL",
        "STREAM, EPHEMERAL",
        "STREAM, INTERMITTENT",
        "STREAM, PERENNIAL",
        "STREAM, TIDAL",
        "STREAM/CREEK/RIVER",
    ]
    for which_wilderness in water_list:
        slug_wilderness = slugify(which_wilderness[2])
        slug_agency = slugify(which_wilderness[1])
        out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

        awilderness_file = slug_wilderness + "." + out_ext
        awilderness_cea_file = slug_wilderness + "-cea." + out_ext
        awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext

        awilderness = geopandas.read_file(out_dir + awilderness_file)
        awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)

        url_list = []
        url_list.append(["_su"])  # attribute summary
        # url_list.append(['_co']) # control
        url_list.append(["_ct"])  # catchment
        url_list.append(["_hu"])  # huc12
        url_list.append(["_ap"])  # parameters

        a_pl = get_file_rev_nwps(slug_agency, slug_wilderness + "_pl.json", rev_date)
        a_ln = get_file_rev_nwps(slug_agency, slug_wilderness + "_ln.json", rev_date)
        a_pt = get_file_rev_nwps(slug_agency, slug_wilderness + "_pt.json", rev_date)
        a_ca = get_file_rev_nwps(slug_agency, slug_wilderness + "_ca.json", rev_date)
        a_ty = get_file_rev_nwps(slug_agency, slug_wilderness + "_ty.json", rev_date)

        log(None, None, "WHITE", "reading attains")
        if a_pl.split(".")[-1] == "txt":
            # if os.path.exists(water_dir + rev_date + slash + slug_wilderness + '_pl.txt'):
            pl = geopandas.GeoDataFrame(columns=["geometry"], geometry="geometry")
            pl_assessed_count = 0
            pl_assessed_acres = 0
            pl_impaired_count = 0
            pl_impaired_acres = 0
            pl_ty_lake = geopandas.GeoDataFrame(
                columns=["geometry"], crs=awilderness.crs
            )
            log(
                None,
                None,
                "WHITE",
                rev_date + slash + slug_wilderness + "_pl.json empty",
            )
        else:
            pl = geopandas.read_file(a_pl)
            ty = geopandas.read_file(a_ty)
            # pl = geopandas.read_file(water_dir + rev_date + slash + slug_wilderness + '_pl.json')
            # ty = geopandas.read_file(water_dir + rev_date + slash + slug_wilderness + '_ty.json')
            ty = ty[["assmnt_joinkey", "watertype"]].copy()
            pl_ty = pl.merge(ty, on="assmnt_joinkey", how="left")
            pl_ty_lake = pl_ty[pl_ty["watertype"].isin(def_lake)]
            pl = geopandas.GeoDataFrame(pl_ty_lake)
            if pl.empty:
                pl_assessed_count = 0
                pl_assessed_acres = 0
                pl_impaired_count = 0
                pl_impaired_acres = 0
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    rev_date + slash + slug_wilderness + "_pl.json lakes empty",
                )
            else:
                pl = pl.to_crs(awilderness.crs)
                pl_assessed = pl[pl["isassessed"] == "Y"]
                pl_impaired = pl[pl["isimpaired"] == "Y"]
                pl_in = geopandas.overlay(pl, awilderness, how="intersection")
                if pl_in.empty:
                    pl_assessed_count = 0
                    pl_assessed_acres = 0
                    pl_impaired_count = 0
                    pl_impaired_acres = 0
                    log(
                        slug_wilderness,
                        slug_agency,
                        "WHITE",
                        rev_date + slash + slug_wilderness + "_pl_in.json lakes empty",
                    )
                else:
                    pl_in = pl_in.to_crs({"proj": "cea"})
                    pl_in["acres_cea"] = pl_in["geometry"].area * 0.000247105
                    pl_in.to_file(
                        driver="GeoJSON",
                        filename=out_dir + slug_wilderness + "_pl_in.json",
                    )
                    pl_in_assessed = pl_in[pl_in["isassessed"] == "Y"]
                    pl_in_impaired = pl_in[pl_in["isimpaired"] == "Y"]
                    pl_in_assessed = pl_in_assessed.to_crs(awilderness.crs)
                    pl_in_impaired = pl_in_impaired.to_crs(awilderness.crs)
                    pl_assessed_count = pl_in_assessed.shape[0]
                    pl_assessed_acres = pl_in_assessed["acres_cea"].sum()
                    pl_assessed_acres = "{0:.2f}".format(pl_assessed_acres)
                    pl_impaired_count = pl_in_impaired.shape[0]
                    pl_impaired_acres = pl_in_impaired["acres_cea"].sum()
                    pl_impaired_acres = "{0:.2f}".format(pl_impaired_acres)
                    pl_in_groups = pl_in.groupby(
                        [
                            "organizationname",
                            "assessmentunitidentifier",
                            "assessmentunitname",
                            "reportingcycle",
                            "isassessed",
                            "isimpaired",
                            "ircategory",
                        ],
                        as_index=False,
                    ).agg({"acres_cea": ["sum", "count"]})
                    # pl_in_groups = (pl_in.groupby(['isassessed', 'isimpaired', 'ircategory',], as_index=False).agg({'acres_cea': ['sum', 'count']}))
                    pl_in_groups.columns = pl_in_groups.columns.map("_".join).str.strip(
                        "_"
                    )
                    pl_in_groups.to_csv(
                        out_dir + slug_wilderness + "-pl_in_groups.csv", index=False
                    )
                    extra_cols = [e for e in pl_in.columns if e in ["geometry"]]
                    pl_in = pl_in.drop(columns=extra_cols)
                    pl_in.to_csv(out_dir + slug_wilderness + "-pl_in.csv", index=False)
        if a_ln.split(".")[-1] == "txt":
            # if os.path.exists(water_dir + rev_date + slash + slug_wilderness + '_ln.txt'):
            ln = geopandas.GeoDataFrame(columns=["geometry"], geometry="geometry")
            ln_assessed_count = 0
            ln_assessed_miles = 0
            ln_impaired_count = 0
            ln_impaired_miles = 0
            log(
                None,
                None,
                "WHITE",
                rev_date + slash + slug_wilderness + "_ln.json empty",
            )
        else:
            ln = geopandas.read_file(a_ln)
            ty = geopandas.read_file(a_ty)
            # ln = geopandas.read_file(water_dir + rev_date + slash + slug_wilderness + '_ln.json')
            # ty = geopandas.read_file(water_dir + rev_date + slash + slug_wilderness + '_ty.json')
            ty = ty[["assmnt_joinkey", "watertype"]].copy()
            ln_ty = ln.merge(ty, on="assmnt_joinkey", how="left")
            ln_ty_stream = ln_ty[ln_ty["watertype"].isin(def_stream)]
            ln = geopandas.GeoDataFrame(ln_ty_stream, crs=ln.crs)
            pl_ty_lake = pl_ty_lake.to_crs(ln.crs)
            if not pl_ty_lake.empty and not ln.empty:
                ln = geopandas.overlay(ln, pl_ty_lake, how="difference")
            if ln.empty:
                ln_assessed_count = 0
                ln_assessed_miles = 0
                ln_impaired_count = 0
                ln_impaired_miles = 0
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    rev_date + slash + slug_wilderness + "_ln.json streams empty",
                )
            else:
                ln = ln.to_crs(awilderness.crs)
                ln_assessed = ln[ln["isassessed"] == "Y"]
                ln_impaired = ln[ln["isimpaired"] == "Y"]
                ln_in = geopandas.clip(ln, awilderness, keep_geom_type=True)
                if ln_in.empty:
                    ln_assessed_count = 0
                    ln_assessed_miles = 0
                    ln_impaired_count = 0
                    ln_impaired_miles = 0
                    log(
                        slug_wilderness,
                        slug_agency,
                        "WHITE",
                        rev_date
                        + slash
                        + slug_wilderness
                        + "_ln_in.json streams empty",
                    )
                else:
                    ln_in = ln_in.to_crs({"proj": "cea"})
                    ln_in["miles_cea"] = ln_in["geometry"].length / 1609.344
                    ln_in.to_file(
                        driver="GeoJSON",
                        filename=out_dir + slug_wilderness + "_ln_in.json",
                    )
                    ln_in_assessed = ln_in[ln_in["isassessed"] == "Y"]
                    ln_in_impaired = ln_in[ln_in["isimpaired"] == "Y"]
                    ln_in_assessed = ln_in_assessed.to_crs(awilderness.crs)
                    ln_in_impaired = ln_in_impaired.to_crs(awilderness.crs)
                    ln_assessed_count = ln_in_assessed.shape[0]
                    ln_assessed_miles = ln_in_assessed["miles_cea"].sum()
                    ln_assessed_miles = "{0:.2f}".format(ln_assessed_miles)
                    ln_impaired_count = ln_in_impaired.shape[0]
                    ln_impaired_miles = ln_in_impaired["miles_cea"].sum()
                    ln_impaired_miles = "{0:.2f}".format(ln_impaired_miles)
                    ln_in_groups = ln_in.groupby(
                        [
                            "organizationname",
                            "assessmentunitidentifier",
                            "assessmentunitname",
                            "reportingcycle",
                            "isassessed",
                            "isimpaired",
                            "ircategory",
                        ],
                        as_index=False,
                    ).agg({"miles_cea": "sum"})
                    # ln_in_groups = (ln_in.groupby(['isassessed', 'isimpaired', 'ircategory',], as_index=False).agg({'miles_cea' : 'sum'}))
                    ln_in_groups.to_csv(
                        out_dir + slug_wilderness + "-ln_in_groups.csv", index=False
                    )
                    extra_cols = [e for e in ln_in.columns if e in ["geometry"]]
                    ln_in = ln_in.drop(columns=extra_cols)
                    ln_in.to_csv(out_dir + slug_wilderness + "-ln_in.csv", index=False)
        if a_pt.split(".")[-1] == "txt":
            # if os.path.exists(water_dir + rev_date + slash + slug_wilderness + '_pt.txt'):
            pt = geopandas.GeoDataFrame()
            log(
                slug_wilderness,
                slug_agency,
                "WHITE",
                rev_date + slash + slug_wilderness + "_pt.json empty",
            )
        else:
            pt = geopandas.read_file(a_pt)
            # pt = geopandas.read_file(water_dir + rev_date + slash + slug_wilderness + '_pt.json')
        if a_ca.split(".")[-1] == "txt":
            # if os.path.exists(water_dir + rev_date + slash + slug_wilderness + '_ca.txt'):
            ca = geopandas.GeoDataFrame()
            log(
                slug_wilderness,
                slug_agency,
                "WHITE",
                rev_date + slash + slug_wilderness + "_ca.json empty",
            )
        else:
            ca = geopandas.read_file(a_ca)
            # ca = geopandas.read_file(water_dir + rev_date + slash + slug_wilderness + '_ca.json')
            ca_assessed = ca[ca["isassessed"] == "Y"]
            ca_impaired = ca[ca["isimpaired"] == "Y"]
            ca = ca.to_crs(awilderness.crs)
            ca_in = geopandas.overlay(ca, awilderness, how="intersection")
        jsd = [
            {
                "ln_impaired_miles": str(ln_impaired_miles),
                "ln_assessed_miles": str(ln_assessed_miles),
                "pl_impaired_count": str(pl_impaired_count),
                "pl_assessed_count": str(pl_assessed_count),
            }
        ]
        jsc = "".join(str(v) for v in jsd).replace("'", '"')
        with uopen(out_dir + "index-iw.json", "w") as static_file:
            static_file.write(jsc)

        width = 13
        axis = awilderness_1mi.plot(
            color="none", edgecolor="none", alpha=0.0, figsize=(width, width / 1.618)
        )
        try:
            ca.plot(
                ax=axis,
                color="tab:grey",
                edgecolor="tab:grey",
                alpha=0.1,
                linewidth=0.5,
            )
            ca_in.plot(
                ax=axis,
                color="tab:grey",
                edgecolor="tab:grey",
                alpha=0.5,
                linewidth=0.5,
            )
        except:
            pass
        try:
            pl_assessed.plot(
                ax=axis, color="tab:blue", edgecolor="tab:blue", alpha=1, linewidth=0.5
            )
            pl_impaired.plot(
                ax=axis, color="tab:red", edgecolor="tab:red", alpha=1, linewidth=0.5
            )
            pl_in_assessed.plot(
                ax=axis, color="tab:blue", edgecolor="tab:blue", alpha=1, linewidth=2
            )
            pl_in_impaired.plot(
                ax=axis, color="tab:red", edgecolor="tab:red", alpha=1, linewidth=2
            )
        except:
            pass
        try:
            ln_assessed.plot(
                ax=axis,
                color="tab:blue",
                edgecolor="tab:blue",
                alpha=1,
                legend=False,
                linewidth=0.5,
            )
            ln_impaired.plot(
                ax=axis,
                color="tab:red",
                edgecolor="tab:red",
                alpha=1,
                legend=False,
                linewidth=0.5,
            )
            ln_in_assessed.plot(
                ax=axis,
                color="tab:blue",
                edgecolor="tab:blue",
                alpha=1,
                legend=False,
                linewidth=2,
            )
            ln_in_impaired.plot(
                ax=axis,
                color="tab:red",
                edgecolor="tab:red",
                alpha=1,
                legend=False,
                linewidth=2,
            )
        except:
            pass
        awilderness.plot(ax=axis, color="none", edgecolor="black", alpha=1)
        xlim = [awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]]
        ylim = [awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]]
        pyplot.suptitle(
            "Extent of waterbodies with impaired water quality in "
            + which_wilderness[2]
        )
        txt = (
            str(ln_impaired_miles)
            + " miles impaired streams of\n "
            + str(ln_assessed_miles)
            + " miles assessed streams\n"
            + str(pl_impaired_acres)
            + " acres in "
            + str(pl_impaired_count)
            + " impaired lakes of\n "
            + str(pl_assessed_acres)
            + " acres in "
            + str(pl_assessed_count)
            + " assessed lakes"
        )
        axis.annotate(
            txt,
            xy=(1, 1),
            xytext=(-20, -10),
            xycoords=("figure fraction", "axes fraction"),
            textcoords="offset points",
            bbox={"facecolor": "white", "edgecolor": "black", "pad": 5.0},
            size=8,
            family="monospace",
            ha="right",
            va="top",
        )
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        pyplot.axis("off")
        fig1 = pyplot.gcf()
        pyplot.subplots_adjust(top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0)
        pyplot.margins(0, 0)
        fig1.savefig(out_dir + slug_wilderness + "-waters.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            str(slug_wilderness) + "-waters.png created",
        )

        # tdep_national_file = out_dir + "ntdep-cut-stack.shp"
        # tdep_national = geopandas.read_file(tdep_national_file)
        # tdep_national.crs = ras_epsg
        # extent_df = tdep_national
        # xd = abs(extent_df.total_bounds[0] - extent_df.total_bounds[2])
        # yd = abs(extent_df.total_bounds[1] - extent_df.total_bounds[3])
        # width = xd / 3320
        # hidth = yd / 3320
        # if width <= hidth * 1.1:
        #    width = hidth * 1.1
        # fig1.set_size_inches(width, hidth)
        # fig1.savefig(out_dir + slug_wilderness + "-waters-" + "scaled" + ".png")
        # log(
        #    slug_wilderness,
        #    "GREEN",
        #    str(slug_wilderness) + "-waters-scaled.png created",
        # )
        # quit()

        awilderness_box = awilderness_1mi.copy()
        awilderness_box = awilderness_1mi.to_crs({"proj": "cea"})
        awilderness_box["geometry"] = awilderness_box.geometry.buffer(0.1609344)
        awilderness_box = awilderness_box.to_crs(awilderness_1mi.crs)
        xlim2 = [awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]]
        ylim2 = [awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]]
        axis.set_xlim(xlim2)
        axis.set_ylim(ylim2)
        try_add_basemap(slug_wilderness, slug_agency, axis, awilderness.crs.to_string())
        awilderness.plot(
            ax=axis, color="none", edgecolor="black", linewidth=1.0, alpha=0.9
        )
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        fig1.savefig(out_dir + slug_wilderness + "-waters-base.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            str(slug_wilderness) + "-waters-base.png created",
        )

        width = 13  # streams
        axis = awilderness_1mi.plot(
            color="none", edgecolor="none", alpha=0.0, figsize=(width, width / 1.618)
        )
        try:
            ln_assessed.plot(
                ax=axis,
                color="tab:blue",
                edgecolor="tab:blue",
                alpha=1,
                legend=False,
                linewidth=0.5,
            )
            ln_impaired.plot(
                ax=axis,
                color="tab:red",
                edgecolor="tab:red",
                alpha=1,
                legend=False,
                linewidth=0.5,
            )
            ln_in_assessed.plot(
                ax=axis,
                color="tab:blue",
                edgecolor="tab:blue",
                alpha=1,
                legend=False,
                linewidth=2,
            )
            ln_in_impaired.plot(
                ax=axis,
                color="tab:red",
                edgecolor="tab:red",
                alpha=1,
                legend=False,
                linewidth=2,
            )
        except:
            pass
        awilderness.plot(ax=axis, color="none", edgecolor="black", alpha=1)
        xlim = [awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]]
        ylim = [awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]]
        pyplot.suptitle(
            "Extent of streams with impaired water quality in " + which_wilderness[2]
        )
        txt = (
            str(ln_impaired_miles)
            + " miles impaired streams of\n "
            + str(ln_assessed_miles)
            + " miles assessed streams"
        )
        axis.annotate(
            txt,
            xy=(1, 1),
            xytext=(-20, -10),
            xycoords=("figure fraction", "axes fraction"),
            textcoords="offset points",
            bbox={"facecolor": "white", "edgecolor": "black", "pad": 5.0},
            size=8,
            family="monospace",
            ha="right",
            va="top",
        )
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        pyplot.axis("off")
        fig1 = pyplot.gcf()
        pyplot.subplots_adjust(top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0)
        pyplot.margins(0, 0)
        fig1.savefig(out_dir + slug_wilderness + "-streams.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            str(slug_wilderness) + "-streams.png created",
        )

        awilderness_box = awilderness_1mi.copy()
        awilderness_box = awilderness_1mi.to_crs({"proj": "cea"})
        awilderness_box["geometry"] = awilderness_box.geometry.buffer(0.1609344)
        awilderness_box = awilderness_box.to_crs(awilderness_1mi.crs)
        xlim2 = [awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]]
        ylim2 = [awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]]
        axis.set_xlim(xlim2)
        axis.set_ylim(ylim2)
        try_add_basemap(slug_wilderness, slug_agency, axis, awilderness.crs.to_string())
        awilderness.plot(
            ax=axis, color="none", edgecolor="black", linewidth=1.0, alpha=0.9
        )
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        fig1.savefig(out_dir + slug_wilderness + "-streams-base.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            str(slug_wilderness) + "-streams-base.png created",
        )

        width = 13  # lakes
        axis = awilderness_1mi.plot(
            color="none", edgecolor="none", alpha=0.0, figsize=(width, width / 1.618)
        )
        try:
            pl_assessed.plot(
                ax=axis, color="tab:blue", edgecolor="tab:blue", alpha=1, linewidth=0.5
            )
            pl_impaired.plot(
                ax=axis, color="tab:red", edgecolor="tab:red", alpha=1, linewidth=0.5
            )
            pl_in_assessed.plot(
                ax=axis, color="tab:blue", edgecolor="tab:blue", alpha=1, linewidth=2
            )
            pl_in_impaired.plot(
                ax=axis, color="tab:red", edgecolor="tab:red", alpha=1, linewidth=2
            )
        except:
            pass
        awilderness.plot(ax=axis, color="none", edgecolor="black", alpha=1)
        xlim = [awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]]
        ylim = [awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]]
        pyplot.suptitle(
            "Extent of lakes with impaired water quality in " + which_wilderness[2]
        )
        txt = (
            str(pl_impaired_acres)
            + " acres in "
            + str(pl_impaired_count)
            + " impaired lakes of\n "
            + str(pl_assessed_acres)
            + " acres in "
            + str(pl_assessed_count)
            + " assessed lakes"
        )
        axis.annotate(
            txt,
            xy=(1, 1),
            xytext=(-20, -10),
            xycoords=("figure fraction", "axes fraction"),
            textcoords="offset points",
            bbox={"facecolor": "white", "edgecolor": "black", "pad": 5.0},
            size=8,
            family="monospace",
            ha="right",
            va="top",
        )
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        pyplot.axis("off")
        fig1 = pyplot.gcf()
        pyplot.subplots_adjust(top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0)
        pyplot.margins(0, 0)
        fig1.savefig(out_dir + slug_wilderness + "-lakes.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            str(slug_wilderness) + "-lakes.png created",
        )

        awilderness_box = awilderness_1mi.copy()
        awilderness_box = awilderness_1mi.to_crs({"proj": "cea"})
        awilderness_box["geometry"] = awilderness_box.geometry.buffer(0.1609344)
        awilderness_box = awilderness_box.to_crs(awilderness_1mi.crs)
        xlim2 = [awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]]
        ylim2 = [awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]]
        axis.set_xlim(xlim2)
        axis.set_ylim(ylim2)
        try_add_basemap(slug_wilderness, slug_agency, axis, awilderness.crs.to_string())
        awilderness.plot(
            ax=axis, color="none", edgecolor="black", linewidth=1.0, alpha=0.9
        )
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        fig1.savefig(out_dir + slug_wilderness + "-lakes-base.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            str(slug_wilderness) + "-lakes-base.png created",
        )

        # quit()

        # log(None, 'WHITE', 'reading table')
        # ia = geopandas.read_file(epa303d_gdb, layer='attgeo_303dcaussrce')


def collect_jsons_nwps(water_list, year_min, year_max, rev_date):
    """ 6: json copy without maps, ok without waters_attains? """
    not_waterbody = [
        "BEACH",
        "COASTAL & BAY SHORELINE",
        "COASTAL",
        "GREAT LAKES BEACH",
        "GREAT LAKES SHORELINE",
        "INLAND LAKE SHORELINE",
        "SPRING",
        "SPRINGSHED",
        "WATERSHED",
        "WETLAND",
        "WETLANDS, FRESHWATER",
        "WETLANDS, TIDAL",
    ]
    not_lake_or_stream = [
        "BAY",
        "ESTUARY",
        "GREAT LAKES BAYS AND HARBORS",
        "GREAT LAKES OPEN WATER",
        "IMPOUNDMENT",
        "LAGOON",
        "OCEAN",
        "OCEAN/NEAR COASTAL",
        "SOUND",
    ]
    def_lake = [
        "LAKE",
        "LAKE, FRESHWATER",
        "LAKE, PLAYA",
        "LAKE, SALINE",
        "LAKE, SPRINGS",
        "LAKE, WILD RICE",
        "LAKE/RESERVOIR/POND",
        "POND",
        "RESERVOIR EMBAYMENT",
        "RESERVOIR",
    ]
    def_stream = [
        "CONNECTING CHANNEL",
        "CREEK",
        "DITCH OR CANAL",
        "RIVER",
        "STREAM",
        "STREAM, COASTAL",
        "STREAM, EPHEMERAL",
        "STREAM, INTERMITTENT",
        "STREAM, PERENNIAL",
        "STREAM, TIDAL",
        "STREAM/CREEK/RIVER",
    ]
    for which_wilderness in water_list:
        slug_wilderness = slugify(which_wilderness[2])
        slug_agency = slugify(which_wilderness[1])
        out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

        awilderness_file = slug_wilderness + "." + out_ext
        awilderness_cea_file = slug_wilderness + "-cea." + out_ext
        awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext

        awilderness = geopandas.read_file(out_dir + awilderness_file)
        awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)

        url_list = []
        url_list.append(["_ap"])  # assessment parameters
        # url_list.append(['_co']) # control
        url_list.append(["_ct"])  # catchment no geom
        url_list.append(["_hu"])  # huc12 no geom
        url_list.append(["_su"])  # assessment summary

        a_pl = get_file_rev_nwps(
            slug_agency, slug_wilderness + "_pl.json", rev_date
        )  # poly
        a_ln = get_file_rev_nwps(
            slug_agency, slug_wilderness + "_ln.json", rev_date
        )  # line
        a_pt = get_file_rev_nwps(
            slug_agency, slug_wilderness + "_pt.json", rev_date
        )  # point
        a_ca = get_file_rev_nwps(
            slug_agency, slug_wilderness + "_ca.json", rev_date
        )  # catchement area
        a_ty = get_file_rev_nwps(
            slug_agency, slug_wilderness + "_ty.json", rev_date
        )  # waterbody type

        log(None, None, "WHITE", "reading attains")
        if a_ca.split(".")[-1] == "txt":
            ca = geopandas.GeoDataFrame(columns=["geometry"], geometry="geometry")
            log(
                None,
                None,
                "WHITE",
                rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ca.json empty",
            )
            empty_ca_in = {
                "type": "Topology",
                "objects": {"ca_in": {"type": "GeometryCollection", "geometries": []}},
                "arcs": [],
                "bbox": [],
            }
            with uopen(
                out_dir + slug_wilderness + "_ca_in.json" + ".packed", "w"
            ) as static_file:
                static_file.write(str(empty_ca_in).replace("'", '"'))
        else:
            ca = geopandas.read_file(a_ca)
            print(awilderness.crs)
            awilderness.crs = "EPSG:4269"
            print(ca.crs)
            ca = ca.to_crs(awilderness.crs)
            # print(ca.head)
            #    print(ca.columns)
            # d.au = d.properties.assessmentunitidentifier
            # d.nhd = d.properties.nhdplusid
            # d.huc = d.properties.huc12
            # d.irc = d.properties.ircategory
            # d.os = d.properties.overallstatus
            # d.irc_ = +d.properties.ircategory.slice(0,1)
            # d.rc_ = +d.properties.reportingcycle
            #  x.properties.assmnt_joinkey == item.properties.assmnt_joinkey
            #  x.properties.submissionid == item.properties.submissionid));

            #    'OBJECTID', '', '', '', 'region',
            #   '', '', 'tas303d', '',
            #   '', 'assmnt_joinkey', 'permid_joinkey', '',
            #   '', 'isassessed', 'isimpaired', 'isthreatened',
            #   'on303dlist', 'hastmdl', 'has4bplan', 'hasalternativeplan',
            #   'hasprotectionplan', 'visionpriority303d', '', '',
            #   '', 'catchmentstatecode', 'GLOBALID', '',

            ca_in = geopandas.overlay(ca, awilderness, how="intersection")
            ca_in_groups = ca_in.groupby(
                ["assessmentunitidentifier", "assessmentunitname", "huc12",],
                as_index=False,
            ).agg(
                {
                    "nhdplusid": ["count"],
                    "submissionid": ["count"],
                    "organizationid": ["count"],
                    "areasqkm": ["sum"],
                    "catchmentareasqkm": ["sum"],
                    "geometry": ["first"],
                }
            )
            # ca_in_groups.columns = ca_in_groups.columns.to_flat_index()
            ca_in_groups.columns = [
                "au",
                "aun",
                "huc12",
                "nhd_c",
                "sid_c",
                "org_c",
                "sqkm_sum",
                "ca_sqkm_sum",
                "geometry",
            ]
            ca_in_g = ca_in_groups[
                [
                    "au",
                    "aun",
                    "huc12",
                    "nhd_c",
                    "sid_c",
                    "org_c",
                    "sqkm_sum",
                    "ca_sqkm_sum",
                    "geometry",
                ]
            ]
            print(ca_in.head)
            print(ca_in.columns)
            ca_in_d = ca_in.dissolve(
                as_index=False,
                aggfunc={
                    "assessmentunitidentifier": list,
                    "assessmentunitname": list,
                    "huc12": list,
                    "nhdplusid": list,
                    "reportingcycle": list,
                    "submissionid": list,
                    "state": list,
                    "orgtype": list,
                    "organizationid": list,
                    "organizationname": list,
                    "areasqkm": list,
                    "catchmentareasqkm": list,
                    "waterbodyreportlink": list,
                    "ircategory": list,
                    "overallstatus": list,
                },
            )  # 490 au by huc
            # ca_in_d = ca_in.dissolve(by=['huc12',], as_index=False, aggfunc={'nhdplusid': 'count', 'reportingcycle': 'count', 'submissionid': 'count', 'organizationid': 'count', 'areasqkm': 'sum', 'catchmentareasqkm': 'sum', 'waterbodyreportlink':'first', 'ircategory': ['min', 'max']}) # 172 hucs

            # ca_in_d.columns = ca_in_d.columns.to_flat_index()
            # ca_in_d.columns = ["_".join(a) for a in ca_in_d.columns.to_flat_index()]
            ca_in_d.columns = ca_in_d.columns.get_level_values(0)
            # print(ca_in_d.head)
            # print(ca_in_d.columns)
            # quit()
            ca_in_d.columns = [
                "idx",
                "geometry",
                "au",
                "auname",
                "huc12",
                "nhd",
                "rc",
                "sid",
                "st",
                "ot",
                "oid",
                "on",
                "sqkm",
                "ca_sqkm",
                "wr",
                "irc",
                "os",
            ]
            ca_in_d = ca_in_d[
                [
                    "au",
                    "auname",
                    "huc12",
                    "nhd",
                    "rc",
                    "sid",
                    "st",
                    "ot",
                    "oid",
                    "on",
                    "sqkm",
                    "ca_sqkm",
                    "wr",
                    "irc",
                    "os",
                    "geometry",
                ]
            ]
            # print(ca_in_d.columns)
            # ca_in = geopandas.GeoDataFrame(ca_in_d)
            print(ca_in.columns)
            extra_cols = [
                e
                for e in ca_in.columns
                if e
                not in [
                    "submissionid",
                    "nhdplusid",
                    "state",
                    "organizationid",
                    "orgtype",
                    "organizationname",
                    "reportingcycle",
                    "assessmentunitidentifier",
                    "assessmentunitname",
                    "waterbodyreportlink",
                    "ircategory",
                    "overallstatus",
                    "areasqkm",
                    "huc12",
                    "catchmentareasqkm",
                    "geometry",
                ]
            ]
            ca_in = ca_in.drop(columns=extra_cols)
            print(ca_in.columns)

            ca_in.columns = [
                "sid",
                "nhd",
                "st",
                "oid",
                "ot",
                "on",
                "rc",
                "au",
                "auname",
                "wr",
                "irc",
                "os",
                "sqkm",
                "huc12",
                "ca_sqkm",
                "geometry",
            ]
            ca_in = ca_in[
                [
                    "au",
                    "auname",
                    "huc12",
                    "nhd",
                    "rc",
                    "sid",
                    "st",
                    "ot",
                    "oid",
                    "on",
                    "sqkm",
                    "ca_sqkm",
                    "wr",
                    "irc",
                    "os",
                    "geometry",
                ]
            ]
            print(ca_in.columns)
            ca_in = geopandas.GeoDataFrame(ca_in)
            # quit()

            # extra_cols = [e for e in ca_in_groups.columns if  e not in ['OBJECTID', 'submissionid', 'nhdplusid', 'state', 'region', 'organizationid', 'orgtype', 'tas303d', 'organizationname', 'reportingcycle', 'assessmentunitidentifier', 'assessmentunitname','waterbodyreportlink', 'assmnt_joinkey', 'permid_joinkey', 'ircategory','overallstatus', 'isassessed', 'isimpaired', 'isthreatened','on303dlist', 'hastmdl', 'has4bplan', 'hasalternativeplan','hasprotectionplan', 'visionpriority303d', 'areasqkm', 'huc12','catchmentareasqkm', 'catchmentstatecode', 'GLOBALID', 'geometry']]
            # ca_in_groups = ca_in_groups.drop(columns=extra_cols)
            # quit()
            if ca_in.empty:
                log(
                    None,
                    None,
                    "WHITE",
                    rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + "_ca_in.json empty",
                )
                empty_ca_in = {
                    "type": "Topology",
                    "objects": {
                        "ca_in": {"type": "GeometryCollection", "geometries": []}
                    },
                    "arcs": [],
                    "bbox": [],
                }
                with uopen(
                    out_dir + slug_wilderness + "_ca_in.json" + ".packed", "w"
                ) as static_file:
                    static_file.write(str(empty_ca_in).replace("'", '"'))
            else:
                ca_in = ca_in.to_crs({"proj": "cea"})
                ca_in["acres_cea"] = ca_in["geometry"].area * 0.000247105
                ca_in = ca_in.to_crs(epsg=4326)
                # ca_in.to_file(driver='GeoJSON', filename=wdir + slug_wilderness + '_ca_in.json')
                with uopen(out_dir + slug_wilderness + "_ca_in.json", "w") as wg:
                    wg.write(ca_in.to_json())
                with uopen(out_dir + slug_wilderness + "_ca_in.json") as wg:
                    wj = json.load(wg)
                    topology_ = topology.Topology()
                    topo = topology_({"ca_in": wj})
                    topov = str(topo).replace("'", '"').replace(": None", ": null")
                with uopen(
                    out_dir + slug_wilderness + "_ca_in.json" + ".packed", "w"
                ) as static_file:
                    static_file.write(str(topov))
                log(
                    None,
                    None,
                    "GREEN",
                    rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + "_ca.json written",
                )

        if a_pl.split(".")[-1] == "txt":
            pl = geopandas.GeoDataFrame(columns=["geometry"], geometry="geometry")
            pl_ty_lake = geopandas.GeoDataFrame(
                columns=["geometry"], crs=awilderness.crs
            )
            log(
                None,
                None,
                "WHITE",
                rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pl.json empty",
            )
            empty_pl_in = {
                "type": "Topology",
                "objects": {"pl_in": {"type": "GeometryCollection", "geometries": []}},
                "arcs": [],
                "bbox": [],
            }
            with uopen(
                out_dir + slug_wilderness + "_pl_in.json" + ".packed", "w"
            ) as static_file:
                static_file.write(str(empty_pl_in).replace("'", '"'))
        else:
            pl = geopandas.read_file(a_pl)
            ty = geopandas.read_file(a_ty)
            ty = ty[["assmnt_joinkey", "watertype"]].copy()
            pl_ty = pl.merge(ty, on="assmnt_joinkey", how="left")
            pl_ty_lake = pl_ty[pl_ty["watertype"].isin(def_lake)]
            pl = geopandas.GeoDataFrame(pl_ty_lake)
            if pl.empty:
                log(
                    None,
                    None,
                    "WHITE",
                    rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + "_pl.json lakes empty",
                )
                empty_pl_in = {
                    "type": "Topology",
                    "objects": {
                        "pl_in": {"type": "GeometryCollection", "geometries": []}
                    },
                    "arcs": [],
                    "bbox": [],
                }
                with uopen(
                    out_dir + slug_wilderness + "_pl_in.json" + ".packed", "w"
                ) as static_file:
                    static_file.write(str(empty_pl_in).replace("'", '"'))
            else:
                pl = pl.to_crs(awilderness.crs)
                pl_in = geopandas.overlay(pl, awilderness, how="intersection")
                if pl_in.empty:
                    log(
                        None,
                        None,
                        "WHITE",
                        rev_date
                        + slash
                        + slug_agency
                        + slash
                        + slug_wilderness
                        + "_pl_in.json lakes empty",
                    )
                    empty_pl_in = {
                        "type": "Topology",
                        "objects": {
                            "pl_in": {"type": "GeometryCollection", "geometries": []}
                        },
                        "arcs": [],
                        "bbox": [],
                    }
                    with uopen(
                        out_dir + slug_wilderness + "_pl_in.json" + ".packed", "w"
                    ) as static_file:
                        static_file.write(str(empty_pl_in).replace("'", '"'))
                else:
                    pl_in = pl_in.to_crs({"proj": "cea"})
                    pl_in["acres_cea"] = pl_in["geometry"].area * 0.000247105
                    pl_in = pl_in.to_crs(epsg=4326)
                    pl_in.to_file(
                        driver="GeoJSON",
                        filename=out_dir + slug_wilderness + "_pl_in.json",
                    )
                    with uopen(out_dir + slug_wilderness + "_pl_in.json") as wg:
                        wj = json.load(wg)
                        topology_ = topology.Topology()
                        topo = topology_({"pl_in": wj})
                        topov = str(topo).replace("'", '"').replace(": None", ": null")
                    with uopen(
                        out_dir + slug_wilderness + "_pl_in.json" + ".packed", "w"
                    ) as static_file:
                        static_file.write(str(topov))

        if a_ln.split(".")[-1] == "txt":
            ln = geopandas.GeoDataFrame(columns=["geometry"], geometry="geometry")
            log(
                None,
                None,
                "WHITE",
                rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ln.json empty",
            )
            empty_ln_in = {
                "type": "Topology",
                "objects": {"ln_in": {"type": "GeometryCollection", "geometries": []}},
                "arcs": [],
                "bbox": [],
            }
            with uopen(
                out_dir + slug_wilderness + "_ln_in.json" + ".packed", "w"
            ) as static_file:
                static_file.write(str(empty_ln_in).replace("'", '"'))
        else:
            ln = geopandas.read_file(a_ln)
            ty = geopandas.read_file(a_ty)
            ty = ty[["assmnt_joinkey", "watertype"]].copy()
            ln_ty = ln.merge(ty, on="assmnt_joinkey", how="left")
            ln_ty_stream = ln_ty[ln_ty["watertype"].isin(def_stream)]
            ln = geopandas.GeoDataFrame(ln_ty_stream, crs=ln.crs)
            pl_ty_lake = pl_ty_lake.to_crs(ln.crs)
            if not pl_ty_lake.empty and not ln.empty:
                ln = geopandas.overlay(ln, pl_ty_lake, how="difference")
            if ln.empty:
                log(
                    None,
                    None,
                    "WHITE",
                    rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + "_ln.json streams empty",
                )
                empty_ln_in = {
                    "type": "Topology",
                    "objects": {
                        "ln_in": {"type": "GeometryCollection", "geometries": []}
                    },
                    "arcs": [],
                    "bbox": [],
                }
                with uopen(
                    out_dir + slug_wilderness + "_ln_in.json" + ".packed", "w"
                ) as static_file:
                    static_file.write(str(empty_ln_in).replace("'", '"'))
            else:
                ln = ln.to_crs(awilderness.crs)
                ln_in = geopandas.clip(ln, awilderness, keep_geom_type=True)
                if ln_in.empty:
                    log(
                        None,
                        None,
                        "WHITE",
                        rev_date
                        + slash
                        + slug_wilderness
                        + "_ln_in.json streams empty",
                    )
                    empty_ln_in = {
                        "type": "Topology",
                        "objects": {
                            "ln_in": {"type": "GeometryCollection", "geometries": []}
                        },
                        "arcs": [],
                        "bbox": [],
                    }
                    with uopen(
                        out_dir + slug_wilderness + "_ln_in.json" + ".packed", "w"
                    ) as static_file:
                        static_file.write(str(empty_ln_in).replace("'", '"'))
                else:
                    ln_in = ln_in.to_crs({"proj": "cea"})
                    ln_in["miles_cea"] = ln_in["geometry"].length / 1609.344
                    ln_in = ln_in.to_crs(epsg=4326)
                    ln_in.to_file(
                        driver="GeoJSON",
                        filename=out_dir + slug_wilderness + "_ln_in.json",
                    )
                    with uopen(out_dir + slug_wilderness + "_ln_in.json") as wg:
                        wj = json.load(wg)
                        topology_ = topology.Topology()
                        topo = topology_({"ln_in": wj})
                        topov = str(topo).replace("'", '"').replace(": None", ": null")
                    with uopen(
                        out_dir + slug_wilderness + "_ln_in.json" + ".packed", "w"
                    ) as static_file:
                        static_file.write(topov)

        if a_pt.split(".")[-1] == "txt":
            pt = geopandas.GeoDataFrame()
            log(
                None,
                None,
                "WHITE",
                rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pt.json empty",
            )
        else:
            pt = geopandas.read_file(a_pt)
        if a_ca.split(".")[-1] == "txt":
            ca = geopandas.GeoDataFrame()
            log(
                None,
                None,
                "WHITE",
                rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ca.json empty",
            )
        else:
            ca = geopandas.read_file(a_ca)
            ca = ca.to_crs(awilderness.crs)
            ca_in = geopandas.overlay(ca, awilderness, how="intersection")
            # what
    # quit()


def attains_cycles_to_csv_nwps(wilderness_list, rev_date):
    """ 2: pull attains cycles from epa attains service into local csv """
    # rev_date = str(datetime.now().strftime('%Y-%m-%d'))
    # rev_date = '2022-11-15'
    current_year = str(datetime.now().strftime("%Y"))
    def_lake = [
        "LAKE",
        "LAKE, FRESHWATER",
        "LAKE, PLAYA",
        "LAKE, SALINE",
        "LAKE, SPRINGS",
        "LAKE, WILD RICE",
        "LAKE/RESERVOIR/POND",
        "POND",
        "RESERVOIR EMBAYMENT",
        "RESERVOIR",
    ]
    def_stream = [
        "CONNECTING CHANNEL",
        "CREEK",
        "DITCH OR CANAL",
        "RIVER",
        "STREAM",
        "STREAM, COASTAL",
        "STREAM, EPHEMERAL",
        "STREAM, INTERMITTENT",
        "STREAM, PERENNIAL",
        "STREAM, TIDAL",
        "STREAM/CREEK/RIVER",
    ]
    for which_wilderness in wilderness_list:
        slug_wilderness = slugify(which_wilderness[2])
        slug_agency = slugify(which_wilderness[1])
        out_dir = base_dir + slug_agency + slash + slug_wilderness + slash
        awilderness_file = slug_wilderness + "." + out_ext
        awilderness = geopandas.read_file(out_dir + awilderness_file)
        log(None, None, "WHITE", "reading attains")
        if os.path.exists(
            water_dir
            + rev_date
            + slash
            + slug_agency
            + slash
            + slug_wilderness
            + "_pl.txt"
        ):
            pl = geopandas.GeoDataFrame(columns=["geometry"], geometry="geometry")
            pl_ty_lake = geopandas.GeoDataFrame(columns=["geometry"], crs="epsg:4326")
            pl_get = pandas.DataFrame(
                columns=[
                    "assmnt_joinkey",
                    "watertype",
                    "organizationid",
                    "assessmentunitidentifier",
                    "reportingcycle",
                ]
            )
            log(
                None,
                None,
                "WHITE",
                rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pl.json empty",
            )
        else:
            pl = geopandas.read_file(
                water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_pl.json"
            )
            ty = geopandas.read_file(
                water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ty.json"
            )
            ty = ty[["assmnt_joinkey", "watertype"]].copy()
            pl_ty = pl.merge(ty, on="assmnt_joinkey", how="left")
            pl_ty_lake = pl_ty[pl_ty["watertype"].isin(def_lake)]
            pl = geopandas.GeoDataFrame(pl_ty_lake)
            pl_get = pl[
                [
                    "assmnt_joinkey",
                    "watertype",
                    "organizationid",
                    "assessmentunitidentifier",
                    "reportingcycle",
                ]
            ].copy()
        if os.path.exists(
            water_dir
            + rev_date
            + slash
            + slug_agency
            + slash
            + slug_wilderness
            + "_ln.txt"
        ):
            ln = geopandas.GeoDataFrame(columns=["geometry"], geometry="geometry")
            ln_get = pandas.DataFrame(
                columns=[
                    "assmnt_joinkey",
                    "watertype",
                    "organizationid",
                    "assessmentunitidentifier",
                    "reportingcycle",
                ]
            )
            log(
                None,
                None,
                "WHITE",
                rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ln.json empty",
            )
        else:
            ln = geopandas.read_file(
                water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ln.json"
            )
            ty = geopandas.read_file(
                water_dir
                + rev_date
                + slash
                + slug_agency
                + slash
                + slug_wilderness
                + "_ty.json"
            )
            ty = ty[["assmnt_joinkey", "watertype"]].copy()
            ln_ty = ln.merge(ty, on="assmnt_joinkey", how="left")
            ln_ty_stream = ln_ty[ln_ty["watertype"].isin(def_stream)]
            ln = geopandas.GeoDataFrame(ln_ty_stream)
            if not ln.empty:
                ln = geopandas.overlay(ln, pl_ty_lake, how="difference")
                ln_get = ln[
                    [
                        "assmnt_joinkey",
                        "watertype",
                        "organizationid",
                        "assessmentunitidentifier",
                        "reportingcycle",
                    ]
                ].copy()
            else:
                ln = geopandas.GeoDataFrame(columns=["geometry"], geometry="geometry")
                ln_get = pandas.DataFrame(
                    columns=[
                        "assmnt_joinkey",
                        "watertype",
                        "organizationid",
                        "assessmentunitidentifier",
                        "reportingcycle",
                    ]
                )
                log(
                    None,
                    None,
                    "WHITE",
                    rev_date
                    + slash
                    + slug_agency
                    + slash
                    + slug_wilderness
                    + "_ln.json empty",
                )
        url_df = pandas.concat([pl_get, ln_get], ignore_index=True)
        url_df.to_csv(
            water_dir
            + rev_date
            + slash
            + slug_agency
            + slash
            + slug_wilderness
            + "_url.csv",
            index=False,
        )
        log(
            None,
            None,
            "GREEN",
            "writing "
            + water_dir
            + rev_date
            + slash
            + slug_agency
            + slash
            + slug_wilderness
            + "_url.csv",
        )


def attains_cycles_to_local_nwps(wilderness_list, year_min, year_max, rev_date):
    """ 3: pull attains cycles from epa attains service """
    # rev_date = str(datetime.now().strftime('%Y-%m-%d'))
    # rev_date = '2022-11-15'
    for which_wilderness in wilderness_list:
        slug_wilderness = slugify(which_wilderness[2])
        slug_agency = slugify(which_wilderness[1])
        out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

        awilderness_file = slug_wilderness + "." + out_ext

        log(None, None, "WHITE", "reading attains")
        url_df = pandas.read_csv(
            water_dir
            + rev_date
            + slash
            + slug_agency
            + slash
            + slug_wilderness
            + "_url.csv"
        )
        # url_df = url_df.iloc[1723:]
        year_list = list(range(year_min, year_max + 1))
        year_list = [year for year in year_list if year % 2 != 1]
        for index, row in url_df.iterrows():
            print(row.organizationid)
            for year in year_list:
                queryURL = (
                    "https://attains.epa.gov/attains-public/api/assessments?organizationId="
                    + str(row.organizationid)
                    + "&assessmentUnitIdentifier="
                    + row.assessmentunitidentifier
                    + "&reportingCycle="
                    + str(year)
                )
                cycle_dir = water_dir + rev_date + slash + str(year) + slash
                cycle_json = (
                    str(row.organizationid)
                    + "_"
                    + row.assessmentunitidentifier
                    + ".json"
                )
                if os.path.exists(cycle_dir + cycle_json):
                    log(
                        None,
                        None,
                        "CYAN",
                        slug_wilderness + " " + str(year) + " existing " + cycle_json,
                    )
                else:
                    response = requests.get(queryURL)
                    json = response.json()
                    recs = json["items"]
                    if not recs:
                        log(
                            None,
                            None,
                            "WHITE",
                            slug_wilderness + " " + str(year) + " empty " + cycle_json,
                        )
                    else:
                        if not os.path.exists(cycle_dir):
                            os.makedirs(cycle_dir)
                            print("creating folder " + cycle_dir)
                        with uopen(cycle_dir + cycle_json, "wb") as outf:
                            outf.write(response.content)
                        log(
                            None,
                            None,
                            "CYAN",
                            slug_wilderness
                            + " "
                            + str(year)
                            + " writing "
                            + cycle_json,
                        )


def local_tidys_to_wild_rc_au(do_nwps):
    """ local tidy files to web file """
    req_list = []
    # wilderness_shp = data_dir + "_wilderness" + slash + "_nwps-2022-12-16.topojson"
    wilderness_shp = cache_dir + "nwps_fs.json"
    wilderness_df = geopandas.read_file(wilderness_shp)
    wilderness_df = wilderness_df.drop(columns="state")
    agency_wilderness = wilderness_df[(wilderness_df["a"] == do_nwps)]
    agency_wilderness = agency_wilderness.sort_values(by=["name"])
    log(None, None, "CYAN", "every " + do_nwps + " wilderness, ok!")
    cut = "Aa"
    cut2 = "Zz"
    if do_nwps == "FS":
        skip = ["Holy Cross", "Pecos", "Saint Mary's"]
    if do_nwps == "NPS":
        skip = ["Gulf Islands", "Marjory Stoneman Douglas"]
    if do_nwps == "FWS":
        skip = ["Seney", "Oregon Islands", "Swanquarter", "Red Rock Lakes"]
    if do_nwps == "BLM":
        skip = [
            "Chuckwalla Mountains",
            "Devils Staircase",
            "Big Maria Mountains",
            "Riverside Mountains",
            "Soda Mountains",
        ]
    for i, row in agency_wilderness.iterrows():
        if row["name"] >= cut and row["name"] <= cut2:
            if row["name"] in skip:
                log(None, None, "CYAN", row["name"] + " skipped")
            else:
                req_list.append(["2023-08-14", row["name"], row["a"], "je"])
    log(
        None,
        None,
        "CYAN",
        "from " + req_list[0][1] + " to " + req_list[-1][1] + ", ok!",
    )

    wra = pandas.DataFrame()
    for which_wilderness in req_list:
        slug_wilderness = slugify(which_wilderness[1])
        slug_agency = slugify(which_wilderness[2])
        out_dir = base_dir + slug_agency + slash + slug_wilderness + slash
        print(slug_wilderness)

        if os.path.exists(out_dir + slug_wilderness + "_ln_in.json.packed"):
            ln_in = geopandas.read_file(
                out_dir + slug_wilderness + "_ln_in.json.packed"
            )
            if not ln_in.empty:
                ln_in_au = ln_in.groupby(
                    ["assessmentunitidentifier"], as_index=False
                ).agg({"miles_cea": ["sum", "count"]})
                ln_in_au.columns = ln_in_au.columns.map("_".join).str.strip("_")
            else:
                ln_in_au = pandas.DataFrame(
                    columns=[
                        "assessmentunitidentifier",
                        "miles_cea_sum",
                        "miles_cea_count",
                    ]
                )
            print(ln_in_au.head)

        if os.path.exists(out_dir + slug_wilderness + "_pl_in.json.packed_"):
            pl_in = geopandas.read_file(
                out_dir + slug_wilderness + "_pl_in.json.packed"
            )
            if not pl_in.empty:
                print(pl_in.head)
                pl_in_au = pl_in.groupby(
                    ["assessmentunitidentifier"], as_index=False
                ).agg({"acres_cea": ["sum", "count"]})
                pl_in_au.columns = pl_in_au.columns.map("_".join).str.strip("_")
            else:
                pl_in_au = pandas.DataFrame(
                    columns=[
                        "assessmentunitidentifier",
                        "acres_cea_sum",
                        "acres_cea_count",
                    ]
                )
            print(pl_in_au.head)

        if os.path.exists(out_dir + slug_wilderness + "_ca_in.json.packed"):
            print(out_dir + slug_wilderness + "_ca_in.json.packed")
            ca_in = geopandas.read_file(
                out_dir + slug_wilderness + "_ca_in.json.packed"
            )
            if not ca_in.empty:
                ca_in_au = ca_in.groupby(["au"], as_index=False).agg(
                    {"acres_cea": ["sum", "count"]}
                )
                ca_in_au.columns = ca_in_au.columns.map("_".join).str.strip("_")
            else:
                ca_in_au = pandas.DataFrame(
                    columns=["au", "acres_cea_sum", "acres_cea_count"]
                )
            print(ca_in_au.head)

        if os.path.exists(out_dir + slug_wilderness + "-water-tidy.csv"):
            try:
                tidy_df = pandas.read_csv(out_dir + slug_wilderness + "-water-tidy.csv")
            except:
                # tidy_df = pandas.DataFrame(columns=["au", "rc", "ac", "irc", "os"])
                tidy_df = pandas.DataFrame(
                    [["", "2024", "", "", ""]], columns=["au", "rc", "ac", "irc", "os"]
                )
            print(tidy_df.head)

            ln_full = ln_in_au.merge(
                ca_in_au,
                how="left",
                left_on="assessmentunitidentifier",
                right_on="au",
                left_index=False,
                right_index=False,
                sort=False,
                suffixes=("", "_y"),
                copy=None,
                indicator=False,
                validate=None,
            )
            ln_full = ln_full.drop(columns=["au",])
            print(tidy_df.head)
            print(tidy_df.columns)
            tidy_full = tidy_df.merge(
                ln_full,
                how="left",
                left_on="au",
                right_on="assessmentunitidentifier",
                left_index=False,
                right_index=False,
                sort=False,
                suffixes=("", "_y"),
                copy=None,
                indicator=False,
                validate=None,
            )
            tidy_full = tidy_full.drop(columns=["assessmentunitidentifier",])
            print(tidy_full.head)
            print(tidy_full.columns)
            tidy_full = tidy_full.rename(
                index=str,
                columns={
                    "miles_cea_sum": "miles",
                    "miles_cea_count": "stream_count",
                    "acres_cea_sum": "catchment_acres",
                    "acres_cea_count": "catchment_count",
                },
            )
            print(tidy_full.columns)
            # tidy_full.to_csv(base_dir + slug_agency + slash + slug_agency + "-test.csv", index=False)

            # au_in_rcs = tidy_full.groupby(
            #    ["rc"], as_index=False
            # ).agg({"miles": ["sum", "count"], "acres_cea": ["sum", "count"]})
            # au_in_rcs.columns = au_in_rcs.columns.map(
            #    "_".join
            # ).str.strip("_")
            # print(au_in_rcs.head)
            tidy_full["w"] = which_wilderness[1]
            tidy_full["a"] = do_nwps
            wra = pandas.concat([wra, tidy_full])
            print(tidy_full.head)
            # except pandas.errors.EmptyDataError:
            #    print('empty csv')
            # print(tidy_full.head)

    wra.to_csv(
        base_dir + slug_agency + slash + slug_agency + "-water-tidy.csv", index=False
    )
    log(
        None,
        None,
        "GREEN",
        "writing " + base_dir + slug_agency + slash + slug_agency + "-water-tidy.csv",
    )
    quit()
    # open tidy.csy
    # group by year
    # for rc in rcs:
    #    df.append (which_wilderness[1], rc, au_count)


def local_cycles_to_tidy_nwps(wilderness_list, year_min, year_max, rev_date):
    """ 4: tidy the history """
    for which_wilderness in wilderness_list:
        slug_wilderness = slugify(which_wilderness[2])
        slug_agency = slugify(which_wilderness[1])
        out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

        awilderness_file = slug_wilderness + "." + out_ext

        log(None, None, "WHITE", "tidying attains")
        # quit()
        tidy = []  # pandas.DataFrame(columns=['org', 'au', 'rc', 'ac', 'irc', 'os'])
        url_df = pandas.read_csv(
            water_dir
            + rev_date
            + slash
            + slug_agency
            + slash
            + slug_wilderness
            + "_url.csv"
        )
        # url_df = url_df.iloc[1723:]
        year_list = list(range(year_min, year_max + 1))
        year_list = [year for year in year_list if year % 2 != 1]
        for index, row in url_df.iterrows():
            for year in year_list:
                queryURL = (
                    "https://attains.epa.gov/attains-public/api/assessments?organizationId="
                    + str(row.organizationid)
                    + "&assessmentUnitIdentifier="
                    + row.assessmentunitidentifier
                    + "&reportingCycle="
                    + str(year)
                )
                cycle_dir = water_dir + rev_date + slash + str(year) + slash
                cycle_json = (
                    str(row.organizationid)
                    + "_"
                    + row.assessmentunitidentifier
                    + ".json"
                )
                print(year)
                print(cycle_dir)
                print(cycle_json)
                # cycle_dir = water_dir + rev_date + slash + '2018' + slash
                # cycle_json = 'MTDEQ_MT76H003_020.json'
                if os.path.exists(cycle_dir + cycle_json):
                    log(
                        None,
                        None,
                        "CYAN",
                        slug_wilderness + " " + str(year) + " existing " + cycle_json,
                    )
                    ac = pandas.read_json(cycle_dir + cycle_json)
                    for k, v in ac.items():
                        for kk, vv in v.items():
                            # log(None, 'GREEN', '+++++++++++++++++++++++++')
                            # print(kk, vv)
                            if isinstance(vv, int):
                                pass
                            else:
                                # log(None, 'CYAN', 'vv_orgid ++++++++++++++++++++++')
                                # print(vv["organizationIdentifier"])
                                # print(vv["assessmentUnitIdentifier"])
                                # log(None, 'CYAN', 'vv_assessments ++++++++++++++++++++++')
                                # print(vv["assessments"])

                                # print(type(vv)) # dict
                                # log(None, 'CYAN', 'vv_items ++++++++++++++++++++++')
                                # print(vv.items())
                                for a in vv["assessments"]:
                                    # log(None, 'CYAN', 'a ++++++++++++++++++++++')
                                    new_row = pandas.Series(
                                        {
                                            #   "org": vv["organizationIdentifier"],
                                            "au": a["assessmentUnitIdentifier"],
                                            "rc": vv["reportingCycleText"],
                                            "ac": a["cycleLastAssessedText"],
                                            "irc": a["epaIRCategory"],
                                            "os": a["overallStatus"],
                                        }
                                    )
                                    # print(new_row)
                                    tidy.append(new_row)
        td = pandas.DataFrame(tidy)
        # print(td.head)
        td.to_csv(out_dir + slug_wilderness + "-water-tidy.csv", index=False)
        log(
            None,
            None,
            "GREEN",
            "writing " + out_dir + slug_wilderness + "-water-tidy.csv",
        )
        # quit()


def attains_cycles(wilderness_list, rev_date):
    """ in progress """
    # rev_date = str(datetime.now().strftime('%Y-%m-%d'))
    current_year = str(datetime.now().strftime("%Y"))
    for which_wilderness in wilderness_list:
        slug_wilderness = slugify(which_wilderness)
        out_dir = base_dir + slug_wilderness + slash
        outmaps_dir = base_maps_dir + slug_wilderness + slash
        awilderness_file = slug_wilderness + "." + out_ext

        url_df = pandas.read_csv(
            water_dir + rev_date + slash + slug_wilderness + "_url.csv"
        )
        print(url_df.head)
        # get organizationid + assessmentunitidentifier to list
        # get folders
        # year_list = list(range(year_min, year_max + 1))
        # for cycle in cycles:
        #    read cycle.json
        #    join to ln/pl
    quit()

    json = response.json()
    recs = json["items"]
    df_combinedcycles = pandas.json_normalize(
        recs,
        "combinedCycles",
        [
            "organizationIdentifier",
            "organizationName",
            "organizationTypeText",
            "reportingCycleText",
            "reportStatusCode",
        ],
    ).T
    df_assessments = pandas.json_normalize(
        recs,
        "assessments",
        [
            "organizationIdentifier",
            "organizationName",
            "organizationTypeText",
            "reportingCycleText",
            "reportStatusCode",
        ],
    ).T
    df_documents = pandas.json_normalize(
        recs,
        "documents",
        [
            "organizationIdentifier",
            "organizationName",
            "organizationTypeText",
            "reportingCycleText",
            "reportStatusCode",
        ],
    )
    df_delistedWaters = pandas.json_normalize(
        recs,
        "delistedWaters",
        [
            "organizationIdentifier",
            "organizationName",
            "organizationTypeText",
            "reportingCycleText",
            "reportStatusCode",
        ],
    )
    print(df_combinedcycles)
    print(df_assessments)
    print(df_documents)
    print(df_delistedWaters)
    # print(df_useattainments)
    # print(df_documents.head)
    # print(df_delistedWaters.head)
    quit()
    geojson = [arcgis2geojson(f) for f in json["features"]]
    if GEOPANDAS_VERSION >= packaging.version.parse("0.7"):
        gdf = gpd.GeoDataFrame.from_features(geojson, crs="EPSG:4326")
    else:
        gdf = gpd.GeoDataFrame.from_features(geojson, crs={"init": "epsg:4326"})


def calc_astatus(row):
    """ get assessed status from irc """
    if row["epaIRCategory"] in ["3"]:
        return "N"
    elif row["epaIRCategory"] in ["1", "2"]:
        return "Y"
    else:
        return "Y"


def calc_istatus(row):
    """ get impaired status from irc """
    if row["epaIRCategory"] in ["3"]:
        return "N"
    elif row["epaIRCategory"] in ["1", "2"]:
        return "N"
    else:
        return "Y"


def attains_waters_cycles(water_list, rev_date):
    """ in progress local attains cycles to historic waterbody maps """
    not_waterbody = [
        "BEACH",
        "COASTAL & BAY SHORELINE",
        "COASTAL",
        "GREAT LAKES BEACH",
        "GREAT LAKES SHORELINE",
        "INLAND LAKE SHORELINE",
        "SPRING",
        "SPRINGSHED",
        "WATERSHED",
        "WETLAND",
        "WETLANDS, FRESHWATER",
        "WETLANDS, TIDAL",
    ]
    not_lake_or_stream = [
        "BAY",
        "ESTUARY",
        "GREAT LAKES BAYS AND HARBORS",
        "GREAT LAKES OPEN WATER",
        "IMPOUNDMENT",
        "LAGOON",
        "OCEAN",
        "OCEAN/NEAR COASTAL",
        "SOUND",
    ]
    def_lake = [
        "LAKE",
        "LAKE, FRESHWATER",
        "LAKE, PLAYA",
        "LAKE, SALINE",
        "LAKE, SPRINGS",
        "LAKE, WILD RICE",
        "LAKE/RESERVOIR/POND",
        "POND",
        "RESERVOIR EMBAYMENT",
        "RESERVOIR",
    ]
    def_stream = [
        "CONNECTING CHANNEL",
        "CREEK",
        "DITCH OR CANAL",
        "RIVER",
        "STREAM",
        "STREAM, COASTAL",
        "STREAM, EPHEMERAL",
        "STREAM, INTERMITTENT",
        "STREAM, PERENNIAL",
        "STREAM, TIDAL",
        "STREAM/CREEK/RIVER",
    ]
    for which_wilderness in water_list:
        slug_wilderness = slugify(which_wilderness)
        out_dir = base_dir + slug_wilderness + slash
        outmaps_dir = base_maps_dir + slug_wilderness + slash
        awilderness_file = slug_wilderness + "." + out_ext
        awilderness_cea_file = slug_wilderness + "-cea." + out_ext
        awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext

        awilderness = geopandas.read_file(out_dir + awilderness_file)
        awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)

        url_list = []
        url_list.append(["_su"])  # attribute summary
        # url_list.append(['_co']) # control
        url_list.append(["_ct"])  # catchment
        url_list.append(["_hu"])  # huc12
        url_list.append(["_ap"])  # parameters

        log(None, None, "WHITE", "cycling")
        url_df = pandas.read_csv(
            water_dir + rev_date + slash + slug_wilderness + "_url.csv"
        )
        year_min = 1998
        year_max = 2022
        year_list = list(range(year_min, year_max + 1))
        use_attainment_df = pandas.DataFrame()
        for year in year_list:
            a_year_df = pandas.DataFrame()
            for index, row in url_df.iterrows():  # waterbody year
                cycle_dir = water_dir + rev_date + slash + str(year) + slash
                cycle_json = (
                    str(row.organizationid)
                    + "_"
                    + row.assessmentunitidentifier
                    + ".json"
                )
                if os.path.exists(cycle_dir + cycle_json):
                    log(
                        slug_wilderness,
                        slug_agency,
                        "CYAN",
                        "reading cycle " + str(year),
                    )
                    cycle = pandas.read_json(cycle_dir + cycle_json)
                    # json = cycle.json()
                    recs = cycle["items"]
                    # print(recs['assessments'])
                    # quit()
                    df_combinedcycles = pandas.json_normalize(
                        recs,
                        "combinedCycles",
                        [
                            "organizationIdentifier",
                            "organizationName",
                            "organizationTypeText",
                            "reportingCycleText",
                            "reportStatusCode",
                        ],
                    )
                    df_assessments = pandas.json_normalize(
                        recs,
                        "assessments",
                        [
                            "organizationIdentifier",
                            "organizationName",
                            "organizationTypeText",
                            "reportingCycleText",
                            "reportStatusCode",
                        ],
                    )
                    df_documents = pandas.json_normalize(
                        recs,
                        "documents",
                        [
                            "organizationIdentifier",
                            "organizationName",
                            "organizationTypeText",
                            "reportingCycleText",
                            "reportStatusCode",
                        ],
                    )
                    df_delistedwaters = pandas.json_normalize(
                        recs,
                        "delistedWaters",
                        [
                            "organizationIdentifier",
                            "organizationName",
                            "organizationTypeText",
                            "reportingCycleText",
                            "reportStatusCode",
                        ],
                    )

                    for index, row in df_assessments.iterrows():
                        # print(row.useAttainments)
                        df_useattainments = pandas.json_normalize(row.useAttainments)
                        # print(df_assessments.columns)
                        # print(df_useattainments.columns)
                        # quit()
                        # print(df_assessments.rationaleText)
                        # print(df_assessments.epaIRCategory)
                        # print(df_assessments.overallStatus)
                        # print(df_assessments.cycleLastAssessedText)
                        # print(df_assessments.yearLastMonitoredText)
                        # print(row.rationaleText)
                        # print(row.epaIRCategory)
                        # print(row.overallStatus)
                        # print(row.cycleLastAssessedText)
                        # print(row.yearLastMonitoredText)
                        # print(df_documents.head)
                        # print(df_delistedWaters.head)
                    a_year_df = pandas.concat([a_year_df, df_assessments])
                    # ty_year_df.to_file(driver='GeoJSON', filename=outmaps_dir + slug_wilderness + '_ty_' + year + 'pl_in.json')

                else:
                    log(
                        slug_wilderness,
                        slug_agency,
                        "WHITE",
                        "empty cycle " + str(year),
                    )

            # quit()

            log(None, None, "WHITE", "reading attains")
            if a_year_df.empty or os.path.exists(
                water_dir + rev_date + slash + slug_wilderness + "_pl.txt"
            ):
                pl = geopandas.GeoDataFrame(columns=["geometry"], geometry="geometry")
                pl_assessed_count = 0
                pl_assessed_acres = 0
                pl_impaired_count = 0
                pl_impaired_acres = 0
                pl_ty_lake = geopandas.GeoDataFrame(
                    columns=["geometry"], crs=awilderness.crs
                )
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    rev_date + slash + slug_wilderness + "_pl.json empty",
                )
            else:
                pl = geopandas.read_file(
                    water_dir + rev_date + slash + slug_wilderness + "_pl.json"
                )
                # print(pl.columns)
                # print(a_year_df.columns)
                pl_a = pl.merge(
                    a_year_df,
                    left_on="assessmentunitidentifier",
                    right_on="assessmentUnitIdentifier",
                    how="left",
                )
                extra_cols = [
                    e
                    for e in pl_a.columns
                    if e
                    in ["useAttainments", "probableSources", "parameters", "documents"]
                ]
                pl_a = pl_a.drop(columns=extra_cols)
                pl = pl_a.copy()

                ty = geopandas.read_file(
                    water_dir + rev_date + slash + slug_wilderness + "_ty.json"
                )

                ty = ty[["assmnt_joinkey", "watertype"]].copy()

                pl_ty = pl.merge(ty, on="assmnt_joinkey", how="left")
                pl_ty_lake = pl_ty[pl_ty["watertype"].isin(def_lake)]
                pl = geopandas.GeoDataFrame(pl_ty_lake)
                if pl.empty:
                    pl_assessed_count = 0
                    pl_assessed_acres = 0
                    pl_impaired_count = 0
                    pl_impaired_acres = 0
                    log(
                        slug_wilderness,
                        slug_agency,
                        "WHITE",
                        rev_date + slash + slug_wilderness + "_pl.json lakes empty",
                    )
                else:
                    pl = pl.to_crs(awilderness.crs)
                    pl["isassessed"] = pl.apply(calc_astatus, axis=1)
                    pl["isimpaired"] = pl.apply(calc_istatus, axis=1)
                    pl_assessed = pl[pl["isassessed"] == "Y"]
                    pl_impaired = pl[pl["isimpaired"] == "Y"]
                    # pl_assessed = pl[pl['epaIRCategory'] is in ['1', '2', '4', '4A', '4B','4C', '5']]
                    # pl_impaired = pl[pl['epaIRCategory'] is in ['4', '4A', '4B', '4C', '5']]
                    pl_in = geopandas.overlay(pl, awilderness, how="intersection")
                    if pl_in.empty:
                        pl_assessed_count = 0
                        pl_assessed_acres = 0
                        pl_impaired_count = 0
                        pl_impaired_acres = 0
                        log(
                            slug_wilderness,
                            slug_agency,
                            "WHITE",
                            rev_date
                            + slash
                            + slug_wilderness
                            + "_pl_in.json lakes empty",
                        )
                    else:
                        pl_in = pl_in.to_crs({"proj": "cea"})
                        pl_in["acres_cea"] = pl_in["geometry"].area * 0.000247105
                        pl_in.to_file(
                            driver="GeoJSON",
                            filename=outmaps_dir
                            + slug_wilderness
                            + "_"
                            + str(year)
                            + "_pl_in.json",
                        )
                        pl_in_assessed = pl_in[pl_in["isassessed"] == "Y"]
                        pl_in_impaired = pl_in[pl_in["isimpaired"] == "Y"]
                        pl_in_assessed = pl_in_assessed.to_crs(awilderness.crs)
                        pl_in_impaired = pl_in_impaired.to_crs(awilderness.crs)
                        pl_assessed_count = pl_in_assessed.shape[0]
                        pl_assessed_acres = pl_in_assessed["acres_cea"].sum()
                        pl_assessed_acres = "{0:.2f}".format(pl_assessed_acres)
                        pl_impaired_count = pl_in_impaired.shape[0]
                        pl_impaired_acres = pl_in_impaired["acres_cea"].sum()
                        pl_impaired_acres = "{0:.2f}".format(pl_impaired_acres)
                        pl_in_groups = pl_in.groupby(
                            ["isassessed", "isimpaired", "ircategory",], as_index=False
                        ).agg({"acres_cea": ["sum", "count"]})
                        pl_in_groups.columns = pl_in_groups.columns.map(
                            "_".join
                        ).str.strip("_")
                        pl_in_groups.to_csv(
                            outmaps_dir
                            + slug_wilderness
                            + "_"
                            + str(year)
                            + "-pl_in_groups.csv",
                            index=False,
                        )
                        extra_cols = [e for e in pl_in.columns if e in ["geometry"]]
                        pl_in = pl_in.drop(columns=extra_cols)
                        pl_in.to_csv(
                            outmaps_dir
                            + slug_wilderness
                            + "_"
                            + str(year)
                            + "-pl_in.csv",
                            index=False,
                        )
            if a_year_df.empty or os.path.exists(
                water_dir + rev_date + slash + slug_wilderness + "_ln.txt"
            ):
                ln = geopandas.GeoDataFrame(columns=["geometry"], geometry="geometry")
                ln_assessed_count = 0
                ln_assessed_miles = 0
                ln_impaired_count = 0
                ln_impaired_miles = 0
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    rev_date + slash + slug_wilderness + "_ln.json empty",
                )
            else:
                ln = geopandas.read_file(
                    water_dir + rev_date + slash + slug_wilderness + "_ln.json"
                )

                ln_a = ln.merge(
                    a_year_df,
                    left_on="assessmentunitidentifier",
                    right_on="assessmentUnitIdentifier",
                    how="left",
                )
                extra_cols = [
                    e
                    for e in ln_a.columns
                    if e
                    in ["useAttainments", "probableSources", "parameters", "documents"]
                ]
                ln_a = ln_a.drop(columns=extra_cols)
                ln = ln_a.copy()
                # print(ln.head)
                # print(ln.columns)

                ty = geopandas.read_file(
                    water_dir + rev_date + slash + slug_wilderness + "_ty.json"
                )
                ty = ty[["assmnt_joinkey", "watertype"]].copy()
                ln_ty = ln.merge(ty, on="assmnt_joinkey", how="left")
                ln_ty_stream = ln_ty[ln_ty["watertype"].isin(def_stream)]
                ln = geopandas.GeoDataFrame(ln_ty_stream)
                # pl_ty_lake = pl_ty_lake.to_crs(ln)
                ln = geopandas.overlay(ln, pl_ty_lake, how="difference")
                if ln.empty:
                    ln_assessed_count = 0
                    ln_assessed_miles = 0
                    ln_impaired_count = 0
                    ln_impaired_miles = 0
                    log(
                        slug_wilderness,
                        slug_agency,
                        "WHITE",
                        rev_date + slash + slug_wilderness + "_ln.json streams empty",
                    )
                else:
                    ln = ln.to_crs(awilderness.crs)
                    ln["isassessed"] = ln.apply(calc_astatus, axis=1)
                    ln["isimpaired"] = ln.apply(calc_istatus, axis=1)
                    ln_assessed = ln[ln["isassessed"] == "Y"]
                    ln_impaired = ln[ln["isimpaired"] == "Y"]

                    ln_in = geopandas.clip(ln, awilderness, keep_geom_type=True)
                    if ln_in.empty:
                        ln_assessed_count = 0
                        ln_assessed_miles = 0
                        ln_impaired_count = 0
                        ln_impaired_miles = 0
                        log(
                            slug_wilderness,
                            slug_agency,
                            "WHITE",
                            rev_date
                            + slash
                            + slug_wilderness
                            + "_ln_in.json streams empty",
                        )
                    else:
                        ln_in = ln_in.to_crs({"proj": "cea"})
                        ln_in["miles_cea"] = ln_in["geometry"].length / 1609.344
                        ln_in.to_file(
                            driver="GeoJSON",
                            filename=outmaps_dir
                            + slug_wilderness
                            + "_"
                            + str(year)
                            + "_ln_in.json",
                        )
                        ln_in_assessed = ln_in[ln_in["isassessed"] == "Y"]
                        ln_in_impaired = ln_in[ln_in["isimpaired"] == "Y"]
                        ln_in_assessed = ln_in_assessed.to_crs(awilderness.crs)
                        ln_in_impaired = ln_in_impaired.to_crs(awilderness.crs)
                        ln_assessed_count = ln_in_assessed.shape[0]
                        ln_assessed_miles = ln_in_assessed["miles_cea"].sum()
                        ln_assessed_miles = "{0:.2f}".format(ln_assessed_miles)
                        ln_impaired_count = ln_in_impaired.shape[0]
                        ln_impaired_miles = ln_in_impaired["miles_cea"].sum()
                        ln_impaired_miles = "{0:.2f}".format(ln_impaired_miles)
                        ln_in_groups = ln_in.groupby(
                            ["isassessed", "isimpaired", "ircategory",], as_index=False
                        ).agg({"miles_cea": "sum"})
                        ln_in_groups.to_csv(
                            outmaps_dir
                            + slug_wilderness
                            + "_"
                            + str(year)
                            + "-ln_in_groups.csv",
                            index=False,
                        )
                        extra_cols = [e for e in ln_in.columns if e in ["geometry"]]
                        ln_in = ln_in.drop(columns=extra_cols)
                        ln_in.to_csv(
                            outmaps_dir
                            + slug_wilderness
                            + "_"
                            + str(year)
                            + "-ln_in.csv",
                            index=False,
                        )
            if a_year_df.empty or os.path.exists(
                water_dir + rev_date + slash + slug_wilderness + "_pt.txt"
            ):
                pt = geopandas.GeoDataFrame()
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    rev_date + slash + slug_wilderness + "_pt.json empty",
                )
            else:
                pt = geopandas.read_file(
                    water_dir + rev_date + slash + slug_wilderness + "_pt.json"
                )
            if a_year_df.empty or os.path.exists(
                water_dir + rev_date + slash + slug_wilderness + "_ca.txt"
            ):
                ca = geopandas.GeoDataFrame()
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    rev_date + slash + slug_wilderness + "_ca.json empty",
                )
            else:
                ca = geopandas.read_file(
                    water_dir + rev_date + slash + slug_wilderness + "_ca.json"
                )
                ca_a = ca.merge(
                    a_year_df,
                    left_on="assessmentunitidentifier",
                    right_on="assessmentUnitIdentifier",
                    how="left",
                )
                extra_cols = [
                    e
                    for e in ca_a.columns
                    if e
                    in ["useAttainments", "probableSources", "parameters", "documents"]
                ]
                ca_a = ca_a.drop(columns=extra_cols)
                ca = ca_a.copy()

                ca["isassessed"] = ca.apply(calc_astatus, axis=1)
                ca["isimpaired"] = ca.apply(calc_istatus, axis=1)
                ca_assessed = ca[ca["isassessed"] == "Y"]
                ca_impaired = ca[ca["isimpaired"] == "Y"]
                ca = ca.to_crs(awilderness.crs)
                ca_in = geopandas.overlay(ca, awilderness, how="intersection")

            if a_year_df.empty:
                pass
            else:
                width = 13
                axis = awilderness_1mi.plot(
                    color="none",
                    edgecolor="none",
                    alpha=0.0,
                    figsize=(width, width / 1.618),
                )
                try:
                    ca.plot(
                        ax=axis,
                        color="tab:grey",
                        edgecolor="tab:grey",
                        alpha=0.1,
                        linewidth=0.5,
                    )
                    ca_in.plot(
                        ax=axis,
                        color="tab:grey",
                        edgecolor="tab:grey",
                        alpha=0.5,
                        linewidth=0.5,
                    )
                except:
                    pass
                try:
                    pl_assessed.plot(
                        ax=axis,
                        color="tab:blue",
                        edgecolor="tab:blue",
                        alpha=1,
                        linewidth=0.5,
                    )
                    pl_impaired.plot(
                        ax=axis,
                        color="tab:red",
                        edgecolor="tab:red",
                        alpha=1,
                        linewidth=0.5,
                    )
                    pl_in_assessed.plot(
                        ax=axis,
                        color="tab:blue",
                        edgecolor="tab:blue",
                        alpha=1,
                        linewidth=2,
                    )
                    pl_in_impaired.plot(
                        ax=axis,
                        color="tab:red",
                        edgecolor="tab:red",
                        alpha=1,
                        linewidth=2,
                    )
                except:
                    pass
                try:
                    ln_assessed.plot(
                        ax=axis,
                        color="tab:blue",
                        edgecolor="tab:blue",
                        alpha=1,
                        legend=False,
                        linewidth=0.5,
                    )
                    ln_impaired.plot(
                        ax=axis,
                        color="tab:red",
                        edgecolor="tab:red",
                        alpha=1,
                        legend=False,
                        linewidth=0.5,
                    )
                    ln_in_assessed.plot(
                        ax=axis,
                        color="tab:blue",
                        edgecolor="tab:blue",
                        alpha=1,
                        legend=False,
                        linewidth=2,
                    )
                    ln_in_impaired.plot(
                        ax=axis,
                        color="tab:red",
                        edgecolor="tab:red",
                        alpha=1,
                        legend=False,
                        linewidth=2,
                    )
                except:
                    pass
                awilderness.plot(ax=axis, color="none", edgecolor="black", alpha=1)
                xlim = [
                    awilderness_1mi.total_bounds[0],
                    awilderness_1mi.total_bounds[2],
                ]
                ylim = [
                    awilderness_1mi.total_bounds[1],
                    awilderness_1mi.total_bounds[3],
                ]
                pyplot.suptitle(
                    "Extent of waterbodies with impaired water quality in "
                    + which_wilderness
                )
                txt = (
                    str(ln_impaired_miles)
                    + " miles impaired streams of\n "
                    + str(ln_assessed_miles)
                    + " miles assessed streams\n"
                    + str(pl_impaired_acres)
                    + " acres in "
                    + str(pl_impaired_count)
                    + " impaired lakes of\n "
                    + str(pl_assessed_acres)
                    + " acres in "
                    + str(pl_assessed_count)
                    + " assessed lakes"
                )
                axis.annotate(
                    txt,
                    xy=(1, 1),
                    xytext=(-20, -10),
                    xycoords=("figure fraction", "axes fraction"),
                    textcoords="offset points",
                    bbox={"facecolor": "white", "edgecolor": "black", "pad": 5.0},
                    size=8,
                    family="monospace",
                    ha="right",
                    va="top",
                )
                axis.set_xlim(xlim)
                axis.set_ylim(ylim)
                pyplot.axis("off")
                fig1 = pyplot.gcf()
                pyplot.subplots_adjust(
                    top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0
                )
                pyplot.margins(0, 0)
                # pyplot.show()
                # quit()

                fig1.savefig(
                    outmaps_dir + slug_wilderness + "_" + str(year) + "-waters.png"
                )
                log(
                    slug_wilderness,
                    slug_agency,
                    "GREEN",
                    str(slug_wilderness) + "_" + str(year) + "-waters.png created",
                )

                # quit()

                # log(None, 'WHITE', 'reading table')
                # ia = geopandas.read_file(epa303d_gdb, layer='attgeo_303dcaussrce')
