""" Visibility. """

import json

import geopandas
import pandas
import topojson
from django.utils.text import slugify

from utils import *

vis_groups = data_dir + "_visibility" + slash + "improve.csv"
vis_stations = data_dir + "_visibility" + slash + "fs_wild_wk draft 10_2018.XLS"
vis_data = (
    # data_dir + "_visibility" + slash + "Impairment_5_year_avg_all_end_years_2_22.csv"
    data_dir
    + "_visibility"
    + slash
    + "Impairment_5_year_avg_all_end_years_12_22.csv"
)


def visibility_json():
    """ vis_data csv to vis stations geojson """
    vis_df = pandas.read_csv(vis_data)
    print(vis_df.columns)
    vis_df = vis_df[vis_df.impairment_Group == 90]
    extra_cols = [e for e in vis_df.columns if "_DV" not in e]
    extra_cols = [
        value
        for value in extra_cols
        if value
        not in [
            "site",
            "SiteName",
            "affiliationCode",
            "siteTypeCode",
            "Elevation_m",
            "State",
            "Latitude",
            "Longitude",
        ]
    ]
    vis_df = vis_df.drop(columns=extra_cols)
    renames = {
        "SiteName": "name",
        "affiliationCode": "affiliation",
        "siteTypeCode": "type",
        "Elevation_m": "elev_m",
        "State": "state",
        "Longitude": "lon",
        "Latitude": "lat",
    }
    vis_df = vis_df.rename(index=str, columns=renames)
    vis_df = vis_df[
        [
            "site",
            "name",
            "affiliation",
            "state",
            "type",
            "lon",
            "lat",
            "elev_m",
            "fye93_DV",
            "fye94_DV",
            "fye95_DV",
            "fye96_DV",
            "fye97_DV",
            "fye98_DV",
            "fye99_DV",
            "fye00_DV",
            "fye01_DV",
            "fye02_DV",
            "fye03_DV",
            "fye04_DV",
            "fye05_DV",
            "fye06_DV",
            "fye07_DV",
            "fye08_DV",
            "fye09_DV",
            "fye10_DV",
            "fye11_DV",
            "fye12_DV",
            "fye13_DV",
            "fye14_DV",
            "fye15_DV",
            "fye16_DV",
            "fye17_DV",
            "fye18_DV",
            "fye19_DV",
            "fye20_DV",
        ]
    ]
    print(vis_df.columns)
    vis_groups_df = pandas.read_csv(vis_groups)
    extra_cols = [
        value for value in vis_groups_df.columns if value not in ["site", "group",]
    ]
    vis_groups_df = vis_groups_df.drop(columns=extra_cols)
    print(vis_groups_df.head)

    # vdf = vis_df.set_index("site").join(vis_groups_df.set_index("site"), how="left")
    vdf = pandas.merge(vis_df, vis_groups_df, on="site", how="left")
    print(vdf.head)
    vdf.to_csv(base_dir + "visibility.csv")
    log(None, None, "GREEN", "visibility csv created")

    vis_df["geometry"] = geopandas.points_from_xy(vis_df.lon, vis_df.lat)
    vis_gdf = geopandas.GeoDataFrame(vis_df, crs="EPSG:4326")
    vis_gdf.to_file(cache_dir + "vis_stations.json", driver="GeoJSON", index=False)
    log(None, None, "GREEN", "visibility json created")


