from datetime import datetime
import os

import colorama
import django
import geopandas
import json

from settings import *
from utils import *
from _topojson import topojson

def shps_to_geojsons_to_topojsons(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    in_dir = base_dir + slug_wilderness + '\\'
    out_dir = static_dir + 'wcm\\' + slug_wilderness + '\\'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    tails = ['', '-wcc', '-streams', '-lakes', '-ntdep-grid', '-stdep-grid', '-rem-out-fin', '-rem-in-fin']
    shp_list = [slug_wilderness + s + '.shp' for s in tails]
    for ashp in shp_list:
        filename = os.path.splitext(ashp)[0]
        if not os.path.exists(in_dir + ashp):
            print(ashp + ' skipped')
        else:
            in_shp = geopandas.read_file(in_dir + ashp)
            in_shp['geometry'] = in_shp.geometry.apply(cast_to_multigeometry)
            if filename == slug_wilderness:
                extra_cols = [e for e in in_shp.columns if e not in ['WILDERNESS', 'NAME', 'geometry']]
                renames = {'WILDERNESS': 'number', 'NAME': 'name', }
            if filename == slug_wilderness + '-wcc':
                extra_cols = [e for e in in_shp.columns if e not in ['WATERSHED_', 'WATERSHE_1', 'WATERSHE_2', 'acres', 'geometry']]
                renames = {'WATERSHED_': 'number', 'WATERSHE_1': 'name', 'WATERSHE_2': 'wcc', }
            if filename == slug_wilderness + '-streams':
                extra_cols = [e for e in in_shp.columns if e not in ['REACHCODE', 'miles', 'geometry']]
                renames = {'REACHCODE': 'reachcode', }
            if filename == slug_wilderness + '-lakes':
                extra_cols = [e for e in in_shp.columns if e not in ['REACHCODE', 'geometry']]
                renames = {'REACHCODE': 'reachcode', }
            if filename == slug_wilderness + '-ntdep-grid':
                extra_cols = [e for e in in_shp.columns if e not in ['c', '20170', '20160', '20150', '20140', '20130', '20120', '20110', '20100', '20090', '20080', '20070', '20060', '20050', '20040', '20030', '20020', '20010', '20000', 'y', 'x', 'm', 'b', 'endy', 'p_value', 'geometry']]
                renames = {'20170': '2017', '20160': '2016', '20150': '2015', '20140': '2014', '20130': '2013', '20120': '2012', '20110': '2011', '20100': '2010', '20090': '2009', '20080': '2008', '20070': '2007', '20060': '2006', '20050': '2005', '20040': '2004', '20030': '2003', '20020': '2002', '20010': '2001', '20000': '2000', }
            if filename == slug_wilderness + '-stdep-grid':
                extra_cols = [e for e in in_shp.columns if e not in ['c', '20170', '20160', '20150', '20140', '20130', '20120', '20110', '20100', '20090', '20080', '20070', '20060', '20050', '20040', '20030', '20020', '20010', '20000', 'y', 'x', 'm', 'b', 'endy', 'p_value', 'geometry']]
                renames = {'20170': '2017', '20160': '2016', '20150': '2015', '20140': '2014', '20130': '2013', '20120': '2012', '20110': '2011', '20100': '2010', '20090': '2009', '20080': '2008', '20070': '2007', '20060': '2006', '20050': '2005', '20040': '2004', '20030': '2003', '20020': '2002', '20010': '2001', '20000': '2000', }
            if filename == slug_wilderness + '-rem-out-fin':
                extra_cols = [e for e in in_shp.columns if e not in ['acres', 'geometry']]
                renames = {}
            if filename == slug_wilderness + '-rem-in-fin':
                extra_cols = [e for e in in_shp.columns if e not in ['acres', 'geometry']]
                renames = {}
            cut = in_shp.drop(columns=extra_cols).rename(index=str, columns=renames)
            out_shp = cut.to_crs(epsg=4326)
            out_shp.to_file(out_dir + filename + '.json', driver="GeoJSON")
            try:
                topojson(out_dir + filename + '.json', out_dir + filename + '.json.packed', quantization=1e6, simplify=0.0001)
                if os.path.exists(out_dir + filename + '.json'):
                    os.remove(out_dir + filename + '.json')
                print(colorama.Fore.GREEN + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + filename + ' writing')
            except TypeError:
                print(colorama.Fore.RED + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + filename + ' - weird topojson error')

def b_shps_to_geojsons_to_topojsons(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    in_dir = base_dir + slug_wilderness + '\\'
    out_dir = static_dir + 'wcm\\' + slug_wilderness + '\\'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    tails = ['-streams-around', '-lakes-around', '-streamsb', '-lakesb', '-streamsb-around', '-lakesb-around', '-rem-roadcore2-in', '-rem-roadcore2-out', '-rem-devln-in', '-rem-devln-out', '-rem-devpt-in', '-rem-devpt-out', '-rem-devpl-in', '-rem-devpl-out']
    shp_list = [slug_wilderness + s + '.shp' for s in tails]
    for ashp in shp_list:
        filename = os.path.splitext(ashp)[0]
        if not os.path.exists(in_dir + ashp):
            print(ashp + ' skipped')
        else:
            in_shp = geopandas.read_file(in_dir + ashp)
            in_shp['geometry'] = in_shp.geometry.apply(cast_to_multigeometry)
            extra_cols = []
            renames = {}
            if filename == slug_wilderness:
                extra_cols = [e for e in in_shp.columns if e not in ['WILDERNESS', 'NAME', 'geometry']]
                renames = {'WILDERNESS': 'number', 'NAME': 'name', }
            if filename == slug_wilderness + '-streams-around':
                extra_cols = [e for e in in_shp.columns if e not in ['REACHCODE', 'miles', 'geometry']]
                renames = {'REACHCODE': 'reachcode', }
            if filename == slug_wilderness + '-lakes-around':
                extra_cols = [e for e in in_shp.columns if e not in ['REACHCODE', 'geometry']]
                renames = {'REACHCODE': 'reachcode', }
            if filename == slug_wilderness + '-streamsb-around':
                extra_cols = [e for e in in_shp.columns if e not in ['REACHCODE', 'miles', 'geometry']]
                renames = {'REACHCODE': 'reachcode', }
            if filename == slug_wilderness + '-lakesb-around':
                extra_cols = [e for e in in_shp.columns if e not in ['REACHCODE', 'geometry']]
                renames = {'REACHCODE': 'reachcode', }
            if filename == slug_wilderness + '-rem-roadcore2-in':
                extra_cols = [e for e in in_shp.columns if e not in ['acres', 'geometry']]
                renames = {}
            if filename == slug_wilderness + '-rem-roadcore2-out':
                extra_cols = [e for e in in_shp.columns if e not in ['acres', 'geometry']]
                renames = {}
            if filename == slug_wilderness + '-rem-devln-in':
                extra_cols = [e for e in in_shp.columns if e not in ['acres', 'geometry']]
                renames = {}
            if filename == slug_wilderness + '-rem-devln-out':
                extra_cols = [e for e in in_shp.columns if e not in ['acres', 'geometry']]
                renames = {}
            if filename == slug_wilderness + '-rem-devpt-in':
                extra_cols = [e for e in in_shp.columns if e not in ['acres', 'geometry']]
                renames = {}
            if filename == slug_wilderness + '-rem-devpt-out':
                extra_cols = [e for e in in_shp.columns if e not in ['acres', 'geometry']]
                renames = {}
            if filename == slug_wilderness + '-rem-devpl-in':
                extra_cols = [e for e in in_shp.columns if e not in ['acres', 'geometry']]
                renames = {}
            if filename == slug_wilderness + '-rem-devpl-out':
                extra_cols = [e for e in in_shp.columns if e not in ['acres', 'geometry']]
                renames = {}
            cut = in_shp.drop(columns=extra_cols).rename(index=str, columns=renames)
            out_shp = cut.to_crs(epsg=4326)
            out_shp.to_file(out_dir + filename + '.json', driver="GeoJSON")
            try:
                topojson(out_dir + filename + '.json', out_dir + filename + '.json.packed', quantization=1e6, simplify=0.0001)
                if os.path.exists(out_dir + filename + '.json'):
                    os.remove(out_dir + filename + '.json')
                print(colorama.Fore.GREEN + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + filename + ' writing')
            except TypeError:
                print(colorama.Fore.RED + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + filename + ' - weird topojson error')

def collect_downloads(which_wilderness):
    from shutil import copyfile
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    source_dir = 'c:\\_\\wcmm\\output\\' + slug_wilderness + '\\'
    out_dir = static_dir + 'wcm\\' + slug_wilderness + '\\'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    vis_csvs = [fn for fn in os.listdir(source_dir)
                if fn.endswith('.csv') and '-visibility-' in fn]
    print(vis_csvs)
    for file in vis_csvs:
        copyfile(source_dir + file, out_dir + file)
    file_list = ['-lakes.csv', '-streams.csv', '-wcc.csv', '-303d.png', '-lakes.png', '-ntdep.png', '-ntdep.csv', '-ntdep-graph.png', '-ntdep-graph-extended.png', '-rem-all-fin.png', '-rem-all-fin-27in.png', '-rem-in-fin.png', '-rem-out-fin.png', '-stdep.png', '-stdep.csv', '-stdep-graph.png', '-stdep-graph-extended.png', '-streams.png', '-visibility-graph.png', '-visibility-graph-extended.png', '-wcc.png']
    file_list.extend(['-303d-base.png', '-lakes-base.png', '-ntdep-base.png', '-rem-all-fin-base.png', '-rem-all-fin-27in-base.png', '-rem-in-fin-base.png', '-rem-out-fin-base.png', '-stdep-base.png', '-streams-base.png', '-wcc-base.png'])
    file_list.extend(['-303d-base-own.png', '-lakes-base-own.png', '-ntdep-base-own.png', '-rem-all-fin-by-own-base.png', '-rem-all-fin-27in-by-own-base.png', '-rem-in-fin-by-own-base.png', '-rem-out-fin-by-own-base.png', '-stdep-base-own.png', '-streams-base-own.png', '-wcc-by-own-base.png'])
    for file in file_list:
        if not os.path.exists(source_dir + slug_wilderness + file):
            print(colorama.Fore.CYAN + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + slug_wilderness + file + ' skipped')
        else:
            print(colorama.Fore.GREEN + str(datetime.now().strftime('%Y%m%d_%H%M')) + colorama.Style.BRIGHT +  ' ' + slug_wilderness + file + ' writing')
            copyfile(source_dir + slug_wilderness + file, out_dir + slug_wilderness + file)

def build_wcm(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    source_dir = 'c:\\_\\wcmm\\output\\' + slug_wilderness + '\\'
    out_dir = static_dir + 'wcm\\' + slug_wilderness + '\\'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    vis_csvs = [fn for fn in os.listdir(out_dir)
                if fn.endswith('.csv') and '-visibility-' in fn]
    file_list = ['-lakes.csv', '-streams.csv', '-wcc.csv', '-303d.png', '-lakes.png', '-ntdep.png', '-ntdep.csv', '-ntdep-graph.png', '-rem-all-fin.png', '-rem-all-fin-27in.png', '-rem-in-fin.png', '-rem-out-fin.png', '-stdep.png', '-stdep.csv', '-stdep-graph.png', '-streams.png', '-visibility-graph.png', '-wcc.png']
    file_list.extend(['-303d-base.png', '-lakes-base.png', '-ntdep-base.png', '-rem-all-fin-base.png', '-rem-all-fin-27in-base.png', '-rem-in-fin-base.png', '-rem-out-fin-base.png', '-stdep-base.png', '-streams-base.png', '-wcc-base.png'])
    file_list.extend(['-303d-base-own.png', '-lakes-base-own.png', '-ntdep-base-own.png', '-rem-all-fin-by-own-base.png', '-rem-all-fin-27in-by-own-base.png', '-rem-in-fin-by-own-base.png', '-rem-out-fin-by-own-base.png', '-stdep-base-own.png', '-streams-base-own.png', '-wcc-by-own-base.png'])
    ntdep_ext = '-ntdep-graph-extended.png'
    stdep_ext = '-stdep-graph-extended.png'
    vis_ext = '-visibility-graph-extended.png'
    for file in file_list:
        if not os.path.exists(out_dir + slug_wilderness + file):
            print(slug_wilderness + file + ' skipped')
        else:
            print(slug_wilderness + file + ' added')
    if not vis_csvs:
        context = {'name': which_wilderness, 'slug': slug_wilderness, 'vis_csv': ''}
    else:
        context = {'name': which_wilderness, 'slug': slug_wilderness, 'vis_csv': vis_csvs[0]}
    if not os.path.exists(out_dir + slug_wilderness + ntdep_ext):
        print(slug_wilderness + ntdep_ext + ' skipped')
        context.update({'nt_ext': ''})
    else:
        print(slug_wilderness + ntdep_ext + ' added')
        context.update({'nt_ext': slug_wilderness + ntdep_ext})
    if not os.path.exists(out_dir + slug_wilderness + stdep_ext):
        print(slug_wilderness + stdep_ext + ' skipped')
        context.update({'st_ext': ''})
    else:
        print(slug_wilderness + stdep_ext + ' added')
        context.update({'st_ext': slug_wilderness + stdep_ext})
    if not os.path.exists(out_dir + slug_wilderness + vis_ext):
        print(slug_wilderness + vis_ext + ' skipped')
        context.update({'vis_ext': ''})
    else:
        print(slug_wilderness + vis_ext + ' added')
        context.update({'vis_ext': slug_wilderness + vis_ext})

    with open(source_dir + 'index-inout.json') as jsf:
        data = json.load(jsf)
        context.update({"io": data})
    with open(source_dir + 'index-iw.json') as jsf:
        data = json.load(jsf)
        context.update({"iw": data})
    with open(source_dir + 'index-wcc.json') as jsf:
        data = json.load(jsf)
        context.update({"wcc": data})
    try:
        with open(source_dir + 'index-ntdep.json') as jsf:
            data = json.load(jsf)
            context.update({"ntdep": data})
    except FileNotFoundError:
        log(slug_wilderness, 'RED', 'index-ntdep.json does not exist')
        jsd = [{
            "yr_min": "NA",
            "yr_max": "NA",
            "endy": "NA",
            "m": "NA",
            "p": "NA"
            }]
        jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
        context.update({"ntdep": jsc})
    try:
        with open(source_dir + 'index-stdep.json') as jsf:
            data = json.load(jsf)
            context.update({"stdep": data})
    except FileNotFoundError:
        log(slug_wilderness, 'RED', 'index-stdep.json does not exist')
        jsd = [{
            "yr_min": "NA",
            "yr_max": "NA",
            "endy": "NA",
            "m": "NA",
            "p": "NA"
            }]
        jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
        context.update({"stdep": jsc})
    try:
        with open(source_dir + 'index-vis.json') as jsf:
            data = json.load(jsf)
            context.update({"vis": data})
    except FileNotFoundError:
        log(slug_wilderness, 'RED', 'index-vis.json does not exist')
        jsd = [{
            "yr_min": "NA",
            "yr_max": "NA",
            "endy": "NA",
            "m": "NA",
            "p": "NA"
            }]
        jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
        context.update({"vis": jsc})
    template = django.template.loader.get_template("build_wcm.html")
    content = template.render(context)
    with open(out_dir + 'index.html', 'w') as static_file:
        static_file.write(content)
    template = django.template.loader.get_template("build_wcm.js")
    content = template.render(context)
    with open(out_dir + 'data.js', 'w') as static_file:
        static_file.write(content)

def build_index():
    out_dir = static_dir + 'wcm\\' + '\\'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    rev_date = str(datetime.now().strftime('%Y%m%d_%H%M'))
    context = {'rev_date': rev_date, 'wilderness_count': '447', 'to_date': '2015', 'admin_email': admin_email}
    template = django.template.loader.get_template("build_index.html")
    content = template.render(context)
    print('ok')
    with open(out_dir + 'index.html', 'w') as static_file:
        static_file.write(content)
    template = django.template.loader.get_template("build_index.js")
    content = template.render(context)
    with open(out_dir + 'data.js', 'w') as static_file:
        static_file.write(content)
