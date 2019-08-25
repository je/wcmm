import os
from datetime import datetime

import django
import django.conf
import colorama
import contextily
import matplotlib
import numpy
import scipy
import shapely.geometry
from osgeo import osr, ogr
from sklearn import linear_model

from settings import *

django.conf.settings.configure(
    DEBUG=False,
    TEMPLATES=[
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': template_folder,
            'APP_DIRS': False,
        },
    ])
django.setup()
colorama.init(autoreset=True)

def log(slug_wilderness, color, txt):
    with open(base_dir + slug_wilderness + '\\' + slug_wilderness + '.txt', 'a') as logfile:
        logfile.write(str(datetime.now().strftime('%Y%m%d_%H%M')) + ' ' + txt + '\n')
    if color == 'GREEN':
        print(colorama.Fore.GREEN + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + txt)
    if color == 'CYAN':
        print(colorama.Fore.CYAN + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + txt)
    if color == 'RED':
        print(colorama.Fore.RED + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + txt)
    if color == 'WHITE':
        print(colorama.Fore.WHITE + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + txt)

def lines_poly(shp, clip_obj):
    poly = clip_obj.geometry.unary_union
    spatial_index = shp.sindex
    bbox = poly.bounds
    sidx = list(spatial_index.intersection(bbox))
    shp_sub = shp.iloc[sidx]
    clipped = shp_sub.copy()
    clipped['geometry'] = shp_sub.intersection(poly)
    final_clipped = clipped[clipped.geometry.notnull()]
    return final_clipped

def gdb_shp_multi(agdb, alayer, afile, geom): # TODO: broken, maybe deprec
    ashp = base_dir + afile
    gdbdriver = ogr.GetDriverByName('OpenFileGDB')
    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(ashp):
        print(colorama.Fore.CYAN + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + afile + ' already exists')
    else:
        gdb = ogr.Open(agdb)
        lyr = gdb.GetLayer(alayer)
        in_spatial_ref = lyr.GetSpatialRef()
        out_spatial_ref = osr.SpatialReference()
        out_spatial_ref.ImportFromEPSG(4326)
        coord_trans = osr.CoordinateTransformation(in_spatial_ref, out_spatial_ref)
        in_dataset = gdbdriver.Open(agdb, 0)
        in_layer = in_dataset.GetLayer(alayer)
        if os.path.exists(ashp):
            shpdriver.DeleteDataSource(ashp)
        out_dataset = shpdriver.CreateDataSource(ashp)
        if geom == 'wkbMultiLineString':
            out_layer = out_dataset.CreateLayer('r', geom_type=ogr.wkbMultiLineString)
        elif geom == 'wkbMultiPolygon':
            out_layer = out_dataset.CreateLayer('r', geom_type=ogr.wkbMultiPolygon)
        in_layer_def = in_layer.GetLayerDefn()
        for i in range(0, in_layer_def.GetFieldCount()):
            field_def = in_layer_def.GetFieldDefn(i)
            out_layer.CreateField(field_def)
        out_layer_def = out_layer.GetLayerDefn()
        in_feature = in_layer.GetNextFeature()
        while in_feature:
            geom = in_feature.GetGeometryRef()
            if geom is not None:
                geom.Transform(coord_trans)
                out_feature = ogr.Feature(out_layer_def)
                out_feature.SetGeometry(geom)
                for i in range(0, out_layer_def.GetFieldCount()):
                    out_feature.SetField(out_layer_def.GetFieldDefn(i).GetNameRef(), in_feature.GetField(i))
                out_layer.CreateFeature(out_feature)
                out_feature = None
            in_feature = in_layer.GetNextFeature()
        print(colorama.Fore.GREEN + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + afile + ' created from gdb')

