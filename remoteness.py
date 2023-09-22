""" Remoteness. """

import json
import geopandas
import pandas
import pickle
from pyogrio import read_dataframe

import topojson
from pytopojson import topology
from django.utils.text import slugify

import web
from utils import *


def devx_join():
    """ join all the devx by shape """
    rev_date = str(datetime.now().strftime("%Y-%m-%d"))

    fstopo_building_pt = web.get_gdb_rev("S_USA.FSTopo_Building_PT.gdb.zip", rev_date)
    fstopo_culture_pt = web.get_gdb_rev("S_USA.FSTopo_Culture_PT.gdb.zip", rev_date)
    fstopo_recfacility_pt = web.get_gdb_rev(
        "S_USA.FSTopo_RecFacility_PT.gdb.zip", rev_date
    )
    fstopo_largetank_pt = web.get_gdb_rev("S_USA.FSTopo_LargeTank_PT.gdb.zip", rev_date)
    fstopo_airfield_pt = web.get_gdb_rev("S_USA.FSTopo_Airfield_PT.gdb.zip", rev_date)
    fstopo_transport_pt = web.get_gdb_rev("S_USA.FSTopo_Transport_PT.gdb.zip", rev_date)
    dev_pt_gdb_as_list = [
        fstopo_building_pt,
        fstopo_culture_pt,
        fstopo_recfacility_pt,
        fstopo_largetank_pt,
        fstopo_airfield_pt,
        fstopo_transport_pt,
    ]

    gdb_list = []
    for gdbf in dev_pt_gdb_as_list:
        log(None, None, "WHITE", str(gdbf) + " reading")
        gdb = geopandas.read_file(gdbf)
        gdb_list.append(gdb)
    dev_pt_gdb = geopandas.GeoDataFrame(pandas.concat(gdb_list), crs=gdb.crs)
    dev_pt_gdb["REV_DATE"] = pandas.Series(dev_pt_gdb["REV_DATE"], dtype="string")
    dev_pt_file = cache_dir + "devx_pt." + out_ext
    log(None, None, "WHITE", str(dev_pt_file) + " writing")
    dev_pt_gdb.to_file(driver=out_driver, filename=dev_pt_file)
    log(None, None, "GREEN", str(dev_pt_file) + " created")

    roadcore_fs_gdb = web.get_gdb_rev("S_USA.RoadCore_FS.gdb.zip", rev_date)
    road_mvm_gdb = web.get_gdb_rev("S_USA.Road_MVUM.gdb.zip", rev_date)
    road_ln_gdb_as_list = [roadcore_fs_gdb, road_mvm_gdb]

    gdb_list = []
    for gdbf in road_ln_gdb_as_list:
        log(None, None, "WHITE", str(gdbf) + " reading")
        gdb = geopandas.read_file(gdbf)
        gdb_list.append(gdb)
    road_ln_gdb = geopandas.GeoDataFrame(pandas.concat(gdb_list), crs=gdb.crs)
    print(road_ln_gdb.columns)
    print(road_ln_gdb.dtypes)
    # road_ln_gdb['REV_DATE'] = pandas.Series(road_ln_gdb['REV_DATE'], dtype="string")
    road_ln_file = cache_dir + "devx_road." + out_ext
    log(None, None, "WHITE", str(road_ln_file) + " writing")
    road_ln_gdb.to_file(driver=out_driver, filename=road_ln_file)
    log(None, None, "GREEN", str(road_ln_file) + " created")

    fstopo_building_pl = web.get_gdb_rev("S_USA.FSTopo_Building_PL.gdb.zip", rev_date)
    fstopo_builduparea_pl = web.get_gdb_rev(
        "S_USA.FSTopo_BuiltupArea_PL.gdb.zip", rev_date
    )
    fstopo_culture_pl = web.get_gdb_rev("S_USA.FSTopo_Culture_PL.gdb.zip", rev_date)
    dev_pl_gdb_as_list = [fstopo_building_pl, fstopo_builduparea_pl, fstopo_culture_pl]

    gdb_list = []
    for gdbf in dev_pl_gdb_as_list:
        log(None, None, "WHITE", str(gdbf) + " reading")
        gdb = geopandas.read_file(gdbf)
        gdb_list.append(gdb)
    dev_pl_gdb = geopandas.GeoDataFrame(pandas.concat(gdb_list), crs=gdb.crs)
    dev_pl_gdb["REV_DATE"] = pandas.Series(dev_pl_gdb["REV_DATE"], dtype="string")
    dev_pl_file = cache_dir + "devx_pl." + out_ext
    log(None, None, "WHITE", str(dev_pl_file) + " writing")
    dev_pl_gdb.to_file(driver=out_driver, filename=dev_pl_file)
    log(None, None, "GREEN", str(dev_pl_file) + " created")