def visibility_topojson():
    """ copeland xls to vis field topojson """
    vis_df = pandas.read_csv(vis_data)
    vis_df["geometry"] = geopandas.points_from_xy(vis_df.Longitude, vis_df.Latitude)
    vis_gdf = geopandas.GeoDataFrame(vis_df, crs="EPSG:4326")
    extra_cols = [e for e in vis_gdf.columns if "_DV" not in e]
    extra_cols = [
        value
        for value in extra_cols
        if value
        not in [
            "site",
            "SiteName",
            "affiliationCode",
            "siteTypeCode",
            "Elevation_m",
            "State",
            "geometry",
        ]
    ]
    vis_gdf = vis_gdf.drop(columns=extra_cols)
    vis_gdf.to_file(cache_dir + "vis_field.json", driver="GeoJSON", index=False)
    log(None, None, "GREEN", "vis_field json created")
    # topo = topojson.Topology(wilderness_fixture, wilderness_fixture + '.packed', quantization=1e6, simplify=0.0001)
    with uopen(cache_dir + "vis_field.json") as vg:
        vj = json.load(vg)
    topo = topojson.Topology(
        vj
    ).to_json()  # , cache_dir + 'vis_field.json' + '.packed')
    print(topo)
    with uopen(cache_dir + "vis_field.json" + ".packed", "w") as static_file:
        static_file.write(topo)
    # topo = topojson.Topology(wilderness_geojson, wilderness_geojson + '.packed')
    # with uopen(wilderness_geojson + '.packed', 'w') as static_file:
    #    static_file.write(topo)

    # topo.to_json(base_dir + 'test_data.json.packed')
    log(
        None,
        None,
        "GREEN",
        "vis_field packed to topojson " + cache_dir + "vis_field.json" + ".packed",
    )