def trend(x_list, y_list, cca):
    x_split = x_list.split()
    x_split = x_split[::-1]
    y_split = y_list.split()
    y_split = y_split[::-1]
    x_vals = [int(value) for value in x_split]
    y_vals = [float(value) for value in y_split]
    endy = y_vals[-1]

    xmin = min(x_vals)
    xmax = max(x_vals)
    x_array = numpy.array(x_vals)
    big_x = x_array[:, numpy.newaxis]

    y_array = numpy.array(y_vals)
    big_y = y_array[:, numpy.newaxis]

    matplotlib.pyplot.scatter(x_vals, y_vals, color=cca[1], marker='x', s=40)
    line_x = numpy.array([xmin, xmax])

    lm = linear_model.TheilSenRegressor()
    lm.fit(big_x, big_y.ravel())
    params = numpy.append(lm.intercept_, lm.coef_)
    predictions = lm.predict(big_x)

    y_pred = lm.predict(line_x.reshape(2, 1))

    newX = numpy.append(numpy.ones((len(big_x), 1)), big_x, axis=1)
    MSE = (sum((big_y.ravel()-predictions)**2))/(len(newX)-len(newX[0]))

    var_b = MSE*(numpy.linalg.inv(numpy.dot(newX.T, newX)).diagonal())
    sd_b = numpy.sqrt(var_b)
    ts_b = params/sd_b
    p_values = [2*(1-scipy.stats.t.cdf(numpy.abs(i), (len(newX)-1))) for i in ts_b]
    sd_b = numpy.round(sd_b, 3)
    ts_b = numpy.round(ts_b, 3)
    p_values = numpy.round(p_values, 20)
    params = numpy.round(params, 4)

    p_value = p_values[1]

    years = []
    for row in x_vals:
        years.append(row)
    y_theil = []
    m = (y_pred[1]-y_pred[0])/(xmax-xmin)
    b = y_pred[0] - (m*xmin)
    for row in x_vals:
        y_theil.append(m*row+b)
    cols = numpy.column_stack([years, y_vals])
    cols = numpy.column_stack([cols, y_theil])
    matplotlib.pyplot.plot(line_x, y_pred, color=cca[0], alpha=cca[2], linewidth=2, label=None)

    ymax = max(y_vals)
    pmax = max(y_pred)
    plotmax = max([pmax, ymax])
    matplotlib.pyplot.ylim(0, plotmax)

    width = 13
    matplotlib.pyplot.axis('tight')
    matplotlib.pyplot.xticks(x_vals)
    fig2 = matplotlib.pyplot.gcf()
    fig2.set_size_inches(width, width/1.618, forward=True)
    return [m, b, endy, p_value, cols]

def try_add_basemap(slug_wilderness, axis, crs):
    log(slug_wilderness, 'WHITE', str(datetime.now().strftime('%Y%m%d_%H%M')) + ' ' + slug_wilderness + ' adding terrain basemap')
    try:
        contextily.add_basemap(axis, zoom=14, crs=crs)
        log(slug_wilderness, 'WHITE', str(datetime.now().strftime('%Y%m%d_%H%M')) + ' ' + slug_wilderness + ' trying zoom 14')
    except:
        try:
            contextily.add_basemap(axis, zoom=13, crs=crs)
            log(slug_wilderness, 'WHITE', str(datetime.now().strftime('%Y%m%d_%H%M')) + ' ' + slug_wilderness + ' trying zoom 13')
        except:
            try:
                contextily.add_basemap(axis, zoom=12, crs=crs)
                log(slug_wilderness, 'WHITE', str(datetime.now().strftime('%Y%m%d_%H%M')) + ' ' + slug_wilderness + ' trying zoom 12')
            except:
                contextily.add_basemap(axis, zoom=11, crs=crs)
                log(slug_wilderness, 'WHITE', str(datetime.now().strftime('%Y%m%d_%H%M')) + ' ' + slug_wilderness + ' trying zoom 11')

def cast_to_multigeometry(geom):
    upcast_dispatch = {shapely.geometry.Point: shapely.geometry.MultiPoint,
                       shapely.geometry.LineString: shapely.geometry.MultiLineString,
                       shapely.geometry.Polygon: shapely.geometry.MultiPolygon}
    caster = upcast_dispatch.get(type(geom), lambda x: x[0])
    return caster([geom])
