import os
from datetime import datetime

import django
import geopandas
import pandas

from settings import *
from utils import *

def wilderness_year_designated():
    inr = geopandas.read_file(base_dir + wilderness_file)
    inx = pandas.read_table(in_xls)
    inv = pandas.read_table(wilderness_tsv)
    inr = inr.rename(columns={'WILDERNE_1': 'NAME'})
    inx = inx.rename(columns={'WILDERNESS NAME': 'NAME', 'YEAR DESIGNATED': 'DESIGNATED'})
    inx = inx.sort_values('DESIGNATED', ascending=False).drop_duplicates('NAME', keep='last').sort_index()
    inv = inv.rename(columns={'Wilderness ': 'NAME'})
    inv['NAME'] = inv['NAME'] + 'Wilderness'
    inr = inr.merge(inx, on='NAME', how="left")
    inr = inr.merge(inv, on='NAME', how="left")
    inr = inr.drop(columns=['UNIT ACREAGE (in acres)', 'TOTAL ACREAGE (in acres)', 'Unnamed: 6', 'AGENCY', 'STATE', 'State ', 'Acres', 'Hectares '])
    inr = inr.sort_values('DESIGNATED', ascending=False).drop_duplicates('NAME', keep='last').sort_index()
    inr = inr.rename(columns={'Designated_y': 'Designated'})
    inr['Designated'] = pandas.to_datetime(inr['Designated'])
    inr['DESIGNATED'] = pandas.to_numeric(inr['DESIGNATED'], downcast='integer')
    inr['Designated Year'] = pandas.to_numeric(inr['Designated'].dt.year, downcast='integer')
    inr.loc[inr['DESIGNATED'] == inr['Designated Year'], 'DY'] = inr['Designated Year']
    inr['Designated'] = inr['Designated'].dt.strftime('%Y-%m-%d')
    inr.loc[pandas.isnull(inr['DY']), 'Designated'] = ''
    inr = inr.drop(columns=['DY', 'DESIGNATED', 'Designated Year'])
    inr.loc[inr['NAME'] == 'Anaconda Pintler Wilderness', 'Designated'] = '1964-12-31'
    inr.loc[inr['NAME'] == 'Cecil D. Andrus-White Clouds Wilderness', 'Designated'] = '2015-12-31'
    inr.loc[inr['NAME'] == 'East Humboldts Wilderness', 'Designated'] = '1989-12-31'
    inr.loc[inr['NAME'] == 'Frank Church-River of No Return Wilderness', 'Designated'] = '1980-12-31'
    inr.loc[inr['NAME'] == 'Gospel-Hump Wilderness', 'Designated'] = '1978-12-31'
    inr.loc[inr['NAME'] == 'Granite Mountain Wilderness (AZ)', 'Designated'] = '1984-12-31'
    inr.loc[inr['NAME'] == 'Granite Mountain Wilderness (CA)', 'Designated'] = '1984-12-31'
    inr.loc[inr['NAME'] == 'Hemingway-Boulders Wilderness', 'Designated'] = '2015-12-31'
    inr.loc[inr['NAME'] == 'Hercules-Glades Wilderness', 'Designated'] = '1976-12-31'
    inr.loc[inr['NAME'] == 'Hunter-Fryingpan Wilderness', 'Designated'] = '1978-12-31'
    inr.loc[inr['NAME'] == 'Jim McClure-Jerry Peak Wilderness', 'Designated'] = '2015-12-31'
    inr.loc[inr['NAME'] == 'Laurel Fork South Wilderness', 'Designated'] = '1983-12-31'
    inr.loc[inr['NAME'] == 'Lower White River Wilderness (BLM)', 'Designated'] = '2009-12-31'
    inr.loc[inr['NAME'] == 'Maroon Bells-Snowmass Wilderness', 'Designated'] = '1964-12-31'
    inr.loc[inr['NAME'] == 'Maurille Islands Wilderness', 'Designated'] = '1980-12-31'
    inr.loc[inr['NAME'] == 'Misty Fiords National Monument Wilderness', 'Designated'] = '1980-12-31'
    inr.loc[inr['NAME'] == 'Mud Swamp/New River Wilderness', 'Designated'] = '1984-12-31'
    inr.loc[inr['NAME'] == 'Petersburg Creek-Duncan Salt Chuck Wilderness', 'Designated'] = '1980-12-31'
    inr.loc[inr['NAME'] == 'Pleasant/Lemusurier/Inian Islands Wilderness', 'Designated'] = '1990-12-31'
    inr.loc[inr['NAME'] == 'Richland Creek Wilderness', 'Designated'] = '1984-12-31'
    inr.loc[inr['NAME'] == 'Rogue-Umpqua Divide Wilderness', 'Designated'] = '1984-12-31'
    inr.loc[inr['NAME'] == 'Salmon-Huckleberry Wilderness', 'Designated'] = '1984-12-31'
    inr.loc[inr['NAME'] == 'Uncompahgre Wilderness', 'Designated'] = '1980-12-31'
    inr.loc[inr['NAME'] == 'Upland Island Wilderness', 'Designated'] = '1984-12-31'
    inr.loc[inr['NAME'] == 'Ventana Wilderness', 'Designated'] = '1969-12-31'
    inr.loc[inr['NAME'] == 'Wenaha-Tucannon Wilderness', 'Designated'] = '1978-12-31'
    inr.loc[inr['NAME'] == 'Wild Rogue Wilderness', 'Designated'] = '1978-12-31'
    inr.loc[inr['NAME'] == 'Wovoka Wilderness', 'Designated'] = '2014-12-31'
    inr.loc[inr['NAME'] == 'Yolla Bolly-Middle Eel Wilderness', 'Designated'] = '1964-12-31'
    inr.loc[inr['NAME'] == 'Misty Fiords Wilderness', 'NAME'] = 'Misty Fjords Wilderness'
    inr = inr.sort_values('NAME', ascending=True).sort_index()
    inr['Baseline'] = ''
    inr.loc[inr['Baseline'] == 'Anaconda Pintler Wilderness', 'Baseline'] = '2018'

    extra_cols = [e for e in inr.columns if e not in ['WILDERNESS', 'NAME', 'AREAID', 'BOUNDARYST', 'GIS_ACRES', 'WID', 'Designated', 'Baseline', 'geometry', 'acres']]
    inr = inr.drop(columns=extra_cols)
    inr.to_file(driver='ESRI Shapefile', filename=base_dir + wilderness_file)
    inr = inr.drop(columns=['geometry'])
    inr.to_csv(path_or_buf=base_dir + 'wilderness-check.csv', index=False)