def visibility_nwps(which_wilderness, cap_year):
    """ copeland xls to vis graph """
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    awilderness_file = slug_wilderness + "." + out_ext
    empty_file_out = out_dir + slug_wilderness + "-vis-empty.txt"

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    # awilderness.loc[awilderness['NAME'] == 'Ventana Wilderness', 'Designated'] = '1969-12-31'
    wilderness_designation_year = awilderness["dd"].iloc[0][0:4]
    stations = pandas.read_excel(open(vis_stations, "rb"))
    print(which_wilderness)
    print(stations.columns)
    station = stations[
        stations["WILDERNESS_NAME"] == which_wilderness[2] + " Wilderness"
    ]
    if station.empty:
        log(
            slug_wilderness,
            slug_agency,
            "RED",
            str(which_wilderness[2]) + " visibility empty",
        )
        with uopen(empty_file_out, "a"):
            os.utime(empty_file_out, None)
    else:
        site = station["IMPROVE_SITE_CODE"].values[0]
        data = pandas.read_csv(vis_data)
        datum1 = data[data["site"] == site]
        datum = datum1[datum1["impairment_Group"] == 90]
        datum = datum.dropna(axis=1)
        extra_cols = [e for e in datum.columns if "_DV" not in e]
        extra_cols = [value for value in extra_cols if value != "site"]
        datum = datum.drop(columns=extra_cols)
        xlist = ""
        datum["y_total"] = ""
        for col in list(datum):
            if col not in (
                "site",
                "c",
                "y_total",
                "x_total",
                "m",
                "b",
                "endy",
                "p_value",
                "trend_text",
                "acres",
            ):
                yearcol = int(col[3:5])
                if yearcol > 90:
                    yearcol = str(1900 + yearcol)
                elif yearcol <= 90:
                    yearcol = str(2000 + yearcol)
                xlist = xlist + yearcol + " "
                datum["y_total"] = datum["y_total"] + datum[col].astype(str) + " "
        datum["x_total"] = xlist
        xlist = ""
        datum["y"] = ""
        for col in list(datum):
            if col not in (
                "site",
                "c",
                "y",
                "x",
                "y_total",
                "x_total",
                "m",
                "b",
                "endy",
                "p_value",
                "trend_text",
                "acres",
            ):
                yearcol = int(col[3:5])
                if yearcol > 90:
                    yearcol = str(1900 + yearcol)
                elif yearcol <= 90:
                    yearcol = str(2000 + yearcol)
                # if int(yearcol) >= int(wilderness_designation_year) + 4:
                if int(yearcol) >= int(wilderness_designation_year) + 0:
                    xlist = xlist + yearcol + " "
                    datum["y"] = datum["y"] + datum[col].astype(str) + " "
        datum["x"] = xlist

        if datum.empty:
            log(
                slug_wilderness,
                slug_agency,
                "RED",
                str(which_wilderness[2]) + " visibility data empty",
            )
            with uopen(empty_file_out, "a"):
                os.utime(empty_file_out, None)
        else:
            if not datum["x_total"].values[0] == datum["x"].values[0]:  # extended graph
                x_vals0 = datum["x_total"].values[0]
                y_vals0 = datum["y_total"].values[0]

                x_vals0 = [int(i) for i in x_vals0.split()]
                y_vals0 = [float(i) for i in y_vals0.split()]
                df = pandas.DataFrame()
                df["years_x"] = x_vals0
                df["observations_y"] = y_vals0

                df = df.reset_index()
                df = df.sort_values("years_x", ascending=False)
                df["years_x"] = pandas.to_numeric(df["years_x"])
                df["observations_y"] = pandas.to_numeric(df["observations_y"])
                x_vals0 = df["years_x"]
                y_vals0 = df["observations_y"]
                (
                    m0,
                    b0,
                    endy0,
                    p_value0,
                    trend_text0,
                    mkr_p_value0,
                    mkr_trend_text0,
                    cols,
                ) = trender(x_vals0, y_vals0)

                cols = pandas.DataFrame(
                    {
                        "years_x": cols[:, 0],
                        "observations_y": cols[:, 1],
                        "t_predicted_y": cols[:, 3],
                    }
                )
                cols_to_plot(
                    cols["years_x"],
                    cols["observations_y"],
                    cols["t_predicted_y"],
                    ["tab:red", "tab:gray", 0.5, 1.0],
                    13,
                )

                x_vals = datum["x"].values[0]
                y_vals = datum["y"].values[0]
                x_vals = [int(i) for i in x_vals.split()]
                y_vals = [float(i) for i in y_vals.split()]
                df = pandas.DataFrame()
                df["years_x"] = x_vals
                df["observations_y"] = y_vals

                df = df.reset_index()
                df = df.sort_values("years_x", ascending=False)
                df["years_x"] = pandas.to_numeric(df["years_x"])
                df["observations_y"] = pandas.to_numeric(df["observations_y"])
                x_vals = df["years_x"]
                y_vals = df["observations_y"]
                numpy.savetxt(
                    out_dir
                    + slug_wilderness
                    + "-visibility-"
                    + site.replace(" ", "")
                    + "-all.csv",
                    cols,
                    delimiter=",",
                    fmt=["%4.0f", "%.4f", "%.4f"],
                    header="year,5yr-moving-avg-dv,trend",
                    comments="",
                )

                (
                    m,
                    b,
                    endy,
                    p_value,
                    trend_text,
                    mkr_p_value,
                    mkr_trend_text,
                    cols,
                ) = trender(x_vals, y_vals)
                cols = pandas.DataFrame(
                    {
                        "years_x": cols[:, 0],
                        "observations_y": cols[:, 1],
                        "t_predicted_y": cols[:, 3],
                    }
                )
                cols_to_plot(
                    cols["years_x"],
                    cols["observations_y"],
                    cols["t_predicted_y"],
                    ["tab:red", "tab:gray", 0.5, 1.0],
                    13,
                )

                fig1 = pyplot.gcf()
                width = 13
                fig1.set_size_inches(width, width / 1.618, forward=True)
                xmin0 = min(x_vals0)
                xmax0 = max(x_vals0)
                ymax0 = max(y_vals0)
                ytop0 = ymax0 + 2
                if ymax0 <= 1:
                    ytop0 = ((ymax0 * 100) + 2) / 100
                pyplot.axis([xmin0 - 1, xmax0 + 1, 0, ytop0])
                pyplot.xticks(x_vals0)

                xmin = min(x_vals)
                xmax = max(x_vals)

                print(x_vals0)
                print(y_vals0)

                print(xmin0)
                print(xmax0)
                print(ymax0)
                print(ytop0)

                print(x_vals)
                print(y_vals)

                print(xmin)
                print(xmax)


                ax = fig1.gca()
                if len(x_vals) >= 23:
                    temp = ax.xaxis.get_ticklabels()
                    temp = list(set(temp) - set(temp[::2]))
                    for label in temp:
                        label.set_visible(False)

                pyplot.suptitle(
                    which_wilderness[1]
                    + " "
                    + which_wilderness[2]
                    + "\nVisibility Trend from "
                    + year_formatter(xmin)
                    + " to "
                    + year_formatter(xmax),
                    y=0.95,
                )
                txt = (
                    "latest avg dv = "
                    + float_formatter(endy)
                    + "\navg dv trend = "
                    + mkr_trend_text
                    + "\n\ntrend p-value = "
                    + p_formatter(mkr_p_value)
                )
                ax.annotate(
                    txt,
                    xy=(1, 1),
                    xytext=(-12, -12),
                    xycoords="axes fraction",
                    fontsize=8,
                    family="monospace",
                    textcoords="offset points",
                    ha="right",
                    va="top",
                    bbox={"facecolor": "white", "edgecolor": "black", "pad": 5.0},
                )

                fig1.savefig(
                    out_dir + slug_wilderness + "-visibility-graph-extended.png"
                )
                log(
                    slug_wilderness,
                    slug_agency,
                    "GREEN",
                    slug_wilderness + "-visibility-graph-extended.png saved",
                )
                fig1.clf()
                pyplot.clf()
                pyplot.cla()
                pyplot.close()

            x_vals = datum["x"].values[0]
            y_vals = datum["y"].values[0]
            x_vals = [int(i) for i in x_vals.split()]
            y_vals = [float(i) for i in y_vals.split()]
            df = pandas.DataFrame()
            df["years_x"] = x_vals
            df["observations_y"] = y_vals

            df = df.reset_index()
            df = df.sort_values("years_x", ascending=False)
            df["years_x"] = pandas.to_numeric(df["years_x"])
            df["observations_y"] = pandas.to_numeric(df["observations_y"])
            x_vals = df["years_x"]
            y_vals = df["observations_y"]
            vis_minyr = df["years_x"].min()
            vis_maxyr = df["years_x"].max()

            # vis_minyr0 = vis_minyr + 4
            vis_minyr0 = vis_minyr + 5  # 5 per kdv
            vis_minyr5 = vis_minyr0 + 5
            vis_minyr10 = vis_minyr0 + 10
            vis_minyr15 = vis_minyr0 + 15
            vis_minyr20 = vis_minyr0 + 20
            vis_minyr25 = vis_minyr0 + 25
            vis_minyr30 = vis_minyr0 + 30
            vis_minyr35 = vis_minyr0 + 35
            vis_minyr40 = vis_minyr0 + 40

            if cap_year:
                vis_maxyr = min(cap_year, vis_maxyr)

            if vis_minyr0 < vis_maxyr:
                vis5 = df[df.years_x.between(vis_minyr, vis_minyr0)]
                (
                    m,
                    b,
                    endy,
                    p_value,
                    trend_text,
                    mkr_p_value,
                    mkr_trend_text,
                    cols,
                ) = trender(vis5["years_x"], vis5["observations_y"])
                cols = pandas.DataFrame(
                    {
                        "years_x": cols[:, 0],
                        "observations_y": cols[:, 1],
                        "o_predicted_y": cols[:, 2],
                        "t_predicted_y": cols[:, 3],
                    }
                )
                cols_to_plot(
                    cols["years_x"],
                    cols["observations_y"],
                    cols["t_predicted_y"],
                    ["tab:red", "tab:gray", 0.5, 1.0],
                    13,
                )
                txt = (
                    str(vis_minyr)
                    + "-"
                    + str(vis_minyr0)
                    + " : "
                    + mkr_trend_text
                    + " "
                    + "(p="
                    + p_formatter(mkr_p_value)
                    + ")"
                )
            if vis_minyr5 < vis_maxyr:
                vis5 = df[df.years_x.between(vis_minyr, vis_minyr5)]
                (
                    m,
                    b,
                    endy,
                    p_value,
                    trend_text,
                    mkr_p_value,
                    mkr_trend_text,
                    cols,
                ) = trender(vis5["years_x"], vis5["observations_y"])
                cols = pandas.DataFrame(
                    {
                        "years_x": cols[:, 0],
                        "observations_y": cols[:, 1],
                        "o_predicted_y": cols[:, 2],
                        "t_predicted_y": cols[:, 3],
                    }
                )
                cols_to_plot(
                    cols["years_x"],
                    cols["observations_y"],
                    cols["t_predicted_y"],
                    ["tab:red", "tab:gray", 0.5, 1.0],
                    13,
                )
                txt = (
                    txt
                    + "\n"
                    + str(vis_minyr)
                    + "-"
                    + str(vis_minyr5)
                    + " : "
                    + mkr_trend_text
                    + " "
                    + "(p="
                    + p_formatter(mkr_p_value)
                    + ")"
                )
            if vis_minyr10 < vis_maxyr:
                vis10 = df[df.years_x.between(vis_minyr, vis_minyr10)]
                (
                    m,
                    b,
                    endy,
                    p_value,
                    trend_text,
                    mkr_p_value,
                    mkr_trend_text,
                    cols,
                ) = trender(vis10["years_x"], vis10["observations_y"])
                cols = pandas.DataFrame(
                    {
                        "years_x": cols[:, 0],
                        "observations_y": cols[:, 1],
                        "o_predicted_y": cols[:, 2],
                        "t_predicted_y": cols[:, 3],
                    }
                )
                cols_to_plot(
                    cols["years_x"],
                    cols["observations_y"],
                    cols["t_predicted_y"],
                    ["tab:red", "tab:gray", 0.5, 1.0],
                    13,
                )
                txt = (
                    txt
                    + "\n"
                    + str(vis_minyr)
                    + "-"
                    + str(vis_minyr10)
                    + " : "
                    + mkr_trend_text
                    + " "
                    + "(p="
                    + p_formatter(mkr_p_value)
                    + ")"
                )
            if vis_minyr15 < vis_maxyr:
                vis15 = df[df.years_x.between(vis_minyr, vis_minyr15)]
                (
                    m,
                    b,
                    endy,
                    p_value,
                    trend_text,
                    mkr_p_value,
                    mkr_trend_text,
                    cols,
                ) = trender(vis15["years_x"], vis15["observations_y"])
                cols = pandas.DataFrame(
                    {
                        "years_x": cols[:, 0],
                        "observations_y": cols[:, 1],
                        "o_predicted_y": cols[:, 2],
                        "t_predicted_y": cols[:, 3],
                    }
                )
                cols_to_plot(
                    cols["years_x"],
                    cols["observations_y"],
                    cols["t_predicted_y"],
                    ["tab:red", "tab:gray", 0.5, 1.0],
                    13,
                )
                txt = (
                    txt
                    + "\n"
                    + str(vis_minyr)
                    + "-"
                    + str(vis_minyr15)
                    + " : "
                    + mkr_trend_text
                    + " "
                    + "(p="
                    + p_formatter(mkr_p_value)
                    + ")"
                )
            if vis_minyr20 < vis_maxyr:
                vis20 = df[df.years_x.between(vis_minyr, vis_minyr20)]
                (
                    m,
                    b,
                    endy,
                    p_value,
                    trend_text,
                    mkr_p_value,
                    mkr_trend_text,
                    cols,
                ) = trender(vis20["years_x"], vis20["observations_y"])
                cols = pandas.DataFrame(
                    {
                        "years_x": cols[:, 0],
                        "observations_y": cols[:, 1],
                        "o_predicted_y": cols[:, 2],
                        "t_predicted_y": cols[:, 3],
                    }
                )
                cols_to_plot(
                    cols["years_x"],
                    cols["observations_y"],
                    cols["t_predicted_y"],
                    ["tab:red", "tab:gray", 0.5, 1.0],
                    13,
                )
                txt = (
                    txt
                    + "\n"
                    + str(vis_minyr)
                    + "-"
                    + str(vis_minyr20)
                    + " : "
                    + mkr_trend_text
                    + " "
                    + "(p="
                    + p_formatter(mkr_p_value)
                    + ")"
                )
            if vis_minyr25 < vis_maxyr:
                vis25 = df[df.years_x.between(vis_minyr, vis_minyr25)]
                (
                    m,
                    b,
                    endy,
                    p_value,
                    trend_text,
                    mkr_p_value,
                    mkr_trend_text,
                    cols,
                ) = trender(vis25["years_x"], vis25["observations_y"])
                cols = pandas.DataFrame(
                    {
                        "years_x": cols[:, 0],
                        "observations_y": cols[:, 1],
                        "o_predicted_y": cols[:, 2],
                        "t_predicted_y": cols[:, 3],
                    }
                )
                cols_to_plot(
                    cols["years_x"],
                    cols["observations_y"],
                    cols["t_predicted_y"],
                    ["tab:red", "tab:gray", 0.5, 1.0],
                    13,
                )
                txt = (
                    txt
                    + "\n"
                    + str(vis_minyr)
                    + "-"
                    + str(vis_minyr25)
                    + " : "
                    + mkr_trend_text
                    + " "
                    + "(p="
                    + p_formatter(mkr_p_value)
                    + ")"
                )
            if vis_minyr30 < vis_maxyr:
                vis30 = df[df.years_x.between(vis_minyr, vis_minyr30)]
                (
                    m,
                    b,
                    endy,
                    p_value,
                    trend_text,
                    mkr_p_value,
                    mkr_trend_text,
                    cols,
                ) = trender(vis30["years_x"], vis30["observations_y"])
                cols = pandas.DataFrame(
                    {
                        "years_x": cols[:, 0],
                        "observations_y": cols[:, 1],
                        "o_predicted_y": cols[:, 2],
                        "t_predicted_y": cols[:, 3],
                    }
                )
                cols_to_plot(
                    cols["years_x"],
                    cols["observations_y"],
                    cols["t_predicted_y"],
                    ["tab:red", "tab:gray", 0.5, 1.0],
                    13,
                )
                txt = (
                    txt
                    + "\n"
                    + str(vis_minyr)
                    + "-"
                    + str(vis_minyr30)
                    + " : "
                    + mkr_trend_text
                    + " "
                    + "(p="
                    + p_formatter(mkr_p_value)
                    + ")"
                )
            if vis_minyr35 < vis_maxyr:
                vis35 = df[df.years_x.between(vis_minyr, vis_minyr35)]
                (
                    m,
                    b,
                    endy,
                    p_value,
                    trend_text,
                    mkr_p_value,
                    mkr_trend_text,
                    cols,
                ) = trender(vis35["years_x"], vis35["observations_y"])
                cols = pandas.DataFrame(
                    {
                        "years_x": cols[:, 0],
                        "observations_y": cols[:, 1],
                        "o_predicted_y": cols[:, 2],
                        "t_predicted_y": cols[:, 3],
                    }
                )
                cols_to_plot(
                    cols["years_x"],
                    cols["observations_y"],
                    cols["t_predicted_y"],
                    ["tab:red", "tab:gray", 0.5, 1.0],
                    13,
                )
                txt = (
                    txt
                    + "\n"
                    + str(vis_minyr)
                    + "-"
                    + str(vis_minyr35)
                    + " : "
                    + mkr_trend_text
                    + " "
                    + "(p="
                    + p_formatter(mkr_p_value)
                    + ")"
                )
            if vis_minyr40 < vis_maxyr:
                vis40 = df[df.years_x.between(vis_minyr, vis_minyr40)]
                (
                    m,
                    b,
                    endy,
                    p_value,
                    trend_text,
                    mkr_p_value,
                    mkr_trend_text,
                    cols,
                ) = trender(vis40["years_x"], vis40["observations_y"])
                cols = pandas.DataFrame(
                    {
                        "years_x": cols[:, 0],
                        "observations_y": cols[:, 1],
                        "o_predicted_y": cols[:, 2],
                        "t_predicted_y": cols[:, 3],
                    }
                )
                cols_to_plot(
                    cols["years_x"],
                    cols["observations_y"],
                    cols["t_predicted_y"],
                    ["tab:red", "tab:gray", 0.5, 1.0],
                    13,
                )
                txt = (
                    txt
                    + "\n"
                    + str(vis_minyr)
                    + "-"
                    + str(vis_minyr40)
                    + " : "
                    + mkr_trend_text
                    + " "
                    + "(p="
                    + p_formatter(mkr_p_value)
                    + ")"
                )

            vis_full = df[df.years_x.between(vis_minyr, vis_maxyr)]
            (
                m,
                b,
                endy,
                p_value,
                trend_text,
                mkr_p_value,
                mkr_trend_text,
                cols,
            ) = trender(vis_full["years_x"], vis_full["observations_y"])
            cols = pandas.DataFrame(
                {
                    "years_x": cols[:, 0],
                    "observations_y": cols[:, 1],
                    "o_predicted_y": cols[:, 2],
                    "t_predicted_y": cols[:, 3],
                }
            )
            cols_to_plot(
                cols["years_x"],
                cols["observations_y"],
                cols["t_predicted_y"],
                ["tab:red", "tab:gray", 1.0, 1.0],
                13,
            )
            txt = (
                txt
                + "\n"
                + str(vis_minyr)
                + "-"
                + str(vis_maxyr)
                + " : "
                + mkr_trend_text
                + " "
                + "(p="
                + p_formatter(mkr_p_value)
                + ")"
            )

            if "o_predicted_y" in cols.columns:
                cols = cols.drop(columns=["o_predicted_y"])
            numpy.savetxt(
                out_dir
                + slug_wilderness
                + "-visibility-"
                + site.replace(" ", "")
                + ".csv",
                cols,
                delimiter=",",
                fmt=["%4.0f", "%.4f", "%.4f"],
                header="year,5yr-moving-avg-dv,trend",
                comments="",
            )

            fig1 = pyplot.gcf()
            width = 13
            fig1.set_size_inches(width, width / 1.618, forward=True)
            xmin = min(x_vals)
            xmax = max(x_vals)
            ymax = max(y_vals)
            ytop = ymax + 2
            if ymax <= 1:
                ytop = ((ymax * 100) + 2) / 100

            ymax = max(y_vals)
            ypred = []
            for x in x_vals:
                ypred.append(m * x + b)
            pmax = max(ypred)
            plotmax = max([pmax, ymax])
            ytop = plotmax

            if cap_year:
                xmax = min(xmax, cap_year)

            pyplot.xticks(x_vals)
            pyplot.xlim(xmin - 1, xmax + 1)

            pyplot.xticks(x_vals)
            pyplot.xlim(xmin - 1, xmax + 1)

            ax = fig1.gca()
            if len(x_vals) >= 23:
                temp = ax.xaxis.get_ticklabels()
                temp = list(set(temp) - set(temp[::2]))
                for label in temp:
                    label.set_visible(False)

            pyplot.suptitle(
                which_wilderness[1]
                + " "
                + which_wilderness[2]
                + "\nVisibility Trends from "
                + year_formatter(xmin)
                + " to "
                + year_formatter(xmax)
                + " at "
                + site,
                y=0.95,
            )
            ax.annotate(
                txt,
                xy=(1, 1),
                xytext=(-12, -12),
                xycoords="axes fraction",
                fontsize=8,
                family="monospace",
                textcoords="offset points",
                ha="right",
                va="top",
                bbox={"facecolor": "white", "edgecolor": "black", "pad": 5.0},
            )

            fig1.savefig(out_dir + slug_wilderness + "-visibility-graph.png")
            ax.set_xlabel("Year")
            ax.set_ylabel("5-year average of 20% most impaired days, deciviews")
            fig1.savefig(out_dir + slug_wilderness + "-visibility-graph-labels.png")
            fig1.clf()
            pyplot.clf()
            pyplot.cla()
            pyplot.close()
            log(
                slug_wilderness,
                slug_agency,
                "GREEN",
                slug_wilderness + "-visibility-graph.png saved",
            )

            jsd = [
                {
                    "yr_min": year_formatter(xmin),
                    "yr_max": year_formatter(xmax),
                    "endy": float_formatter(endy),
                    "trend_text": mkr_trend_text,
                    "m": float_formatter(m),
                    "p": p_formatter(mkr_p_value),
                }
            ]
            jsc = "".join(str(v) for v in jsd).replace("'", '"')
            with uopen(out_dir + "index-vis.json", "w") as static_file:
                static_file.write(jsc)
