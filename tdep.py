import os
from datetime import datetime

import colorama
import django
import geopandas
from matplotlib import pyplot, colors
import pandas
import rasterio
from rasterio.features import shapes
import fiona
import rasterio.mask
import gdal

from settings import *
from utils import *

max_iter = 9999

def tdep2_awilderness(which_wilderness, ns): # cut and stack rasters to shp, this rules
    tdep_national = data_dir + ns + '-stacked.tif'
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    awilderness_n_file = slug_wilderness + '-n.' + out_ext
    awilderness_n_1mi_file = slug_wilderness + '-n-buffer.' + out_ext
    awilderness_n_5mi_file = slug_wilderness + '-n5-buffer.' + out_ext
    tdep_wgrid_file = slug_wilderness + '-' + ns + 'tdep-grid.' + out_ext
    tdep_w_file = slug_wilderness + '-' + ns + 'tdep.' + out_ext

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    wilderness_designation_year = awilderness['Designated'].iloc[0][0:4]

    awilderness_5mi = awilderness.copy()
    awilderness_5mi['geometry'] = awilderness_5mi.geometry.buffer(.01609344*5) # warns but ok
    awilderness_5mi = awilderness_5mi.to_crs(ras_epsg)
    awilderness_5mi.to_file(driver=out_driver, filename=out_dir + awilderness_n_5mi_file)
    log(slug_wilderness, 'GREEN', str(awilderness_n_5mi_file) + ' created')

    with fiona.open(out_dir + awilderness_n_5mi_file, "r") as shapefile:
        shapefeatures = [feature["geometry"] for feature in shapefile]
    with rasterio.open(tdep_national) as src:
        out_image, out_transform = rasterio.mask.mask(src, shapefeatures, crop=True)
        out_meta = src.meta
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})
    with rasterio.open(out_dir + slug_wilderness + '-' + ns + '.tif', "w", **out_meta) as dest:
        dest.write(out_image)
    log(slug_wilderness, 'GREEN', str(slug_wilderness) + ' ' +  ns + ' tdep mask created')

    tdep_years = ['20190', '20180', '20170', '20160', '20150', '20140', '20130', '20120', '20110', '20100', '20090', '20080', '20070', '20060', '20050', '20040', '20030', '20020', '20010', '20000'] # 20 out
    #tdep_years = ['20200', '20190', '20180', '20170', '20160', '20150', '20140', '20130', '20120', '20110', '20100', '20090', '20080', '20070', '20060', '20050', '20040', '20030', '20020', '20010'] # 21 out
    first = 0
    for tdep_year in tdep_years:
        first = first + 1
        bandnum = int(tdep_year[:4])-1999
        with rasterio.open(out_dir + slug_wilderness + '-' + ns + '.tif') as rds:
            band = rds.read(bandnum)
            transform = rds.transform
            mask = None
            if first == 1:
                colname = tdep_year[-5:]
                print(colorama.Fore.WHITE + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT + ' vectorizing ' + colname + ' grid')
                results = (
                    {'properties': {'c': i, 'raster_val': v}, 'geometry': s}
                    for i, (s, v)
                    in enumerate(
                        shapes(band, mask=mask, transform=transform)))
                geoms = list(results)
                pd_raster = geopandas.GeoDataFrame.from_features(geoms)
                pd_raster.crs = ras_epsg
                pd_raster = pd_raster.rename(columns={'raster_val': colname})
                pd_raster = pd_raster[['c', colname, 'geometry']]
                tdep_stack = pd_raster 
            else:
                colname = tdep_year[-5:]
                print(colorama.Fore.WHITE + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT + ' indexing ' + colname + ' grid')
                results = (
                    {'properties': {'c': i, 'raster_val': v}, 'geometry': s}
                    for i, (s, v)
                    in enumerate(
                        shapes(band, mask=mask, transform=transform)))
                geoms = list(results)
                pd_raster = geopandas.GeoDataFrame.from_features(geoms)
                pd_raster = pd_raster.rename(columns={'raster_val': colname})
                pd_raster = pd_raster[['c', colname, 'geometry']]

                points = pd_raster.copy()
                points.crs = ras_epsg
                theboth = geopandas.sjoin(tdep_stack, points, how="left", op='contains')

                tdep_stack = geopandas.GeoDataFrame(theboth, geometry='geometry')
                extra_cols = [e for e in tdep_stack.columns if e not in ['FID', '20210', '20200', '20190', '20180', '20170', '20160', '20150', '20140', '20130', '20120', '20110', '20100', '20090', '20080', '20070', '20060', '20050', '20040', '20030', '20020', '20010', '20000', 'geometry']]
                tdep_stack = tdep_stack.drop(columns=extra_cols)
                tdep_stack.crs = ras_epsg

    tdep_stack.to_file(driver=out_driver, filename=out_dir + ns + 'tdep-cut-stack.shp')
    print(colorama.Fore.GREEN + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT + ' ' + ns + ' tdep-cut-stack.shp' + ' created')

