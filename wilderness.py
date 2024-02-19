""" Wilderness layer operations. """

import json
import math
import os
from datetime import datetime

from matplotlib import pyplot, colors
import geopandas
import pandas
import topojson
from pytopojson import topology
from django.utils.text import slugify
from shapely.validation import make_valid

import web
from settings import *
from settings_lists import *
from utils import log, try_add_basemap

from utils import *

# deprec wilderness_gdb = data_dir + '2021-04-15\\' + 'S_USA.Wilderness.gdb.zip'
nwps_wilderness_xls = "_wilderness" + slash + "NWPS.xls"  # designation years
wikipedia_wilderness_tsv = (
    "_wilderness" + slash + "wilderness_designated.tsv"
)  # designation dates
wilderness_shp = cache_dir + "wilderness.shp"  # TODO: gdb write errors
wilderness_csv = cache_dir + "wilderness.csv"
wilderness_fixture = cache_dir + "wilderness.json"
wilderness_geojson = cache_dir + "data.json"


def wilderness_year_designated_nwps():
    """ wilderness_gdb to wilderness_shp """
    rev_date = str(datetime.now().strftime("%Y-%m-%d"))
    inr = geopandas.read_file(web.get_gdb_rev("S_USA.Wilderness.gdb.zip", rev_date))

    cw = [
        "WILDERNESSID",
        "WILDERNESSNAME",
        "AREAID",
        "BOUNDARYSTATUS",
        "GIS_ACRES",
        "WID",
        "SHAPE_Length",
        "SHAPE_Area",
        "geometry",
    ]
    inr = inr.drop(columns=["SHAPE_Length", "SHAPE_Area"])
    inr["name"] = inr["WILDERNESSNAME"].str.replace(" Wilderness", "")
    inr["name"] = inr["name"].str.replace("Granite Mountain (AZ)", "Granite Mountain")
    inr["name"] = inr["name"].str.replace("Maurille Islands", "Maurelle Islands")
    inr["a"] = "FS"

    nwps_shp = data_dir + "_wilderness" + slash + "_nwps-2022-12-16.topojson"
    nwps = geopandas.read_file(nwps_shp)

    for index, row in inr.iterrows():
        if not row["geometry"].is_valid:
            log(None, None, "RED", "invalid geom at " + row["name"])
            row["geometry"] = make_valid(row["geometry"])
    for index, row in nwps.iterrows():
        if not row["geometry"].is_valid:
            log(None, None, "RED", "invalid geom at " + row["name"])
            row["geometry"] = make_valid(row["geometry"])

    cn = ["id", "name", "state", "acreage", "dd", "a", "geometry"]
    # id = nan, drop
    # name is plain
    # state is two letters
    # acreage is
    # dd is yyy-mm-dd
    # a is agency tla

    # nwps_fs = nwps.merge(inr, left_on=["name", "a"], right_on=["name", "a"], how="outer", validate="1:1", indicator=True)
    nwps_fs = geopandas.GeoDataFrame(
        nwps.merge(
            inr,
            left_on=["name", "a"],
            right_on=["name", "a"],
            how="outer",
            indicator=True,
        ),
        crs=nwps.crs,
    )
    # nwps_fs = nwps_fs[((nwps_fs["geometry_x"] != None) & (nwps_fs["geometry_y"] != None) & (nwps_fs["a"] == 'FS'))]
    # nwps_fs["geometry_x"] = nwps_fs["geometry_y"]
    nwps_fs.loc[(nwps_fs["a"] == "FS"), "geometry_x"] = nwps_fs["geometry_y"]
    # nwps_fs.loc[~(nwps_fs['a'] == 'Value'), 'c2'] = df['c3']
    nwps_fs = nwps_fs.set_geometry("geometry_x").drop(columns=["geometry_y", "_merge"])
    # nwps_gfs = nwps_fs.set_geometry('geometry_y').drop(columns=["geometry_x", "_merge"])
    nwps_fs.set_geometry("geometry_x")
    # nwps_gfs.set_geometry('geometry_y')
    nwps_fs.crs = inr.crs
    print(nwps_fs.columns)
    print(nwps_fs.crs)
    nwps_fs.to_file(cache_dir + "nwps_fs.json", driver="GeoJSON", index=False)
    # nwps_gfs.to_file(cache_dir + "nwps_gfs.json", driver="GeoJSON", index=False)
    # print(nwps_gmt.crs)
    # nwps_gmt['same'] = nwps_gmt.geom_almost_equals(nwps_gfs, align=False)
    # print(nwps_gmt.columns)
    # nwps_gmt.to_csv(path_or_buf=cache_dir + "nwps_test.csv", index=False)
    # log(None, None, "GREEN", cache_dir + "nwps_test.csv" + " written")
    quit()

    nwps_diff = geopandas.GeoDataFrame()
    for index, row in nwps_fs.iterrows():
        if not row["geometry_x"].is_valid:
            log(None, None, "RED", "invalid geom x at " + row["name"])
            row["geometry_x"] = make_valid(row["geometry_x"])
        if not row["geometry_y"].is_valid:
            log(None, None, "RED", "invalid geom y at " + row["name"])
            row["geometry_y"] = make_valid(row["geometry_y"])
        # print(row['name'])
        nwps_fss.geom_equals(s2, align=False)
        row["geometry_z"] = row["geometry_x"].symmetric_difference(row["geometry_y"])
        print(row["geometry_z"])
        # nwps_diff = nwps_diff.append(row)
        nwps_diff = geopandas.GeoDataFrame(
            pandas.concat([nwps_diff, row]), crs=nwps.crs
        )
    nwps_diff.to_csv(path_or_buf=cache_dir + "nwps_test.csv", index=False)
    log(None, None, "GREEN", cache_dir + "nwps_test.csv" + " written")

    print(nwps_diff.columns)
    nwps_diff = nwps_diff.drop(columns=["geometry_y", "geometry_x", "_merge"])
    nwps_diff2 = nwps_diff.set_geometry("geometry_z")
    nwps_diff2.to_file(cache_dir + "nwps_test.json", driver="GeoJSON", index=False)
    quit()

    # nwps_fs = nwps_fs.drop(columns=["geometry"])

    quit()

    inr = inr.rename(columns={"WILDERNESSNAME": "NAME"})

    inr.to_file(driver="ESRI Shapefile", filename=wilderness_shp)
    log(None, None, "GREEN", wilderness_shp + " written")
    inrf = inr.copy()
    inr = inr.drop(columns=["geometry"])
    inr.to_csv(path_or_buf=wilderness_csv, index=False)
    log(None, None, "GREEN", wilderness_csv + " written")
    quit()

    topbit = "[\n"
    with uopen(wilderness_fixture, "w+") as outfile:
        outfile.write(topbit)
    pkey = 1
    created = datetime.utcnow().isoformat()[:-7] + "Z"
    for i, row in inrf.iterrows():
        comma = ",\n"
        if pkey == 1:
            comma = ""
        pkey = pkey + 1
        year_designated = '"' + str(row["Designated"]) + '"'
        if year_designated == '"nan"':
            year_designated = "null"
        date_updated = '"' + str(row["Updated"]) + '"'
        if date_updated == '"nan"':
            date_updated = "null"
        year_baseline = '"' + str(row["Baseline"]) + '"'
        if year_baseline == '"nan"':
            year_baseline = "null"
        wilderness_id = (
            str(row["WID"]).replace("\r", "").replace("\n", "").replace(" ", "")
        )
        fields = (
            '{\n        "geom": "'
            + str(row["geometry"])
            + '",\n        "name": "'
            + str(row["NAME"])
            + '",\n        "slug": "'
            + str(slugify(row["NAME"]))
            + '",\n        "wilderness_id": "'
            + wilderness_id
            + '",\n        "area_id": "'
            + str(row["AREAID"])
            + '",\n        "w_id": "'
            + str(row["WID"])
            + '",\n        "boundary_status": "'
            + str(row["BOUNDARYSTATUS"])
            + '",\n        "year_designated": '
            + year_designated
            + ',\n        "year_baseline": '
            + year_baseline
            + ',\n        "updated": '
            + date_updated
            + ',\n        "gis_acres": '
            + str(row["GIS_ACRES"])
            + ',\n        "created": "'
            + str(created)
            + '",\n        "modified": null,\n        "author": 2\n    }\n'
        )
        record = (
            comma
            + '{\n    "model": "wilder.wilderness",\n    "pk": '
            + str(pkey)
            + ',\n    "fields": '
            + fields
            + "}"
        )
        with uopen(wilderness_fixture, "a") as outfile:
            outfile.write(record)
    endbit = "\n]"
    with uopen(wilderness_fixture, "a") as outfile:
        outfile.write(endbit)
    log(None, None, "GREEN", wilderness_fixture + " fixture written")


