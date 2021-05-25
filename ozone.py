from math import radians, cos, sin, asin, sqrt
import geopandas
import pandas
import numpy

from shapely.geometry import Point
from shapely.ops import nearest_points
from adjustText import adjust_text
from scipy.ndimage.filters import uniform_filter1d

from settings import *
from utils import *

def ozone_trends():
    out_dir = data_dir + '\\'

    if os.path.exists(out_dir + 'ozone_.csv'):
        log(None, 'CYAN', 'ozone.csv already exists')
        stations = pandas.read_csv(out_dir + 'ozone.csv')
    else:
        years = list(range(1990, 2021)) # don't use data before 1990
        stations = pandas.DataFrame()
        for year in years:
            monitors_xls = "C:\\_\\cda_data_20200804\\annual_conc_by_monitor_" + str(year) + ".csv"
            stations_year = pandas.read_csv(monitors_xls)
            extra_cols = [e for e in stations_year.columns if e not in ['State Code', 'County Code', 'Site Num', 'Local Site Name', 'Year', 'Latitude', 'Longitude', 'Sample Duration', '4th Max Value']]
            stations_year = stations_year.drop(columns=extra_cols)
            stations_year = stations_year[stations_year['Sample Duration'] == '8-HR RUN AVG BEGIN HOUR']
            stations_year['State Code'] = stations_year['State Code'].map(lambda x: f'{x:0>3}')
            stations_year['County Code'] = stations_year['County Code'].map(lambda x: f'{x:0>3}')
            stations_year['Site Num'] = stations_year['Site Num'].map(lambda x: f'{x:0>5}')
            stations_year.loc[stations_year["Local Site Name"] == '','Local Site Name'] = stations_year["State Code"].astype(str) + stations_year["County Code"].astype(str) + stations_year["Site Num"].astype(str)
            stations_year.loc[stations_year["Local Site Name"].isnull(),'Local Site Name'] = stations_year["State Code"].astype(str) + stations_year["County Code"].astype(str) + stations_year["Site Num"].astype(str)
            stations_year = (stations_year.groupby(['State Code', 'County Code', 'Site Num', 'Local Site Name', 'Year', 'Latitude', 'Longitude'], as_index=False).agg({'4th Max Value' : 'mean'}))
            stations_year = stations_year.drop_duplicates(['State Code', 'County Code', 'Site Num', 'Local Site Name', 'Year', 'Latitude', 'Longitude'], keep='last')
            stations = stations.append(stations_year)
        stations.to_csv(out_dir + 'ozone.csv')

    stations = pandas.read_csv(out_dir + 'ozone.csv')
    df = stations.groupby(['State Code', 'County Code', 'Site Num', 'Local Site Name', 'Latitude', 'Longitude'], as_index=False)[['Year', '4th Max Value']].agg(list)

    for index, row in df.iterrows():
        x_vals = row['Year']
        y_vals = row['4th Max Value']
        x_vals = ' '.join(str(e) for e in x_vals)
        y_vals = ' '.join(str(e) for e in y_vals)

    stations['geometry'] = geopandas.points_from_xy(stations.Longitude, stations.Latitude)
    plots = geopandas.GeoDataFrame(stations, crs='EPSG:4326')
    plots.to_file(driver='ESRI Shapefile', filename=out_dir + 'ozone_data.shp')

