import geopandas

from settings import *
from utils import *

def grazing_allotments(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_cea_file = slug_wilderness + '-cea.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    grazing_file = slug_wilderness + '-grazing.' + out_ext
    grazing_full_file = slug_wilderness + '-grazing-full.' + out_ext

    grazing = geopandas.read_file(grazing_gdb, layer='Allotment')
    extra_cols = [e for e in grazing.columns if e not in ['MANAGING_ORG_NAME', 'ALLOTMENT_NUM', 'ALLOTMENT_NAME', 'ALLOTMENT_STATUS', 'geometry', 'acres']]
    grazing = grazing.drop(columns=extra_cols)
    grazing['gt'] = grazing['geometry'].geom_type
    grazing = grazing.loc[grazing['gt'].isin(['Polygon', 'MultiPolygon'])]
    awilderness = geopandas.read_file(out_dir + awilderness_cea_file)
    awilderness = awilderness.to_crs(grazing.crs)
    try:
        grazing_inside = geopandas.overlay(grazing, awilderness, how='intersection')
        grazing_full = (grazing[grazing['ALLOTMENT_NUM'].isin(grazing_inside['ALLOTMENT_NUM'])])
        grazing_full.to_file(driver=out_driver, encoding='utf-8', filename=out_dir + grazing_full_file)
        log(slug_wilderness, 'GREEN', str(grazing_full_file) + ' created')
        grazing_inside = grazing_inside.to_crs({'proj':'cea'})
        grazing_inside['acres'] = grazing_inside['geometry'].area/4046.856
        grazing_inside = grazing_inside.to_crs(awilderness.crs)
        grazing_inside.to_file(driver=out_driver, encoding='utf-8', filename=out_dir + grazing_file)
        log(slug_wilderness, 'GREEN', str(grazing_file) + ' created')

        w_ac = awilderness['acres'].sum()
        ia_ac = grazing_inside.loc[grazing_inside['ALLOTMENT_STATUS'] == 'ACTIVE', 'acres'].sum()
        ib_ac = grazing_inside.loc[grazing_inside['ALLOTMENT_STATUS'] == 'VACANT', 'acres'].sum()
        ic_ac = grazing_inside.loc[grazing_inside['ALLOTMENT_STATUS'] == 'CLOSED', 'acres'].sum()
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
        with open(out_dir + 'index-grazing.json', 'w') as static_file:
            static_file.write(jsc)

        awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
        grazing_fullc = grazing_full.copy()
        grazing_insidec = grazing_inside.copy()
        colors = {'ACTIVE': 'green', 'VACANT': 'orange', 'CLOSED': 'red'}

        extra_cols = [e for e in grazing_insidec.columns if e not in ['MANAGING_ORG_NAME', 'ALLOTMENT_NUM', 'ALLOTMENT_NAME', 'ALLOTMENT_STATUS', 'geometry', 'acres']]
        grazingcv = grazing_insidec.drop(columns=extra_cols).rename(index=str, columns={'acres': 'acres_inside_wilderness', })
        grazingcv.to_csv(out_dir + slug_wilderness +'-grazing.csv')
        axis = grazing_fullc.plot(color=[colors[i] for i in grazing_insidec['ALLOTMENT_STATUS']], edgecolor='white', alpha=0.2, figsize=(width, width/1.618))
        grazing_green = (grazing_insidec[grazing_insidec['ALLOTMENT_STATUS'] == 'ACTIVE'])
        grazing_orange = (grazing_insidec[grazing_insidec['ALLOTMENT_STATUS'] == 'VACANT'])
        grazing_red = (grazing_insidec[grazing_insidec['ALLOTMENT_STATUS'] == 'CLOSED'])
        if not grazing_green.empty:
            grazing_green.plot(ax=axis, color='green', edgecolor='white', alpha=0.8, legend=False)
        if not grazing_orange.empty:
            grazing_orange.plot(ax=axis, color='orange', edgecolor='white', alpha=0.8, legend=False)
        if not grazing_red.empty:
            grazing_red.plot(ax=axis, color='red', edgecolor='white', alpha=0.8, legend=False)
        awilderness.plot(ax=axis, color='none', edgecolor='black', alpha=1)

        xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
        ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
        matplotlib.pyplot.suptitle(which_wilderness + '\nSupplemental: Grazing allotments')
        txt = str(w_ac) + ' acres total wilderness area' + '\n' + str(ia_ac) + ' acres \'ACTIVE\'  (' + str(ia_pct) + '%)' + '\n' + str(ib_ac) + ' acres \'VACANT\'  (' + str(ib_pct) + '%)' + '\n' + str(ic_ac) + ' acres \'CLOSED\'  (' + str(ic_pct) + '%)'
        matplotlib.pyplot.gcf().text(0.7, 0.89, txt, fontsize=8, fontdict=mono)
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        matplotlib.pyplot.axis('off')
        fig1 = matplotlib.pyplot.gcf()
        fig1.savefig(out_dir + slug_wilderness + '-grazing.png')
        awilderness_box = awilderness_1mi.copy()
        awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
        xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
        ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
        awilderness_box['geometry'] = awilderness_box.geometry.envelope
        fill = matplotlib.colors.colorConverter.to_rgba('tab:brown', alpha=0.1)
        try_add_basemap(slug_wilderness, axis, awilderness.crs)
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        fig1.savefig(out_dir + slug_wilderness + '-grazing-base.png')
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
        fig1.savefig(out_dir + slug_wilderness + '-grazing-base-own.png')
        fig1.clf()
        matplotlib.pyplot.clf()
        matplotlib.pyplot.cla()
        matplotlib.pyplot.close()
    except KeyError:
        log(slug_wilderness, 'WHITE', 'grazing clipped empty')
        empty_file_out = out_dir + slug_wilderness + '-grazing-empty.txt'
        with open(empty_file_out, 'a'):
            os.utime(empty_file_out, None)

def cmap_colors():
    from pylab import cm
    cmap = cm.get_cmap('cividis', 9)
    for i in range(cmap.N):
        rgb = cmap(i)[:3]
        print(matplotlib.colors.rgb2hex(rgb))

def wilderness_dams(): # special for sandeno
    dams_shp = 'C:\\_\\cda_data_nat\\S_USA_DAM.shp'
    dams_wilderness_file = 'dams-wilderness.' + out_ext
    dams_wilderness_csv = 'dams-wilderness.csv'

    wilderness = geopandas.read_file(wilderness_gdb)
    dams = geopandas.read_file(dams_shp)
    damsnotnull = dams[dams['geometry'].notnull()]
    extra_cols = [e for e in wilderness.columns if e not in ['WILDERNESSNAME', 'geometry',]]
    wilderness = wilderness.drop(columns=extra_cols)
    dams_wilderness = geopandas.sjoin(damsnotnull, wilderness, how='left', op='within')
    #dams_wilderness = dams_wilderness[dams_wilderness['WILDERNESSNAME'].notnull()]
    dams_wilderness = dams_wilderness.drop(columns=['index_right'])
    dams_wilderness.to_file(driver=out_driver, filename=base_dir + dams_wilderness_file)
    dams_wilderness = dams_wilderness.drop(columns=['geometry'])
    dams_wilderness.to_csv(base_dir + dams_wilderness_csv)

def ownermaps(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_cea_file = slug_wilderness + '-cea.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    own_blm_file = slug_wilderness + '-own-blm.' + out_ext
    own_usfs_file = slug_wilderness + '-own-usfs.' + out_ext

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

    blm_agy_shp = 'C:\\_\\cda_data_nat\\blm_agency.shp'
    if not os.path.exists(base_dir + 'blm_blm.' + out_ext):
        log(slug_wilderness, 'WHITE', 'blm_agy_shp reading')
        blm_agy = geopandas.read_file(blm_agy_shp)
        log(slug_wilderness, 'WHITE', 'blm_agy_shp read')

        blm_blm = blm_agy[blm_agy['ADMIN_AGEN'] == 'BLM']
        blm_blm = blm_blm.to_crs(epsg=4269)
        log(slug_wilderness, 'GREEN', 'blm_blm writing')
        blm_blm.to_file(driver=out_driver, filename=base_dir + 'blm_blm.' + out_ext)
        blm_usfs = blm_agy[blm_agy['ADMIN_AGEN'] == 'USFS']
        blm_usfs = blm_usfs.to_crs(epsg=4269)
        log(slug_wilderness, 'GREEN', 'blm_usfs writing')
        blm_usfs.to_file(driver=out_driver, filename=base_dir + 'blm_usfs.' + out_ext)

    awilderness = geopandas.read_file(out_dir + awilderness_cea_file)
    awilderness = awilderness.to_crs(epsg=4269)
    if os.path.exists(out_dir + own_blm_file):
        blm_inside = geopandas.read_file(out_dir + own_blm_file)
        blm_ac = blm_inside['acres'].sum()
        log(slug_wilderness, 'CYAN', str(own_blm_file) + ' already exists')
    else:
        blm_blm = geopandas.read_file(base_dir + 'blm_blm.' + out_ext)
        try:
            blm_inside = geopandas.overlay(blm_blm, awilderness, how='intersection')
            blm_inside = blm_inside.to_crs({'proj':'cea'})
            blm_inside['acres'] = blm_inside['geometry'].area/4046.856
            blm_inside = blm_inside.to_crs(awilderness.crs)
            blm_inside.to_file(driver=out_driver, encoding='utf-8', filename=out_dir + own_blm_file)
            blm_ac = blm_inside['acres'].sum()
            log(slug_wilderness, 'GREEN', str(own_blm_file) + ' created')
        except Exception:
            blm_ac = 0
            log(slug_wilderness, 'white', str(own_blm_file) + ' empty')
    if os.path.exists(out_dir + own_usfs_file):
        usfs_inside = geopandas.read_file(out_dir + own_usfs_file)
        usfs_ac = usfs_inside['acres'].sum()
        log(slug_wilderness, 'CYAN', str(own_usfs_file) + ' already exists')
    else:
        blm_usfs = geopandas.read_file(base_dir + 'blm_usfs.' + out_ext)
        try:
            usfs_inside = geopandas.overlay(blm_usfs, awilderness, how='intersection')
            usfs_inside = usfs_inside.to_crs({'proj':'cea'})
            usfs_inside['acres'] = usfs_inside['geometry'].area/4046.856
            usfs_inside = usfs_inside.to_crs(awilderness.crs)
            usfs_inside.to_file(driver=out_driver, encoding='utf-8', filename=out_dir + own_usfs_file)
            log(slug_wilderness, 'GREEN', str(own_usfs_file) + ' created')
            usfs_ac = usfs_inside['acres'].sum()
        except Exception:
            usfs_ac = 0
            log(slug_wilderness, 'white', str(own_usfs_file) + ' empty')

    w_ac = awilderness['acres'].sum()
    blm_pct = '{0:.0f}'.format((blm_ac/w_ac) * 100)
    usfs_pct = '{0:.0f}'.format((usfs_ac/w_ac) * 100)
    w_ac = '{0:.2f}'.format(w_ac)
    b_ac = '{0:.2f}'.format(blm_ac)
    u_ac = '{0:.2f}'.format(usfs_ac)
    zeros = len(str(int(float(w_ac)))) - len(str(int(float(b_ac))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        b_ac = space + b_ac
    zeros = len(str(int(float(w_ac)))) - len(str(int(float(u_ac))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        u_ac = space + u_ac
    mxp = max(len(str(int(float(blm_pct)))), len(str(int(float(usfs_pct)))))
    zeros = mxp - len(str(int(float(blm_pct))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        blm_pct = space + blm_pct
    zeros = mxp - len(str(int(float(usfs_pct))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        usfs_pct = space + usfs_pct
    width = 13

    icp = 'tab:pink'
    ocp = 'tab:cyan'

    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)

    axis = awilderness.plot(color='none', edgecolor='black', linewidth=2.0, alpha=0.9, figsize=(width, width/1.618))
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
    awilderness.plot(ax=axis, color='none', edgecolor='black', linewidth=2.0, alpha=0.9)
    xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
    ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    matplotlib.pyplot.suptitle(which_wilderness + '\nBLM and USFS Ownership')
    txt = str(w_ac) + ' wilderness acres' + '\n' + str(b_ac) + ' blm acres  (' + str(blm_pct) + '%)' + '\n' + str(u_ac) + ' usfs acres (' + str(usfs_pct) + '%)'
    matplotlib.pyplot.gcf().text(0.8, 0.9, txt, fontsize=8, fontdict=mono)
    matplotlib.pyplot.axis('off')
    matplotlib.pyplot.savefig(out_dir + slug_wilderness + '-own.png')
    awilderness_box = awilderness_1mi.copy()
    awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
    xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
    ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
    axis.set_xlim(xlim2)
    axis.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, axis, awilderness.crs)
    matplotlib.pyplot.savefig(out_dir + slug_wilderness + '-own-base-x2.png')
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)

    fig1 = matplotlib.pyplot.gcf()
    fig1.savefig(out_dir + slug_wilderness + '-own-base-x1.png')
    fig1.clf()
    matplotlib.pyplot.clf()
    matplotlib.pyplot.cla()
    matplotlib.pyplot.close()
    quit()

    if os.path.exists(out_dir + inroads_file):
        inroads = geopandas.read_file(out_dir + inroads_file)
    else:
        inroads = geopandas.GeoDataFrame()
        inroads['geometry'] = None
        inroads['acres'] = inroads['geometry'].area/4046.856
        inroads.crs = depsg
    inroads = inroads.to_crs(epsg=4269)
    try:
        blm_inroads = geopandas.overlay(inroads, blm_inside, how='intersection')
        blm_inroads = blm_inroads.to_crs({'proj':'cea'})
        blm_inroads['acres'] = blm_inroads['geometry'].area/4046.856
        blm_inroads = blm_inroads.to_crs(awilderness.crs)
        blm_inroads_ac = blm_inroads['acres'].sum()
    except Exception:
        blm_inroads_ac = 0
    try:
        usfs_inroads = geopandas.overlay(inroads, usfs_inside, how='intersection')
        usfs_inroads = usfs_inroads.to_crs({'proj':'cea'})
        usfs_inroads['acres'] = usfs_inroads['geometry'].area/4046.856
        usfs_inroads = usfs_inroads.to_crs(awilderness.crs)
        usfs_inroads_ac = usfs_inroads['acres'].sum()
    except Exception:
        usfs_inroads_ac = 0

    if os.path.exists(out_dir + outroads_file):
        outroads = geopandas.read_file(out_dir + outroads_file)
    else:
        outroads = geopandas.GeoDataFrame()
        outroads['geometry'] = None
        outroads['acres'] = outroads['geometry'].area/4046.856
        outroads.crs = depsg
    outroads = outroads.to_crs(epsg=4269)
    try:
        blm_outroads = geopandas.overlay(outroads, blm_inside, how='intersection')
        blm_outroads = blm_outroads.to_crs({'proj':'cea'})
        blm_outroads['acres'] = blm_outroads['geometry'].area/4046.856
        blm_outroads = blm_outroads.to_crs(awilderness.crs)
        blm_outroads_ac = blm_outroads['acres'].sum()
    except Exception:
        blm_outroads_ac = 0
    try:
        usfs_outroads = geopandas.overlay(outroads, usfs_inside, how='intersection')
        usfs_outroads = usfs_outroads.to_crs({'proj':'cea'})
        usfs_outroads['acres'] = usfs_outroads['geometry'].area/4046.856
        usfs_outroads = usfs_outroads.to_crs(awilderness.crs)
        usfs_outroads_ac = usfs_outroads['acres'].sum()
    except Exception:
        usfs_outroads_ac = 0

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


    i_ac = inroads['acres'].sum()
    o_ac = outroads['acres'].sum()
    i_pct = '{0:.0f}'.format((i_ac/float(w_ac)) * 100)
    o_pct = '{0:.0f}'.format((o_ac/float(w_ac)) * 100)
    i_ac = '{0:.2f}'.format(i_ac)
    o_ac = '{0:.2f}'.format(o_ac)

    if blm_ac == 0:
        bi_pct = 0
        bo_pct = 0
    else:
        bi_pct = '{0:.0f}'.format((blm_inroads_ac/blm_ac) * 100)
        bo_pct = '{0:.0f}'.format((blm_outroads_ac/blm_ac) * 100)
    b_ac = '{0:.2f}'.format(blm_ac)
    bi_ac = '{0:.2f}'.format(blm_inroads_ac)
    bo_ac = '{0:.2f}'.format(blm_outroads_ac)
    if usfs_ac == 0:
        ui_pct = 0
        uo_pct = 0
    else:
        ui_pct = '{0:.0f}'.format((usfs_inroads_ac/usfs_ac) * 100)
        uo_pct = '{0:.0f}'.format((usfs_outroads_ac/usfs_ac) * 100)
    u_ac = '{0:.2f}'.format(usfs_ac)
    ui_ac = '{0:.2f}'.format(usfs_inroads_ac)
    uo_ac = '{0:.2f}'.format(usfs_outroads_ac)

    axis = awilderness.plot(color='none', edgecolor='black', linewidth=2.0, alpha=0.9, figsize=(width, width/1.618))
    try:
        usfs_inside.plot(ax=axis, color=ufill, edgecolor='white', linewidth=2.0,)
    except:
        pass
    try:
        blm_inside.plot(ax=axis, color=bfill, edgecolor='white', linewidth=2.0,)
    except:
        pass

    inroads.plot(ax=axis, color=icp, edgecolor=icp, alpha=0.7)
    inroads_devln.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    inroads_devpt.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1, markersize=5)
    inroads_devpl.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    inroads_roadcore.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    awilderness.plot(ax=axis, color='none', edgecolor='black', linewidth=2.0, alpha=0.9)
    xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
    ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
    matplotlib.pyplot.suptitle(which_wilderness + '\nRemoteness from activity inside wilderness: Acres of wilderness away from access and travel routes and developments inside wilderness')
    txt = str(i_ac) + ' inroads acres (' + str(i_pct) + '%) of ' + str(w_ac) + ' wilderness acres' + '\n' + str(bi_ac) + ' blm inroads acres (' + str(bi_pct) + '%) of ' + str(b_ac) + ' blm acres (' + str(blm_pct) + '%)' + '\n' + str(ui_ac) + ' usfs inroads acres (' + str(ui_pct) + '%) of ' + str(u_ac) + ' usfs acres (' + str(usfs_pct) + '%)'
    matplotlib.pyplot.gcf().text(0.6, 0.9, txt, fontsize=8, fontdict=mono)
    matplotlib.pyplot.axis('off')
    awilderness_box = awilderness_1mi.copy()
    awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
    xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
    ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
    axis.set_xlim(xlim2)
    axis.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, axis, awilderness.crs)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    fig1 = matplotlib.pyplot.gcf()
    fig1.savefig(out_dir + slug_wilderness + '-rem-in-fin-by-own-base.png')
    fig1.clf()
    matplotlib.pyplot.clf()
    matplotlib.pyplot.cla()
    matplotlib.pyplot.close()

    axis = awilderness.plot(color='none', edgecolor='black', linewidth=2.0, alpha=0.9, figsize=(width, width/1.618))
    try:
        usfs_inside.plot(ax=axis, color=ufill, edgecolor='white', linewidth=2.0,)
    except:
        pass
    try:
        blm_inside.plot(ax=axis, color=bfill, edgecolor='white', linewidth=2.0,)
    except:
        pass

    outroads.plot(ax=axis, color=ocp, edgecolor=ocp, alpha=0.7)
    outroads_devln.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    outroads_devpt.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1, markersize=5)
    outroads_devpl.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    outroads_roadcore.plot(ax=axis, color='tab:gray', edgecolor='tab:gray', alpha=1)
    awilderness.plot(ax=axis, color='none', edgecolor='black', linewidth=2.0, alpha=0.9)
    xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
    ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
    matplotlib.pyplot.suptitle(which_wilderness + '\nRemoteness from activity outside wilderness: Acres of wilderness away from access and travel routes and developments outside wilderness')
    txt = str(o_ac) + ' outroads acres (' + str(o_pct) + '%) of ' + str(w_ac) + ' wilderness acres' + '\n' + str(bo_ac) + ' blm outroads acres (' + str(bo_pct) + '%) of ' + str(b_ac) + ' blm acres (' + str(blm_pct) + '%)' + '\n' + str(uo_ac) + ' usfs outroads acres (' + str(uo_pct) + '%) of ' + str(u_ac) + ' usfs acres (' + str(usfs_pct) + '%)'
    matplotlib.pyplot.gcf().text(0.6, 0.9, txt, fontsize=8, fontdict=mono)
    matplotlib.pyplot.axis('off')
    awilderness_box = awilderness_1mi.copy()
    awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
    xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
    ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
    axis.set_xlim(xlim2)
    axis.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, axis, awilderness.crs)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    fig1 = matplotlib.pyplot.gcf()
    fig1.savefig(out_dir + slug_wilderness + '-rem-out-fin-by-own-base.png')
    fig1.clf()
    matplotlib.pyplot.clf()
    matplotlib.pyplot.cla()
    matplotlib.pyplot.close()

    wcc_file = slug_wilderness + '-wcc.' + out_ext
    wcc_full_file = slug_wilderness + '-wcc-full.' + out_ext

    if os.path.exists(out_dir + wcc_file):
        wcc = geopandas.read_file(out_dir + wcc_file)
    else:
        wcc = geopandas.GeoDataFrame()
        wcc['geometry'] = None
        wcc['acres'] = wcc['geometry'].area/4046.856
        wcc.crs = depsg
    wcc = wcc.to_crs(epsg=4269)

    extra_cols = [e for e in wcc.columns if e not in ['WATERSHED_', 'WATERSHE_1', 'WATERSHE_2', 'acres', 'geometry']]
    wcc = wcc.drop(columns=extra_cols).rename(index=str, columns={'WATERSHED_': 'WATERSHED_CODE', 'WATERSHE_1': 'WATERSHED_NAME', 'WATERSHE_2': 'WATERSHED_CONDITION_FS_AREA', })
    w_ac = awilderness['acres'].sum()
    ia_ac = wcc.loc[wcc['WATERSHED_CONDITION_FS_AREA'] == 'Functioning Properly', 'acres'].sum()
    ib_ac = wcc.loc[wcc['WATERSHED_CONDITION_FS_AREA'] == 'Functioning at Risk', 'acres'].sum()
    ic_ac = wcc.loc[wcc['WATERSHED_CONDITION_FS_AREA'] == 'Impaired Function', 'acres'].sum()
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

    try:
        blm_wcc = geopandas.overlay(wcc, blm_inside, how='intersection')
        blm_wcc = blm_wcc.to_crs({'proj':'cea'})
        blm_wcc['acres'] = blm_wcc['geometry'].area/4046.856
        blm_wcc = blm_wcc.to_crs(awilderness.crs)
        blm_wcc_ac = blm_wcc['acres'].sum()
        extra_cols = [e for e in blm_wcc.columns if e not in ['WATERSHED_CODE', 'WATERSHED_NAME', 'WATERSHED_CONDITION_FS_AREA', 'acres', 'geometry']]
        blm_wcc = blm_wcc.drop(columns=extra_cols)
        bia_ac = blm_wcc.loc[blm_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Functioning Properly', 'acres'].sum()
        bib_ac = blm_wcc.loc[blm_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Functioning at Risk', 'acres'].sum()
        bic_ac = blm_wcc.loc[blm_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Impaired Function', 'acres'].sum()
        bwcc_green = (blm_wcc[blm_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Functioning Properly'])
        bwcc_orange = (blm_wcc[blm_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Functioning at Risk'])
        bwcc_red = (blm_wcc[blm_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Impaired Function'])
    except Exception:
        blm_wcc_ac = 0
        bia_ac = 0
        bib_ac = 0
        bic_ac = 0
        blm_wcc = geopandas.GeoDataFrame()
        bwcc_green = geopandas.GeoDataFrame()
        bwcc_orange = geopandas.GeoDataFrame()
        bwcc_red = geopandas.GeoDataFrame()
    try:
        usfs_wcc = geopandas.overlay(wcc, usfs_inside, how='intersection')
        usfs_wcc = usfs_wcc.to_crs({'proj':'cea'})
        usfs_wcc['acres'] = usfs_wcc['geometry'].area/4046.856
        usfs_wcc = usfs_wcc.to_crs(awilderness.crs)
        usfs_wcc_ac = usfs_wcc['acres'].sum()
        uia_ac = usfs_wcc.loc[usfs_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Functioning Properly', 'acres'].sum()
        uib_ac = usfs_wcc.loc[usfs_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Functioning at Risk', 'acres'].sum()
        uic_ac = usfs_wcc.loc[usfs_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Impaired Function', 'acres'].sum()
        uwcc_green = (usfs_wcc[usfs_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Functioning Properly'])
        uwcc_orange = (usfs_wcc[usfs_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Functioning at Risk'])
        uwcc_red = (usfs_wcc[usfs_wcc['WATERSHED_CONDITION_FS_AREA'] == 'Impaired Function'])
    except Exception:
        usfs_wcc_ac = 0
        ua_ac = 0
        uib_ac = 0
        uic_ac = 0
        usfs_wcc = geopandas.GeoDataFrame()
        uwcc_green = geopandas.GeoDataFrame()
        uwcc_orange = geopandas.GeoDataFrame()
        uwcc_red = geopandas.GeoDataFrame()

    w_ac = awilderness['acres'].sum()
    bia_pct = '{0:.0f}'.format((bia_ac/w_ac) * 100)
    bib_pct = '{0:.0f}'.format((bib_ac/w_ac) * 100)
    bic_pct = '{0:.0f}'.format((bic_ac/w_ac) * 100)
    w_ac = '{0:.2f}'.format(w_ac)
    bia_ac = '{0:.2f}'.format(bia_ac)
    bib_ac = '{0:.2f}'.format(bib_ac)
    bic_ac = '{0:.2f}'.format(bic_ac)
    zeros = len(str(int(float(w_ac)))) - len(str(int(float(bia_ac))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        bia_ac = space + bia_ac
    zeros = len(str(int(float(w_ac)))) - len(str(int(float(bib_ac))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        bib_ac = space + bib_ac
    zeros = len(str(int(float(w_ac)))) - len(str(int(float(bic_ac))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        bic_ac = space + bic_ac
    mxp = max(len(str(int(float(bia_pct)))), len(str(int(float(bib_pct)))), len(str(int(float(bic_pct)))))
    zeros = mxp - len(str(int(float(bia_pct))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        bia_pct = space + bia_pct
    zeros = mxp - len(str(int(float(bib_pct))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        bib_pct = space + bib_pct
    zeros = mxp - len(str(int(float(bic_pct))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        bic_pct = space + bic_pct

    uia_pct = '{0:.0f}'.format((uia_ac/float(w_ac)) * 100)
    uib_pct = '{0:.0f}'.format((uib_ac/float(w_ac)) * 100)
    uic_pct = '{0:.0f}'.format((uic_ac/float(w_ac)) * 100)
    w_ac = '{0:.2f}'.format(float(w_ac))
    uia_ac = '{0:.2f}'.format(uia_ac)
    uib_ac = '{0:.2f}'.format(uib_ac)
    uic_ac = '{0:.2f}'.format(uic_ac)
    zeros = len(str(int(float(w_ac)))) - len(str(int(float(uia_ac))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        uia_ac = space + uia_ac
    zeros = len(str(int(float(w_ac)))) - len(str(int(float(uib_ac))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        uib_ac = space + uib_ac
    zeros = len(str(int(float(w_ac)))) - len(str(int(float(uic_ac))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        uic_ac = space + uic_ac
    mxp = max(len(str(int(float(uia_pct)))), len(str(int(float(uib_pct)))), len(str(int(float(uic_pct)))))
    zeros = mxp - len(str(int(float(uia_pct))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        uia_pct = space + uia_pct
    zeros = mxp - len(str(int(float(uib_pct))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        uib_pct = space + uib_pct
    zeros = mxp - len(str(int(float(uic_pct))))
    if zeros > 0:
        space = ''
        space += ' ' * zeros
        uic_pct = space + uic_pct

    width = 13

    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    wcc_fullc = geopandas.read_file(out_dir + wcc_full_file)
    colors = {'Functioning Properly': 'green', 'Functioning at Risk': 'orange', 'Impaired Function': 'red'}

    extra_cols = [e for e in wcc_fullc.columns if e not in ['WATERSHED_', 'WATERSHE_1', 'WATERSHE_2', 'acres', 'geometry']]
    wcc_fullc = wcc_fullc.drop(columns=extra_cols).rename(index=str, columns={'WATERSHED_': 'WATERSHED_CODE', 'WATERSHE_1': 'WATERSHED_NAME', 'WATERSHE_2': 'WATERSHED_CONDITION_FS_AREA', })

    axis = wcc_fullc.plot(color=[colors[i] for i in wcc_fullc['WATERSHED_CONDITION_FS_AREA']], edgecolor='white', alpha=0.2, figsize=(width, width/1.618))
    if not bwcc_green.empty:
        bwcc_green.plot(ax=axis, color='green', edgecolor='white', alpha=0.8, legend=False)
    if not bwcc_orange.empty:
        bwcc_orange.plot(ax=axis, color='orange', edgecolor='white', alpha=0.8, legend=False)
    if not bwcc_red.empty:
        bwcc_red.plot(ax=axis, color='red', edgecolor='white', alpha=0.8, legend=False)
    if not uwcc_green.empty:
        uwcc_green.plot(ax=axis, color='green', edgecolor='white', alpha=0.8, legend=False)
    if not uwcc_orange.empty:
        uwcc_orange.plot(ax=axis, color='orange', edgecolor='white', alpha=0.8, legend=False)
    if not uwcc_red.empty:
        uwcc_red.plot(ax=axis, color='red', edgecolor='white', alpha=0.8, legend=False)
    awilderness.plot(ax=axis, color='none', edgecolor='black', alpha=1)

    xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
    ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
    matplotlib.pyplot.suptitle(which_wilderness + '\nEcological processes: Watershed condition class')
    txt = str(bia_ac) + ' blm acres (' + str(bia_pct) + '%) + ' + str(uia_ac) + ' usfs acres \'functioning properly\' (' + str(uia_pct) + '%)' + '\n' + str(bib_ac) + ' blm acres  (' + str(bib_pct) + '%) + ' + str(uib_ac) + ' usfs acres \'functioning at risk\'  (' + str(uib_pct) + '%)' + '\n' + str(bic_ac) + ' blm acres    (' + str(bic_pct) + '%) + ' + str(uic_ac) + ' usfs acres \'impaired function\'    (' + str(uic_pct) + '%)'
    matplotlib.pyplot.gcf().text(0.55, 0.9, txt, fontsize=8, fontdict=mono)
    matplotlib.pyplot.axis('off')
    awilderness_box = awilderness_1mi.copy()
    awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
    xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
    ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
    axis.set_xlim(xlim2)
    axis.set_ylim(ylim2)
    try_add_basemap(slug_wilderness, axis, awilderness.crs)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)
    fig1 = matplotlib.pyplot.gcf()
    fig1.savefig(out_dir + slug_wilderness + '-wcc-by-own-base.png')
    fig1.clf()
    matplotlib.pyplot.clf()
    matplotlib.pyplot.cla()
    matplotlib.pyplot.close()