def awilderness_datestamps(which_wilderness, which_request_date, which_request_by):
    """ update wilderness_shp """
    slug_wilderness = slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + slash
    outmaps_dir = base_maps_dir + slug_wilderness + slash
    awilderness_file = slug_wilderness + "." + out_ext
    awilderness_cea_file = slug_wilderness + "-cea." + out_ext

    up_date = str(datetime.now().strftime("%Y-%m-%d"))
    wilderness = geopandas.read_file(wilderness_shp)
    wilderness.loc[wilderness["NAME"] == which_wilderness, "Baseline"] = up_date
    wilderness.loc[
        wilderness["NAME"] == which_wilderness, "Req_Date"
    ] = which_request_date
    wilderness.loc[wilderness["NAME"] == which_wilderness, "Req_By"] = which_request_by
    # awilderness = wilderness[wilderness['NAME'] == which_wilderness]
    wilderness.to_file(driver="ESRI Shapefile", filename=wilderness_shp)
    log(None, None, "GREEN", slug_wilderness + " datestamps updated")


def awilderness_datestamp_all():
    """ update wilderness_shp for all areas """
    req_list = []
    req_list.extend(y2018_req_list())
    req_list.extend(y2019_req_list())
    req_list.extend(y2020_req_list())
    req_list.extend(y2021_req_list())
    req_list.extend(y2022_req_list())
    req_list.extend(y2023_req_list())

    up_date = str(datetime.now().strftime("%Y-%m-%d"))
    wilderness = geopandas.read_file(wilderness_shp)
    for which_wilderness in req_list:
        wilderness.loc[
            wilderness["NAME"] == which_wilderness[1], "date_requested"
        ] = which_wilderness[0]
        wilderness.loc[
            wilderness["NAME"] == which_wilderness[1], "requested_by"
        ] = which_wilderness[2]
    renames = {
        "NAME": "name",
        "Designated": "year_designated",
        "Baseline": "year_baseline",
        "Updated": "year_updated",
        "GIS_ACRES": "acres",
        "BOUNDARYST": "boundary_status",
    }
    wilderness = wilderness.rename(index=str, columns=renames)
    # wilderness = wilderness[['name', 'year_designated', 'year_baseline', 'year_updated', 'acres', 'boundary_status', 'geometry']]
    wilderness = wilderness[
        [
            "name",
            "acres",
            "boundary_status",
            "year_designated",
            "year_baseline",
            "date_requested",
            "requested_by",
            "year_updated",
        ]
    ]
    print(wilderness.head)

    wilderness.to_csv(base_dir + "req_list.csv")
    log(None, None, "GREEN", "wilderness datestamps updated")