def devx_clip_nwps(remoteness_list, dev_layer):  # [date, a, w, init]
    """ clip devx to wilderness list """
    rev_date = str(datetime.now().strftime("%Y-%m-%d"))
    dev_pt_file = cache_dir + "devx_pt." + out_ext
    dev_ln_file = cache_dir + "devx_ln." + out_ext
    dev_pl_file = cache_dir + "devx_pl." + out_ext
    road_ln_file = cache_dir + "devx_road." + out_ext

    log(None, None, "WHITE", dev_layer + " loading")
    if dev_layer == "devpt":
        # devx = geopandas.read_file(dev_pt_gdb, layer='dev_pt_201904')
        # devx = geopandas.read_file(dev_pt_file)
        devx = read_dataframe(dev_pt_file)
    elif dev_layer == "devpl":
        # devx = geopandas.read_file(dev_pl_gdb, layer='dev_pl_201904')
        # devx = geopandas.read_file(dev_pl_file)
        devx = read_dataframe(dev_pl_file)
    elif dev_layer == "devln":
        # devx = geopandas.read_file(dev_ln_gdb, layer='dev_ln_201904')
        # devx = geopandas.read_file(dev_ln_file)
        devx = read_dataframe(dev_ln_file)
    elif dev_layer == "roadcore2":
        # roadcore2_file = 'usa_roadcore_201904.shp' # ...why? # ealdwine stuff
        # devx = geopandas.read_file(cache_dir + roadcore2_file) # ealdwine stuff
        # devx = geopandas.read_file(road_ln_file)
        devx = read_dataframe(road_ln_file)
        # devx.crs = 'EPSG:4269'
        # roadcore_gdb = 'C:\\_\\cda_workspace\\exports.gdb'
        # devx = geopandas.read_file(roadcore_gdb, layer='usa_roadcore_201904')
    elif dev_layer == "trails":
        # z = zipfile.ZipFile(trail_nfs_gdb)
        # devx = geopandas.read_file(trails_gdb, layer=trails_fc)
        # devx = geopandas.read_file(trail_nfs_gdb, layer=trail_nfs_fc)
        # devx = geopandas.read_file(
        devx = read_dataframe(
            web.get_gdb_rev("S_USA.TrailNFS_Publish.gdb.zip", rev_date)
        )
        devx.crs = "EPSG:4269"
    for which_wilderness in remoteness_list:
        slug_wilderness = slugify(which_wilderness[2])
        slug_agency = slugify(which_wilderness[1])
        out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

        awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext
        devx_awilderness_1mi_file = (
            slug_wilderness + "-rem-" + dev_layer + "." + out_ext
        )
        devx_awilderness_1mi_json = (
            slug_wilderness + "-rem-" + dev_layer + "." + out_ext
        )
        empty_file_out = out_dir + slug_wilderness + "-rem-" + dev_layer + "-empty.txt"

        awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
        log(None, None, "WHITE", dev_layer + " copying")
        adevx = devx.copy()
        log(slug_wilderness, slug_agency, "WHITE", dev_layer + " corrections")
        if dev_layer == "devpt":
            if which_wilderness in [
                "Tray Mountain Wilderness",
                "Rich Mountain Wilderness",
            ]:
                add_shp = data_other + "Mount Rogers trails" + slash + "trails.shp"
                adevx = geopandas.read_file(add_shp)  # kealdwine, selecting outside
            if which_wilderness in [
                "Pasayten Wilderness",
                "Lake Chelan-Sawtooth Wilderness",
                "Glacier Peak Wilderness",
                "Henry M. Jackson Wilderness",
                "Alpine Lakes Wilderness",
                "Norse Peak Wilderness",
                "William O. Douglas Wilderness",
                "Goat Rocks Wilderness",
                "Glacier View Wilderness",
                "Tatoosh Wilderness",
            ]:  # v jarvis
                xl_in = data_other + "2020_WA_WCM_baseline_acres-away-inside_MVRD.xlsx"
                xl = pandas.read_excel(xl_in)
                xl["geometry"] = geopandas.points_from_xy(xl.LONGITUDE, xl.LATITUDE)
                add = geopandas.GeoDataFrame(xl, crs="EPSG:4326")
                xl_in = (
                    data_other + "2020_WA_WCM_baseline_acres-away-inside_AL_HMJ_GP.xlsx"
                )
                xl = pandas.read_excel(xl_in)
                xl["geometry"] = geopandas.points_from_xy(xl.LONGITUDE, xl.LATITUDE)
                add2 = geopandas.GeoDataFrame(xl, crs="EPSG:4326")
                add = add.append(add2)
                add.to_file(driver="ESRI Shapefile", filename=out_dir + "devpt_add.shp")
                log(slug_wilderness, slug_agency, "GREEN", "devpt_add created")
                add = add.to_crs(awilderness_1mi.crs)
                adevx = adevx.append(add)
            if which_wilderness in ["Coronation Island Wilderness"]:
                add_shp = data_other + "coronation-island-additions.shp"  # adds
                add = geopandas.read_file(add_shp)
                add = add.to_crs(awilderness_1mi.crs)
                adevx = adevx.append(add)
            if which_wilderness in ["Clifty Wilderness"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{E2C4512E-EEBA-4E9A-A964-941C5B772D3A}",
                            "{02BD7119-463D-41EB-939C-23A7D7AA7DAB}",
                            "{E2E54A13-3C32-4699-B0F1-D4EEB4EA67D4}",
                            "{1830E8C8-235E-43EA-B436-189B7E726D47}",
                            "{6D88D1CE-3088-4A43-83AE-86DD0CF05BFE}",
                        ]
                    )
                ]  # kristy ealdwine
            if which_wilderness in ["Mokelumne Wilderness"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{30001574-42E7-47F6-9789-D6AEA589BEFF}",
                            "{35F67BEC-7809-49CD-B96F-860380D72786}",
                            "{A333409D-8DA0-4DCC-B3E9-1AD5D75D8919}",
                            "{B66DBE3B-1090-4022-9CEF-88AF198C2B9A}",
                        ]
                    )
                ]  # andrew vaselka
            if which_wilderness in ["Some Jacob Thing"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{2EA2D949-92E6-4CBC-8225-8837F04FD0D2}",
                            "{AC6810CE-A553-4587-9C3F-57EBD660B14A}",
                            "{BD9C2EAC-2E08-4A92-990C-061F361313E1}",
                        ]
                    )
                ]  # jsmith
            if which_wilderness == "Shining Rock Wilderness":
                adevx = devx[
                    devx["GLOBALID"] != "{E8B2CFB2-3BDF-48B7-9072-8BCA926A9FDC}"
                ]  # kdv
            if which_wilderness == "Headwaters Wilderness":
                adevx = devx[
                    devx["GLOBALID"] == "{EAB52D3B-0E4E-42B6-8BEC-FAA1265F9D3C}"
                ]  # jsmith, selecting one outside
            if which_wilderness == "Little Lake George Wilderness":
                adevx = devx[
                    devx["GLOBALID"] == "{EAB52D3B-0E4E-42B6-8BEC-FAA1265F9D3C}"
                ]  # lct, selecting one outside
        elif dev_layer == "devpl":
            if which_wilderness in ["Bradwell Bay Wilderness_"]:
                add_shp = data_other + "bradwell-bay-devpl.shp"  # sb use local roads
                adevx = geopandas.read_file(add_shp)
                adevx = adevx.to_crs(awilderness_1mi.crs)
            elif which_wilderness in ["Mud Swamp/New River Wilderness_"]:
                add_shp = data_other + "mud-swamp-devpl.shp"  # sb use local roads
                adevx = geopandas.read_file(add_shp)
                adevx = adevx.to_crs(awilderness_1mi.crs)
            if which_wilderness in ["Big Gum Swamp Wilderness"]:
                add_shp = data_other + "big_gum_eastern_buf5.shp"  # sb use local road
                adevx = geopandas.read_file(add_shp)
                adevx = adevx.to_crs(awilderness_1mi.crs)
        elif dev_layer == "devln":
            if which_wilderness in ["Chumash Wilderness"]:
                adevx = adevx[~adevx["FCSUBTYPE"].isin([107])]
            if which_wilderness in [
                "Tray Mountain Wilderness",
                "Rich Mountain Wilderness",
            ]:
                add_shp = data_other + "Mount Rogers trails" + slash + "trails.shp"
                adevx = geopandas.read_file(add_shp)  # kealdwine, selecting outside
            if which_wilderness in ["Tatoosh Wilderness"]:  # v jarvis
                adevx = devx[
                    ~(adevx["FCSUBTYPE"].isin([106]) & adevx["NAME"].isin(["BRIDLE"]))
                ]
            if which_wilderness in [
                "Cranberry Wilderness",
                "Spice Run Wilderness",
                "Big Draft Wilderness",
                "Laurel Fork South Wilderness",
            ]:
                adevx = devx[
                    devx["GLOBALID"] == "{BFB05FAF-CEBC-41F9-BE99-379D7DE133F7}"
                ]  # one outsides
            if which_wilderness in ["Clifty Wilderness"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        ["{FACDFA06-8184-4F0A-9464-7A928CC6D765}", "", ""]
                    )
                ]  # kristy ealdwine
                cuts = adevx[(adevx["FCSUBTYPE"].isin([517]) & adevx["NAME"].isnull())]
                adevx = adevx[
                    ~(adevx["FCSUBTYPE"].isin([517]) & adevx["NAME"].isnull())
                ]  # kristy ealdwine

                add_shp = (
                    data_other
                    + "clifty acres away"
                    + slash
                    + "Clifty_acres_away_with_user_trails.shp"
                )  # ke
                add = geopandas.read_file(add_shp)
                add = add.to_crs(awilderness_1mi.crs)
                adevx = adevx.append(add)
                # adevx.to_file(driver=out_driver, filename=out_dir + 'adevx_test.shp')
            if which_wilderness in ["Little Wilson Creek Wilderness"]:
                adevx = devx[
                    devx["GLOBALID"] == "{BFB05FAF-CEBC-41F9-BE99-379D7DE133F7}"
                ]  # one outside
            if which_wilderness in ["Cummins Creek Wilderness"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{3CEA9091-3204-4C86-A80C-0EB893906BA6}",
                            "{4EBEEDD7-5BFD-42B9-AE62-585E3CB49DE3}",
                            "{BFB96BBA-7832-48F9-8816-E6D4109C3F84}",
                        ]
                    )
                ]  # ellen sulser
            if which_wilderness in ["Drift Creek Wilderness"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(["{12838B09-ABFC-4E41-BC74-84FA8FE6A460}"])
                ]  # ellen sulser
            if which_wilderness in ["Mokelumne Wilderness"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{A2567269-8865-45D9-93E8-9E8D1828D9F1}",
                            "{88A069E0-D5F2-421E-B3C7-75C3F258F603}",
                            "{0FFE1C14-62F1-4CDD-8E43-43B96E31622D}",
                            "{0510D19A-F72A-4EB7-960F-8F58F779CADE}",
                            "{32773BE9-6559-4E1D-A79E-F2C7278CCB71}",
                            "{B9FEE554-6C36-40AA-B1DF-84D980DE5519}",
                        ]
                    )
                ]  # andrew vaselka
            elif which_wilderness in [
                "Alexander Springs Wilderness",
                "Billies Bay Wilderness",
                "Juniper Prairie Wilderness",
                "Little Lake George Wilderness",
            ]:
                add_shp = data_other + "ocala-roads.shp"  # lct use local roads
                adevx = geopandas.read_file(add_shp)
            elif which_wilderness in [
                "Rainbow Mountain Wilderness",
                "La Madre Mountain Wilderness",
                "Mt. Charleston Wilderness",
            ]:
                add_shp = (
                    data_other
                    + "User trails"
                    + slash
                    + "La Madre"
                    + slash
                    + "User_Created_Trails_LaMadreWilderness.shp"
                )  # kzamuda user trails
                adevx2 = geopandas.read_file(add_shp)
                adevx2 = adevx2.to_crs(adevx.crs)
                adevx = adevx.append(adevx2)
                add_shp = (
                    data_other
                    + "User trails"
                    + slash
                    + "Mt. Charleston"
                    + slash
                    + "User_Created_Trails_MtCharlestonWilderness.shp"
                )  # kzamuda user trails
                adevx2 = geopandas.read_file(add_shp)
                adevx2 = adevx2.to_crs(adevx.crs)
                adevx = adevx.append(adevx2)
            elif which_wilderness in ["Stone Mountain Wilderness"]:
                adevx = devx[
                    devx["GLOBALID"] != "{3F222A1C-B61E-4B97-B4B1-A3EF0932C94E}"
                ]  # kristy ealdwine
            elif which_wilderness in ["Saddle Mountain Wilderness"]:
                add_shp = (
                    data_other + "BuffaloPipeline_Project.shp"
                )  # sarah rodrigquez easements
                adevx2 = geopandas.read_file(add_shp)
                adevx2 = adevx2.to_crs(adevx.crs)
                adevx = adevx.append(adevx2)
            elif which_wilderness in ["Kanab Creek Wilderness"]:
                adevx = devx[
                    devx["GLOBALID"] != "{F5C4A637-2FCA-495E-B497-C141C67AA047}"
                ]  # sarah rodrigquez
            elif which_wilderness in ["Big Gum Swamp Wilderness_"]:
                add_shp = data_other + "RairoadTramStudy.shp"  # sb use local
                adevx = geopandas.read_file(add_shp)
                adevx = adevx.to_crs(awilderness_1mi.crs)
            elif which_wilderness in ["Bradwell Bay Wilderness_"]:
                add_shp = data_other + "bradwell-bay-devln.shp"  # sb use local roads
                adevx = geopandas.read_file(add_shp)
                adevx = adevx.to_crs(awilderness_1mi.crs)
            elif which_wilderness in ["Mud Swamp/New River Wilderness_"]:
                add_shp = data_other + "mud-swamp-devln.shp"  # sb use local roads
                adevx = geopandas.read_file(add_shp)
                adevx = adevx.to_crs(awilderness_1mi.crs)
            elif which_wilderness in [
                "??? Deletions",
                "Jacob Deletions",
                "Esulser Deletions",
                "JZ Deletions",
            ]:
                adevx = devx[
                    devx["GLOBALID"] != "{809F15C5-BDBB-4473-A716-31C409516D00}"
                ]  # ???
                adevx = devx[
                    devx["GLOBALID"] != "{C922985D-4F46-40C2-8822-1BDE429E5D36}"
                ]  # esulser
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{35A2C157-8798-4DB9-BAC6-6A7AF0667773}",
                            "{543C523B-E67E-43B7-A2F4-0CA837B28A7D}",
                            "{5E4FD60F-BC6F-449F-BEDD-275205128C9D}",
                            "{7CC9A5C3-A0D8-4D10-AA0C-61168110933F}",
                            "{99045906-3AD5-4B93-BCB3-402CD11351B7}",
                            "{A1F8C478-8977-4316-8C9F-29125A2392CB}",
                            "{B7BE3BE9-9898-48F9-BB9E-C58C5D752576}",
                            "{D446CE34-A185-41BB-BD66-9735A8728BE2}",
                        ]
                    )
                ]  # jz
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{40019859-9328-431B-A8A7-E16ACA535C3D}",
                            "{4EA9263E-1F43-42E7-A824-DFEEA8801C1E}",
                        ]
                    )
                ]  # jsmith
            elif which_wilderness == "Billies Bay Wilderness":
                adevx = devx[
                    ~devx["GLOBALID"].isin(["{2DEA10ED-415C-446A-BFC0-7B4B08BF9F05}"])
                ]  # lct
            elif which_wilderness == "Juniper Prairie Wilderness":
                adevx = devx[
                    ~devx["GLOBALID"].isin(["{4EB86EA5-0BAB-4EBE-96FD-5341DDCCF1B9}"])
                ]  # lct
            elif which_wilderness == "Shining Rock Wilderness":
                adevx = devx[
                    ~devx["GLOBALID"].isin(["{9E48C695-5540-4269-88A1-CF4939C40A1B}"])
                ]  # kdv
            elif which_wilderness == "Blackjack Springs Wilderness":
                adevx = devx[
                    devx["GLOBALID"].isin(
                        [
                            "{BFB05FAF-CEBC-41F9-BE99-379D7DE133F7}",
                            "{A7CAD51C-0DE3-4600-AC25-EC3265E4F32B}",
                            "{322AF7ED-14C2-4E2C-9E76-0AE92CE552E0}",
                            "{CFAC4601-8B91-4E19-93DD-2A897004BC3C}",
                        ]
                    )
                ]  # jsmith -- {656880C7-CB0E-4818-B46E-063E689126A2} has a short segment to the south so we leave it out
            elif which_wilderness == "Headwaters Wilderness":
                adevx = devx[
                    devx["GLOBALID"].isin(
                        [
                            "{0220252A-2D6B-4FAC-A569-6E12DE35EE68}",
                            "{34D15EA5-5152-4B63-9805-EC98FA9DA133}",
                        ]
                    )
                ]  # jsmith
            elif which_wilderness == "Porcupine Lakes Wilderness":
                adevx = devx[
                    ~devx["GLOBALID"].isin(["{483BCEAB-1F49-4A60-BB15-792C1935FA37}"])
                ]  # jsmith -- full segment drop
            elif which_wilderness == "Whisker Lake Wilderness":
                adevx = devx[
                    ~devx["GLOBALID"].isin(["{89767A19-1C80-408F-B549-D5E9046220CB}"])
                ]  # jsmith -- full segment drop
                add_shp = data_other + "whisker-lake-trail.shp"
                add = geopandas.read_file(add_shp)
                adevx = geopandas.GeoDataFrame(
                    pandas.concat([devx, add], ignore_index=True)
                )
            elif which_wilderness in ["Wambaw Creek Wilderness"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{C735D36B-85C3-4D97-BBA4-5D855E72CDA9}",
                            "{30E5AE00-A164-4AF9-A1FB-73E41878BCF4}",
                            "{B4DCD96E-269D-4C9A-9833-1691492EB138}",
                            "{2465FB5D-9C02-4C7F-8542-96410B885FA3}",
                            "{622C673F-C4CE-466A-8A7D-E379F09413A8}",
                            "{E540A8A8-0FBB-4727-8503-EC2ECAC3F57A}",
                            "{FCBC9BCC-EC12-423B-BE56-E2B4E7E214F4}",
                            "{CBA9BCDF-E5D7-46A8-AA78-D206AE94AD42}",
                        ]
                    )
                ]  # carter collins inside
        elif dev_layer == "roadcore2":
            if which_wilderness in [
                "Tray Mountain Wilderness",
                "Rich Mountain Wilderness",
            ]:
                add_shp = data_other + "Mount Rogers trails" + slash + "trails.shp"
                adevx = geopandas.read_file(add_shp)  # kealdwine, selecting outside
            if which_wilderness in ["Tatoosh Wilderness"]:  # v jarvis
                adevx = devx[~devx["RTE_CN"].isin(["2785010274"])]
            if which_wilderness in [
                "Cranberry Wilderness",
                "Spice Run Wilderness",
                "Big Draft Wilderness",
                "Laurel Fork South Wilderness",
            ]:
                adevx = devx[
                    devx["GLOBALID"] == "{BF69F8B4-8269-44B6-BABF-7D2D1023AE4F}"
                ]  # one outsides
            if which_wilderness in ["Clifty Wilderness"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{9EEFB46D-0F80-4758-98A4-F63F34F788A7}",
                            "{6D877F38-A0DE-4BB8-8C86-F22E955EBDB7}",
                            "{713DCCCF-29D6-4A76-BFA0-A856E35EC944}",
                            "{FB230312-42BE-404F-80EC-C87FCE7FB33D}",
                            "{F97566C9-3F67-4219-AA5C-A3D2F28A2935}",
                            "{0BCCA3ED-DF87-4D66-8115-B8BC1C5A8FDB}",
                            "{21F3CB3A-7372-4017-B148-067D6B3B0F61}",
                            "{820CA0FE-C928-4FB6-A3D9-1262F41CDCCC}",
                            "{CBE7D9B0-2643-455E-AE80-09F4933DEFA0}",
                        ]
                    )
                ]  # kristy ealdwine
            if which_wilderness in ["Little Wilson Creek Wilderness"]:
                adevx = devx[
                    devx["GLOBALID"] == "{BF69F8B4-8269-44B6-BABF-7D2D1023AE4F}"
                ]  # one outside
            if which_wilderness in ["Cummins Creek Wilderness"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{626090AD-01A1-4A3B-A25A-465033EFFE06}",
                            "{E1388599-9A90-41E8-A3CD-BB5B1FCE6349}",
                            "{5E79FBA9-8DBF-44CD-A818-00A84579D7E7}",
                        ]
                    )
                ]  # ellen sulser
            if which_wilderness in ["Drift Creek Wilderness"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{45C63A29-146A-412A-8D26-DB668FA1EAA7}",
                            "{C7BD7C41-571E-4D74-BB2E-5300CBFF5A8D}",
                            "{B5815113-9E67-4580-8FCA-85D49365537E}",
                            "{24D0962E-70C9-45A7-BD56-62890E6FB06A}",
                        ]
                    )
                ]  # ellen sulser
            if which_wilderness in ["Wambaw Creek Wilderness"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{A6721867-8E1C-4D5E-A13B-6C5F72A311EA}",
                            "{2F4E7766-59B0-47C3-AD7B-73F51835B253}",
                            "{BBF86853-B388-4876-B94D-F82EDD2F3BD2}",
                            "{0983B387-1397-46E7-9B5F-E27175076E93}",
                            "{18296D89-6597-4500-B9AD-62B5C6C2F609}",
                            "{CF20AAB5-D9C8-421D-A6E7-3472E2C346CA}",
                            "{CF20AAB5-D9C8-421D-A6E7-3472E2C346CA}",
                        ]
                    )
                ]  # carter collins inside
            elif which_wilderness in [
                "Alexander Springs Wilderness",
                "Billies Bay Wilderness",
                "Juniper Prairie Wilderness",
                "Little Lake George Wilderness",
            ]:
                add_shp = data_other + "ocala-roads.shp"  # lct use local roads
                adevx = geopandas.read_file(add_shp)
                adevx = adevx.to_crs(awilderness_1mi.crs)
            elif which_wilderness in ["Big Gum Swamp Wilderness_"]:
                add_shp = data_other + "RairoadTramStudy.shp"  # sb use local
                adevx = geopandas.read_file(add_shp)
                adevx = adevx.to_crs(awilderness_1mi.crs)
            elif which_wilderness in ["Bradwell Bay Wilderness"]:
                add_shp = data_other + "bradwell-bay-devln.shp"  # sb use local roads
                adevx = geopandas.read_file(add_shp)
                adevx = adevx.to_crs(awilderness_1mi.crs)
            elif which_wilderness in ["Mud Swamp/New River Wilderness"]:
                add_shp = data_other + "mud-swamp-devln.shp"  # sb use local roads
                adevx = geopandas.read_file(add_shp)
                adevx = adevx.to_crs(awilderness_1mi.crs)
            elif which_wilderness in ["Jacob Deletions"]:
                adevx = devx[
                    ~devx["GLOBALID"].isin(
                        [
                            "{85800AB6-9291-460C-81B5-5B46DE83E119}",
                            "{4EA9263E-1F43-42E7-A824-DFEEA8801C1E}",
                            "{EFFC5213-878F-4939-BDD6-07654471B05A}",
                            "{13C50CEA-231F-4546-97CF-693BD8EC6D31}",
                            "{735639C9-3716-4975-8A17-79BBF5732CC3}",
                            "{86C66183-35F0-4345-B256-04DB6C2CD862}",
                            "{DFB89FCF-139E-49C5-9AAE-ADB327015B7A}",
                            "{3E305234-8495-4CEA-8016-65B69E1DFC8F}",
                            "{F441F13A-281D-410E-811F-772C159EABDD}",
                            "{400D0A97-7A80-4BA3-8F6C-C4175F772CD3}",
                            "{048A0DD4-941B-4520-BAF2-D334D9206F0B}",
                            "{09D1F9F2-2EA2-4BF1-B582-DED829DBEAD3}",
                            "{C47B06C7-65C9-495F-93F1-1A8B2F0C234D}",
                            "{DC80315B-F3BA-4E6C-9AC6-B735C9A90F4B}",
                            "{21977D17-A230-418C-B36F-E5142D4EF2B8}",
                            "{4EEB44F5-5D1E-4FB1-B7C6-4D0427C1A3FE}",
                            "{F18732C3-3A1F-4541-8C98-A0F7939F6270}",
                            "{378D41FE-F8A8-4965-9A42-A51DFAD99332}",
                            "{C1820D1E-8CA6-4CBB-A887-58DEA966A851}",
                            "{27DE5C1F-725A-40EC-B462-5C0CE9F5D079}",
                            "{BB82F30A-AB80-4C9B-9AF3-893AE20A89FC}",
                        ]
                    )
                ]  # jsmith
            elif which_wilderness == "Shining Rock Wilderness":
                adevx = devx[
                    devx["GLOBALID"] != "{CF823791-2ACF-4374-A6F4-24BC19DB06CE}"
                ]  # kdv
            elif which_wilderness == "Blackjack Springs Wilderness":
                adevx = devx[
                    devx["GLOBALID"] == "{BF69F8B4-8269-44B6-BABF-7D2D1023AE4F}"
                ]  # jsmith, selecting one outside
            elif which_wilderness == "Headwaters Wilderness":
                adevx = devx[
                    devx["GLOBALID"] == "{BF69F8B4-8269-44B6-BABF-7D2D1023AE4F}"
                ]  # jsmith, selecting one outside
            elif which_wilderness == "Porcupine Lakes Wilderness":
                adevx = devx[
                    ~devx["GLOBALID"].isin(["{EFE6F545-1860-4981-A31B-A38EAE75B8BE}"])
                ]  # jsmith -- full segment drop
            adevx.crs = "EPSG:4269"
        elif dev_layer == "trails":
            if which_wilderness in ["Chumash Wilderness"]:
                adevx = adevx[adevx["TRAIL_NO"].isin(["21W03", "22W02", "22W21"])]
            # if which_wilderness in ['Tray Mountain Wilderness']:
            #    adevx = devx[~devx['TRAIL_CN'].isin(["5236.005951"])] # kealdwine
            if which_wilderness in ["Tray Mountain Wilderness"]:
                add_shp = (
                    data_other
                    + "side-trails-tray-merge_shape"
                    + slash
                    + "side-trails-tray-merge.shp"
                )
                adevx = geopandas.read_file(add_shp)  # kealdwine trails
            if which_wilderness in ["Rich Mountain Wilderness"]:
                add_shp = data_other + "Mount Rogers trails" + slash + "trails.shp"
                adevx = geopandas.read_file(add_shp)  # kealdwine, selecting outside
            if which_wilderness in ["Mokelumne Wilderness"]:
                adevx = devx[~devx["TRAIL_CN"].isin(["5038.003661"])]  # andrew vaselka
            if which_wilderness in ["Little Wilson Creek Wilderness"]:
                add_shp = (
                    data_other + "Mount Rogers trails" + slash + "trails.shp"
                )  # kathleen pangan
                adevx = geopandas.read_file(add_shp)
                adevx = adevx.to_crs(awilderness_1mi.crs)
            log(
                slug_wilderness,
                slug_agency,
                "WHITE",
                dev_layer + " clipping to " + devx_awilderness_1mi_file,
            )

        if dev_layer == "devpl":
            xmin, ymin, xmax, ymax = awilderness_1mi.total_bounds
            devx_around = adevx.cx[xmin:xmax, ymin:ymax]
            if devx_around.empty:
                devx_awilderness_1mi = geopandas.GeoDataFrame()
            else:
                devx_awilderness_1mi = geopandas.overlay(
                    adevx, awilderness_1mi, how="intersection"
                )
        elif dev_layer == "devpt":
            devx_tagged = geopandas.sjoin(
                adevx,
                awilderness_1mi[["name", "geometry"]],
                how="left",
                predicate="within",
            )
            devx_awilderness_1mi = devx_tagged[devx_tagged["name"].notnull()]
        else:
            # devx_awilderness_1mi = lines_poly(adevx, awilderness_1mi) # deprec?
            devx_awilderness_1mi = geopandas.overlay(
                adevx, awilderness_1mi, how="intersection"
            )

        if devx_awilderness_1mi.empty:
            log(
                slug_wilderness,
                slug_agency,
                "WHITE",
                slug_wilderness + " " + dev_layer + " clipped empty",
            )
            with uopen(empty_file_out, "a"):
                os.utime(empty_file_out, None)

            empty_devx_in = {
                "type": "Topology",
                "objects": {
                    dev_layer: {"type": "GeometryCollection", "geometries": []}
                },
                "arcs": [],
                "bbox": [],
            }
            with uopen(
                out_dir + slug_wilderness + "_" + dev_layer + ".json" + ".packed", "w"
            ) as static_file:
                static_file.write(str(empty_devx_in).replace("'", '"'))
            log(
                None,
                None,
                "RED",
                slug_wilderness + "_" + dev_layer + ".json written empty",
            )

        else:
            log(
                slug_wilderness,
                slug_agency,
                "WHITE",
                str(devx_awilderness_1mi_file) + " writing",
            )
            devx_awilderness_1mi.to_file(
                driver=out_driver, filename=out_dir + devx_awilderness_1mi_file
            )
            log(
                slug_wilderness,
                slug_agency,
                "GREEN",
                str(devx_awilderness_1mi_file) + " created",
            )

            # print(devx_awilderness_1mi.head)
            # print('devx_awilderness_1mi.crs')
            # print(devx_awilderness_1mi.crs)
            # devx_awilderness_1mi = devx_awilderness_1mi.to_crs(epsg=4326)
            devx_extra_cols = [
                "SHAPE_Area",
                "SHAPE_Length",
                "id",
                "name",
                "acreage",
                "dd",
                "a",
                "WILDERNESS",
                "WILDERNE_1",
                "AREAID",
                "BOUNDARYST",
                "GIS_ACRES",
                "WID",
                "index_right",
            ]
            extra_cols = [
                e for e in devx_awilderness_1mi.columns if e in devx_extra_cols
            ]
            devx_awilderness_1mi = devx_awilderness_1mi.drop(columns=extra_cols)

            # ca_in.to_file(driver='GeoJSON', filename=wdir + slug_wilderness + '_ca_in.json')
            with uopen(
                out_dir + slug_wilderness + "_" + dev_layer + ".json", "w"
            ) as wg:
                wg.write(devx_awilderness_1mi.to_json())
            with uopen(out_dir + slug_wilderness + "_" + dev_layer + ".json") as wg:
                wj = json.load(wg)
                topology_ = topology.Topology()
                topo = topology_({dev_layer: wj})
                topov = str(topo).replace("'", '"').replace(": None", ": null")
            with uopen(
                out_dir + slug_wilderness + "_" + dev_layer + ".json" + ".packed", "w"
            ) as static_file:
                static_file.write(str(topov))
            log(
                None, None, "GREEN", slug_wilderness + "_" + dev_layer + ".json written"
            )


