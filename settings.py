""" Settings; paths, projections, formats mostly. """

import contextily

server = True
if server:
    slash = "/"
    data_dir = "/Volumes/PATRIOT/cda_data/"
    template_folder = ["/Volumes/PATRIOT/wcmm/templates/"]
    base_dir = "/Volumes/PATRIOT/cda_output/"
    cache_dir = "/Volumes/PATRIOT/cda_output/_basic/"
    static_dir = "/Volumes/PATRIOT/cda_output/_static/"
    web_dir = "/Volumes/PATRIOT/ordvac/webapps/wilderness_ordvac_wcm/"
    contextily.tile.memory.store_backend.location = (
        "/Volumes/PATRIOT/cda_output//_context_cache"
    )
    water_dir = "/Volumes/PATRIOT/cda_data/_waters/"
    data_other = "/Volumes/PATRIOT/data_other/"
else:
    slash = "\\"
    data_dir = "d:\\cda_data\\"
    template_folder = ["d:\\wcmm\\templates\\"]
    base_dir = "d:\\cda_output\\"
    cache_dir = "d:\\cda_output\\_basic\\"
    static_dir = "d:\\cda_output\\_static\\"
    web_dir = "d:\\ordvac\\webapps\\wilderness_ordvac_wcm\\"
    contextily.tile.memory.store_backend.location = "d:\\cda_output\\_context_cache"
    water_dir = "d:\\cda_data\\_waters\\"
    data_other = "C:\\_\\data_other\\"

out_ext = "shp"  # 'shp' or 'geojson' # TODO: benchmark write formats
out_driver = "ESRI Shapefile"  # 'ESRI Shapefile' or 'GeoJSON'

depsg = "+proj=eqdc +lat_0=39 +lon_0=-96 +lat_1=33 +lat_2=45 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
ras_epsg = {
    "proj": "aea",
    "lat_1": 29.5,
    "lat_2": 45.5,
    "lat_0": 23,
    "lon_0": -96,
    "x_0": 0,
    "y_0": 0,
    "datum": "WGS84",
    "units": "m",
    "no_defs": True,
}
mono = {"family": "monospace"}
float_formatter = lambda x: "%.4f" % x
p_formatter = lambda x: "%.8f" % x
year_formatter = lambda x: "%4.0f" % x