def wilderness_write_json():
    """ wilderness_shp to wilderness_geojson and packed """
    wilder_gdf = geopandas.read_file(wilderness_shp)
    wilder_gdf = wilder_gdf.to_crs(epsg=4326)
    wilder_gdf = wilder_gdf.drop(columns=["AREAID", "WID"])
    renames = {
        "NAME": "name",
        "Designated": "year_designated",
        "Baseline": "year_baseline",
        "Updated": "year_updated",
        "GIS_ACRES": "acres",
        "BOUNDARYST": "boundary_status",
    }
    wilder_gdf = wilder_gdf.rename(index=str, columns=renames)
    wilder_gdf.to_file(wilderness_geojson, driver="GeoJSON", index=False)
    # topo = topojson.Topology(wilderness_fixture, wilderness_fixture + '.packed', quantization=1e6, simplify=0.0001)
    with uopen(wilderness_geojson) as wg:
        wj = json.load(wg)
    topo = topojson.Topology(wj, wilderness_geojson + ".packed")
    # topo = topojson.Topology(wilderness_geojson, wilderness_geojson + '.packed')
    # with uopen(wilderness_geojson + '.packed', 'w') as static_file:
    #    static_file.write(topo)

    # topo.to_json(base_dir + 'test_data.json.packed')
    log(
        None,
        None,
        "GREEN",
        "wilderness areas packed to topojson " + wilderness_geojson + ".packed",
    )