def devx_to_awilderness_nwps(which_wilderness, dev_layer, io):  # [date, a, w, init]
    """ clip devx to single wilderness """
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    if io == "in":
        awilderness_file = slug_wilderness + "." + out_ext
    elif io == "out":
        awilderness_file = slug_wilderness + "-ring." + out_ext
    devx_awilderness_1mi_file = slug_wilderness + "-rem-" + dev_layer + "." + out_ext
    awilderness_devx_file = (
        slug_wilderness + "-rem-" + io + "-" + dev_layer + "." + out_ext
    )
    empty_file_in = out_dir + slug_wilderness + "-rem-" + dev_layer + "-empty.txt"
    empty_file_out = (
        out_dir + slug_wilderness + "-rem-" + io + "-" + dev_layer + "-empty.txt"
    )

    if os.path.exists(empty_file_in):
        log(slug_wilderness, slug_agency, "RED", devx_awilderness_1mi_file + " empty")
        with uopen(empty_file_out, "a"):
            os.utime(empty_file_out, None)
    else:
        log(
            slug_wilderness,
            slug_agency,
            "WHITE",
            devx_awilderness_1mi_file + " loading",
        )
        devx_awilderness_1mi = geopandas.read_file(out_dir + devx_awilderness_1mi_file)
        awilderness = geopandas.read_file(out_dir + awilderness_file)

        log(
            slug_wilderness,
            slug_agency,
            "WHITE",
            dev_layer + " clipping to " + awilderness_devx_file,
        )
        if dev_layer == "devpl":
            xmin, ymin, xmax, ymax = awilderness.total_bounds
            devx_around = devx_awilderness_1mi.cx[xmin:xmax, ymin:ymax]
            if devx_around.empty:
                awilderness_devx = geopandas.GeoDataFrame()
            else:
                awilderness_devx = geopandas.overlay(
                    devx_awilderness_1mi, awilderness, how="intersection"
                )
                awilderness_devx.crs = "EPSG:4269"
        elif dev_layer == "devpt":
            devx_tagged = geopandas.sjoin(
                devx_awilderness_1mi,
                awilderness[["name", "geometry"]],
                how="left",
                predicate="within",
            )
            awilderness_devx = devx_tagged[devx_tagged["name_right"].notnull()]
        else:
            # awilderness_devx = lines_poly(devx_awilderness_1mi, awilderness) # deprec?
            awilderness_devx = geopandas.overlay(
                devx_awilderness_1mi, awilderness, how="intersection"
            )
            if awilderness_devx.empty:
                with uopen(empty_file_out, "a"):
                    os.utime(empty_file_out, None)
            else:
                awilderness_devx["gt"] = awilderness_devx["geometry"].geom_type
                for index, row in awilderness_devx.iterrows():
                    if row["gt"] in ["GeometryCollection"]:
                        for g in row["geometry"]:
                            newrow = row
                            newrow["geometry"] = g
                            newrow["gt"] = newrow["geometry"].geom_type
                            awilderness_devx = awilderness_devx.append(
                                newrow, ignore_index=True
                            )
                awilderness_devx = awilderness_devx[
                    awilderness_devx["gt"].isin(["LineString", "MultiLineString"])
                ]
        if awilderness_devx.empty:
            with uopen(empty_file_out, "a"):
                os.utime(empty_file_out, None)
            log(slug_wilderness, slug_agency, "YELLOW", io + "-" + dev_layer + " empty")
        else:
            # awilderness_devx['geometry'] = awilderness_devx.geometry.apply(cast_to_multigeometry) # deprec?
            log(
                slug_wilderness,
                slug_agency,
                "WHITE",
                str(awilderness_devx_file) + " writing",
            )
            awilderness_devx.to_file(
                driver=out_driver, filename=out_dir + awilderness_devx_file
            )
            log(
                slug_wilderness,
                slug_agency,
                "GREEN",
                str(awilderness_devx_file) + " created",
            )


