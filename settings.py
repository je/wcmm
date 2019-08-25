admin_email: 'je@example.com'

wilderness_gdb = 'C:\\_\\cda_data_nat-2019\\S_USA.Wilderness.gdb'
in_xls = 'C:\\_\\cda_data_nat-2019\\NWPS.xls'
wilderness_tsv = 'C:\\_\\cda_data_nat-2019\\wilderness_designated.tsv'
wcc_gdb = 'C:\\_\\cda_data_nat-2019\\S_USA.WatershedConditionClass.gdb'
grazing_gdb = 'C:\\_\\cda_data_nat-2019\\S_USA.Allotment.gdb'
epa303d_gdb = 'C:\\_\\cda_data_nat-2019\\rad_303d_20150501.gdb'
epa305b_gdb = 'C:\\_\\cda_data_nat-2019\\rad_assd305b_20150618.gdb'
roadcore_gdb = 'C:\\_\\cda_workspace\\exports.gdb'
dev_ln_gdb = 'C:\\_\\cda_workspace\\exports.gdb'
dev_pl_gdb = 'C:\\_\\cda_workspace\\exports.gdb'
dev_pt_gdb = 'C:\\_\\cda_workspace\\exports.gdb'
ntdep_dir = 'C:\\_\\cda_data_nat-2019\\tdep_n\\'
stdep_dir = 'C:\\_\\cda_data_nat-2019\\tdep_s\\'
vis_stations = 'C:\\_\\cda_data_nat-2019\\fs_wild_wk draft 10_2018.XLS'
vis_data = 'C:\\_\\cda_data_nat-2019\\RHR3_Five_year_avg_all_end_years_07_19_group_90.csv'
blm_gdb = 'C:\\_\\cda_data_nat\\BLM_National_Surface_Management_Agency\\sma_wm.gdb'
usfs_af_gdb = 'C:\\_\\cda_data_nat\\S_USA.AdministrativeForest.gdb'
usfs_rd_gdb = 'C:\\_\\cda_data_nat\\S_USA.RangerDistrict.gdb'
usfs_ng_gdb = 'C:\\_\\cda_data_nat\\S_USA.NationalGrassland.gdb'
usfs_nfs_gdb = 'C:\\_\\cda_data_nat\\S_USA.NFSLandUnit.gdb'
lichen_xls = 'C:\\_\\cda_data_nat-2019\\lichen\\Wilderness N deposition.xlsx'

out_ext = 'shp' # 'shp' or 'geojson' # TODO: benchmark write formats
out_driver = 'ESRI Shapefile' # 'ESRI Shapefile' or 'GeoJSON'
base_dir = 'C:\\_\\wcmm\\output\\'
static_dir = 'C:\\_\\wcmm\\output_static\\'
template_folder = ['c:\\_\\wcmm\\templates\\']

devpl2_file = 'devpl_201904.shp'
roadcore2_file = 'usa_roadcore_201904.shp'
wilderness_file = 'wilderness.shp'
wilderness_csv = base_dir + 'wilderness.csv'
wilderness_fixture = base_dir + 'wilderness.json'
wilderness_geojson = static_dir + '\\wilderness\\' + 'data.json'
wilderness_topojson = static_dir + '\\wilderness\\' + 'data.json.packed'

depsg = '+proj=eqdc +lat_0=39 +lon_0=-96 +lat_1=33 +lat_2=45 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
ras_epsg = {'proj': 'aea', 'lat_1': 29.5, 'lat_2': 45.5, 'lat_0': 23, 'lon_0': -96, 'x_0': 0, 'y_0': 0, 'datum': 'WGS84', 'units': 'm', 'no_defs': True}

mono = {'family' : 'monospace'}
float_formatter = lambda x: '%.2f' % x
p_formatter = lambda x: '%.8f' % x
year_formatter = lambda x: '%4.0f' % x