def awilderness_boundary_nwps(which_wilderness):
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash
    awilderness_file = slug_wilderness + "." + out_ext
    awilderness_cea_file = slug_wilderness + "-cea." + out_ext

    # wilderness_shp = data_dir + "_wilderness" + slash + "_nwps-2022-12-16.topojson"
    wilderness_shp = cache_dir + "nwps_fs.json"
    wilderness = geopandas.read_file(wilderness_shp)
    wilderness = wilderness.drop(columns="state")
    awilderness = wilderness[
        (
            (wilderness["name"] == which_wilderness[2])
            & (wilderness["a"] == which_wilderness[1])
        )
    ]

    if which_wilderness[2] == "Ellicott Rock":
        awilderness_fix = geopandas.read_file(data_dir + "_wilderness" + slash + "wilderness-ellicott-rock-fix.geojson")
        awilderness_fix = awilderness_fix.to_crs(epsg=4269)
        fixed = geopandas.overlay(awilderness, awilderness_fix, how='union')
        #awilderness.geometry = awilderness.geometry.dissolve(awilderness_fix.geometry)
        awilderness = fixed.dissolve()
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            slug_agency + slash + slug_wilderness + " data folder created",
        )

    awilderness.to_file(driver=out_driver, filename=out_dir + awilderness_file)
    log(slug_wilderness, slug_agency, "GREEN", str(awilderness_file) + " created")
    awilderness.crs = "EPSG:4269"
    awilderness = awilderness.to_crs({"proj": "cea"})
    awilderness["acres"] = awilderness["geometry"].area / 4046.856
    awilderness.to_file(driver=out_driver, filename=out_dir + awilderness_cea_file)
    log(slug_wilderness, slug_agency, "GREEN", str(awilderness_cea_file) + " created")

    awilderness = awilderness.to_crs(epsg=4326)
    # ca_in.to_file(driver='GeoJSON', filename=wdir + slug_wilderness + '_ca_in.json')
    with uopen(out_dir + slug_wilderness + ".json", "w") as wg:
        wg.write(awilderness.to_json())
    with uopen(out_dir + slug_wilderness + ".json") as wg:
        wj = json.load(wg)
        topology_ = topology.Topology()
        topo = topology_({"wilderness": wj})
        topov = str(topo).replace("'", '"').replace(": None", ": null")
    with uopen(out_dir + slug_wilderness + ".json" + ".packed", "w") as static_file:
        static_file.write(str(topov))
    log(slug_wilderness, slug_agency, "GREEN", slug_wilderness + ".json written")

    year_baseline = str(datetime.now().strftime("%Y"))
    up_date = str(datetime.now().strftime("%Y-%m-%d"))
    # if updated is None or updated == "" or math.isnan(updated):
    updated = up_date
    log(
        slug_wilderness,
        slug_agency,
        "CYAN",
        str(year_baseline)
        + " "
        + str(updated)
        + " "
        + which_wilderness[1]
        + " "
        + which_wilderness[2],
    )

    jsd = [
        {
            "name": awilderness["name"].values[0],
            # "number": awilderness['WILDERNESS'].values[0],
            "agency": awilderness["a"].values[0],
            "acres": awilderness["acreage"].values[0],
            "year_designated": awilderness["dd"].values[0],
            "year_baseline": year_baseline,
            "updated": updated,
        }
    ]
    jsc = "".join(str(v) for v in jsd).replace("'", '"')
    with uopen(out_dir + "index-wilderness.json", "w") as static_file:
        static_file.write(jsc)


