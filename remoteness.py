import os

import django
import geopandas
import matplotlib

from settings import *
from utils import *

def devx_to_awilderness_1mi(which_wilderness, dev_layer):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    devx_awilderness_1mi_file = slug_wilderness + '-rem-' + dev_layer + '.' + out_ext
    empty_file_out = out_dir + slug_wilderness + '-rem-' + dev_layer + '-empty.txt'

    if os.path.exists(out_dir + devx_awilderness_1mi_file):
        log(slug_wilderness, 'CYAN', devx_awilderness_1mi_file + ' already exists')
    else:
        log(slug_wilderness, 'WHITE', dev_layer + ' loading')
        if dev_layer == 'devpt':
            devx = geopandas.read_file(dev_pt_gdb, layer='dev_pt_201904')
        elif dev_layer == 'devpl':
            devx = geopandas.read_file(dev_pl_gdb, layer='dev_pl_201904')
        elif dev_layer == 'devln':
            devx = geopandas.read_file(dev_ln_gdb, layer='dev_ln_201904')
            devx = devx[devx['GLOBALID'] != "{809F15C5-BDBB-4473-A716-31C409516D00}"] # ???
            devx = devx[devx['GLOBALID'] != "{C922985D-4F46-40C2-8822-1BDE429E5D36}"] # esulser
        elif dev_layer == 'roadcore2':
            devx = geopandas.read_file(base_dir + roadcore2_file)
            devx.crs = {'init': 'epsg:4269'}
        awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
        log(slug_wilderness, 'WHITE', dev_layer + ' clipping to ' + devx_awilderness_1mi_file)
        if dev_layer == 'devpl':
            xmin, ymin, xmax, ymax = awilderness_1mi.total_bounds
            devx_around = devx.cx[xmin:xmax, ymin:ymax]
            if devx_around.empty:
                devx_awilderness_1mi = geopandas.GeoDataFrame()
            else:
                devx_awilderness_1mi = geopandas.overlay(devx, awilderness_1mi, how='intersection')
        elif dev_layer == 'devpt':
            devx_tagged = geopandas.sjoin(devx, awilderness_1mi[['NAME', 'geometry']], how='left', op='within')
            devx_awilderness_1mi = devx_tagged[devx_tagged['NAME'].notnull()]
        else:
            devx_awilderness_1mi = lines_poly(devx, awilderness_1mi)
        if devx_awilderness_1mi.empty:
            log(slug_wilderness, 'WHITE', dev_layer + ' clipped empty')
            with open(empty_file_out, 'a'):
                os.utime(empty_file_out, None)
        else:
            devx_awilderness_1mi.to_file(driver=out_driver, filename=out_dir + devx_awilderness_1mi_file)
            log(slug_wilderness, 'GREEN', str(devx_awilderness_1mi_file) + ' created')

