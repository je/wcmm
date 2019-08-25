# c:\bin\python37-64\python C:\_\wcmm\wcmm.py

from datetime import datetime
import os

import django

from settings import *
from settings_lists import *
from utils import *

import lichen
import ozone
import remoteness
import tdep
import visibility
import water
import web
import wilderness

def main():
    gdb_shp_multi(wilderness_gdb, 'Wilderness', wilderness_file, 'wkbMultiPolygon')
    wilderness.wilderness_year_designated()
    wilderness.wilderness_write_fixture()
    gdb_shp_multi(roadcore_gdb, 'usa_roadcore_201904', roadcore2_file, 'wkbMultiLineString')
    #gdb_shp_multi(dev_pl_gdb, 'dev_pl_merge', devpl2_file, 'wkbMultiPolygon') # TODO: remove after devpl tests correct
    tdep.tdep_stack('n')
    tdep.tdep_stack('s')
    #ozone.ozone_trends()
    #extra.wilderness_dams()
    #web.build_index()

    #returned_list = test_wilderness_list()
    #returned_list = pilot_wilderness_list()
    #returned_list = y2019_short_wilderness_list()
    #returned_list = y2019_wilderness_list()
    #returned_list = other_wilderness_list()
    #returned_list = alaska_wilderness_list()
    #returned_list = all_wilderness_list()

    #returned_list = ['Absaroka-Beartooth Wilderness']
    returned_list = ['Absaroka-Beartooth Wilderness', 'Agua Tibia Wilderness']
    #returned_list = ['Absaroka-Beartooth Wilderness','Anaconda Pintler Wilderness','Agua Tibia Wilderness','Cabinet Mountains Wilderness','Mount Sneffels Wilderness']
    #returned_list = ['Anaconda Pintler Wilderness']
    #returned_list = ['Bald Mountain Wilderness']
    #returned_list = ['Cabinet Mountains Wilderness']
    #returned_list = ['Cloud Peak Wilderness']
    #returned_list = ['Frank Church-River of No Return Wilderness', 'Winegar Hole Wilderness']
    #returned_list = ['Frank Church-River of No Return Wilderness', 'Petersburg Creek-Duncan Salt Chuck Wilderness', 'Stikine-LeConte Wilderness']
    #returned_list = ['Linville Gorge Wilderness']
    #returned_list = ['Raggeds Wilderness']
    #returned_list = ['Sanhedrin Wilderness']
    #returned_list = ['South Fork San Jacinto Wilderness', 'Cahuilla Mountain Wilderness']
    #returned_list = ['Spanish Peaks Wilderness']
    #returned_list = ['White Mountain Wilderness','Winegar Hole Wilderness','Whisker Lake Wilderness']

    for which_wilderness in returned_list:
        slug_wilderness = django.utils.text.slugify(which_wilderness)
        out_dir = base_dir + slug_wilderness + '\\'
        print(out_dir)
        if os.path.exists(out_dir):
            log(slug_wilderness, 'CYAN', str(datetime.now().strftime('%Y%m%d_%H%M')) + ' ' + slug_wilderness + ' data folder already exists')

            wilderness.awilderness_boundary(which_wilderness)
            wilderness.awilderness_buffers(which_wilderness)
            #water.impaired_waters(which_wilderness)
            #water.impaired_waters_plots(which_wilderness)
            #extra.ownermaps(which_wilderness)
            #water.impaired_waters_plots(which_wilderness)
            #remoteness.remoteness(which_wilderness, 'in')
            #remoteness.remoteness_plots(which_wilderness)
            #tdep.tdep_wilderness(which_wilderness, 'n')
            #tdep.tdep_wilderness_plots(which_wilderness, 'n')
            #tdep.tdep_wilderness(which_wilderness, 's')
            #tdep.tdep_wilderness_plots(which_wilderness, 's')
            #visibility.visibility(which_wilderness)
            #water.watershed_condition(which_wilderness)
            #extra.grazing_allotments(which_wilderness)
            #lichen.lichen(which_wilderness)
            #ozone.ozone(which_wilderness)
        else:
            wilderness.awilderness_boundary(which_wilderness)
            wilderness.awilderness_buffers(which_wilderness)

            #ozone.ozone(which_wilderness)
            #quit()
            lichen.lichen(which_wilderness)
            #quit()

            remoteness.devx_to_awilderness_1mi(which_wilderness, 'roadcore2')
            remoteness.devx_to_awilderness(which_wilderness, 'roadcore2', 'in')
            remoteness.devx_to_awilderness(which_wilderness, 'roadcore2', 'out')
            remoteness.devx_to_awilderness_buffer_erase(which_wilderness, 'roadcore2', 'in')
            remoteness.devx_to_awilderness_buffer_erase(which_wilderness, 'roadcore2', 'out')

            remoteness.devx_to_awilderness_1mi(which_wilderness, 'devln')
            remoteness.devx_to_awilderness(which_wilderness, 'devln', 'in')
            remoteness.devx_to_awilderness(which_wilderness, 'devln', 'out')
            remoteness.devx_to_awilderness_buffer_erase(which_wilderness, 'devln', 'in')
            remoteness.devx_to_awilderness_buffer_erase(which_wilderness, 'devln', 'out')

            remoteness.devx_to_awilderness_1mi(which_wilderness, 'devpt')
            remoteness.devx_to_awilderness(which_wilderness, 'devpt', 'in')
            remoteness.devx_to_awilderness(which_wilderness, 'devpt', 'out')
            remoteness.devx_to_awilderness_buffer_erase(which_wilderness, 'devpt', 'in')
            remoteness.devx_to_awilderness_buffer_erase(which_wilderness, 'devpt', 'out')

            remoteness.devx_to_awilderness_1mi(which_wilderness, 'devpl')
            remoteness.devx_to_awilderness(which_wilderness, 'devpl', 'in')
            remoteness.devx_to_awilderness(which_wilderness, 'devpl', 'out')
            remoteness.devx_to_awilderness_buffer_erase(which_wilderness, 'devpl', 'in')
            remoteness.devx_to_awilderness_buffer_erase(which_wilderness, 'devpl', 'out')

            remoteness.remoteness(which_wilderness, 'in')
            remoteness.remoteness(which_wilderness, 'out')
            remoteness.remoteness_plots(which_wilderness)

            visibility.visibility(which_wilderness)

            tdep.tdep_wilderness(which_wilderness, 'n')
            tdep.tdep_wilderness_plots(which_wilderness, 'n')
            tdep.tdep_wilderness(which_wilderness, 's')
            tdep.tdep_wilderness_plots(which_wilderness, 's')

            water.watershed_condition(which_wilderness)

            water.impaired_waters(which_wilderness)
            water.impaired_waters_plots(which_wilderness)

        out_dir = static_dir + 'wcm\\' + slug_wilderness + '\\'
        if os.path.exists(out_dir):
            log(slug_wilderness, 'CYAN', str(datetime.now().strftime('%Y%m%d_%H%M')) + ' ' + slug_wilderness + ' static folder already exists')
            web.shps_to_geojsons_to_topojsons(which_wilderness)
            web.b_shps_to_geojsons_to_topojsons(which_wilderness)
            web.collect_downloads(which_wilderness)
            web.build_wcm(which_wilderness)
        else:
            web.shps_to_geojsons_to_topojsons(which_wilderness)
            web.b_shps_to_geojsons_to_topojsons(which_wilderness)
            web.collect_downloads(which_wilderness)
            web.build_wcm(which_wilderness)

if __name__ == '__main__':
    main()