def awilderness_buffers_nwps(which_wilderness):
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    awilderness_file = slug_wilderness + "." + out_ext
    awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext
    awilderness_1mi_ring_file = slug_wilderness + "-ring." + out_ext

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    awilderness.crs = "EPSG:4269"
    awilderness_1mi = awilderness.copy()
    aw = awilderness.geometry.unary_union.centroid
    cust_epsg = {
        "proj": "aeqd",
        "lat_0": aw.y,
        "lon_0": aw.x,
        "datum": "WGS84",
        "units": "m",
    }

    awilderness_1mi = awilderness_1mi.to_crs(cust_epsg)
    awilderness_ = awilderness.to_crs(cust_epsg)
    log(slug_wilderness, slug_agency, "WHITE", str(awilderness_1mi_file) + " buffering")
    awilderness_1mi["geometry"] = awilderness_1mi.geometry.buffer(1609.34)  # 1mi
    log(slug_wilderness, slug_agency, "GREEN", str(awilderness_1mi_file) + " created")
    awilderness_1mi_ring = geopandas.overlay(
        awilderness_1mi, awilderness_, how="difference"
    )
    log(slug_wilderness, slug_agency, "WHITE", str(awilderness_1mi_file) + " ringed")
    awilderness_1mi = awilderness_1mi.to_crs(awilderness.crs)
    awilderness_1mi.to_file(driver=out_driver, filename=out_dir + awilderness_1mi_file)

    awilderness_1mi_ring = awilderness_1mi_ring.to_crs(awilderness.crs)
    awilderness_1mi_ring.to_file(
        driver=out_driver, filename=out_dir + awilderness_1mi_ring_file
    )
    log(
        slug_wilderness,
        slug_agency,
        "GREEN",
        str(awilderness_1mi_ring_file) + " created",
    )