def devx_to_awilderness(which_wilderness, dev_layer, io):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    if io == 'in':
        awilderness_file = slug_wilderness + '.' + out_ext
    elif io == 'out':
        awilderness_file = slug_wilderness + '-ring.' + out_ext
    devx_awilderness_1mi_file = slug_wilderness + '-rem-' + dev_layer + '.' + out_ext
    awilderness_devx_file = slug_wilderness + '-rem-' + dev_layer + '-' + io + '.' + out_ext
    empty_file_in = out_dir + slug_wilderness + '-rem-' + dev_layer + '-empty.txt'
    empty_file_out = out_dir + slug_wilderness + '-rem-' + dev_layer + '-' + io +'-empty.txt'

    if os.path.exists(out_dir + awilderness_devx_file):
        log(slug_wilderness, 'CYAN', awilderness_devx_file + ' already exists')
    elif os.path.exists(empty_file_in):
        log(slug_wilderness, 'RED', devx_awilderness_1mi_file + ' empty')
        with open(empty_file_out, 'a'):
            os.utime(empty_file_out, None)
    else:
        log(slug_wilderness, 'WHITE', devx_awilderness_1mi_file + ' loading')
        devx_awilderness_1mi = geopandas.read_file(out_dir + devx_awilderness_1mi_file)
        awilderness = geopandas.read_file(out_dir + awilderness_file)

        log(slug_wilderness, 'WHITE', dev_layer + ' clipping to ' + awilderness_devx_file)
        if dev_layer == 'devpl':
            xmin, ymin, xmax, ymax = awilderness.total_bounds
            devx_around = devx_awilderness_1mi.cx[xmin:xmax, ymin:ymax]
            if devx_around.empty:
                awilderness_devx = geopandas.GeoDataFrame()
            else:
                awilderness_devx = geopandas.overlay(devx_awilderness_1mi, awilderness, how='intersection')
            awilderness_devx.crs = {'init': 'epsg:4269'}
        elif dev_layer == 'devpt':
            devx_tagged = geopandas.sjoin(devx_awilderness_1mi, awilderness[['NAME', 'geometry']], how='left', op='within')
            awilderness_devx = devx_tagged[devx_tagged['NAME_right'].notnull()]
        else:
            awilderness_devx = lines_poly(devx_awilderness_1mi, awilderness)
        if awilderness_devx.empty:
            with open(empty_file_out, 'a'):
                os.utime(empty_file_out, None)
            log(slug_wilderness, 'RED', dev_layer + ' ' + io + ' empty')
        else:
            awilderness_devx.to_file(driver=out_driver, filename=out_dir + awilderness_devx_file)
            log(slug_wilderness, 'GREEN', str(awilderness_devx_file) + ' created')

def devx_to_awilderness_buffer_erase(which_wilderness, dev_layer, io):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_devx_file = slug_wilderness + '-rem-' + dev_layer + '-' + io + '.' + out_ext
    devx_awilderness_buffer_file = slug_wilderness + '-rem-' + dev_layer + '-' + io + '-buffer.' + out_ext
    devx_awilderness_erase_file = slug_wilderness + '-rem-' + dev_layer + '-' + io + '-erase.' + out_ext
    empty_file_in = out_dir + slug_wilderness + '-rem-' + dev_layer + '-' + io + '-empty.txt'
    empty_file_out = out_dir + slug_wilderness + '-rem-' + dev_layer + '-' + io + '-erase-empty.txt'

    if os.path.exists(out_dir + devx_awilderness_buffer_file):
        log(slug_wilderness, 'CYAN', devx_awilderness_buffer_file + ' already exists')
        devx_awilderness_buffer = None
    elif os.path.exists(empty_file_in):
        log(slug_wilderness, 'WHITE', awilderness_devx_file + ' empty, no buffers')
        devx_awilderness_buffer = None
    else:
        awilderness_devx = geopandas.read_file(out_dir + awilderness_devx_file)
        log(slug_wilderness, 'WHITE', 'buffering ' + awilderness_devx_file)
        devx_awilderness_buffer = awilderness_devx.copy()
        devx_awilderness_buffer['geometry'] = devx_awilderness_buffer.geometry.buffer(.00804672)
        devx_awilderness_buffer.to_file(driver=out_driver, filename=out_dir + devx_awilderness_buffer_file)
        log(slug_wilderness, 'GREEN', str(devx_awilderness_buffer_file) + ' created')
    if os.path.exists(out_dir + devx_awilderness_erase_file):
        log(slug_wilderness, 'CYAN', devx_awilderness_erase_file + ' already exists')
    elif os.path.exists(empty_file_in):
        log(slug_wilderness, 'WHITE', awilderness_devx_file + ' empty, erased is full wilderness')
        devx_erase_poly = geopandas.read_file(out_dir + awilderness_file)
        devx_erase = geopandas.GeoDataFrame(devx_erase_poly)
        devx_erase.crs = {'init': 'epsg:4269'}
        devx_erase.to_file(driver=out_driver, filename=out_dir + devx_awilderness_erase_file)
        log(slug_wilderness, 'GREEN', str(devx_awilderness_erase_file) + ' created')
    else:
        if devx_awilderness_buffer is not None:
            pass
        else:
            devx_awilderness_buffer = geopandas.read_file(out_dir + devx_awilderness_buffer_file)
        awilderness = geopandas.read_file(out_dir + awilderness_file)
        if dev_layer == 'devpt':
            devx_awilderness_buffer = devx_awilderness_buffer.to_crs(awilderness.crs)
        log(slug_wilderness, 'WHITE', 'erasing ' + devx_awilderness_buffer_file)
        devx_erase_poly = geopandas.overlay(awilderness, devx_awilderness_buffer, how='difference')
        devx_erase_poly.explode()
        devx_erase = geopandas.GeoDataFrame(devx_erase_poly)
        devx_erase = devx_erase.rename(columns={0:'geometry'}).set_geometry('geometry')
        devx_erase.crs = {'init': 'epsg:4269'}
        if devx_erase.empty:
            with open(empty_file_out, 'a'):
                os.utime(empty_file_out, None)
            log(slug_wilderness, 'WHITE', dev_layer + ' covers wilderness, erased is empty')
        else:
            devx_erase.to_file(driver=out_driver, filename=out_dir + devx_awilderness_erase_file)
            log(slug_wilderness, 'GREEN', str(devx_awilderness_erase_file) + ' created')