def devx_to_awilderness_buffer_erase_nwps(
    which_wilderness, dev_layer, io
):  # [date, a, w, init]
    """ buffer devx and erase from wilderness """
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    awilderness_file = slug_wilderness + "." + out_ext
    awilderness_devx_file = (
        slug_wilderness + "-rem-" + io + "-" + dev_layer + "." + out_ext
    )
    devx_awilderness_buffer_file = (
        slug_wilderness + "-rem-" + io + "-" + dev_layer + "-buffer." + out_ext
    )
    devx_awilderness_erase_file = (
        slug_wilderness + "-rem-" + io + "-" + dev_layer + "-erase." + out_ext
    )
    empty_file_in = (
        out_dir + slug_wilderness + "-rem-" + io + "-" + dev_layer + "-empty.txt"
    )
    empty_file_out = (
        out_dir + slug_wilderness + "-rem-" + io + "-" + dev_layer + "-erase-empty.txt"
    )

    if os.path.exists(empty_file_in):
        log(
            slug_wilderness,
            slug_agency,
            "WHITE",
            awilderness_devx_file + " empty, no buffers",
        )
        devx_awilderness_buffer = None
    else:
        awilderness_devx = geopandas.read_file(out_dir + awilderness_devx_file)
        log(slug_wilderness, slug_agency, "WHITE", "buffering " + awilderness_devx_file)
        devx_awilderness_buffer = awilderness_devx.copy()
        devx_awilderness_buffer["geometry"] = devx_awilderness_buffer.geometry.buffer(
            0.00804672
        )
        devx_awilderness_buffer.to_file(
            driver=out_driver, filename=out_dir + devx_awilderness_buffer_file
        )
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            str(devx_awilderness_buffer_file) + " created",
        )
    if os.path.exists(empty_file_in):
        log(
            slug_wilderness,
            slug_agency,
            "WHITE",
            awilderness_devx_file + " empty, erased is full wilderness",
        )
        devx_erase_poly = geopandas.read_file(out_dir + awilderness_file)
        devx_erase = geopandas.GeoDataFrame(devx_erase_poly)
        devx_erase.crs = "EPSG:4269"
        devx_erase.to_file(
            driver=out_driver, filename=out_dir + devx_awilderness_erase_file
        )
        log(
            slug_wilderness,
            slug_agency,
            "GREEN",
            str(devx_awilderness_erase_file) + " created",
        )
    else:
        if devx_awilderness_buffer is not None:
            pass
        else:
            devx_awilderness_buffer = geopandas.read_file(
                out_dir + devx_awilderness_buffer_file
            )
        awilderness = geopandas.read_file(out_dir + awilderness_file)
        if dev_layer == "devpt":
            devx_awilderness_buffer = devx_awilderness_buffer.to_crs(awilderness.crs)
        log(
            slug_wilderness,
            slug_agency,
            "WHITE",
            "erasing " + devx_awilderness_buffer_file,
        )
        devx_erase_poly = geopandas.overlay(
            awilderness, devx_awilderness_buffer, how="difference"
        )
        devx_erase_poly.explode(index_parts=True)
        devx_erase = geopandas.GeoDataFrame(devx_erase_poly)
        devx_erase = devx_erase.rename(columns={0: "geometry"}).set_geometry("geometry")
        devx_erase.crs = "EPSG:4269"
        if devx_erase.empty:
            with uopen(empty_file_out, "a"):
                os.utime(empty_file_out, None)
            log(
                slug_wilderness,
                slug_agency,
                "WHITE",
                dev_layer + " covers wilderness, erased is empty",
            )
        else:
            devx_erase.to_file(
                driver=out_driver, filename=out_dir + devx_awilderness_erase_file
            )
            log(
                slug_wilderness,
                slug_agency,
                "GREEN",
                str(devx_awilderness_erase_file) + " created",
            )