def wilderness_maps_nwps(wilderness_list):
    """ some basic wilderness maps """
    rev_date = str(datetime.now().strftime("%Y-%m-%d"))
    us_lines = geopandas.read_file(
        web.get_gdb_rev("S_USA.ALPGeopoliticalUnit.gdb.zip", rev_date)
    )
    us_states = us_lines[us_lines["TYPENAMEREFERENCE"] == "State"]
    us_counties = us_lines[us_lines["TYPENAMEREFERENCE"] == "County"]
    us_forest = geopandas.read_file(
        web.get_gdb_rev("S_USA.AdministrativeForest.gdb.zip", rev_date)
    )
    us_ranger = geopandas.read_file(
        web.get_gdb_rev("S_USA.RangerDistrict.gdb.zip", rev_date)
    )
    width = 13

    # us_forest.to_feather('temp.feather')
    # us_forest = geopandas.read_feather('temp.feather')

    # us_forest_temp = data_dir + 'usforest_shp.shp'
    # us_forest_.to_file(driver='ESRI Shapefile', filename=us_forest_temp)
    # us_forest = geopandas.read_file(us_forest_temp)
    # us_forest = us_forest.buffer(0)
    # us_forest['geometry'] = us_forest.geometry.buffer(0)

    # us_forest_temp = data_dir + 'usforest_shp.csv'
    # us_forest.to_csv(us_forest_temp)
    # us_forest = geopandas.read_file(us_forest_temp)

    # from shapely.wkt import loads
    # for index, row in us_forest.iterrows():
    # it will throw an error where the geometry WKT isn't valid
    # csv_gdf.set_value(index, 'geometry', loads(row['geometry'])) --> deprecated
    #    us_forest.loc[index, 'geometry'] = loads(row['geometry'])

    # us_forest['valid'] = us_forest.is_valid
    # us_forest_temp = us_forest[us_forest['valid'] == False]
    # print(us_forest_temp.head)
    # us_forest_tempfile = data_dir + 'usforest_invalid_.json'
    # us_forest_temp.to_file(us_forest_tempfile, driver="GeoJSON", index=False)

    # us_forest = us_forest[~us_forest['valid'] == False]

    for which_wilderness in wilderness_list:
        slug_wilderness = slugify(which_wilderness[2])
        slug_agency = slugify(which_wilderness[1])
        out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

        awilderness_file = slug_wilderness + "." + out_ext
        awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext

        awilderness = geopandas.read_file(out_dir + awilderness_file)
        awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
        xlim_w = [awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]]
        ylim_w = [awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]]
        # aw = awilderness.geometry.unary_union.centroid
        # cust_epsg = {'proj': 'aeqd', 'lat_0': aw.y, 'lon_0': aw.x, 'datum': 'WGS84', 'units': 'm',}
        log(
            slug_wilderness,
            slug_agency,
            "WHITE",
            slug_wilderness + " overlaying forests",
        )

        # forestcut = geopandas.overlay(awilderness, us_forest, how="identity")
        # forest_list = forestcut['FORESTNAME'].tolist()
        # forestcut = us_forest[us_forest['FORESTNAME'].isin(forest_list)]
        log(
            slug_wilderness,
            slug_agency,
            "WHITE",
            slug_wilderness + " overlaying states",
        )

        statecut = geopandas.overlay(awilderness, us_states, how="identity")
        state_list = statecut["STATENAME"].tolist()
        if slug_wilderness == "southern-nantahala-wilderness":
            state_list = ["Georgia", "North Carolina"]
        print(state_list)
        statecut = us_states[us_states["STATENAME"].isin(state_list)]
        countycut = us_counties[us_counties["STATENAME"].isin(state_list)]
        statecut_box = statecut.copy()
        # statecut_box = statecut_box.to_crs({'proj':'cea'}) # maybe
        statecut_box = statecut_box.to_crs(epsg=4326)  # maybe
        statecut_box["geometry"] = statecut_box.geometry.buffer(
            0.1609344
        )  # what distance?
        # statecut_box = statecut_box.to_crs(statecut.crs)
        xlim_s = [statecut_box.total_bounds[0], statecut_box.total_bounds[2]]
        ylim_s = [statecut_box.total_bounds[1], statecut_box.total_bounds[3]]

        w = statecut_box.total_bounds[0]
        s = statecut_box.total_bounds[1]
        e = statecut_box.total_bounds[2]
        n = statecut_box.total_bounds[3]

        log(
            slug_wilderness,
            slug_agency,
            "WHITE",
            slug_wilderness + " computing tile zoom",
        )
        # print('tile zoom')
        # zoomlev = contextily.tile._calculate_zoom(w, s, e, n)
        # us_forest['valid'] = us_forest.is_valid
        # print(us_forest.head)
        # statecut['valid'] = statecut.is_valid
        # print(statecut.head)
        # us_forest['geometry'] = us_forest['geometry'].buffer(0)
        # print(us_forest.head)

        # from shapely import wkt
        # statecut['geometry'] = statecut['geometry'].astype(str).apply(wkt.loads)
        # statecut['valid'] = statecut.is_valid
        # print(statecut.head)
        # us_forest['geometry'] = us_forest['geometry'].astype(str).apply(wkt.loads)
        # us_forest['valid'] = us_forest.is_valid
        # print(us_forest.head)
        # quit()

        # usfs_inside = geopandas.clip(us_forest, statecut, keep_geom_type=False)
        # usfs_inside = geopandas.overlay(us_forest, statecut, how='intersection')
        usfs_inside = us_forest
        log(slug_wilderness, slug_agency, "WHITE", slug_wilderness + " plotting maps")

        # print(awilderness.crs)
        # awilderness = awilderness.to_crs(epsg=4326)
        # countycut = countycut.to_crs(awilderness.crs)
        # statecut = statecut.to_crs(awilderness.crs)
        # statecut_box = statecut_box.to_crs(awilderness.crs)
        # xlim_s = ([statecut_box.total_bounds[0], statecut_box.total_bounds[2]])
        # ylim_s = ([statecut_box.total_bounds[1], statecut_box.total_bounds[3]])

        axis = awilderness.plot(
            color="none",
            edgecolor="black",
            linewidth=1.0,
            alpha=0.9,
            figsize=(width, width / 1.618),
        )
        countycut.plot(
            ax=axis, color="tab:olive", edgecolor="tab:red", linewidth=1.0, alpha=0.2
        )
        statecut.plot(
            ax=axis, color="none", edgecolor="tab:red", linestyle=":", linewidth=3.0,
        )
        awilderness.plot(
            ax=axis, color="none", edgecolor="black", linewidth=1.0, alpha=0.9
        )

        axis.set_xlim(xlim_s)
        axis.set_ylim(ylim_s)
        pyplot.axis("off")
        fig1 = pyplot.gcf()
        fig1.suptitle(which_wilderness[1] + " " + which_wilderness[2])
        pyplot.subplots_adjust(top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0)
        pyplot.margins(0, 0)
        fig1.savefig(out_dir + slug_wilderness + "-map-s.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            slug_wilderness + "-map-s.png created",
        )
        # quit()

        ufill = colors.colorConverter.to_rgba("tab:green", alpha=0.2)
        usfs_inside.plot(
            ax=axis, color=ufill, edgecolor="white", linewidth=2.0,
        )

        countycut.plot(
            ax=axis, color="none", edgecolor="tab:red", linewidth=1.0, alpha=0.2
        )
        statecut.plot(
            ax=axis, color="none", edgecolor="tab:red", linestyle=":", linewidth=3.0,
        )
        awilderness.plot(
            ax=axis, color="none", edgecolor="black", linewidth=1.0, alpha=0.9
        )
        fig1.suptitle(which_wilderness[1] + " " + which_wilderness[2])
        fig1.savefig(out_dir + slug_wilderness + "-map-sf.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            slug_wilderness + "-map-sf.png created",
        )

        # try_add_basemap_(slug_wilderness, axis, awilderness.crs)
        # log(slug_wilderness, 'WHITE', str(datetime.now().strftime('%Y%m%d_%H%M')) + ' ' + slug_wilderness + ' adding terrain basemap at zoom ' + str(zoomlev))
        # contextily.add_basemap(axis, zoom=zoomlev, crs=awilderness.crs)
        # fig1 = pyplot.gcf()
        # fig1.savefig(out_dir + slug_wilderness + '-map-terrain-sf.png')
        # log(slug_wilderness, 'GREEN', slug_wilderness + '-map-terrain-sf.png created')

        fig1.clf()
        pyplot.clf()
        pyplot.cla()
        pyplot.close()

        axis = awilderness.plot(
            color="none",
            edgecolor="black",
            linewidth=1.0,
            alpha=0.9,
            figsize=(width, width / 1.618),
        )
        countycut.plot(
            ax=axis, color="tab:olive", edgecolor="tab:red", linewidth=1.0, alpha=0.2
        )
        statecut.plot(
            ax=axis, color="none", edgecolor="tab:red", linestyle=":", linewidth=3.0,
        )
        awilderness.plot(
            ax=axis, color="none", edgecolor="black", linewidth=1.0, alpha=0.9
        )

        axis.set_xlim(xlim_w)
        axis.set_ylim(ylim_w)
        pyplot.axis("off")
        fig1 = pyplot.gcf()
        fig1.suptitle(which_wilderness[1] + " " + which_wilderness[2])
        pyplot.subplots_adjust(top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0)
        pyplot.margins(0, 0)
        fig1.savefig(out_dir + slug_wilderness + "-mapw-s.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            slug_wilderness + "-mapw-s.png created",
        )

        ufill = colors.colorConverter.to_rgba("tab:green", alpha=0.2)
        usfs_inside.plot(
            ax=axis, color=ufill, edgecolor="white", linewidth=2.0,
        )

        countycut.plot(
            ax=axis, color="none", edgecolor="tab:red", linewidth=1.0, alpha=0.2
        )
        statecut.plot(
            ax=axis, color="none", edgecolor="tab:red", linestyle=":", linewidth=3.0,
        )
        awilderness.plot(
            ax=axis, color="none", edgecolor="black", linewidth=1.0, alpha=0.9
        )
        fig1.suptitle(which_wilderness[1] + " " + which_wilderness[2])
        fig1.savefig(out_dir + slug_wilderness + "-mapw-sf.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            slug_wilderness + "-mapw-sf.png created",
        )

        awilderness_box = awilderness_1mi.copy()
        awilderness_box = awilderness_1mi.to_crs({"proj": "cea"})  # breaks basemap
        awilderness_box["geometry"] = awilderness_box.geometry.buffer(
            0.1609344
        )  # how far?
        awilderness_box = awilderness_box.to_crs(awilderness_1mi.crs)  # back

        xlim2 = [awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]]
        ylim2 = [awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]]
        axis.set_xlim(xlim2)
        axis.set_ylim(ylim2)
        # print(awilderness.crs) # 4269
        # quit()
        try_add_basemap(awilderness_box.total_bounds, slug_wilderness, slug_agency, axis, awilderness.crs.to_string())
        awilderness.plot(
            ax=axis, color="none", edgecolor="black", linewidth=1.0, alpha=0.9
        )
        axis.set_xlim(xlim_w)
        axis.set_ylim(ylim_w)
        fig1 = pyplot.gcf()
        pyplot.subplots_adjust(top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0)
        pyplot.margins(0, 0)
        fig1.savefig(out_dir + slug_wilderness + "-mapw-terrain-sf.png")
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            slug_wilderness + "-mapw-terrain-sf.png created",
        )

        fig1.clf()
        pyplot.clf()
        pyplot.cla()
        pyplot.close()