def remoteness(which_wilderness, io):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    devpt_awilderness_erase_file = slug_wilderness + '-rem-devpt-' + io + '-erase.' + out_ext
    devpt_empty_file_in = out_dir + slug_wilderness + '-rem-devpt-' + io + '-erase-empty.txt'
    devln_awilderness_erase_file = slug_wilderness + '-rem-devln-' + io + '-erase.' + out_ext
    devln_empty_file_in = out_dir + slug_wilderness + '-rem-devln-' + io + '-erase-empty.txt'
    devpl_awilderness_erase_file = slug_wilderness + '-rem-devpl-' + io + '-erase.' + out_ext
    devpl_empty_file_in = out_dir + slug_wilderness + '-rem-devpl-' + io + '-erase-empty.txt'
    roadcore_awilderness_erase_file = slug_wilderness + '-rem-roadcore2-' + io + '-erase.' + out_ext
    roadcore_empty_file_in = out_dir + slug_wilderness + '-rem-roadcore2-' + io + '-erase-empty.txt'
    inroads_file = slug_wilderness + '-rem-' + io + '-fin.' + out_ext
    empty_file_out = out_dir + slug_wilderness + '-rem-' + io + '-fin-empty.txt'

    if os.path.exists(devpt_empty_file_in):
        inroads = None
    elif os.path.exists(devln_empty_file_in):
        inroads = None
    elif os.path.exists(devpl_empty_file_in):
        inroads = None
    elif os.path.exists(roadcore_empty_file_in):
        inroads = None
    else:
        if os.path.exists(out_dir + devpt_awilderness_erase_file):
            devpt_awilderness_erase = geopandas.read_file(out_dir + devpt_awilderness_erase_file)
            devpt_awilderness_erase.crs = {'init': 'epsg:4269'}
        else:
            log(slug_wilderness, 'RED', devpt_awilderness_erase_file + ' does not exist')
            devpt_awilderness_erase = None

        if os.path.exists(out_dir + devln_awilderness_erase_file):
            devln_awilderness_erase = geopandas.read_file(out_dir + devln_awilderness_erase_file)
            devln_awilderness_erase.crs = {'init': 'epsg:4269'}
        else:
            log(slug_wilderness, 'RED', devln_awilderness_erase_file + ' does not exist')
            devln_awilderness_erase = None

        if devpt_awilderness_erase is not None and devln_awilderness_erase is not None:
            try:
                auto_inter = geopandas.overlay(devpt_awilderness_erase, devln_awilderness_erase, how='intersection')
            except KeyError:
                log(slug_wilderness, 'WHITE', io + 'devpt/devln clipped empty')
                auto_inter = None
        elif devln_awilderness_erase is not None:
            auto_inter = devln_awilderness_erase.copy()
        elif devpt_awilderness_erase is not None:
            auto_inter = devpt_awilderness_erase.copy()
        else:
            auto_inter = None

        if os.path.exists(out_dir + devpl_awilderness_erase_file):
            devpl_awilderness_erase = geopandas.read_file(out_dir + devpl_awilderness_erase_file)
            devpl_awilderness_erase.crs = {'init': 'epsg:4269'}
        else:
            log(slug_wilderness, 'RED', devpl_awilderness_erase_file + ' does not exist')
            devpl_awilderness_erase = None

        if auto_inter is not None and devpl_awilderness_erase is not None:
            try:
                auto_inter2 = geopandas.overlay(auto_inter, devpl_awilderness_erase, how='intersection')
            except KeyError:
                log(slug_wilderness, 'WHITE', io + 'devpt/devln/devpl clipped empty')
                auto_inter2 = None
        elif devpl_awilderness_erase is not None:
            auto_inter2 = devpl_awilderness_erase.copy()
        elif auto_inter is not None:
            auto_inter2 = auto_inter.copy()
        else:
            auto_inter2 = None

        if os.path.exists(out_dir + roadcore_awilderness_erase_file):
            roadcore_awilderness_erase = geopandas.read_file(out_dir + roadcore_awilderness_erase_file)
            roadcore_awilderness_erase.crs = {'init': 'epsg:4269'}
        else:
            log(slug_wilderness, 'RED', roadcore_awilderness_erase_file + ' does not exist')
            roadcore_awilderness_erase = None

        if auto_inter2 is not None and roadcore_awilderness_erase is not None:
            try:
                inroads = geopandas.overlay(auto_inter2, roadcore_awilderness_erase, how='intersection')
            except KeyError:
                log(slug_wilderness, 'WHITE', io + 'devpt/devln/devpl/roadcore clipped empty')
                inroads = None
        elif roadcore_awilderness_erase is not None:
            inroads = roadcore_awilderness_erase.copy()
        elif auto_inter2 is not None:
            inroads = auto_inter2.copy()
        else:
            inroads = None

    if inroads is not None:
        inroads = inroads.to_crs({'proj':'cea'})
        extra_cols = [e for e in inroads.columns if e not in ['geometry']]
        inroads = inroads.drop(columns=extra_cols)
        inroads['acres'] = inroads['geometry'].area/4046.856
        inroads.to_file(driver=out_driver, filename=out_dir + inroads_file)
        log(slug_wilderness, 'GREEN', str(inroads_file) + ' created')
    else:
        with open(empty_file_out, 'a'):
            os.utime(empty_file_out, None)
        log(slug_wilderness, 'RED', io + ' measure empty')