def remoteness_nwps(which_wilderness, io):  # [date, a, w, init]
    """ layer erases to remoteness poly """
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    devpt_awilderness_erase_file = (
        slug_wilderness + "-rem-" + io + "-devpt-erase." + out_ext
    )
    devpt_empty_file_in = (
        out_dir + slug_wilderness + "-rem-" + io + "-devpt-erase-empty.txt"
    )
    devln_awilderness_erase_file = (
        slug_wilderness + "-rem-" + io + "-devln-erase." + out_ext
    )
    devln_empty_file_in = (
        out_dir + slug_wilderness + "-rem-" + io + "-devln-erase-empty.txt"
    )
    devpl_awilderness_erase_file = (
        slug_wilderness + "-rem-" + io + "-devpl-erase." + out_ext
    )
    devpl_empty_file_in = (
        out_dir + slug_wilderness + "-rem-" + io + "-devpl-erase-empty.txt"
    )
    roadcore_awilderness_erase_file = (
        slug_wilderness + "-rem-" + io + "-roadcore2-erase." + out_ext
    )
    roadcore_empty_file_in = (
        out_dir + slug_wilderness + "-rem-" + io + "-roadcore2-erase-empty.txt"
    )
    trails_awilderness_erase_file = (
        slug_wilderness + "-rem-" + io + "-trails-erase." + out_ext
    )
    trails_empty_file_in = (
        out_dir + slug_wilderness + "-rem-" + io + "-trails-erase-empty.txt"
    )
    inroads_file = slug_wilderness + "-rem-" + io + "-fin." + out_ext
    empty_file_out = out_dir + slug_wilderness + "-rem-" + io + "-fin-empty.txt"

    if os.path.exists(devpt_empty_file_in):
        inroads = None
    elif os.path.exists(devln_empty_file_in):
        inroads = None
    elif os.path.exists(devpl_empty_file_in):
        inroads = None
    elif os.path.exists(roadcore_empty_file_in):
        inroads = None
    elif os.path.exists(trails_empty_file_in):
        inroads = None
    else:
        if os.path.exists(out_dir + devpt_awilderness_erase_file):
            devpt_awilderness_erase = geopandas.read_file(
                out_dir + devpt_awilderness_erase_file
            )
            devpt_awilderness_erase.crs = "EPSG:4269"
        else:
            log(
                slug_wilderness,
                slug_agency,
                "RED",
                devpt_awilderness_erase_file + " does not exist",
            )
            devpt_awilderness_erase = None

        if os.path.exists(out_dir + devln_awilderness_erase_file):
            devln_awilderness_erase = geopandas.read_file(
                out_dir + devln_awilderness_erase_file
            )
            devln_awilderness_erase.crs = "EPSG:4269"
        else:
            log(
                slug_wilderness,
                slug_agency,
                "RED",
                devln_awilderness_erase_file + " does not exist",
            )
            devln_awilderness_erase = None

        if devpt_awilderness_erase is not None and devln_awilderness_erase is not None:
            try:
                auto_inter = geopandas.overlay(
                    devpt_awilderness_erase, devln_awilderness_erase, how="intersection"
                )
            except KeyError:
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    io + " devpt/devln clipped empty",
                )
                auto_inter = None
        elif devln_awilderness_erase is not None:
            auto_inter = devln_awilderness_erase.copy()
        elif devpt_awilderness_erase is not None:
            auto_inter = devpt_awilderness_erase.copy()
        else:
            auto_inter = None

        if os.path.exists(out_dir + devpl_awilderness_erase_file):
            devpl_awilderness_erase = geopandas.read_file(
                out_dir + devpl_awilderness_erase_file
            )
            devpl_awilderness_erase.crs = "EPSG:4269"
        else:
            log(
                slug_wilderness,
                slug_agency,
                "RED",
                devpl_awilderness_erase_file + " does not exist",
            )
            devpl_awilderness_erase = None

        if auto_inter is not None and devpl_awilderness_erase is not None:
            try:
                auto_inter2 = geopandas.overlay(
                    auto_inter, devpl_awilderness_erase, how="intersection"
                )
            except KeyError:
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    io + " devpt/devln/devpl clipped empty",
                )
                auto_inter2 = None
        elif devpl_awilderness_erase is not None:
            auto_inter2 = devpl_awilderness_erase.copy()
        elif auto_inter is not None:
            auto_inter2 = auto_inter.copy()
        else:
            auto_inter2 = None

        if os.path.exists(out_dir + roadcore_awilderness_erase_file):
            roadcore_awilderness_erase = geopandas.read_file(
                out_dir + roadcore_awilderness_erase_file
            )
            roadcore_awilderness_erase.crs = "EPSG:4269"
        else:
            log(
                slug_wilderness,
                slug_agency,
                "RED",
                roadcore_awilderness_erase_file + " does not exist",
            )
            roadcore_awilderness_erase = None

        if auto_inter2 is not None and roadcore_awilderness_erase is not None:
            try:
                ai3 = geopandas.overlay(
                    auto_inter2, roadcore_awilderness_erase, how="intersection"
                )
            except KeyError:
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    io + " devpt/devln/devpl/roadcore clipped empty",
                )
                ai3 = None
        elif roadcore_awilderness_erase is not None:
            ai3 = roadcore_awilderness_erase.copy()
        elif auto_inter2 is not None:
            ai3 = auto_inter2.copy()
        else:
            ai3 = None

        if os.path.exists(out_dir + trails_awilderness_erase_file):
            trails_awilderness_erase = geopandas.read_file(
                out_dir + trails_awilderness_erase_file
            )
            trails_awilderness_erase.crs = "EPSG:4269"
        else:
            log(
                slug_wilderness,
                slug_agency,
                "RED",
                trails_awilderness_erase_file + " does not exist",
            )
            trails_awilderness_erase = None

        if ai3 is not None and trails_awilderness_erase is not None:
            try:
                inroads = geopandas.overlay(
                    ai3, trails_awilderness_erase, how="intersection"
                )
            except KeyError:
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    io + " devpt/devln/devpl/roadcore/trails clipped empty",
                )
                inroads = None
        elif trails_awilderness_erase is not None:
            inroads = trails_awilderness_erase.copy()
        elif ai3 is not None:
            inroads = ai3.copy()
        else:
            inroads = None

    if inroads is not None:
        inroads = inroads.to_crs({"proj": "cea"})
        extra_cols = [e for e in inroads.columns if e not in ["geometry"]]
        inroads = inroads.drop(columns=extra_cols)
        inroads["acres"] = inroads["geometry"].area / 4046.856
        inroads.to_file(driver=out_driver, filename=out_dir + inroads_file)
        log(slug_wilderness, slug_agency, "GREEN", str(inroads_file) + " created")
    else:
        with uopen(empty_file_out, "a"):
            os.utime(empty_file_out, None)
        log(slug_wilderness, slug_agency, "RED", io + " measure empty")


