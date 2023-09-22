""" Wilderness Character Monitoring Measures.
"""

import django.conf
from django.utils.text import slugify
import geopandas

import extra
import lichen
import nonrec
import ozone
import remoteness
import tdep
import visibility
import water
import web
import wetdep
import wilderness
from utils import *

django.conf.settings.configure(
    DEBUG=False,
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": template_folder,
            "APP_DIRS": False,
        },
    ],
)
django.setup()
colorama.init(autoreset=True)


def main():
    new_data = []
    req_list = []
    wilderness_list = []
    wilderness_maps_list = []
    wetdep_list = []
    tdep_list = []
    vis_list = []
    ozone_list = []
    lichen_list = []
    wcc_list = []
    waters_list = []
    remoteness_list = []
    remoteness_plot_list = []
    nonrec_list = []
    static_list = []
    fire_list = []
    wsr_list = []

    log(None, None, "GREEN", "let's go let's go")

    new_data = 0
    if new_data:
        web.pull_edw_links()
        web.pull_edw_local()
        web.pull_edw_data()
        remoteness.devx_join()
        # ozone.ozone_trends()
        # tdep.tdep_stack('n')
        # tdep.tdep_stack('s')
        quit()

    req_list = []
    req_list.append(["2023-09-19", "FS", "Cabinet Mountains", ""])
    req_list.append(["2023-09-19", "FS", "Mission Mountains", ""])
    req_list.append(["2023-09-19", "FS", "Gates of the Mountains", " "])

    do_nwps = ""  # 'BLM' # 'NPS' 'FS' 'FWS'
    if do_nwps:
        req_list = []
        wilderness_shp = cache_dir + "nwps_fs.json"
        wilderness_df = geopandas.read_file(wilderness_shp)
        wilderness_df = wilderness_df.drop(columns="state")
        agency_wilderness = wilderness_df[(wilderness_df["a"] == do_nwps)]
        agency_wilderness = agency_wilderness.sort_values(by=["name"])
        log(None, None, "CYAN", "every " + do_nwps + " wilderness, ok!")
        cut = "A"
        cut2 = "Dz"
        if do_nwps == "FS":
            skip = []
            skip.append("Devils Staircase")  # bad boundary
        elif do_nwps == "NPS":
            skip = []
            skip.append("Gulf Islands")  # no water
            skip.append("Marjory Stoneman Douglas")  # no water
        elif do_nwps == "FWS":
            skip = []
            skip.append("Oregon Islands")  # no water
            skip.append("Seney")  # no water
            skip.append("Swanquarter")  # no water
        elif do_nwps == "BLM":
            skip = []
            skip.append("Big Maria Mountains")  # no water
            skip.append("Chuckwalla Mountains")  # no water
            skip.append("Devils Staircase")  # no water
            skip.append("Riverside Mountains")  # no water
            skip.append("Soda Mountains")  # no water
        for i, row in agency_wilderness.iterrows():
            if row["name"] >= cut and row["name"] <= cut2:
                if row["name"] in skip:
                    log(None, None, "CYAN", row["name"] + " skipped")
                else:
                    req_list.append(["2023-08-30", row["a"], row["name"], "je"])
        log(
            None,
            None,
            "CYAN",
            "from " + req_list[0][2] + " to " + req_list[-1][2] + ", ok!",
        )

    lint = ""
    if lint:
        run_pylint("wilderness")
        run_pylint("tdep")
        run_pylint("wetdep")
        run_pylint("ozone")
        run_pylint("visibility")
        run_pylint("remoteness")
        run_pylint("water")
        run_pylint("lichen")
        run_pylint("web")
        run_pylint("utils")
        run_pylint("settings")
        run_pylint("settings_lists")
        print("lint collected")
        quit()

    go = ""
    if go:
        for which_wilderness in req_list:
            wilderness.awilderness_boundary_nwps(which_wilderness)
            wilderness.awilderness_buffers_nwps(which_wilderness)
        wilderness.wilderness_maps_nwps(req_list)
        water.watershed_conditions_nwps(req_list)
        # stack tdeps with rio.exe
        for which_wilderness in req_list:
            # wilderness.awilderness_station_buffers(which_wilderness, ['LIGO1', 'JARI1'])
            tdep.tdep2_awilderness_nwps(which_wilderness, "n")
            tdep.tdep_awilderness_graphs_nwps(which_wilderness, "n")
            tdep.tdep_wilderness_maps_nwps(which_wilderness, "n")
            tdep.tdep_do_nwps(which_wilderness, "n")
            tdep.tdep2_awilderness_nwps(which_wilderness, "s")
            tdep.tdep_awilderness_graphs_nwps(which_wilderness, "s")
            tdep.tdep_wilderness_maps_nwps(which_wilderness, "s")
            tdep.tdep_do_nwps(which_wilderness, "s")
        for which_wilderness in req_list:
            ozone.ozone_nwps(which_wilderness)
            ozone.ozone_trendplots_multi_nwps(which_wilderness, "")
        for which_wilderness in req_list:
            visibility.visibility_nwps(which_wilderness)
        for which_wilderness in req_list:
            wetdep.wetdep_nwps(which_wilderness, "n")
            wetdep.wetdep_nwps(which_wilderness, "s")

        remoteness.devx_clip_nwps(req_list, "devpt")
        remoteness.devx_clip_nwps(req_list, "devln")
        remoteness.devx_clip_nwps(req_list, "roadcore2")
        remoteness.devx_clip_nwps(req_list, "trails")
        remoteness.devx_clip_nwps(req_list, "devpl")
        for which_wilderness in req_list:
            remoteness.devx_to_awilderness_nwps(which_wilderness, "devln", "in")
            remoteness.devx_to_awilderness_nwps(which_wilderness, "devln", "out")
            remoteness.devx_to_awilderness_buffer_erase_nwps(
                which_wilderness, "devln", "in"
            )
            remoteness.devx_to_awilderness_buffer_erase_nwps(
                which_wilderness, "devln", "out"
            )

            remoteness.devx_to_awilderness_nwps(which_wilderness, "roadcore2", "in")
            remoteness.devx_to_awilderness_nwps(which_wilderness, "roadcore2", "out")
            remoteness.devx_to_awilderness_buffer_erase_nwps(
                which_wilderness, "roadcore2", "in"
            )
            remoteness.devx_to_awilderness_buffer_erase_nwps(
                which_wilderness, "roadcore2", "out"
            )

            remoteness.devx_to_awilderness_nwps(which_wilderness, "trails", "in")
            remoteness.devx_to_awilderness_nwps(which_wilderness, "trails", "out")
            remoteness.devx_to_awilderness_buffer_erase_nwps(
                which_wilderness, "trails", "in"
            )
            remoteness.devx_to_awilderness_buffer_erase_nwps(
                which_wilderness, "trails", "out"
            )

            remoteness.devx_to_awilderness_nwps(which_wilderness, "devpt", "in")
            remoteness.devx_to_awilderness_nwps(which_wilderness, "devpt", "out")
            remoteness.devx_to_awilderness_buffer_erase_nwps(
                which_wilderness, "devpt", "in"
            )
            remoteness.devx_to_awilderness_buffer_erase_nwps(
                which_wilderness, "devpt", "out"
            )

            remoteness.devx_to_awilderness_nwps(which_wilderness, "devpl", "in")
            remoteness.devx_to_awilderness_nwps(which_wilderness, "devpl", "out")
            remoteness.devx_to_awilderness_buffer_erase_nwps(
                which_wilderness, "devpl", "in"
            )
            remoteness.devx_to_awilderness_buffer_erase_nwps(
                which_wilderness, "devpl", "out"
            )

            remoteness.remoteness_nwps(which_wilderness, "in")
            remoteness.remoteness_nwps(which_wilderness, "out")
            remoteness.remoteness_plots(which_wilderness)

        for which_wilderness in req_list:
            water.attains_geoms_to_local_nwps(req_list, "2022-11-15")
            water.attains_cycles_to_csv_nwps(req_list, "2022-11-15")
            water.attains_cycles_to_local_nwps(req_list, 1998, 2022, "2022-11-15")
            water.collect_jsons_nwps(req_list, 1998, 2022, "2022-11-15")
            water.local_cycles_to_tidy_nwps(req_list, 1998, 2022, "2022-11-15")

        water.attains_waters_nwps(req_list, "2022-11-15")  # todo get lastest <= request

        for which_wilderness in req_list:
            web.collect_downloads_nwps(which_wilderness)
            web.build_wcm_baseline_nwps(which_wilderness)

        for which_wilderness in static_list:
            slug_wilderness = slugify(which_wilderness)
            print("/togo/" + slug_wilderness)


if __name__ == "__main__":
    main()
    # try:
    #    main()
    # except Exception as e:
    #    logger.exception("main crashed. Error: %s", e)