def wilderness_write_fixture():
    inr = geopandas.read_file(base_dir + wilderness_file)
    inr.to_csv(path_or_buf=wilderness_csv, index=False)
    inr = pandas.read_csv(wilderness_csv, sep=',')
    topbit = '[\n'
    with open(wilderness_fixture, 'a') as outfile:
        outfile.write(topbit)
    pkey = 1
    created = datetime.utcnow().isoformat()[:-7] + 'Z'
    for i, row in inr.iterrows():
        comma = ',\n'
        if pkey == 1:
            comma = ''
        pkey = pkey + 1
        year_designated = '"' + str(row['Designated']) + '"'
        if year_designated == '"nan"':
            year_designated = 'null'
        fields = '{\n        "geom": "' + str(row['geometry']) + '",\n        "name": "' + str(row['NAME']) + '",\n        "slug": "' + str(django.utils.text.slugify(row['NAME'])) + '",\n        "wilderness_id": "' + str(row['WILDERNESS']) + '",\n        "area_id": "' + str(row['AREAID']) + '",\n        "w_id": "' + str(row['WID']) + '",\n        "boundary_status": "' + str(row['BOUNDARYST']) + '",\n        "year_designated": ' + year_designated + ',\n        "gis_acres": '+ str(row['GIS_ACRES']) + ',\n        "created": "' + str(created) + '",\n        "modified": null,\n        "author": 2\n    }\n'
        record = comma + '{\n    "model": "wilder.wilderness",\n    "pk": '+ str(pkey) + ',\n    "fields": ' + fields + '}'
        with open(wilderness_fixture, 'a') as outfile:
            outfile.write(record)
    endbit = '\n]'
    with open(wilderness_fixture, 'a') as outfile:
        outfile.write(endbit)

def awilderness_boundary(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_cea_file = slug_wilderness + '-cea.' + out_ext

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    wilderness = geopandas.read_file(base_dir + wilderness_file)
    awilderness = wilderness[wilderness['NAME'] == which_wilderness]
    awilderness.crs = {'init': 'epsg:4269'}
    awilderness.to_file(driver=out_driver, filename=out_dir + awilderness_file)
    log(slug_wilderness, 'GREEN', str(awilderness_file) + ' created')
    awilderness = awilderness.to_crs({'proj':'cea'})
    awilderness['acres'] = awilderness['geometry'].area/4046.856
    awilderness.to_file(driver=out_driver, filename=out_dir + awilderness_cea_file)
    log(slug_wilderness, 'GREEN', str(awilderness_cea_file) + ' created')

def awilderness_buffers(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    awilderness_1mi_ring_file = slug_wilderness + '-ring.' + out_ext

    if os.path.exists(out_dir + awilderness_1mi_file):
        log(slug_wilderness, 'CYAN', awilderness_1mi_file + ' already exists')
    else:
        awilderness = geopandas.read_file(out_dir + awilderness_file)
        awilderness_1mi = awilderness.copy()
        awilderness_1mi['geometry'] = awilderness.geometry.buffer(.01609344)
        awilderness_1mi.to_file(driver=out_driver, filename=out_dir + awilderness_1mi_file)
        log(slug_wilderness, 'GREEN', str(awilderness_1mi_file) + ' created')
        awilderness_1mi_ring = geopandas.overlay(awilderness_1mi, awilderness, how='difference')
        awilderness_1mi_ring.to_file(driver=out_driver, filename=out_dir + awilderness_1mi_ring_file)
        log(slug_wilderness, 'GREEN', str(awilderness_1mi_ring_file) + ' created')