def remoteness_web_nwps(which_wilderness):
    """make the geojsons """
    slug_w = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_w + slash

    file_list = []
    file_list.append("_trails")
    file_list.append("_roadcore2")
    file_list.append("_devpt")
    file_list.append("_devln")
    file_list.append("_devpl")
    file_list = []
    file_list.append("-rem-in-fin")
    file_list.append("-rem-out-fin")
    file_list.append("-rem-in-roadcore2")
    file_list.append("-rem-in-trails")
    file_list.append("-rem-in-devln")
    file_list.append("-rem-in-devpl")
    file_list.append("-rem-in-devpt")
    file_list.append("-rem-out-roadcore2")
    file_list.append("-rem-out-trails")
    file_list.append("-rem-out-devln")
    file_list.append("-rem-out-devpl")
    file_list.append("-rem-out-devpt")

    print(out_dir)
    for f in file_list:
        file = slug_w + f
        layer = f.replace("-", "_")
        if os.path.exists(out_dir + file + "." + out_ext):
            gdf = geopandas.read_file(out_dir + file + "." + out_ext)
            gdf = gdf.to_crs(epsg=4326)
            print("oh yes -- " + file + " ok at " + "str(gdf.count)")
            gdf.to_file(out_dir + file + ".json", driver="GeoJSON", index=False)

            with uopen(out_dir + file + ".json", "w") as wg:
                wg.write(gdf.to_json())
            print("...out as " + file + ".json")
            with uopen(out_dir + file + ".json") as wg:
                wj = json.load(wg)
                topology_ = topology.Topology()
                topo = topology_({layer: wj})
                topov = str(topo).replace("'", '"').replace(": None", ": null")
            with uopen(out_dir + file + ".json" + ".packed", "w") as static_file:
                static_file.write(str(topov))
            print("...and as " + file + ".json.packed")
        elif os.path.exists(out_dir + file + "-empty.txt"):
            print("fuck you, " + file + " empty")
            gdf = {
                "type": "Topology",
                "objects": {layer: {"type": "GeometryCollection", "geometries": []}},
                "arcs": [],
                "bbox": [],
            }
            with uopen(out_dir + file + ".json" + ".packed", "w") as static_file:
                static_file.write(str(gdf))  # .replace("'", '"'))
            print("...empty - " + file + ".json.packed")
        else:
            print("...no no - " + file + " missing")
            gdf = {
                "type": "Topology",
                "objects": {layer: {"type": "GeometryCollection", "geometries": []}},
                "arcs": [],
                "bbox": [],
            }
            with uopen(out_dir + file + ".json" + ".packed", "w") as static_file:
                static_file.write(str(gdf))  # .replace("'", '"'))
            print("...empty - " + file + ".json.packed")
    # quit()


