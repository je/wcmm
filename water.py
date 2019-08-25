import django
import geopandas
import json
import matplotlib

from settings import *
from utils import *

def watershed_condition(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_cea_file = slug_wilderness + '-cea.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    wcc_file = slug_wilderness + '-wcc.' + out_ext
    wcc_full_file = slug_wilderness + '-wcc-full.' + out_ext

    wcc = geopandas.read_file(wcc_gdb, layer='WatershedConditionClass')
    extra_cols = [e for e in wcc.columns if e not in ['FOREST_NAME', 'WATERSHED_CODE', 'WATERSHED_NAME', 'WATERSHED_CONDITION_FS_AREA', 'geometry', 'acres']]
    wcc = wcc.drop(columns=extra_cols)
    awilderness = geopandas.read_file(out_dir + awilderness_cea_file)
    awilderness = awilderness.to_crs(wcc.crs)
    try:
        wcc_inside = geopandas.overlay(wcc, awilderness, how='intersection')
        wcc_full = (wcc[wcc['WATERSHED_CODE'].isin(wcc_inside['WATERSHED_CODE'])])
        wcc_full.to_file(driver=out_driver, encoding='utf-8', filename=out_dir + wcc_full_file)
        log(slug_wilderness, 'GREEN', str(wcc_full_file) + ' created')
        wcc_inside = wcc_inside.to_crs({'proj':'cea'})
        wcc_inside['acres'] = wcc_inside['geometry'].area/4046.856
        wcc_inside = wcc_inside.to_crs(awilderness.crs)
        wcc_inside.to_file(driver=out_driver, encoding='utf-8', filename=out_dir + wcc_file)
        log(slug_wilderness, 'GREEN', str(wcc_file) + ' created')

        w_ac = awilderness['acres'].sum()
        ia_ac = wcc_inside.loc[wcc_inside['WATERSHED_CONDITION_FS_AREA'] == 'Functioning Properly', 'acres'].sum()
        ib_ac = wcc_inside.loc[wcc_inside['WATERSHED_CONDITION_FS_AREA'] == 'Functioning at Risk', 'acres'].sum()
        ic_ac = wcc_inside.loc[wcc_inside['WATERSHED_CONDITION_FS_AREA'] == 'Impaired Function', 'acres'].sum()
        ia_pct = '{0:.0f}'.format((ia_ac/w_ac) * 100)
        ib_pct = '{0:.0f}'.format((ib_ac/w_ac) * 100)
        ic_pct = '{0:.0f}'.format((ic_ac/w_ac) * 100)
        w_ac = '{0:.2f}'.format(w_ac)
        ia_ac = '{0:.2f}'.format(ia_ac)
        ib_ac = '{0:.2f}'.format(ib_ac)
        ic_ac = '{0:.2f}'.format(ic_ac)
        zeros = len(str(int(float(w_ac)))) - len(str(int(float(ia_ac))))
        if zeros > 0:
            space = ''
            space += ' ' * zeros
            ia_ac = space + ia_ac
        zeros = len(str(int(float(w_ac)))) - len(str(int(float(ib_ac))))
        if zeros > 0:
            space = ''
            space += ' ' * zeros
            ib_ac = space + ib_ac
        zeros = len(str(int(float(w_ac)))) - len(str(int(float(ic_ac))))
        if zeros > 0:
            space = ''
            space += ' ' * zeros
            ic_ac = space + ic_ac
        mxp = max(len(str(int(float(ia_pct)))), len(str(int(float(ib_pct)))), len(str(int(float(ic_pct)))))
        zeros = mxp - len(str(int(float(ia_pct))))
        if zeros > 0:
            space = ''
            space += ' ' * zeros
            ia_pct = space + ia_pct
        zeros = mxp - len(str(int(float(ib_pct))))
        if zeros > 0:
            space = ''
            space += ' ' * zeros
            ib_pct = space + ib_pct
        zeros = mxp - len(str(int(float(ic_pct))))
        if zeros > 0:
            space = ''
            space += ' ' * zeros
            ic_pct = space + ic_pct
        width = 13

        jsd = [{
            "w_ac": w_ac,
            "ia_ac": ia_ac,
            "ib_ac": ib_ac,
            "ic_ac": ic_ac,
            "ia_pct": ia_pct,
            "ib_pct": ib_pct,
            "ic_pct": ic_pct
            }]
        jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
        with open(out_dir + 'index-wcc.json', 'w') as static_file:
            static_file.write(jsc)

        awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
        wcc_fullc = wcc_full.copy()
        wcc_insidec = wcc_inside.copy()
        colors = {'Functioning Properly': 'green', 'Functioning at Risk': 'orange', 'Impaired Function': 'red'}

        extra_cols = [e for e in wcc_insidec.columns if e not in ['WATERSHED_CODE', 'WATERSHED_NAME', 'WATERSHED_CONDITION_FS_AREA', 'acres']]
        wcccv = wcc_insidec.drop(columns=extra_cols).rename(index=str, columns={'acres': 'acres_inside_wilderness', })
        wcccv.to_csv(out_dir + slug_wilderness +'-wcc.csv')
        axis = wcc_fullc.plot(color=[colors[i] for i in wcc_insidec['WATERSHED_CONDITION_FS_AREA']], edgecolor='white', alpha=0.2, figsize=(width, width/1.618))
        wcc_green = (wcc_insidec[wcc_insidec['WATERSHED_CONDITION_FS_AREA'] == 'Functioning Properly'])
        wcc_orange = (wcc_insidec[wcc_insidec['WATERSHED_CONDITION_FS_AREA'] == 'Functioning at Risk'])
        wcc_red = (wcc_insidec[wcc_insidec['WATERSHED_CONDITION_FS_AREA'] == 'Impaired Function'])
        if not wcc_green.empty:
            wcc_green.plot(ax=axis, color='green', edgecolor='white', alpha=0.8, legend=False)
        if not wcc_orange.empty:
            wcc_orange.plot(ax=axis, color='orange', edgecolor='white', alpha=0.8, legend=False)
        if not wcc_red.empty:
            wcc_red.plot(ax=axis, color='red', edgecolor='white', alpha=0.8, legend=False)
        awilderness.plot(ax=axis, color='none', edgecolor='black', alpha=1)

        xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
        ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
        matplotlib.pyplot.suptitle(which_wilderness + '\nEcological processes: Watershed condition class')
        txt = str(w_ac) + ' acres total wilderness area' + '\n' + str(ia_ac) + ' acres \'functioning properly\' (' + str(ia_pct) + '%)' + '\n' + str(ib_ac) + ' acres \'functioning at risk\'  (' + str(ib_pct) + '%)' + '\n' + str(ic_ac) + ' acres \'impaired function\'    (' + str(ic_pct) + '%)'
        matplotlib.pyplot.gcf().text(0.7, 0.89, txt, fontsize=8, fontdict=mono)
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        matplotlib.pyplot.axis('off')
        fig1 = matplotlib.pyplot.gcf()
        fig1.savefig(out_dir + slug_wilderness + '-wcc.png')
        awilderness_box = awilderness_1mi.copy()
        awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
        xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
        ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
        awilderness_box['geometry'] = awilderness_box.geometry.envelope
        fill = matplotlib.colors.colorConverter.to_rgba('tab:brown', alpha=0.1)
        try_add_basemap(slug_wilderness, axis, awilderness.crs)
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        fig1.savefig(out_dir + slug_wilderness + '-wcc-base.png')
        own_blm_file = slug_wilderness + '-own-blm.' + out_ext
        own_usfs_file = slug_wilderness + '-own-usfs.' + out_ext
        if os.path.exists(out_dir + own_blm_file):
            blm_inside = geopandas.read_file(out_dir + own_blm_file)
        if os.path.exists(out_dir + own_usfs_file):
            usfs_inside = geopandas.read_file(out_dir + own_usfs_file)
        bfill = matplotlib.colors.colorConverter.to_rgba('tab:brown', alpha=0.2)
        ufill = matplotlib.colors.colorConverter.to_rgba('tab:green', alpha=0.2)
        try:
            usfs_inside.plot(ax=axis, color=ufill, edgecolor='white', linewidth=2.0,)
        except:
            pass
        try:
            blm_inside.plot(ax=axis, color=bfill, edgecolor='white', linewidth=2.0,)
        except:
            pass
        fig1.savefig(out_dir + slug_wilderness + '-wcc-base-own.png')
        fig1.clf()
        matplotlib.pyplot.clf()
        matplotlib.pyplot.cla()
        matplotlib.pyplot.close()
    except KeyError:
        log(slug_wilderness, 'WHITE', 'wcc clipped empty')
        empty_file_out = out_dir + slug_wilderness + '-wcc-empty.txt'
        with open(empty_file_out, 'a'):
            os.utime(empty_file_out, None)

def impaired_waters(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    lakes_file = slug_wilderness + '-lakes.' + out_ext
    lakes_full_file = slug_wilderness + '-lakes-full.' + out_ext
    lakes_around_file = slug_wilderness + '-lakes-around.' + out_ext
    lakesb_file = slug_wilderness + '-lakesb.' + out_ext
    lakesb_full_file = slug_wilderness + '-lakesb-full.' + out_ext
    lakesb_around_file = slug_wilderness + '-lakesb-around.' + out_ext
    streams_file = slug_wilderness + '-streams.' + out_ext
    streams_full_file = slug_wilderness + '-streams-full.' + out_ext
    streams_around_file = slug_wilderness + '-streams-around.' + out_ext
    streamsb_file = slug_wilderness + '-streamsb.' + out_ext
    streamsb_full_file = slug_wilderness + '-streamsb-full.' + out_ext
    streamsb_around_file = slug_wilderness + '-streamsb-around.' + out_ext

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    lakes = geopandas.read_file(epa303d_gdb, layer='rad_303d_a')
    xmin, ymin, xmax, ymax = awilderness.total_bounds
    lakes_around = lakes.cx[xmin:xmax, ymin:ymax]
    if lakes_around.empty:
        log(slug_wilderness, 'WHITE', 'impaired lakes around empty')
        lakes_inside = geopandas.GeoDataFrame()
        lakes_inside.crs = {'init': 'epsg:4269'}
        lakes_full = geopandas.GeoDataFrame()
        lakes_full.crs = {'init': 'epsg:4269'}
        slakes = 0
    else:
        lakes_inside = geopandas.overlay(lakes_around, awilderness, how='intersection') # 303d part inside wilderness (red)
        lakes_full = (lakes[lakes['REACHCODE'].isin(lakes_inside['REACHCODE'])]) # 303d part outside (thin red)
        lakes_inside = lakes_inside.to_crs({'proj':'cea'})
        slakes = len(lakes_inside.dissolve(by='REACHCODE').index)
        lakes_inside = lakes_inside.to_crs(awilderness.crs)
        if lakes_inside.empty:
            log(slug_wilderness, 'WHITE', 'impaired lakes inside empty')
        else:
            lakes_inside.to_file(driver=out_driver, filename=out_dir + lakes_file)
            log(slug_wilderness, 'GREEN', str(lakes_file) + ' created')
            lakes_full.to_file(driver=out_driver, filename=out_dir + lakes_full_file)
            log(slug_wilderness, 'GREEN', str(lakes_full_file) + ' created')
            lakes_inside.to_csv(out_dir + slug_wilderness + '-lakes.csv')

    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    lakes2 = geopandas.read_file(epa305b_gdb, layer='rad_assd305b_a')
    lakes2_around = lakes2.cx[xmin:xmax, ymin:ymax] # nearby blue
    if lakes2_around.empty: # no blue around, set all blank
        lakes2_around_minus = lakes2_around.copy()
        lakes2_inside_minus = lakes2_around.copy()
        lakes2_full_minus = lakes2_around.copy()
        slakes2 = 0
        log(slug_wilderness, 'WHITE', 'inventoried lakes around empty')
    if lakes_around.empty and not lakes2_around.empty: # clip blue to wilderness
        lakes2_around_minus = lakes2_around.copy()
        lakes2_inside_minus = geopandas.overlay(lakes2_around_minus, awilderness, how='intersection')
        lakes2_full_minus = (lakes2_around[lakes2_around['REACHCODE'].isin(lakes2_inside_minus['REACHCODE'])]) # 305b part outside
        if not lakes2_full_minus.empty:
            lakes2_full_minus.to_file(driver=out_driver, filename=out_dir + lakesb_full_file)
            log(slug_wilderness, 'GREEN', str(lakesb_full_file) + ' created')
        lakes2_inside = geopandas.overlay(lakes2_around, awilderness, how='intersection')
        slakes2 = len(lakes2_inside.dissolve(by='REACHCODE').index)
        log(slug_wilderness, 'WHITE', 'impaired lakes inside empty')
    if lakes2_around.empty or lakes_around.empty:
        pass
    else:
        lakes2_around_minus = geopandas.overlay(lakes2_around, lakes_around, how='difference') # nearby 305b minus 303d
        if lakes2_around_minus.empty:
            lakes2_inside_minus = lakes2_around_minus.copy()
        else:
            lakes2_inside_minus = geopandas.overlay(lakes2_around_minus, awilderness, how='intersection') # 305b part inside (blue)
        lakes2_full_minus = (lakes2_around[lakes2_around['REACHCODE'].isin(lakes2_inside_minus['REACHCODE'])]) # 305b part outside (thin blue)
        if not lakes2_full_minus.empty:
            lakes2_full_minus.to_file(driver=out_driver, filename=out_dir + lakesb_full_file)
            log(slug_wilderness, 'GREEN', str(lakesb_full_file) + ' created')
        lakes2_inside_minus = lakes2_inside_minus.to_crs({'proj':'cea'})
        lakes2_inside = geopandas.overlay(lakes2_around, awilderness, how='intersection')
        lakes2_inside = lakes2_inside.to_crs({'proj':'cea'})

        if lakes2_inside.empty:
            log(slug_wilderness, 'WHITE', 'inventoried lakes inside empty')
        else:
            lakes2_inside.to_file(driver=out_driver, filename=out_dir + lakesb_file)
            log(slug_wilderness, 'GREEN', str(lakesb_file) + ' created')

        slakes2 = len(lakes2_inside.dissolve(by='REACHCODE').index)
        lakes2_inside = lakes2_inside.to_crs(awilderness.crs)
        lakes2_inside_minus = lakes2_inside_minus.to_crs(awilderness.crs)

    streamsd = geopandas.read_file(epa303d_gdb, layer='rad_303d_l')
    streams_around = streamsd.cx[xmin:xmax, ymin:ymax]
    if streams_around.empty:
        log(slug_wilderness, 'WHITE', 'impaired streams empty')
    else:
        streams_around.to_file(driver=out_driver, filename=out_dir + streams_around_file)
        log(slug_wilderness, 'GREEN', str(streams_around_file) + ' created')

    if lakes_around.empty:
        streams = streams_around
    else:
        lakes_around.to_file(driver=out_driver, filename=out_dir + lakes_around_file)
        log(slug_wilderness, 'GREEN', str(lakes_around_file) + ' created')
        mask = geopandas.overlay(awilderness, lakes_around, how='difference')
        if mask.empty or streams_around.empty:
            print('mask or streams empty')
            streams = streams_around
        else:
            mask.to_file(driver=out_driver, filename=out_dir + 'si_mask.shp')
            log(slug_wilderness, 'WHITE', 'streams to mask')
            streams = lines_poly(streams_around, mask)
            streams['gt'] = streams['geometry'].geom_type
            for index, row in streams.iterrows():
                if row['gt'] in ['GeometryCollection']:
                    for g in row['geometry']:
                        newrow = row
                        newrow['geometry'] = g
                        newrow['gt'] = newrow['geometry'].geom_type
                        streams = streams.append(newrow, ignore_index=True)
            streams = streams[streams['gt'].isin(['LineString', 'MultiLineString'])]
            if streams.empty:
                log(slug_wilderness, 'WHITE', 'masked streams empty')
            else:
                streams.to_file(driver=out_driver, filename=out_dir + 'si_masked.shp')

    if streams.empty:
        log(slug_wilderness, 'WHITE', 'streams empty')
        streams_inside = streams
    else:
        log(slug_wilderness, 'WHITE', 'streams to wilderness')
        streams_inside = lines_poly(streams, awilderness)
        streams_inside['gt'] = streams_inside['geometry'].geom_type
        for index, row in streams_inside.iterrows():
            if row['gt'] in ['GeometryCollection']:
                for g in row['geometry']:
                    newrow = row
                    newrow['geometry'] = g
                    newrow['gt'] = newrow['geometry'].geom_type
                    streams_inside = streams_inside.append(newrow, ignore_index=True)
        streams_inside = streams_inside[streams_inside['gt'].isin(['LineString', 'MultiLineString'])]
        if streams_inside.empty:
            log(slug_wilderness, 'WHITE', 'streams inside empty')
        else:
            streams_inside.to_file(driver=out_driver, filename=out_dir + 'si_inside.shp')

    streams_full = streams.copy()
    streams_full = (streams_full[streams_full['REACHCODE'].isin(streams_inside['REACHCODE'])])
    streams_full['gt'] = streams_full['geometry'].geom_type
    streams_full = streams_full[streams_full['gt'].isin(['LineString', 'MultiLineString'])]
    streams_inside = streams_inside.to_crs({'proj':'cea'})
    streams_inside['miles'] = streams_inside['geometry'].length/1609.344
    smiles = streams_inside['miles'].sum()
    smiles = '{0:.2f}'.format(smiles)
    streams_inside = streams_inside.to_crs(awilderness.crs)
    streams_inside['gt'] = streams_inside['geometry'].geom_type
    streams_inside = streams_inside[streams_inside['gt'].isin(['LineString', 'MultiLineString'])]

    if streams_inside.empty:
        log(slug_wilderness, 'WHITE', 'streams empty')
    else:
        streams_inside.to_file(driver=out_driver, filename=out_dir + streams_file)
        log(slug_wilderness, 'GREEN', str(streams_file) + ' created')
        streams_full.to_file(driver=out_driver, filename=out_dir + streams_full_file)
        log(slug_wilderness, 'GREEN', str(streams_full_file) + ' created')
        streams_inside.to_csv(out_dir + slug_wilderness + '-streams.csv')

    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)

    streams2 = geopandas.read_file(epa305b_gdb, layer='rad_assd305b_l')
    if streams.empty:
        streams_in = streams
    else:
        streams_in = lines_poly(streams, awilderness)
    if lakes_inside.empty:
        streams_inside = streams_in
    else:
        mask = geopandas.overlay(awilderness, lakes_inside, how='difference')
        if mask.empty or streams_in.empty:
            streams_inside = streams
        else:
            streams_inside = lines_poly(streams_in, mask)

    streams2_around = streams2.cx[xmin:xmax, ymin:ymax]
    if lakes2_around.empty:
        pass
    else:
        lakes2_around.to_file(driver=out_driver, filename=out_dir + lakesb_around_file)
        log(slug_wilderness, 'GREEN', str(lakesb_around_file) + ' created')
        wenv = awilderness.envelope
        wenvf = geopandas.GeoDataFrame(geopandas.GeoSeries(wenv), columns=['geometry'])
        mask = geopandas.overlay(wenvf, lakes2_around, how='difference')
        if mask.empty or streams2_around.empty:
            pass
        else:
            streams2_around = lines_poly(streams2_around, mask)
    streams2_around['gt'] = streams2_around['geometry'].geom_type
    streams2_around = streams2_around[streams2_around['gt'].isin(['LineString', 'MultiLineString'])]
    if not streams2_around.empty:
        streams2_around.to_file(driver=out_driver, filename=out_dir + streamsb_around_file)
        log(slug_wilderness, 'GREEN', str(streamsb_around_file) + ' created')
    streams_inside['gt'] = streams_inside['geometry'].geom_type
    streams_inside = streams_inside[streams_inside['gt'].isin(['LineString', 'MultiLineString'])]
    streams_full['gt'] = streams_full['geometry'].geom_type
    streams_full = streams_full[streams_full['gt'].isin(['LineString', 'MultiLineString'])]
    if streams2_around.empty:
        streams2_inside = streams2_around.copy()
    else:
        streams2_inside = lines_poly(streams2_around, awilderness)
    streams2_inside['gt'] = streams2_inside['geometry'].geom_type
    streams2_inside = streams2_inside[streams2_inside['gt'].isin(['LineString', 'MultiLineString'])]
    streams2_full = streams2_around.copy()
    streams2_full = (streams2_full[streams2_full['REACHCODE'].isin(streams2_inside['REACHCODE'])])
    streams2_full['gt'] = streams2_full['geometry'].geom_type
    streams2_full = streams2_full[streams2_full['gt'].isin(['LineString', 'MultiLineString'])]
    if not streams2_full.empty:
        streams2_full.to_file(driver=out_driver, filename=out_dir + streamsb_full_file)
        log(slug_wilderness, 'GREEN', str(streamsb_full_file) + ' created')
    streams2_inside = streams2_inside.to_crs({'proj':'cea'})
    streams2_inside['miles'] = streams2_inside['geometry'].length/1609.344
    smiles2 = streams2_inside['miles'].sum()
    smiles2 = '{0:.2f}'.format(smiles2)
    streams2_inside = streams2_inside.to_crs(awilderness.crs)
    if not streams2_inside.empty:
        streams2_inside.to_file(driver=out_driver, filename=out_dir + streamsb_file)
        log(slug_wilderness, 'GREEN', str(streamsb_file) + ' created')

    jsd = [{
        "smiles": smiles,
        "smiles2": smiles2,
        "slakes": slakes,
        "slakes2": slakes2
        }]
    jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
    with open(out_dir + 'index-iw.json', 'w') as static_file:
        static_file.write(jsc)

def impaired_waters_plots(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    lakes_file = slug_wilderness + '-lakes.' + out_ext
    lakes_full_file = slug_wilderness + '-lakes-full.' + out_ext
    lakes_around_file = slug_wilderness + '-lakes-around.' + out_ext
    lakesb_file = slug_wilderness + '-lakesb.' + out_ext
    lakesb_full_file = slug_wilderness + '-lakesb-full.' + out_ext
    lakesb_around_file = slug_wilderness + '-lakesb-around.' + out_ext
    streams_file = slug_wilderness + '-streams.' + out_ext
    streams_full_file = slug_wilderness + '-streams-full.' + out_ext
    streams_around_file = slug_wilderness + '-streams-around.' + out_ext
    streamsb_file = slug_wilderness + '-streamsb.' + out_ext
    streamsb_full_file = slug_wilderness + '-streamsb-full.' + out_ext
    streamsb_around_file = slug_wilderness + '-streamsb-around.' + out_ext

    with open(out_dir + 'index-iw.json') as jsf:
        data = json.load(jsf)

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    if os.path.exists(out_dir + lakesb_around_file):
        lakes2_around = geopandas.read_file(out_dir + lakesb_around_file)
    if os.path.exists(out_dir + lakesb_full_file):
        lakes2_full_minus = geopandas.read_file(out_dir + lakesb_full_file)
    if os.path.exists(out_dir + lakesb_file):
        lakes2_inside = geopandas.read_file(out_dir + lakesb_file)
    if os.path.exists(out_dir + lakes_around_file):
        lakes_around = geopandas.read_file(out_dir + lakes_around_file)
    if os.path.exists(out_dir + lakes_full_file):
        lakes_full = geopandas.read_file(out_dir + lakes_full_file)
    if os.path.exists(out_dir + lakes_file):
        lakes_inside = geopandas.read_file(out_dir + lakes_file)

    width = 13
    axis = awilderness_1mi.plot(color='none', edgecolor='none', alpha=0.0, figsize=(width, width/1.618))
    try:
        lakes2_around.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.2)
    except:
        pass
    try:
        lakes2_full_minus.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.2)
    except:
        pass
    try:
        lakes2_inside_minus.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.9)
    except:
        pass
    try:
        lakes_around.plot(ax=axis, color='red', edgecolor='red', alpha=0.4)
    except:
        pass
    try:
        lakes_full.plot(ax=axis, color='red', edgecolor='red', alpha=0.4)
    except:
        pass
    try:
        lakes_inside.plot(ax=axis, color='red', edgecolor='red', alpha=0.9)
    except:
        pass

    awilderness.plot(ax=axis, color='none', edgecolor='black', alpha=1)
    xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
    ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
    matplotlib.pyplot.suptitle(which_wilderness + '\nAir and water: Extent of waterbodies with impaired water quality')
    txt = str(data['slakes']) + ' impaired lakes of ' + str(data['slakes2']) + ' inventoried lakes'
    matplotlib.pyplot.gcf().text(0.65, 0.9, txt, fontsize=8, fontdict=mono)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    matplotlib.pyplot.axis('off')
    fig1 = matplotlib.pyplot.gcf()
    fig1.savefig(out_dir + slug_wilderness + '-lakes.png')
    log(slug_wilderness, 'GREEN', str(slug_wilderness) + '-lakes.png created')
    awilderness_box = awilderness_1mi.copy()
    awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
    xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
    ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
    axis.set_xlim(xlim2)
    axis.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, axis, awilderness.crs)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    fig1.savefig(out_dir + slug_wilderness + '-lakes-base.png')
    log(slug_wilderness, 'GREEN', str(slug_wilderness) + '-lakes-base.png created')
    own_blm_file = slug_wilderness + '-own-blm.' + out_ext
    own_usfs_file = slug_wilderness + '-own-usfs.' + out_ext
    if os.path.exists(out_dir + own_blm_file):
        blm_inside = geopandas.read_file(out_dir + own_blm_file)
    if os.path.exists(out_dir + own_usfs_file):
        usfs_inside = geopandas.read_file(out_dir + own_usfs_file)
    bfill = matplotlib.colors.colorConverter.to_rgba('tab:brown', alpha=0.2)
    ufill = matplotlib.colors.colorConverter.to_rgba('tab:green', alpha=0.2)
    try:
        usfs_inside.plot(ax=axis, color=ufill, edgecolor='white', linewidth=2.0,)
    except:
        pass
    try:
        blm_inside.plot(ax=axis, color=bfill, edgecolor='white', linewidth=2.0,)
    except:
        pass
    fig1.savefig(out_dir + slug_wilderness + '-lakes-base-own.png')
    log(slug_wilderness, 'GREEN', str(slug_wilderness) + '-lakes-base-own.png created')
    fig1.clf()
    matplotlib.pyplot.clf()
    matplotlib.pyplot.cla()
    matplotlib.pyplot.close()

    if os.path.exists(out_dir + streamsb_around_file):
        streams2_around = geopandas.read_file(out_dir + streamsb_around_file)
    if os.path.exists(out_dir + streamsb_full_file):
        streams2_full = geopandas.read_file(out_dir + streamsb_full_file)
    if os.path.exists(out_dir + streamsb_file):
        streams2_inside = geopandas.read_file(out_dir + streamsb_file)
    if os.path.exists(out_dir + streams_around_file):
        streams_around = geopandas.read_file(out_dir + streams_around_file)
    if os.path.exists(out_dir + streams_full_file):
        streams_full = geopandas.read_file(out_dir + streams_full_file)
    if os.path.exists(out_dir + streams_file):
        streams_inside = geopandas.read_file(out_dir + streams_file)

    axis = awilderness_1mi.plot(color='none', edgecolor='none', alpha=0.0, figsize=(width, width/1.618))
    try:
        streams2_around.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.2)
    except:
        pass
    try:
        streams2_full.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.2)
    except:
        pass
    try:
        streams2_inside.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.9, legend=False)
    except:
        pass
    try:
        streams_around.plot(ax=axis, color='red', edgecolor='red', alpha=0.4)
    except:
        pass
    try:
        streams_full.plot(ax=axis, color='red', edgecolor='red', alpha=0.4)
    except:
        pass
    try:
        streams_inside.plot(ax=axis, color='red', edgecolor='red', alpha=0.9, legend=False)
    except:
        pass
    awilderness.plot(ax=axis, color='none', edgecolor='black', alpha=1)
    xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
    ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
    matplotlib.pyplot.suptitle(which_wilderness + '\nAir and water: Extent of waterbodies with impaired water quality')
    txt = str(data['smiles']) + ' miles impaired streams of ' + str(data['smiles2']) + ' miles inventoried streams'
    matplotlib.pyplot.gcf().text(0.65, 0.9, txt, fontsize=8, fontdict=mono)

    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    matplotlib.pyplot.axis('off')
    fig1 = matplotlib.pyplot.gcf()
    fig1.savefig(out_dir + slug_wilderness + '-streams.png')
    log(slug_wilderness, 'GREEN', str(slug_wilderness) + '-streams.png created')
    awilderness_box = awilderness_1mi.copy()
    awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
    xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
    ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
    axis.set_xlim(xlim2)
    axis.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, axis, awilderness.crs)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    fig1.savefig(out_dir + slug_wilderness + '-streams-base.png')
    log(slug_wilderness, 'GREEN', str(slug_wilderness) + '-streams-base.png created')
    own_blm_file = slug_wilderness + '-own-blm.' + out_ext
    own_usfs_file = slug_wilderness + '-own-usfs.' + out_ext
    if os.path.exists(out_dir + own_blm_file):
        blm_inside = geopandas.read_file(out_dir + own_blm_file)
    if os.path.exists(out_dir + own_usfs_file):
        usfs_inside = geopandas.read_file(out_dir + own_usfs_file)
    bfill = matplotlib.colors.colorConverter.to_rgba('tab:brown', alpha=0.2)
    ufill = matplotlib.colors.colorConverter.to_rgba('tab:green', alpha=0.2)
    try:
        usfs_inside.plot(ax=axis, color=ufill, edgecolor='white', linewidth=2.0,)
    except:
        pass
    try:
        blm_inside.plot(ax=axis, color=bfill, edgecolor='white', linewidth=2.0,)
    except:
        pass
    fig1.savefig(out_dir + slug_wilderness + '-streams-base-own.png')
    log(slug_wilderness, 'GREEN', str(slug_wilderness) + '-streams-base-own.png created')
    fig1.clf()
    matplotlib.pyplot.clf()
    matplotlib.pyplot.cla()
    matplotlib.pyplot.close()

    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    axis = awilderness_1mi.plot(color='none', edgecolor='none', alpha=0.0, figsize=(width, width/1.618))
    try:
        lakes2_around.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.2)
    except:
        pass
    try:
        lakes2_full_minus.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.2)
    except:
        pass
    try:
        lakes2_inside_minus.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.9)
    except:
        pass
    try:
        lakes_full.plot(ax=axis, color='red', edgecolor='red', alpha=0.4)
    except:
        pass
    try:
        lakes_inside.plot(ax=axis, color='red', edgecolor='red', alpha=0.9)
    except:
        pass
    try:
        streams2_around.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.2)
    except:
        pass
    try:
        streams2_full.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.2)
    except:
        pass
    try:
        streams2_inside.plot(ax=axis, color='blue', edgecolor='blue', alpha=0.9, legend=False)
    except:
        pass
    try:
        streams_around.plot(ax=axis, color='red', edgecolor='red', alpha=0.4)
    except:
        pass
    try:
        streams_full.plot(ax=axis, color='red', edgecolor='red', alpha=0.4)
    except:
        pass
    try:
        streams_inside.plot(ax=axis, color='red', edgecolor='red', alpha=0.9, legend=False)
    except:
        pass
    awilderness.plot(ax=axis, color='none', edgecolor='black', alpha=1)
    xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
    ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
    matplotlib.pyplot.suptitle(which_wilderness + '\nAir and water: Extent of waterbodies with impaired water quality')
    txt = str(data['smiles']) + ' miles impaired streams of ' + str(data['smiles2']) + ' miles inventoried streams\n' + str(data['slakes']) + ' impaired lakes of ' + str(data['slakes2']) + ' inventoried lakes'
    matplotlib.pyplot.gcf().text(0.65, 0.9, txt, fontsize=8, fontdict=mono)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    matplotlib.pyplot.axis('off')
    fig1 = matplotlib.pyplot.gcf()
    fig1.savefig(out_dir + slug_wilderness + '-303d.png')
    log(slug_wilderness, 'GREEN', str(slug_wilderness) + '-303d.png created')
    awilderness_box = awilderness_1mi.copy()
    awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
    xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
    ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
    axis.set_xlim(xlim2)
    axis.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, axis, awilderness.crs)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    fig1.savefig(out_dir + slug_wilderness + '-303d-base.png')
    own_blm_file = slug_wilderness + '-own-blm.' + out_ext
    own_usfs_file = slug_wilderness + '-own-usfs.' + out_ext
    if os.path.exists(out_dir + own_blm_file):
        blm_inside = geopandas.read_file(out_dir + own_blm_file)
    if os.path.exists(out_dir + own_usfs_file):
        usfs_inside = geopandas.read_file(out_dir + own_usfs_file)
    bfill = matplotlib.colors.colorConverter.to_rgba('tab:brown', alpha=0.2)
    ufill = matplotlib.colors.colorConverter.to_rgba('tab:green', alpha=0.2)
    try:
        usfs_inside.plot(ax=axis, color=ufill, edgecolor='white', linewidth=2.0,)
    except:
        pass
    try:
        blm_inside.plot(ax=axis, color=bfill, edgecolor='white', linewidth=2.0,)
    except:
        pass
    fig1.savefig(out_dir + slug_wilderness + '-303d-base-own.png')
    log(slug_wilderness, 'GREEN', str(slug_wilderness) + '-303d-base-own.png created')
    fig1.clf()
    matplotlib.pyplot.clf()
    matplotlib.pyplot.cla()
    matplotlib.pyplot.close()