def remoteness_plots(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '-cea.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    inroads_file = slug_wilderness + '-rem-in-fin.' + out_ext
    outroads_file = slug_wilderness + '-rem-out-fin.' + out_ext
    inroads_empty_file = slug_wilderness + '-rem-in-fin-empty.txt'
    outroads_empty_file = slug_wilderness + '-rem-out-fin-empty.txt'
    inroads_roadcore_file = slug_wilderness + '-rem-roadcore2-in.' + out_ext
    inroads_devln_file = slug_wilderness + '-rem-devln-in.' + out_ext
    inroads_devpl_file = slug_wilderness + '-rem-devpl-in.' + out_ext
    inroads_devpt_file = slug_wilderness + '-rem-devpt-in.' + out_ext
    outroads_roadcore_file = slug_wilderness + '-rem-roadcore2-out.' + out_ext
    outroads_devln_file = slug_wilderness + '-rem-devln-out.' + out_ext
    outroads_devpl_file = slug_wilderness + '-rem-devpl-out.' + out_ext
    outroads_devpt_file = slug_wilderness + '-rem-devpt-out.' + out_ext

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    if os.path.exists(out_dir + inroads_file):
        inroads = geopandas.read_file(out_dir + inroads_file)
    else:
        inroads = geopandas.GeoDataFrame()
        inroads['geometry'] = None
        inroads['acres'] = inroads['geometry'].area/4046.856
        inroads.crs = depsg
    if os.path.exists(out_dir + outroads_file):
        outroads = geopandas.read_file(out_dir + outroads_file)
    else:
        outroads = geopandas.GeoDataFrame()
        outroads['geometry'] = None
        outroads['acres'] = outroads['geometry'].area/4046.856
        outroads.crs = depsg
    if os.path.exists(out_dir + inroads_devln_file):
        inroads_devln = geopandas.read_file(out_dir + inroads_devln_file)
    else:
        inroads_devln = geopandas.GeoDataFrame()
        inroads_devln['geometry'] = None
        inroads_devln.crs = depsg
    if os.path.exists(out_dir + outroads_devln_file):
        outroads_devln = geopandas.read_file(out_dir + outroads_devln_file)
    else:
        outroads_devln = geopandas.GeoDataFrame()
        outroads_devln['geometry'] = None
        outroads_devln.crs = depsg
    if os.path.exists(out_dir + inroads_devpt_file):
        inroads_devpt = geopandas.read_file(out_dir + inroads_devpt_file)
    else:
        inroads_devpt = geopandas.GeoDataFrame()
        inroads_devpt['geometry'] = None
        inroads_devpt.crs = depsg
    if os.path.exists(out_dir + outroads_devpt_file):
        outroads_devpt = geopandas.read_file(out_dir + outroads_devpt_file)
    else:
        outroads_devpt = geopandas.GeoDataFrame()
        outroads_devpt['geometry'] = None
        outroads_devpt.crs = depsg
    if os.path.exists(out_dir + inroads_devpl_file):
        inroads_devpl = geopandas.read_file(out_dir + inroads_devpl_file)
    else:
        inroads_devpl = geopandas.GeoDataFrame()
        inroads_devpl['geometry'] = None
        inroads_devpl.crs = depsg
    if os.path.exists(out_dir + outroads_devpl_file):
        outroads_devpl = geopandas.read_file(out_dir + outroads_devpl_file)
    else:
        outroads_devpl = geopandas.GeoDataFrame()
        outroads_devpl['geometry'] = None
        outroads_devpl.crs = depsg
    if os.path.exists(out_dir + inroads_roadcore_file):
        inroads_roadcore = geopandas.read_file(out_dir + inroads_roadcore_file)
    else:
        inroads_roadcore = geopandas.GeoDataFrame()
        inroads_roadcore['geometry'] = None
        inroads_roadcore.crs = depsg
    if os.path.exists(out_dir + outroads_roadcore_file):
        outroads_roadcore = geopandas.read_file(out_dir + outroads_roadcore_file)
    else:
        outroads_roadcore = geopandas.GeoDataFrame()
        outroads_roadcore['geometry'] = None
        outroads_roadcore.crs = depsg
    if os.path.exists(out_dir + inroads_empty_file) and os.path.exists(out_dir + outroads_empty_file):
        inout = geopandas.GeoDataFrame()
        inout['geometry'] = None
        inout['acres'] = inout['geometry'].area/4046.856
        inout.crs = depsg
    elif os.path.exists(out_dir + inroads_empty_file):
        inout = geopandas.GeoDataFrame()
        inout['geometry'] = None
        inout['acres'] = inout['geometry'].area/4046.856
        inout.crs = depsg
    elif os.path.exists(out_dir + outroads_empty_file):
        inout = geopandas.GeoDataFrame()
        inout['geometry'] = None
        inout['acres'] = inout['geometry'].area/4046.856
        inout.crs = depsg
    else:
        inout = geopandas.overlay(inroads, outroads, how='intersection')

    inout['acres'] = inout['geometry'].area/4046.856
    w_ac = awilderness['acres'].sum()
    i_ac = inroads['acres'].sum()
    o_ac = outroads['acres'].sum()
    io_ac = inout['acres'].sum()
    i_pct = '{0:.0f}'.format((i_ac/w_ac) * 100)
    o_pct = '{0:.0f}'.format((o_ac/w_ac) * 100)
    io_pct = '{0:.0f}'.format((io_ac/w_ac) * 100)
    w_ac = '{0:.2f}'.format(w_ac)
    i_ac = '{0:.2f}'.format(i_ac)
    o_ac = '{0:.2f}'.format(o_ac)
    io_ac = '{0:.2f}'.format(io_ac)

    jsd = [{
        "w_ac": w_ac,
        "i_ac": i_ac,
        "o_ac": o_ac,
        "io_ac": io_ac,
        "i_pct": i_pct,
        "o_pct": o_pct,
        "io_pct": io_pct
        }]
    jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
    with open(out_dir + 'index-inout.json', 'w') as static_file:
        static_file.write(jsc)

    awilderness = awilderness.to_crs(epsg=4269) # from cea
    inroads = inroads.to_crs(epsg=4269) # from cea
    outroads = outroads.to_crs(epsg=4269) #from cea

    icp = 'tab:pink'
    ocp = 'tab:cyan'
    width = 13

    axis = awilderness.plot(color='none', edgecolor='black', linewidth=2.0, alpha=0.9, figsize=(width, width/1.618))
    inroads.plot(ax=axis, color=icp, edgecolor=icp, alpha=0.7)
    inroads_devln.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    inroads_devpt.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1, markersize=5)
    inroads_devpl.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    inroads_roadcore.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    awilderness.plot(ax=axis, color='none', edgecolor='black', linewidth=2.0, alpha=0.9)
    xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
    ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
    matplotlib.pyplot.suptitle(which_wilderness + '\nRemoteness from activity inside wilderness: Acres of wilderness away from access and travel routes and developments inside wilderness')
    txt = str(w_ac) + ' wilderness acres' + '\n' + str(i_ac) + ' inroads acres (' + str(i_pct) + '%)'
    matplotlib.pyplot.gcf().text(0.7, 0.89, txt, fontsize=8, fontdict=mono)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    matplotlib.pyplot.axis('off')
    fig1 = matplotlib.pyplot.gcf()
    fig1.savefig(out_dir + slug_wilderness + '-rem-in-fin.png')
    awilderness_box = awilderness_1mi.copy()
    awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
    xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
    ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
    axis.set_xlim(xlim2)
    axis.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, axis, awilderness.crs)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    fig1.savefig(out_dir + slug_wilderness + '-rem-in-fin-base.png')
    fig1.clf()
    matplotlib.pyplot.clf()
    matplotlib.pyplot.cla()
    matplotlib.pyplot.close()

    axis = awilderness.plot(color='none', edgecolor='black', linewidth=2.0, alpha=0.9, figsize=(width, width/1.618))
    outroads.plot(ax=axis, color=ocp, edgecolor=ocp, alpha=0.7)
    outroads_devln.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    outroads_devpt.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1, markersize=5)
    outroads_devpl.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    outroads_roadcore.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    awilderness.plot(ax=axis, color='none', edgecolor='black', linewidth=2.0, alpha=0.9)
    xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
    ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
    matplotlib.pyplot.suptitle(which_wilderness + '\nRemoteness from activity outside wilderness: Acres of wilderness away from access and travel routes and developments outside wilderness')
    txt = str(w_ac) + ' wilderness acres' + '\n' + str(o_ac) + ' outroads acres (' + str(o_pct) + '%)'
    matplotlib.pyplot.gcf().text(0.7, 0.89, txt, fontsize=8, fontdict=mono)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    matplotlib.pyplot.axis('off')
    fig1 = matplotlib.pyplot.gcf()
    fig1.savefig(out_dir + slug_wilderness + '-rem-out-fin.png')
    awilderness_box = awilderness_1mi.copy()
    awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
    xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
    ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
    axis.set_xlim(xlim2)
    axis.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, axis, awilderness.crs)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    fig1.savefig(out_dir + slug_wilderness + '-rem-out-fin-base.png')
    fig1.clf()
    matplotlib.pyplot.clf()
    matplotlib.pyplot.cla()
    matplotlib.pyplot.close()

    axis = awilderness.plot(color='none', edgecolor='black', linewidth=2.0, alpha=0.9, figsize=(width, width/1.618))
    inroads.plot(ax=axis, color=icp, edgecolor=icp, alpha=0.7)
    outroads.plot(ax=axis, color=ocp, edgecolor=ocp, alpha=0.7)
    inroads_devln.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    outroads_devln.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    inroads_devpt.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1, markersize=5)
    outroads_devpt.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1, markersize=5)
    inroads_devpl.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    outroads_devpl.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    inroads_roadcore.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    outroads_roadcore.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    awilderness.plot(ax=axis, color='none', edgecolor='black', linewidth=2.0, alpha=0.9)
    xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
    ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
    matplotlib.pyplot.suptitle(which_wilderness + '\nRemoteness from activity: Acres of wilderness away from access and travel routes and developments')
    txt = str(w_ac) + ' wilderness acres' + '\n' + str(i_ac) + ' inroads acres (' + str(i_pct) + '%)' + '\n' + str(o_ac) + ' outroads acres (' + str(o_pct) + '%)\n' + str(io_ac) + ' remote acres (' + str(io_pct) + '%)'
    matplotlib.pyplot.gcf().text(0.7, 0.89, txt, fontsize=8, fontdict=mono)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    matplotlib.pyplot.axis('off')
    fig1 = matplotlib.pyplot.gcf()
    fig1.savefig(out_dir + slug_wilderness + '-rem-all-fin.png')
    awilderness_box = awilderness_1mi.copy()
    awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
    xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
    ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
    axis.set_xlim(xlim2)
    axis.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, axis, awilderness.crs)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    fig1.savefig(out_dir + slug_wilderness + '-rem-all-fin-base.png')
    fig1.clf()
    matplotlib.pyplot.clf()
    matplotlib.pyplot.cla()
    matplotlib.pyplot.close()

    width = 27
    axis = awilderness.plot(color='none', edgecolor='black', linewidth=2.0, alpha=0.9, figsize=(width, width/1.618))
    inroads.plot(ax=axis, color=icp, edgecolor=icp, alpha=0.7)
    outroads.plot(ax=axis, color=ocp, edgecolor=ocp, alpha=0.7)
    inroads_devln.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    outroads_devln.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    inroads_devpt.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1, markersize=5)
    outroads_devpt.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1, markersize=5)
    inroads_devpl.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    outroads_devpl.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    inroads_roadcore.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    outroads_roadcore.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    awilderness.plot(ax=axis, color='none', edgecolor='black', linewidth=2.0, alpha=0.9)
    xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
    ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
    matplotlib.pyplot.suptitle(which_wilderness + '\nRemoteness from activity: Acres of wilderness away from access and travel routes and developments')
    txt = str(w_ac) + ' wilderness acres' + '\n' + str(i_ac) + ' inroads acres (' + str(i_pct) + '%)' + '\n' + str(o_ac) + ' outroads acres (' + str(o_pct) + '%)\n' + str(io_ac) + ' remote acres (' + str(io_pct) + '%)'
    matplotlib.pyplot.gcf().text(0.7, 0.89, txt, fontsize=8, fontdict=mono)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    matplotlib.pyplot.axis('off')
    fig1 = matplotlib.pyplot.gcf()
    fig1.savefig(out_dir + slug_wilderness + '-rem-all-fin-' + str(width) + 'in' + '.png')
    awilderness_box = awilderness_1mi.copy()
    awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
    xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
    ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
    axis.set_xlim(xlim2)
    axis.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, axis, awilderness.crs)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    fig1.savefig(out_dir + slug_wilderness + '-rem-all-fin-' + str(width) + 'in-base' + '.png')
    fig1.clf()
    matplotlib.pyplot.clf()
    matplotlib.pyplot.cla()
    matplotlib.pyplot.close()