def tdep_awilderness_maps(which_wilderness, ns):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    tdep_national_file = out_dir + ns + 'tdep-cut-stack.shp'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    awilderness_n_file = slug_wilderness + '-n.' + out_ext
    awilderness_n_1mi_file = slug_wilderness + '-n-buffer.' + out_ext
    tdep_wgrid_file = slug_wilderness + '-' + ns + 'tdep-grid.' + out_ext
    tdep_w_file = slug_wilderness + '-' + ns + 'tdep.' + out_ext

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    wilderness_designation_year = awilderness['Designated'].iloc[0][0:4]

    if ns == 'n':
        nsname = 'Nitrogen'
    elif ns == 's':
        nsname = 'Sulfur'
    awilderness_n = awilderness.to_crs(ras_epsg)
    awilderness_n.to_file(driver=out_driver, filename=out_dir + awilderness_n_file)
    log(slug_wilderness, 'GREEN', str(awilderness_n_file) + ' created')

    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    awilderness_n_1mi = awilderness_1mi.to_crs(ras_epsg)
    awilderness_n_1mi.to_file(driver=out_driver, filename=out_dir + awilderness_n_1mi_file)
    log(slug_wilderness, 'GREEN', str(awilderness_n_1mi_file) + ' created')

    tdep_national = geopandas.read_file(tdep_national_file)
    log(slug_wilderness, 'WHITE', 'clipping grid to wilderness')
    tdep_national.crs = ras_epsg
    extra_cols = [e for e in awilderness_n.columns if e != 'geometry']
    awilderness_n = awilderness_n.drop(columns=extra_cols)

    try:
        tdep_wgrid = geopandas.overlay(tdep_national, awilderness_n, how='intersection')
        tdep_wgrid = tdep_wgrid.fillna('0')
        tdep_wgrid.crs = awilderness_n.crs
    except KeyError:
        log(slug_wilderness, 'WHITE', ns + 'tdep clipped empty')
        empty_file_out = out_dir + slug_wilderness + '-' + ns + 'tdep-empty.txt'
        tdep_wgrid = None
        with open(empty_file_out, 'a'):
            os.utime(empty_file_out, None)

    if tdep_wgrid is not None: # array of grid cells over wilderness
        xlist0 = ''
        tdep_wgrid['y0'] = ''
        for col in list(tdep_wgrid):
            if col not in ('geometry', 'c', 'y', 'x', 'm', 'b', 'endy', 'p_value', 'trend_text', 'acres', 'y0', 'x0', 'm0', 'b0', 'endy0', 'p_value0', 'trend_text0'):
                coly = col[:-1]
                xlist0 = xlist0 + coly + ' '
                tdep_wgrid['y0'] = tdep_wgrid['y0'] + tdep_wgrid[col].astype(str) + ' '

        tdep_wgrid['x0'] = xlist0
        x_vals0 = [int(value) for value in xlist0.split()]
        xmin0 = min(x_vals0)
        xmax0 = max(x_vals0)

        xlist = ''
        tdep_wgrid['y'] = ''
        for col in list(tdep_wgrid):
            if col not in ('geometry', 'c', 'y', 'x', 'm', 'b', 'endy', 'p_value', 'trend_text', 'acres', 'y0', 'x0', 'm0', 'b0', 'endy0', 'p_value0', 'trend_text0'):
                coly = col[:-1]
                if int(coly) >= int(wilderness_designation_year):
                    xlist = xlist + coly + ' '
                    tdep_wgrid['y'] = tdep_wgrid['y'] + tdep_wgrid[col].astype(str) + ' '

        tdep_wgrid['x'] = xlist

        if tdep_wgrid.empty:
            log(slug_wilderness, 'WHITE', ns + 'tdep clipped empty')
            empty_file_out = out_dir + slug_wilderness + '-' + ns + 'tdep-empty.txt'
            tdep_wgrid = None
            with open(empty_file_out, 'a'):
                os.utime(empty_file_out, None)
        elif not xlist:
            log(slug_wilderness, 'WHITE', ns + 'tdep period of record too short')
            empty_file_out = out_dir + slug_wilderness + '-' + ns + 'tdep-empty.txt'
            tdep_wgrid = None
            with open(empty_file_out, 'a'):
                os.utime(empty_file_out, None)
        else:
            fig1 = pyplot.gcf()
            width = 13
            fig1.set_size_inches(width, width/1.618, forward=True)
            x_vals = [int(value) for value in xlist.split()]
            xmin = min(x_vals)
            xmax = max(x_vals)
            ticks = x_vals
            pyplot.suptitle(which_wilderness + '\nTotal ' + nsname + ' Deposition Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax) + ' by Grid Cell', y=.95)
            if not tdep_wgrid['x0'].values[0] == tdep_wgrid['x'].values[0]:
                tdep_wgrid[['m0', 'b0', 'endy0', 'p_value0', 'trend_text0', 'cols0']] = tdep_wgrid.apply(
                    lambda row: pandas.Series(trend2(row['x0'], row['y0'], ['tab:cyan', 'tab:gray', 0.025])), axis=1)
                tdep_wgrid = tdep_wgrid.drop(columns='cols0')

                trend_max = tdep_wgrid.loc[tdep_wgrid['m0'].idxmax()]
                trend_min = tdep_wgrid.loc[tdep_wgrid['m0'].idxmin()]
                x_list0 = [int(i) for i in trend_max['x0'].split()]

                maxline_values = [trend_max['m0'] * int(i) + trend_max['b0'] for i in x_list0]
                minline_values = [trend_min['m0'] * int(i) + trend_min['b0'] for i in x_list0]
                pyplot.plot(x_list0, maxline_values, color='tab:cyan', alpha=0.5, linewidth=2, label=None)
                pyplot.plot(x_list0, minline_values, color='tab:cyan', alpha=0.5, linewidth=2, label=None)
                ticks = x_vals0
                pyplot.suptitle(which_wilderness + '\nTotal ' + nsname + ' Deposition Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax) + ' by Grid Cell\nwith Total ' + nsname + ' Deposition Trend from ' + year_formatter(xmin0) + ' to ' + year_formatter(xmax0) + ' by Grid Cell', y=.95)
            tdep_wgrid[['m', 'b', 'endy', 'p_value', 'trend_text', 'cols']] = tdep_wgrid.apply(
                lambda row: pandas.Series(trend2(row['x'], row['y'], ['tab:green', 'tab:gray', 0.05])), axis=1)
            tdep_wgrid = tdep_wgrid.drop(columns='cols')

            trend_max = tdep_wgrid.loc[tdep_wgrid['m'].idxmax()]
            trend_min = tdep_wgrid.loc[tdep_wgrid['m'].idxmin()]
            x_list = [int(i) for i in trend_max['x'].split()]

            maxline_values = [trend_max['m'] * int(i) + trend_max['b'] for i in x_list]
            minline_values = [trend_min['m'] * int(i) + trend_min['b'] for i in x_list]
            pyplot.plot(x_list, maxline_values, color='tab:green', alpha=1, linewidth=2, label=None)
            pyplot.plot(x_list, minline_values, color='tab:green', alpha=1, linewidth=2, label=None)

            pyplot.xticks(ticks)
            pyplot.suptitle(which_wilderness + '\nTotal ' + nsname + ' Deposition Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax) + ' by Grid Cell\nwith Total ' + nsname + ' Deposition Trend from ' + year_formatter(xmin0) + ' to ' + year_formatter(xmax0) + ' by Grid Cell', y=.95)
            pyplot.margins(0,0)
            fig1.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-' + ns + 'tdep-graph-extended-grid.png')
            fig1.clf()
            pyplot.clf()
            pyplot.cla()
            pyplot.close()

            tdep_wgrid['acres'] = tdep_wgrid['geometry'].area/4046.856

            tdep_wgrid.to_file(driver=out_driver, filename=out_dir + tdep_wgrid_file)
            log(slug_wilderness, 'GREEN', str(tdep_wgrid_file) + ' created with ' + str(len(tdep_wgrid.index)) + ' tdep cells')

            w_acres = tdep_wgrid['acres'].sum()

            if ns == 's':
                pass
                #tdep_wgrid = tdep_wgrid[tdep_wgrid.c != 454443] # TODO: select border by area
            elif ns == 'n':
                pass
                #tdep_wgrid = tdep_wgrid[tdep_wgrid.c != 454467] # TODO: select border by area
            for col in list(tdep_wgrid):
                if col not in ('geometry', 'c', 'x', 'y', 'm', 'b', 'endy', 'p_value', 'trend_text', 'acres', 'c0', 'y0', 'x0', 'm0', 'b0', 'endy0', 'p_value0', 'trend_text0', 'acres0'):
                    tdep_wgrid[col] = pandas.to_numeric(tdep_wgrid[col], errors='coerce')
                    tdep_wgrid[col[:-1] + '_sum'] = (tdep_wgrid[col] * tdep_wgrid['acres']) / w_acres
                    tdep_wgrid[col[:-1] + '_tdep'] = tdep_wgrid[col[:-1] + '_sum'].sum()
                    tdep_wgrid = tdep_wgrid.drop(columns=[col, col[:-1] + '_sum'])

            extra_cols = [e for e in tdep_wgrid.columns if '_tdep' not in e]
            extra_cols = [value for value in extra_cols if value not in ['geometry', 'w_acres', 'y', 'x', 'm', 'b', 'endy', 'p_value', 'trend_text', 'acres', 'y0', 'x0', 'm0', 'b0', 'endy0', 'p_value0', 'trend_text0']]
            tdep_wgrid = tdep_wgrid.drop(columns=extra_cols)
            tdep_w = tdep_wgrid.dissolve(by='x') # cells dissolved to wilderness
            tdep_w['w_acres'] = w_acres

            xlist = ''
            tdep_w['y'] = ''
            for col in list(tdep_w):
                if col not in ('geometry', 'c', 'y0', 'x0', 'y', 'x', 'm0', 'b0', 'endy0', 'p_value0', 'trend_text0', 'm', 'b', 'endy', 'p_value', 'trend_text', 'acres', 'w_acres'):
                    coly = col[:-5]
                    if int(coly) >= int(wilderness_designation_year):
                        tdep_w['y'] = tdep_w['y'] + tdep_w[col].astype(str) + ' '
                        xlist = xlist + coly + ' '
            tdep_w['x'] = xlist

            xlist0 = ''
            tdep_w['y0'] = ''
            for col in list(tdep_w):
                if col not in ('geometry', 'c', 'y0', 'x0', 'y', 'm0', 'x', 'b0', 'endy0', 'p_value0', 'trend_text0', 'm', 'b', 'endy', 'p_value', 'trend_text', 'acres', 'w_acres'):
                    coly = col[:-5]
                    tdep_w['y0'] = tdep_w['y0'] + tdep_w[col].astype(str) + ' '
                    xlist0 = xlist0 + coly + ' '
            tdep_w['x0'] = xlist0

            if tdep_w.empty:
                log(slug_wilderness, 'WHITE', ns + 'tdep clipped empty')
                empty_file_out = out_dir + slug_wilderness + '-' + ns + 'tdep-empty.txt'
                tdep_w = None
                with open(empty_file_out, 'a'):
                    os.utime(empty_file_out, None)
            else:
                fig2 = pyplot.gcf()
                width = 13
                fig2.set_size_inches(width, width/1.618, forward=True)
                x_vals = [int(value) for value in xlist.split()]
                ticks = x_vals
                xmin = min(x_vals)
                xmax = max(x_vals)
                if not tdep_w['x0'].values[0] == tdep_w['x'].values[0]: # check if extended period
                    tdep_w[['m0', 'b0', 'endy0', 'p_value0', 'trendtext0', 'cols0']] = tdep_w.apply(
                        lambda row: pandas.Series(trend2(row['x0'], row['y0'], ['tab:blue', 'black', 0.5])), axis=1)
                    tdep_w = tdep_w.drop(columns='cols0')
                    ticks = x_vals0

                    tdep_w[['m', 'b', 'endy', 'p_value', 'trendtext', 'cols']] = tdep_w.apply(
                        lambda row: pandas.Series(trend2(row['x'], row['y'], ['tab:red', 'black', 1])), axis=1)
                    tdep_w = tdep_w.drop(columns='cols').reset_index(drop=True)

                    tdep_w.to_file(driver=out_driver, filename=out_dir + tdep_w_file)

                    pyplot.xticks(ticks)
                    pyplot.suptitle(which_wilderness + '\nTotal ' + nsname + ' Deposition Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax) + '\nwith Total ' + nsname + ' Deposition Trend from ' + year_formatter(xmin0) + ' to ' + year_formatter(xmax0), y=.95)
                    txt = ns + 'tdep trend = ' + tdep_w['trendtext'][0] + '\n' + ns + 'tdep trend slope  = ' + float_formatter(tdep_w['m'][0]) + '\n' + ns + 'tdep trend p-value = ' + p_formatter(tdep_w['p_value'][0])
                    ax = pyplot.gca()
                    ax.annotate(txt,
                        xy=(0.9, 0.9), xytext=(-100, -0),
                        xycoords=('figure fraction', 'figure fraction'),
                        textcoords='offset points',
                        bbox=dict(facecolor='white', edgecolor='black', pad=5.0),
                        size=8, family='monospace', ha='left', va='bottom')
                    pyplot.margins(0,0)
                    fig2.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-' + ns + 'tdep-graph-extended.png')
                    fig2.clf()
                    fig2.clear()
                    pyplot.clf()
                    pyplot.cla()
                    pyplot.close()
                    pyplot.gcf().clear()

                fig2 = pyplot.gcf()
                width = 13
                fig2.set_size_inches(width, width/1.618, forward=True)
                x_vals = [int(value) for value in xlist.split()]
                ticks = x_vals
                xmin = min(x_vals)
                xmax = max(x_vals)

                tdep_wgrid[['m', 'b', 'endy', 'p_value', 'trend_text', 'cols']] = tdep_wgrid.apply(
                    lambda row: pandas.Series(trend2(row['x'], row['y'], ['tab:green', 'tab:gray', 0.05])), axis=1)
                tdep_wgrid = tdep_wgrid.drop(columns='cols')

                trend_max = tdep_wgrid.loc[tdep_wgrid['m'].idxmax()]
                trend_min = tdep_wgrid.loc[tdep_wgrid['m'].idxmin()]
                x_list = [int(i) for i in trend_max['x'].split()]

                maxline_values = [trend_max['m'] * int(i) + trend_max['b'] for i in x_list]
                minline_values = [trend_min['m'] * int(i) + trend_min['b'] for i in x_list]
                pyplot.plot(x_list, maxline_values, color='tab:green', alpha=1, linewidth=2, label=None)
                pyplot.plot(x_list, minline_values, color='tab:green', alpha=1, linewidth=2, label=None)

                pyplot.xticks(ticks)

                tdep_w[['m', 'b', 'endy', 'p_value', 'trend_text', 'cols']] = tdep_w.apply(
                    lambda row: pandas.Series(trend2(row['x'], row['y'], ['tab:red', 'black', 1])), axis=1)
                tdep_w = tdep_w.drop(columns='cols')
                print('trend2>')
                print(tdep_w['trend_text'][0])
                print(tdep_w['p_value'][0])

                nx = tdep_w['x'].str.split().values.tolist()[0]
                ny = tdep_w['y'].str.split().values.tolist()[0]
                dictny = {'years_x': nx, 'observations_y': ny}
                nxy = pandas.DataFrame.from_dict(dictny)
                nxy['years_x'] = pandas.to_numeric(nxy['years_x'])
                nxy['observations_y'] = pandas.to_numeric(nxy['observations_y'])
                nx = nxy['years_x']
                ny = nxy['observations_y']
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(nx,ny)
                print('trender>')
                print(trend_text)
                print(p_value)
                jsd = [{
                    "yr_min": year_formatter(min(nx)),
                    "yr_max": year_formatter(max(nx)),
                    "endy": float_formatter(endy),
                    "m": float_formatter(m),
                    "trend": trend_text,
                    "p": p_formatter(p_value)
                    }]
                jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
                with open(out_dir + 'index-' + ns + 'tdep-new.json', 'w') as static_file:
                    static_file.write(jsc)

                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                txt = str(min(nx)) + '-' + str(max(nx)) + ' : ' + trend_text + ' ' + '(p=' + p_formatter(p_value) + ')'


                tdep_w.to_csv(out_dir + slug_wilderness + '-' + ns + 'tdep-cols.csv', index=False)
                tdep_w.to_file(driver=out_driver, filename=out_dir + tdep_w_file, index=False)
                tdep_csv = tdep_w.drop(columns=['y0', 'x0', 'y', 'x', 'm', 'b', 'endy', 'p_value', 'trend_text', 'acres', 'w_acres', 'geometry'])
                tdep_csv.columns = tdep_csv.columns.str.rstrip('_tdep')
                tdep_csv = tdep_csv.melt(id_vars=[], var_name="year", value_name=ns + "tdep")
                tdep_csv.to_csv(out_dir + slug_wilderness + '-' + ns + 'tdep.csv', index=False)

                pyplot.xticks(ticks)
                pyplot.suptitle(which_wilderness + '\nTotal ' + nsname + ' Deposition Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax), y=.95)
                txt = ns + 'tdep trend = ' + tdep_w['trend_text'][0] + '\n' + ns + 'tdep trend slope  = ' + float_formatter(tdep_w['m'][0]) + '\n' + ns + 'tdep trend p-value = ' + p_formatter(tdep_w['p_value'][0])
                ax = pyplot.gca()
                ax.annotate(txt,
                    xy=(0.9, 0.9), xytext=(-100, -0),
                    xycoords=('figure fraction', 'figure fraction'),
                    textcoords='offset points',
                    bbox=dict(facecolor='white', edgecolor='black', pad=5.0),
                    size=8, family='monospace', ha='left', va='bottom')
                pyplot.margins(0,0)
                fig2.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-' + ns + 'tdep-graph.png')
                fig2.clf()
                fig2.clear()
                pyplot.clf()
                pyplot.cla()
                pyplot.close()
                pyplot.gcf().clear()

                jsd = [{
                    "yr_min": year_formatter(xmin),
                    "yr_max": year_formatter(xmax),
                    "endy": float_formatter(tdep_w['endy'][0]),
                    "m": float_formatter(tdep_w['m'][0]),
                    "trend": tdep_w['trend_text'][0],
                    "p": p_formatter(tdep_w['p_value'][0])
                    }]
                jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
                with open(out_dir + 'index-' + ns + 'tdep.json', 'w') as static_file:
                    static_file.write(jsc)

def tdep_wilderness_plots(which_wilderness, ns):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    tdep_national_file = out_dir + ns + 'tdep-cut-stack.shp'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    awilderness_n_file = slug_wilderness + '-n.' + out_ext
    awilderness_n_1mi_file = slug_wilderness + '-n-buffer.' + out_ext
    tdep_wgrid_file = slug_wilderness + '-' + ns + 'tdep-grid.' + out_ext
    tdep_w_file = slug_wilderness + '-' + ns + 'tdep.' + out_ext
    empty_file_out = out_dir + slug_wilderness + '-' + ns + 'tdep-empty.txt'
    
    if os.path.exists(empty_file_out):
        log(slug_wilderness, 'WHITE', ns + 'tdep empty')
    else:
        awilderness = geopandas.read_file(out_dir + awilderness_file)
        wilderness_designation_year = awilderness['Designated'].iloc[0][0:4]

        if ns == 'n':
            nsname = 'Nitrogen'
        elif ns == 's':
            nsname = 'Sulfur'
        if os.path.exists(out_dir + awilderness_n_file):
            awilderness_n = geopandas.read_file(out_dir + awilderness_n_file)
            awilderness_n = awilderness_n.to_crs(ras_epsg)
            awilderness_n_1mi = geopandas.read_file(out_dir + awilderness_n_1mi_file)
            awilderness_n_1mi = awilderness_n_1mi.to_crs(ras_epsg)
        if os.path.exists(out_dir + tdep_wgrid_file):
            log(slug_wilderness, 'WHITE', 'reading ' + tdep_wgrid_file)
            tdep_wgrid = geopandas.read_file(out_dir + tdep_wgrid_file)
        if os.path.exists(out_dir + tdep_w_file):
            log(slug_wilderness, 'WHITE', 'reading ' + tdep_w_file)
            tdep_w = geopandas.read_file(out_dir + tdep_w_file)

        width = 13
        cmaps = 'Accent, Accent_r, Blues, Blues_r, BrBG, BrBG_r, BuGn, BuGn_r, BuPu, BuPu_r, CMRmap, CMRmap_r, Dark2, Dark2_r, GnBu, GnBu_r, Greens, Greens_r, Greys, Greys_r, OrRd, OrRd_r, Oranges, Oranges_r, PRGn, PRGn_r, Paired, Paired_r, Pastel1, Pastel1_r, Pastel2, Pastel2_r, PiYG, PiYG_r, PuBu, PuBuGn, PuBuGn_r, PuBu_r, PuOr, PuOr_r, PuRd, PuRd_r, Purples, Purples_r, RdBu, RdBu_r, RdGy, RdGy_r, RdPu, RdPu_r, RdYlBu, RdYlBu_r, RdYlGn, RdYlGn_r, Reds, Reds_r, Set1, Set1_r, Set2, Set2_r, Set3, Set3_r, Spectral, Spectral_r, Wistia, Wistia_r, YlGn, YlGnBu, YlGnBu_r, YlGn_r, YlOrBr, YlOrBr_r, YlOrRd, YlOrRd_r, afmhot, afmhot_r, autumn, autumn_r, binary, binary_r, bone, bone_r, brg, brg_r, bwr, bwr_r, cividis, cividis_r, cool, cool_r, coolwarm, coolwarm_r, copper, copper_r, cubehelix, cubehelix_r, flag, flag_r, gist_earth, gist_earth_r, gist_gray, gist_gray_r, gist_heat, gist_heat_r, gist_ncar, gist_ncar_r, gist_rainbow, gist_rainbow_r, gist_stern, gist_stern_r, gist_yarg, gist_yarg_r, gnuplot, gnuplot2, gnuplot2_r, gnuplot_r, gray, gray_r, hot, hot_r, hsv, hsv_r, inferno, inferno_r, jet, jet_r, magma, magma_r, nipy_spectral, nipy_spectral_r, ocean, ocean_r, pink, pink_r, plasma, plasma_r, prism, prism_r, rainbow, rainbow_r, seismic, seismic_r, spring, spring_r, summer, summer_r, tab10, tab10_r, tab20, tab20_r, tab20b, tab20b_r, tab20c, tab20c_r, terrain, terrain_r, twilight, twilight_r, twilight_shifted, twilight_shifted_r, viridis, viridis_r, winter, winter_r'
        cmaps = 'cividis'
        cmap_list = cmaps.split(', ')
        for cmap in cmap_list:
            fig, axis = pyplot.subplots(figsize=(width, width/1.618))
            tdep_wgrid.plot(ax=axis, column='m', cmap=cmap, edgecolor='white', alpha=1)
            awilderness_n.plot(ax=axis, facecolor='none', edgecolor='black')
            xlim = ([awilderness_n_1mi.total_bounds[0], awilderness_n_1mi.total_bounds[2]])
            ylim = ([awilderness_n_1mi.total_bounds[1], awilderness_n_1mi.total_bounds[3]])
            axis.set_xlim(xlim)
            axis.set_ylim(ylim)
            pyplot.suptitle(which_wilderness + '\n' + nsname + ' Total Deposition')
            txt = ns + 'tdep trend = ' + tdep_w['trend_text'][0] + '\n' + ns + 'tdep trend slope  = ' + float_formatter(tdep_w['m'][0]) + '\n' + ns + 'tdep trend p-value = ' + p_formatter(tdep_w['p_value'][0])
            pyplot.axis('off')
            fig1 = pyplot.gcf()
            pyplot.subplots_adjust(top = 0.95, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            pyplot.margins(0,0)
            axis.annotate(txt,
                        xy=(0.9, 0.9), xytext=(-100, -0),
                        xycoords=('figure fraction', 'figure fraction'),
                        textcoords='offset points',
                        bbox=dict(facecolor='white', edgecolor='black', pad=5.0),
                        size=8, family='monospace', ha='left', va='bottom')
            fig1.savefig(out_dir + slug_wilderness + '-' + ns + 'tdep.png')
            awilderness_box = awilderness_n_1mi.copy()
            awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
            awilderness_box['geometry'] = awilderness_box.geometry.buffer(16093.440)
            xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
            ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
            axis.set_xlim(xlim2)
            axis.set_ylim(ylim2)
            axis.set_xlim(xlim)
            axis.set_ylim(ylim)
            own_blm_file = slug_wilderness + '-own-blm.' + out_ext
            own_usfs_file = slug_wilderness + '-own-usfs.' + out_ext
            if os.path.exists(out_dir + own_blm_file):
                blm_inside = geopandas.read_file(out_dir + own_blm_file)
                blm_inside = blm_inside.to_crs(awilderness_n.crs)
            if os.path.exists(out_dir + own_usfs_file):
                usfs_inside = geopandas.read_file(out_dir + own_usfs_file)
                usfs_inside = usfs_inside.to_crs(awilderness_n.crs)
            bfill = colors.colorConverter.to_rgba('tab:brown', alpha=0.2)
            ufill = colors.colorConverter.to_rgba('tab:green', alpha=0.2)
            try:
                usfs_inside.plot(ax=axis, color=ufill, edgecolor='white', linewidth=2.0,)
            except:
                pass
            try:
                blm_inside.plot(ax=axis, color=bfill, edgecolor='white', linewidth=2.0,)
            except:
                pass
            fig1.savefig(out_dir + slug_wilderness + '-' + ns + 'tdep-own.png')
            fig1.clf()
            pyplot.clf()
            pyplot.cla()
            pyplot.close()