def awilderness_station_buffers(which_wilderness, station_list):
    """ Testing vis stuff """
    slug_wilderness = slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + slash
    awilderness_file = slug_wilderness + "." + out_ext

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    ga = awilderness.GIS_ACRES.values[0]
    print(ga)
    g_meters = ga * 4046.856
    print(g_meters)

    r_meters = math.sqrt(g_meters / math.pi)
    print(r_meters)
    # print(awilderness.columns)
    # awilderness = awilderness.to_crs({'proj':'cea'})
    # awilderness['acres'] = awilderness['geometry'].area/4046.856
    # aw = awilderness.geometry.unary_union.centroid
    # cust_epsg = {'proj': 'aeqd', 'lat_0': aw.y, 'lon_0': aw.x, 'datum': 'WGS84', 'units': 'm',}

    # stations = pandas.read_excel(uopen(vis_stations, 'rb'))
    data = pandas.read_csv(vis_data)
    # print(data.columns)
    datum1 = data[data["impairment_Group"] == 90]
    extra_cols = [
        e for e in datum1.columns if e not in ["site", "Latitude", "Longitude"]
    ]
    datum1 = datum1.drop(columns=extra_cols)
    datum1["geometry"] = geopandas.points_from_xy(datum1.Longitude, datum1.Latitude)
    # datum = datum1[datum1['site'] == 'LIGO1']
    print(station_list)
    datum = datum1[datum1["site"].isin(station_list)]
    # print(datum.Latitude)
    # print(datum.Longitude)
    # datum['geometry'] = geopandas.points_from_xy(datum.Longitude, datum.Latitude)
    # print(datum.head)
    # va = geopandas.GeoDataFrame(datum, crs='EPSG:4326')
    # va = geopandas.GeoDataFrame(datum, crs='EPSG:4269')
    # print(va.Latitude.values[0])
    # print(va.Longitude.values[0])
    cust_epsg = {
        "proj": "aeqd",
        "lat_0": datum.Latitude.values[0],
        "lon_0": datum.Longitude.values[0],
        "datum": "WGS84",
        "units": "m",
    }
    cust_epsg = {"proj": "cea"}
    va = geopandas.GeoDataFrame(datum, crs=awilderness.crs)
    va = va.to_crs(cust_epsg)
    # print(va.head)
    # print(va.columns)
    print(r_meters)
    print(va.crs)
    # va['geometry'] = va.geometry.buffer(1)
    va["geometry"] = va.geometry.buffer(r_meters)
    # va = va.to_crs({'proj':'cea'})
    # va['acres'] = va['geometry'].area/4046.856
    print(va.head)
    # quit()
    # print(awilderness.crs)
    # print(va.crs)
    var = va.to_crs(awilderness.crs)
    var.to_file(driver="ESRI Shapefile", filename=out_dir + "vis_alt.shp")
    # datum['geometry'] = geopandas.points_from_xy(datum.Longitude, datum.Latitude)
    da = geopandas.GeoDataFrame(datum)  # , crs='EPSG:4269')
    da.to_file(driver="ESRI Shapefile", filename=out_dir + "vis_b.shp")

    # print(stations.head)
    # station = stations.query('IMPROVE_SITE_CODE == 'LIGO1' | IMPROVE_SITE_CODE == 'JARI1'')
    # station = stations[stations['IMPROVE_SITE_CODE'] == 'LIGO1']
    # print(station.head)
    # quit()