def ozone_kdv(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    awilderness_10mi_file = slug_wilderness + '-buffer-10mi.' + out_ext
    awilderness_25mi_file = slug_wilderness + '-buffer-25mi.' + out_ext
    empty_file_out = out_dir + slug_wilderness + '-ozone-empty.txt'

    plots = geopandas.read_file(data_dir + 'ozone_data.shp')

    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    plots2 = plots.to_crs(awilderness_1mi.crs)

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    aw = awilderness.geometry.unary_union.centroid
    cust_epsg = {'proj': 'aeqd', 'lat_0': aw.y, 'lon_0': aw.x, 'datum': 'WGS84', 'units': 'm',}
    awilderness = awilderness.to_crs(cust_epsg)

    awilderness_10mi = awilderness.copy()
    buffer_length_in_meters = (10 * 1000) * 1.60934 # mi * 1000 * 1.60934
    awilderness_10mi['geometry'] = awilderness_10mi.geometry.buffer(buffer_length_in_meters)
    awilderness_10mi.to_file(driver=out_driver, filename=out_dir + awilderness_10mi_file)
    log(slug_wilderness, 'GREEN', str(awilderness_10mi_file) + ' created')
    awilderness_25mi = awilderness.copy()
    buffer_length_in_meters = (25 * 1000) * 1.60934 # mi * 1000 * 1.60934
    #buffer_length_in_meters = (50 * 1000) * 1.60934 # mi * 1000 * 1.60934
    awilderness_25mi['geometry'] = awilderness_25mi.geometry.buffer(buffer_length_in_meters)
    awilderness_25mi.to_file(driver=out_driver, filename=out_dir + awilderness_25mi_file)
    log(slug_wilderness, 'GREEN', str(awilderness_25mi_file) + ' created')

    plots2 = plots2.rename(index=str, columns={'County Cod': 'County Code', 'Local Site': 'Local Site Name', '4th Max Va': '4th Max Value'})
    dy = awilderness.Designated[0][0:4]
    plots2['t1'] = plots2['Year'].iloc[0]
    plots2['t2'] = plots2['Year'].iloc[-1]

    plots2 = plots2.groupby(['State Code', 'County Code', 'Site Num', 'Local Site Name', 'Latitude', 'Longitude', 't1', 't2'], as_index=False)[['Year', '4th Max Value']].agg(list)
    plots2['years'] = plots2['Year']
    plots2['t1'] = plots2['years'].str[0]
    plots2['t2'] = plots2['years'].str[-1]
    plots2.to_csv(out_dir + slug_wilderness +'-ozone2.csv', index=False)

    extra_cols = [e for e in plots2.columns if e not in ['State Code', 'County Code', 'Site Num', 'Local Site Name', 'Latitude', 'Longitude', 't1', 't2', 'geometry']]
    plots3 = plots2.drop(columns=extra_cols).rename(index=str, columns={'State Code': 'state', 'County Code': 'co', 'Site Num': 'site', 'Local Site Name': 'name'})

    plots3['geometry'] = geopandas.points_from_xy(plots3.Longitude, plots3.Latitude)
    plots3 = geopandas.GeoDataFrame(plots3, crs='EPSG:4326')
    plots3 = plots3.to_crs(awilderness_25mi.crs)
    plots3 = geopandas.sjoin(plots3, awilderness_25mi[['NAME', 'geometry']], how='left', op='within')
    plots3 = plots3[plots3['NAME'].notnull()]

    plots3['tdist'] = 0.0000
    for index, row in plots3.iterrows():
        d = awilderness.distance(row.geometry)/ (1000 * 1.60934)
        plots3.at[index, 'tdist'] = d

    if not plots3.empty:
        plots3.to_file(driver='ESRI Shapefile', filename=out_dir + slug_wilderness + '-o3-plots.shp')

    plots4 = plots3.copy()
    plots4['station'] = plots4['state'].map('{:0>2}'.format) + '' + plots4['co'].map('{:0>3}'.format) + '' + plots4['site'].map('{:0>4}'.format) + '-' + plots4['name'].map(str)[0:40]
    extra_cols = [e for e in plots4.columns if e not in ['station', 'tdist', 't1', 't2', 'geometry']]
    plots4 = plots4.drop(columns=extra_cols)

    cols = ['station', 'tdist', 't1', 't2', 'geometry']
    plots4 = plots4[cols]

    if not plots4.empty:
        plots4.to_file(driver='ESRI Shapefile', filename=out_dir + slug_wilderness + '-inside.shp')
        plots4.to_csv(out_dir + slug_wilderness +'-inside.csv', index=False)
    else:
        log(slug_wilderness, 'RED', 'no local station with proper period of record')

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    awilderness_10mi = geopandas.read_file(out_dir + awilderness_10mi_file)
    awilderness_25mi = geopandas.read_file(out_dir + awilderness_25mi_file)

    awilderness_10mi = awilderness_10mi.to_crs(epsg=4269)
    awilderness_25mi = awilderness_25mi.to_crs(epsg=4269)
    plots4 = plots4.to_crs(epsg=4269)
    log(slug_wilderness, 'WHITE', slug_wilderness + ' ozone plots projected')

    widths = [13, 27]
    for width in widths:
        axis = awilderness.plot(color='none', edgecolor='black', linewidth=2.0, alpha=0.9, figsize=(width, width/1.618))
        plots4.plot(ax=axis, color='magenta', edgecolor='none', linewidth=2.0, alpha=1.0)
        awilderness_10mi_ring = geopandas.overlay(awilderness_10mi, awilderness, how='difference')
        awilderness_25mi_ring = geopandas.overlay(awilderness_25mi, awilderness, how='difference')
        awilderness_10mi_ring.plot(ax=axis, color='black', edgecolor='black', linewidth=2.0, alpha=0.05)
        awilderness_25mi_ring.plot(ax=axis, color='black', edgecolor='none', linewidth=2.0, alpha=0.05)
        awilderness.plot(ax=axis, color='none', edgecolor='black', linewidth=2.0, alpha=0.9)
        xlim = ([awilderness_25mi.total_bounds[0], awilderness_25mi.total_bounds[2]])
        ylim = ([awilderness_25mi.total_bounds[1], awilderness_25mi.total_bounds[3]])

        if width >= 27:
            pyplot.suptitle('Ozone Stations near ' + which_wilderness, fontsize=20)
        else:
            pyplot.suptitle('Ozone Stations near ' + which_wilderness)
        txt = ''
        axis.annotate(txt, xy=(1, 1), xytext=(-12, -12), xycoords='axes fraction', fontsize=8, family='monospace', textcoords='offset points', ha='right', va='top', bbox=dict(facecolor='white', edgecolor='black', pad=5.0))
        pyplot.axis('off')
        plots4 = plots4.dropna(subset=['station',])
        texts = []
        for x, y, station, tdist, t1, t2 in zip(plots4.geometry.x, plots4.geometry.y, plots4.station, plots4.tdist, plots4.t1, plots4.t2):
            texts.append(pyplot.text(x, y, station + '\nd: ' + str(tdist) + '\n' + str(t1) + '-' + str(t2)))
        adjust_text(texts)
        pyplot.subplots_adjust(top = 0.95, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
        pyplot.margins(0,0)
        fig1 = pyplot.gcf()
        awilderness_box = awilderness_25mi.copy()
        buffer_length_in_meters = (1 * 1.60934/100)
        awilderness_box['geometry'] = awilderness_box.geometry.buffer(buffer_length_in_meters)
        xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
        ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
        axis.set_xlim(xlim2)
        axis.set_ylim(ylim2)
        fig1.savefig(out_dir + slug_wilderness + '-ozone-stations-' + str(width) + 'in' + '.png')
        log(slug_wilderness, 'GREEN', slug_wilderness + '-ozone-stations-' + str(width) + 'in' + '.png created')
        try_add_basemap(slug_wilderness, axis, awilderness.crs)
        awilderness_10mi_ring.plot(ax=axis, color='none', edgecolor='black', linewidth=1.5, alpha=0.5)
        awilderness_25mi_ring.plot(ax=axis, color='none', edgecolor='black', linewidth=1.5, alpha=0.5)
        fig1.savefig(out_dir + slug_wilderness + '-ozone-stations-' + str(width) + 'in-base' + '.png')
        log(slug_wilderness, 'GREEN', slug_wilderness + '-ozone-stations-' + str(width) + 'in-base' + '.png created')
        fig1.clf()
        pyplot.clf()
        pyplot.cla()
        pyplot.close()

def ozone_kdv_trendplots(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    awilderness_10mi_file = slug_wilderness + '-buffer-10mi.' + out_ext

    plots4 = pandas.read_csv(out_dir + slug_wilderness +'-ozone2.csv')
    plots4 = plots4.rename(index=str, columns={'State Code': 'state', 'County Code': 'co', 'Site Num': 'site', 'Local Site Name': 'name'})
    plots4['stcosite'] = plots4['state'].map('{:0>2}'.format) + '' + plots4['co'].map('{:0>3}'.format) + '' + plots4['site'].map('{:0>4}'.format)
    plots4['station'] = plots4['state'].map('{:0>2}'.format) + '' + plots4['co'].map('{:0>3}'.format) + '' + plots4['site'].map('{:0>4}'.format) + '-' + plots4['name'].map(str)[0:40]

    plots4.to_csv(out_dir + slug_wilderness +'-o3-test.csv', index=False)

    if not os.path.exists(out_dir + slug_wilderness + '-inside.csv'):
        log(slug_wilderness, 'RED', 'no ozone inside buffer')
    else:
        plots_in = pandas.read_csv(out_dir + slug_wilderness +'-inside.csv')
        s = plots_in['station'].str.split('-', n=1)
        plots_in['stcosite'], plots_in['name'] = s.str[0], s.str[1]
        extra_cols = [e for e in plots4.columns if e not in ['state', 'co', 'site', 'Latitude', 'Longitude', '4th Max Value', 'years', 'stcosite']]
        plots4 = plots4.drop(columns=extra_cols)
        extra_cols = [e for e in plots_in.columns if e not in ['station', 't1', 't2', 'tdist', 'geometry', 'stcosite']]
        plots_in = plots_in.drop(columns=extra_cols)

        oplots = pandas.merge(plots_in, plots4, on='stcosite', how='inner')
        oplots['yrmin'] = [min(x) for x in oplots.years.tolist()]
        oplots['yrmax'] = [max(x) for x in oplots.years.tolist()]

        plots_in = pandas.read_csv(out_dir + slug_wilderness +'-inside.csv')

        awilderness = geopandas.read_file(out_dir + awilderness_file)
        dy = awilderness.Designated[0][0:4]
        for index, plot in oplots.iterrows():
            plot = dict(plot)
            site = plot['station']
            xlist = plot['years']
            ylist = plot['4th Max Value']
            xlist = xlist.replace('[', '').replace(']', '').replace(' ', '').split(',')
            ylist = ylist.replace('[', '').replace(']', '').replace(' ', '').split(',')
            xydict = dict(zip(xlist, ylist))
            for k in list(xydict.keys()):
                if k.startswith('198') or k.startswith('197'):
                    del xydict[k]
                if k < dy:
                    del xydict[k]
            xlist = list(xydict.keys())
            ylist = list(xydict.values())
            if len(xlist) < 4:
                log(slug_wilderness, 'RED', slug_wilderness + ' record too short at ' + str(site))
            else:
                del xlist[:2]
                x_vals = ' '.join(xlist[::-1])
                y_vals = numpy.array(list(map(float, ylist[::-1])))

                interval = y_vals
                window_size = 3
                window = numpy.ones(int(window_size))/float(window_size)
                news = numpy.convolve(interval, window, 'same')
                news = numpy.convolve(interval, window, 'valid')
                ny_vals = news.astype(numpy.float)
                y_vals = ' '.join(str(x) for x in ny_vals)
                x_vals = [int(i) for i in x_vals.split()]
                y_vals = [float(i) for i in y_vals.split()]
                df = pandas.DataFrame()
                df['years_x'] = x_vals
                df['observations_y'] = y_vals
                df = df.reset_index()
                df = df.sort_values('years_x', ascending=False)
                df['years_x'] = pandas.to_numeric(df['years_x'])
                df['observations_y'] = pandas.to_numeric(df['observations_y'])
                x_vals = df['years_x']
                y_vals = df['observations_y']
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(x_vals, y_vals)

                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'o_predicted_y': cols[:, 4]})

                xlist = list(xydict.keys())
                ylist = list(xydict.values())
                x_vals = ' '.join(xlist[::-1])
                y_vals = ' '.join(ylist[::-1])
                x_vals = [int(i) for i in x_vals.split()]
                y_vals = [float(i) for i in y_vals.split()]
                df = pandas.DataFrame()
                df['years_x'] = x_vals
                df['raw_y'] = y_vals
                cols = pandas.merge(df, cols, on='years_x', how='outer')

                cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:blue', 'tab:gray', 0.5, 1.0], 13)

                site = site.replace(' ', '-').replace('//', '-').replace('/', '-').replace('\'', '').replace('\"', '')
                numpy.savetxt(out_dir + slug_wilderness + '-ozone-' + site + '.csv', cols, delimiter=', ', fmt=['%4.0f', '%.4f', '%.4f', '%.4f'], header='year,4th-max-value,3-yr-avg-of-4th-max-value,trend', comments='')

                fig1 = pyplot.gcf()
                width = 13
                fig1.set_size_inches(width, width/1.618, forward=True)
                xmin = min(x_vals)
                xmax = max(x_vals)
                ymax = max(y_vals)
                ytop = ymax+2
                if ymax <= 1:
                    ytop = ((ymax*100)+2)/100

                ymax = max(y_vals)
                pmax = max(y_vals)
                if trend_text is not None:
                    ypred = []
                    for x in x_vals:
                        ypred.append(m*x+b)
                    pmax = max(ypred)
                plotmax = max([pmax, ymax])
                log(slug_wilderness, 'WHITE', slug_wilderness + ' ozone station: ' + site)
                if not pandas.isnull(plotmax) and trend_text is not None:
                    ytop = plotmax
                    pyplot.xticks(x_vals)
                    pyplot.xlim(xmin-1, xmax+1)
                    ax = fig1.gca()
                    if len(x_vals) >= 21:
                        temp = ax.xaxis.get_ticklabels()
                        temp = list(set(temp) - set(temp[::2]))
                        for label in temp:
                            label.set_visible(False)

                    pyplot.suptitle(which_wilderness + '\nOzone Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax) + '\nat ' + site[0:40], y=.95)
                    txt = 'trend = ' + trend_text + '\ntrend slope = ' + float_formatter(m) + '\ntrend p-value = ' + p_formatter(p_value)
                    ax.annotate(txt, xy=(1, 1), xytext=(-12, -12), xycoords='axes fraction', fontsize=8, family='monospace', textcoords='offset points', ha='right', va='top', bbox=dict(facecolor='white', edgecolor='black', pad=5.0))
                    fig1.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-ozone-' + site + '-graph.png')
                    ax.set_xlabel('Year')
                    ax.set_ylabel('3-year average of annual fourth highest daily maximum 8-hour concentration, parts per million')
                    fig1.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-ozone-' + site + '-graph-labels.png')
                    fig1.clf()
                    pyplot.clf()
                    pyplot.cla()
                    pyplot.close()

                    near_station = oplots.loc[oplots['tdist'].idxmin()]['station']
                    near_station = near_station.replace(' ', '-').replace('//', '-').replace('/', '-').replace('\'', '').replace('\"', '')
                    if site == near_station:
                        jsd = [{
                            "site": site,
                            "yr_min": year_formatter(xmin),
                            "yr_max": year_formatter(xmax),
                            "endy": float_formatter(endy),
                            "trend_text": trend_text,
                            "m": float_formatter(m),
                            "p": p_formatter(p_value)
                            }]
                        jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
                        with open(out_dir + 'index-ozone.json', 'w') as static_file:
                            static_file.write(jsc)