def remoteness_plots(which_wilderness):
    """make the maps """
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    out_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    awilderness_file = slug_wilderness + "-cea." + out_ext
    awilderness_1mi_file = slug_wilderness + "-buffer." + out_ext
    inroads_file = slug_wilderness + "-rem-in-fin." + out_ext
    outroads_file = slug_wilderness + "-rem-out-fin." + out_ext
    inroads_empty_file = slug_wilderness + "-rem-in-fin-empty.txt"
    outroads_empty_file = slug_wilderness + "-rem-out-fin-empty.txt"
    inroads_roadcore_file = slug_wilderness + "-rem-in-roadcore2." + out_ext
    inroads_trails_file = slug_wilderness + "-rem-in-trails." + out_ext
    inroads_devln_file = slug_wilderness + "-rem-in-devln." + out_ext
    inroads_devpl_file = slug_wilderness + "-rem-in-devpl." + out_ext
    inroads_devpt_file = slug_wilderness + "-rem-in-devpt." + out_ext
    outroads_roadcore_file = slug_wilderness + "-rem-out-roadcore2." + out_ext
    outroads_trails_file = slug_wilderness + "-rem-out-trails." + out_ext
    outroads_devln_file = slug_wilderness + "-rem-out-devln." + out_ext
    outroads_devpl_file = slug_wilderness + "-rem-out-devpl." + out_ext
    outroads_devpt_file = slug_wilderness + "-rem-out-devpt." + out_ext

    icp = "tab:pink"
    ocp = "tab:cyan"

    inroads_style = ["tab:pink", "tab:pink", 0.5]
    outroads_style = ["tab:cyan", "tab:cyan", 0.5]
    road_style = ["tab:red", "tab:red", 1]
    devln_style = ["tab:gray", "tab:gray", 1]
    devpl_style = ["tab:gray", "tab:gray", 1]
    devpt_style = ["tab:gray", "tab:gray", 1, "", "o", 5]
    trail_style = ["tab:brown", "tab:brown", 1, "dotted"]

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    if os.path.exists(out_dir + inroads_file):
        inroads = geopandas.read_file(out_dir + inroads_file)
    else:
        inroads = geopandas.GeoDataFrame()
        inroads["geometry"] = None
        inroads["acres"] = inroads["geometry"].area / 4046.856
        inroads.crs = depsg
    if os.path.exists(out_dir + outroads_file):
        outroads = geopandas.read_file(out_dir + outroads_file)
    else:
        outroads = geopandas.GeoDataFrame()
        outroads["geometry"] = None
        outroads["acres"] = outroads["geometry"].area / 4046.856
        outroads.crs = depsg
    if os.path.exists(out_dir + inroads_devln_file):
        inroads_devln = geopandas.read_file(out_dir + inroads_devln_file)
    else:
        inroads_devln = geopandas.GeoDataFrame()
        inroads_devln["geometry"] = None
        inroads_devln.crs = depsg
    if os.path.exists(out_dir + outroads_devln_file):
        outroads_devln = geopandas.read_file(out_dir + outroads_devln_file)
    else:
        outroads_devln = geopandas.GeoDataFrame()
        outroads_devln["geometry"] = None
        outroads_devln.crs = depsg
    if os.path.exists(out_dir + inroads_devpt_file):
        inroads_devpt = geopandas.read_file(out_dir + inroads_devpt_file)
    else:
        inroads_devpt = geopandas.GeoDataFrame()
        inroads_devpt["geometry"] = None
        inroads_devpt.crs = depsg
    if os.path.exists(out_dir + outroads_devpt_file):
        outroads_devpt = geopandas.read_file(out_dir + outroads_devpt_file)
    else:
        outroads_devpt = geopandas.GeoDataFrame()
        outroads_devpt["geometry"] = None
        outroads_devpt.crs = depsg
    if os.path.exists(out_dir + inroads_devpl_file):
        inroads_devpl = geopandas.read_file(out_dir + inroads_devpl_file)
    else:
        inroads_devpl = geopandas.GeoDataFrame()
        inroads_devpl["geometry"] = None
        inroads_devpl.crs = depsg
    if os.path.exists(out_dir + outroads_devpl_file):
        outroads_devpl = geopandas.read_file(out_dir + outroads_devpl_file)
    else:
        outroads_devpl = geopandas.GeoDataFrame()
        outroads_devpl["geometry"] = None
        outroads_devpl.crs = depsg
    if os.path.exists(out_dir + inroads_roadcore_file):
        inroads_roadcore = geopandas.read_file(out_dir + inroads_roadcore_file)
    else:
        inroads_roadcore = geopandas.GeoDataFrame()
        inroads_roadcore["geometry"] = None
        inroads_roadcore.crs = depsg
    if os.path.exists(out_dir + outroads_roadcore_file):
        outroads_roadcore = geopandas.read_file(out_dir + outroads_roadcore_file)
    else:
        outroads_roadcore = geopandas.GeoDataFrame()
        outroads_roadcore["geometry"] = None
        outroads_roadcore.crs = depsg
    if os.path.exists(out_dir + outroads_trails_file):
        outroads_trails = geopandas.read_file(out_dir + outroads_trails_file)
    else:
        outroads_trails = geopandas.GeoDataFrame()
        outroads_trails["geometry"] = None
        outroads_trails.crs = depsg
    if os.path.exists(out_dir + inroads_trails_file):
        inroads_trails = geopandas.read_file(out_dir + inroads_trails_file)
    else:
        inroads_trails = geopandas.GeoDataFrame()
        inroads_trails["geometry"] = None
        inroads_trails.crs = depsg
    if os.path.exists(out_dir + inroads_empty_file) and os.path.exists(
        out_dir + outroads_empty_file
    ):
        inout = geopandas.GeoDataFrame()
        inout["geometry"] = None
        inout["acres"] = inout["geometry"].area / 4046.856
        inout.crs = depsg
    elif os.path.exists(out_dir + inroads_empty_file):
        inout = geopandas.GeoDataFrame()
        inout["geometry"] = None
        inout["acres"] = inout["geometry"].area / 4046.856
        inout.crs = depsg
    elif os.path.exists(out_dir + outroads_empty_file):
        inout = geopandas.GeoDataFrame()
        inout["geometry"] = None
        inout["acres"] = inout["geometry"].area / 4046.856
        inout.crs = depsg
    else:
        inout = geopandas.overlay(inroads, outroads, how="intersection")

    inout["acres"] = inout["geometry"].area / 4046.856
    w_ac = awilderness["acres"].sum()
    i_ac = inroads["acres"].sum()
    o_ac = outroads["acres"].sum()
    io_ac = inout["acres"].sum()
    i_pct = "{0:.0f}".format((i_ac / w_ac) * 100)
    o_pct = "{0:.0f}".format((o_ac / w_ac) * 100)
    io_pct = "{0:.0f}".format((io_ac / w_ac) * 100)
    w_ac = "{0:.2f}".format(w_ac)
    i_ac = "{0:.2f}".format(i_ac)
    o_ac = "{0:.2f}".format(o_ac)
    io_ac = "{0:.2f}".format(io_ac)

    jsd = [
        {
            "w_ac": w_ac,
            "i_ac": i_ac,
            "o_ac": o_ac,
            "io_ac": io_ac,
            "i_pct": i_pct,
            "o_pct": o_pct,
            "io_pct": io_pct,
        }
    ]
    jsc = "".join(str(v) for v in jsd).replace("'", '"')
    with uopen(out_dir + "index-inout.json", "w") as static_file:
        static_file.write(jsc)

    awilderness = awilderness.to_crs(epsg=4269)  # from cea
    inroads = inroads.to_crs(epsg=4269)  # from cea
    outroads = outroads.to_crs(epsg=4269)  # from cea

    width = 13

    ax = awilderness.plot(
        color="none",
        edgecolor="black",
        linewidth=2.0,
        alpha=0.9,
        figsize=(width, width / 1.618),
    )
    inroads.plot(
        aspect=1,
        ax=ax,
        color=inroads_style[0],
        edgecolor=inroads_style[1],
        alpha=inroads_style[2],
    )
    inroads_devln.plot(
        aspect=1,
        ax=ax,
        color=devln_style[0],
        edgecolor=devln_style[1],
        alpha=devln_style[2],
    )
    inroads_devpt.plot(
        aspect=1,
        ax=ax,
        color=devpt_style[0],
        edgecolor=devpt_style[1],
        alpha=devpt_style[2],
        marker=devpt_style[4],
        markersize=devpt_style[5],
    )
    inroads_devpl.plot(
        aspect=1,
        ax=ax,
        color=devpl_style[0],
        edgecolor=devpl_style[1],
        alpha=devpl_style[2],
    )
    inroads_roadcore.plot(
        aspect=1,
        ax=ax,
        color=road_style[0],
        edgecolor=road_style[1],
        alpha=road_style[2],
    )
    inroads_trails.plot(
        aspect=1,
        ax=ax,
        color=trail_style[0],
        edgecolor=trail_style[1],
        alpha=trail_style[2],
        linestyle=trail_style[3],
    )
    awilderness.plot(ax=ax, color="none", edgecolor="black", linewidth=2.0, alpha=0.9)
    xlim = [awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]]
    ylim = [awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]]
    pyplot.suptitle(
        "Acres of wilderness away from access and travel routes and developments inside "
        + which_wilderness[0]
        + " "
        + which_wilderness[1]
    )
    txt = (
        str(w_ac)
        + " wilderness acres"
        + "\n"
        + str(i_ac)
        + " inroads acres ("
        + str(i_pct)
        + "%)"
    )
    ax.annotate(
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
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    pyplot.axis("off")
    fig1 = pyplot.gcf()
    pyplot.subplots_adjust(top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0)
    pyplot.margins(0, 0)
    fig1.savefig(out_dir + slug_wilderness + "-rem-in-fin.png")

    awilderness_box = awilderness_1mi.copy()
    awilderness_box = awilderness_1mi.to_crs({"proj": "cea"})
    awilderness_box["geometry"] = awilderness_box.geometry.buffer(0.1609344)
    awilderness_box = awilderness_box.to_crs(awilderness_1mi.crs)
    xlim2 = [awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]]
    ylim2 = [awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]]
    ax.set_xlim(xlim2)
    ax.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, slug_agency, ax, awilderness.crs.to_string())
    awilderness.plot(ax=ax, color="none", edgecolor="black", linewidth=1.0, alpha=0.9)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    fig1.savefig(out_dir + slug_wilderness + "-rem-in-fin-base.png")
    fig1.clf()
    pyplot.clf()
    pyplot.cla()
    pyplot.close()

    ax = awilderness.plot(
        color="none",
        edgecolor="black",
        linewidth=2.0,
        alpha=0.9,
        figsize=(width, width / 1.618),
    )

    outroads.plot(
        aspect=1,
        ax=ax,
        color=outroads_style[0],
        edgecolor=outroads_style[1],
        alpha=outroads_style[2],
    )
    outroads_devln.plot(
        aspect=1,
        ax=ax,
        color=devln_style[0],
        edgecolor=devln_style[1],
        alpha=devln_style[2],
    )
    outroads_devpt.plot(
        aspect=1,
        ax=ax,
        color=devpt_style[0],
        edgecolor=devpt_style[1],
        alpha=devpt_style[2],
        marker=devpt_style[4],
        markersize=devpt_style[5],
    )
    outroads_devpl.plot(
        aspect=1,
        ax=ax,
        color=devpl_style[0],
        edgecolor=devpl_style[1],
        alpha=devpl_style[2],
    )
    outroads_roadcore.plot(
        aspect=1,
        ax=ax,
        color=road_style[0],
        edgecolor=road_style[1],
        alpha=road_style[2],
    )
    outroads_trails.plot(
        aspect=1,
        ax=ax,
        color=trail_style[0],
        edgecolor=trail_style[1],
        alpha=trail_style[2],
        linestyle=trail_style[3],
    )

    awilderness.plot(ax=ax, color="none", edgecolor="black", linewidth=2.0, alpha=0.9)
    xlim = [awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]]
    ylim = [awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]]
    pyplot.suptitle(
        "Acres of wilderness away from access and travel routes and developments outside "
        + which_wilderness[0]
        + " "
        + which_wilderness[1]
    )
    txt = (
        str(w_ac)
        + " wilderness acres"
        + "\n"
        + str(o_ac)
        + " outroads acres ("
        + str(o_pct)
        + "%)"
    )
    ax.annotate(
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
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    pyplot.axis("off")
    fig1 = pyplot.gcf()
    pyplot.subplots_adjust(top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0)
    pyplot.margins(0, 0)
    fig1.savefig(out_dir + slug_wilderness + "-rem-out-fin.png")

    awilderness_box = awilderness_1mi.copy()
    awilderness_box = awilderness_1mi.to_crs({"proj": "cea"})
    awilderness_box["geometry"] = awilderness_box.geometry.buffer(0.1609344)
    awilderness_box = awilderness_box.to_crs(awilderness_1mi.crs)
    xlim2 = [awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]]
    ylim2 = [awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]]
    ax.set_xlim(xlim2)
    ax.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, slug_agency, ax, awilderness.crs.to_string())
    awilderness.plot(ax=ax, color="none", edgecolor="black", linewidth=1.0, alpha=0.9)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    fig1.savefig(out_dir + slug_wilderness + "-rem-out-fin-base.png")
    fig1.clf()
    pyplot.clf()
    pyplot.cla()
    pyplot.close()

    ax = awilderness.plot(
        color="none",
        edgecolor="black",
        linewidth=2.0,
        alpha=0.9,
        figsize=(width, width / 1.618),
    )
    inroads.plot(
        aspect=1,
        ax=ax,
        color=inroads_style[0],
        edgecolor=inroads_style[1],
        alpha=inroads_style[2],
    )
    outroads.plot(
        aspect=1,
        ax=ax,
        color=outroads_style[0],
        edgecolor=outroads_style[1],
        alpha=outroads_style[2],
    )
    inroads_devln.plot(
        aspect=1,
        ax=ax,
        color=devln_style[0],
        edgecolor=devln_style[1],
        alpha=devln_style[2],
    )
    outroads_devln.plot(
        aspect=1,
        ax=ax,
        color=devln_style[0],
        edgecolor=devln_style[1],
        alpha=devln_style[2],
    )
    inroads_devpt.plot(
        aspect=1,
        ax=ax,
        color=devpt_style[0],
        edgecolor=devpt_style[1],
        alpha=devpt_style[2],
        marker=devpt_style[4],
        markersize=devpt_style[5],
    )
    outroads_devpt.plot(
        aspect=1,
        ax=ax,
        color=devpt_style[0],
        edgecolor=devpt_style[1],
        alpha=devpt_style[2],
        marker=devpt_style[4],
        markersize=devpt_style[5],
    )
    inroads_devpl.plot(
        aspect=1,
        ax=ax,
        color=devpl_style[0],
        edgecolor=devpl_style[1],
        alpha=devpl_style[2],
    )
    outroads_devpl.plot(
        aspect=1,
        ax=ax,
        color=devpl_style[0],
        edgecolor=devpl_style[1],
        alpha=devpl_style[2],
    )
    inroads_roadcore.plot(
        aspect=1,
        ax=ax,
        color=road_style[0],
        edgecolor=road_style[1],
        alpha=road_style[2],
    )
    outroads_roadcore.plot(
        aspect=1,
        ax=ax,
        color=road_style[0],
        edgecolor=road_style[1],
        alpha=road_style[2],
    )
    inroads_trails.plot(
        aspect=1,
        ax=ax,
        color=trail_style[0],
        edgecolor=trail_style[1],
        alpha=trail_style[2],
        linestyle=trail_style[3],
    )
    outroads_trails.plot(
        aspect=1,
        ax=ax,
        color=trail_style[0],
        edgecolor=trail_style[1],
        alpha=trail_style[2],
        linestyle=trail_style[3],
    )
    awilderness.plot(ax=ax, color="none", edgecolor="black", linewidth=2.0, alpha=0.9)
    xlim = [awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]]
    ylim = [awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]]
    pyplot.suptitle(
        "Acres of wilderness away from access and travel routes and developments in and around "
        + which_wilderness[0]
        + " "
        + which_wilderness[1]
    )
    txt = (
        str(w_ac)
        + " wilderness acres"
        + "\n"
        + str(i_ac)
        + " inroads acres ("
        + str(i_pct)
        + "%)"
        + "\n"
        + str(o_ac)
        + " outroads acres ("
        + str(o_pct)
        + "%)\n"
        + str(io_ac)
        + " remote acres ("
        + str(io_pct)
        + "%)"
    )
    ax.annotate(
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
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    pyplot.axis("off")
    fig1 = pyplot.gcf()
    pyplot.subplots_adjust(top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0)
    pyplot.margins(0, 0)
    fig1.savefig(out_dir + slug_wilderness + "-rem-all-fin.png")

    awilderness_box = awilderness_1mi.copy()
    awilderness_box = awilderness_1mi.to_crs({"proj": "cea"})
    awilderness_box["geometry"] = awilderness_box.geometry.buffer(0.1609344)
    awilderness_box = awilderness_box.to_crs(awilderness_1mi.crs)
    xlim2 = [awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]]
    ylim2 = [awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]]
    ax.set_xlim(xlim2)
    ax.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, slug_agency, ax, awilderness.crs.to_string())
    awilderness.plot(ax=ax, color="none", edgecolor="black", linewidth=1.0, alpha=0.9)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    fig1.savefig(out_dir + slug_wilderness + "-rem-all-fin-base.png")
    fig1.clf()
    pyplot.clf()
    pyplot.cla()
    pyplot.close()

    width = 27
    ax = awilderness.plot(
        color="none",
        edgecolor="black",
        linewidth=2.0,
        alpha=0.9,
        figsize=(width, width / 1.618),
    )
    inroads.plot(
        aspect=1,
        ax=ax,
        color=inroads_style[0],
        edgecolor=inroads_style[1],
        alpha=inroads_style[2],
    )
    outroads.plot(
        aspect=1,
        ax=ax,
        color=outroads_style[0],
        edgecolor=outroads_style[1],
        alpha=outroads_style[2],
    )
    inroads_devln.plot(
        aspect=1,
        ax=ax,
        color=devln_style[0],
        edgecolor=devln_style[1],
        alpha=devln_style[2],
    )
    outroads_devln.plot(
        aspect=1,
        ax=ax,
        color=devln_style[0],
        edgecolor=devln_style[1],
        alpha=devln_style[2],
    )
    inroads_devpt.plot(
        aspect=1,
        ax=ax,
        color=devpt_style[0],
        edgecolor=devpt_style[1],
        alpha=devpt_style[2],
        marker=devpt_style[4],
        markersize=devpt_style[5],
    )
    outroads_devpt.plot(
        aspect=1,
        ax=ax,
        color=devpt_style[0],
        edgecolor=devpt_style[1],
        alpha=devpt_style[2],
        marker=devpt_style[4],
        markersize=devpt_style[5],
    )
    inroads_devpl.plot(
        aspect=1,
        ax=ax,
        color=devpl_style[0],
        edgecolor=devpl_style[1],
        alpha=devpl_style[2],
    )
    outroads_devpl.plot(
        aspect=1,
        ax=ax,
        color=devpl_style[0],
        edgecolor=devpl_style[1],
        alpha=devpl_style[2],
    )
    inroads_roadcore.plot(
        aspect=1,
        ax=ax,
        color=road_style[0],
        edgecolor=road_style[1],
        alpha=road_style[2],
    )
    outroads_roadcore.plot(
        aspect=1,
        ax=ax,
        color=road_style[0],
        edgecolor=road_style[1],
        alpha=road_style[2],
    )
    inroads_trails.plot(
        aspect=1,
        ax=ax,
        color=trail_style[0],
        edgecolor=trail_style[1],
        alpha=trail_style[2],
        linestyle=trail_style[3],
    )
    outroads_trails.plot(
        aspect=1,
        ax=ax,
        color=trail_style[0],
        edgecolor=trail_style[1],
        alpha=trail_style[2],
        linestyle=trail_style[3],
    )
    awilderness.plot(ax=ax, color="none", edgecolor="black", linewidth=2.0, alpha=0.9)
    xlim = [awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]]
    ylim = [awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]]
    pyplot.suptitle(
        "Acres of wilderness away from access and travel routes and developments in and around "
        + which_wilderness[0]
        + " "
        + which_wilderness[1],
        fontsize=20,
    )
    txt = (
        str(w_ac)
        + " wilderness acres"
        + "\n"
        + str(i_ac)
        + " inroads acres ("
        + str(i_pct)
        + "%)"
        + "\n"
        + str(o_ac)
        + " outroads acres ("
        + str(o_pct)
        + "%)\n"
        + str(io_ac)
        + " remote acres ("
        + str(io_pct)
        + "%)"
    )
    ax.annotate(
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
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    pyplot.axis("off")
    fig1 = pyplot.gcf()
    pyplot.subplots_adjust(top=0.95, bottom=0, right=1, left=0, hspace=0, wspace=0)
    pyplot.margins(0, 0)
    fig1.savefig(
        out_dir + slug_wilderness + "-rem-all-fin-" + str(width) + "in" + ".png"
    )

    tdep_national_file = out_dir + "ntdep-cut-stack.shp"
    tdep_national = geopandas.read_file(tdep_national_file)
    tdep_national.crs = ras_epsg
    # tdep_national = tdep_national.to_crs({'proj':'cea'})
    extent_df = tdep_national
    xd = abs(extent_df.total_bounds[0] - extent_df.total_bounds[2])
    yd = abs(extent_df.total_bounds[1] - extent_df.total_bounds[3])
    width = xd / 3320
    hidth = yd / 3320
    if width <= hidth * 1.1:
        width = hidth * 1.1
    # print(width)
    # print(hidth)
    fig1.set_size_inches(width, hidth)
    # xlim = ([extent_df.total_bounds[0], extent_df.total_bounds[2]])
    # ylim = ([extent_df.total_bounds[1], extent_df.total_bounds[3]])
    # ax.set_xlim(xlim)
    # ax.set_ylim(ylim)
    # pyplot.show()
    # quit()
    fig1.savefig(out_dir + slug_wilderness + "-rem-all-fin-" + "scaled" + ".png")
    # quit()

    awilderness_box = awilderness_1mi.copy()
    awilderness_box = awilderness_1mi.to_crs({"proj": "cea"})
    awilderness_box["geometry"] = awilderness_box.geometry.buffer(0.1609344)
    awilderness_box = awilderness_box.to_crs(awilderness_1mi.crs)
    xlim2 = [awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]]
    ylim2 = [awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]]
    ax.set_xlim(xlim2)
    ax.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, slug_agency, ax, awilderness.crs.to_string())
    awilderness.plot(ax=ax, color="none", edgecolor="black", linewidth=1.0, alpha=0.9)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    fig1.savefig(out_dir + slug_wilderness + "-rem-all-fin-" + "scaled-base" + ".png")
    fig1.clf()
    pyplot.clf()
    pyplot.cla()
    pyplot.close()
    # quit()
