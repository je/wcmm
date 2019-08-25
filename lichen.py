import django
import geopandas
import pandas

from settings import *
from utils import *

def lichen(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    plots_file = slug_wilderness + '-lichen-plots.' + out_ext
    plots_1mi_file = slug_wilderness + '-lichen-plots-buffer.' + out_ext
    empty_file_out = out_dir + slug_wilderness + '-lichen-empty.txt'
    # compare earliest year > wilderness_designation_year vs most recent

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    wilderness_designation_year = awilderness['Designated'].iloc[0][0:4]
    stations = pandas.read_excel(open(lichen_xls, 'rb'))
    station = stations[stations['wilderns'] == which_wilderness]
    if station.empty:
        log(slug_wilderness, 'CYAN', str(which_wilderness) + ' lichen empty')
        with open(empty_file_out, 'a'):
            os.utime(empty_file_out, None)
    else:
        extra_cols = [e for e in station.columns if e not in ['wilderns', 'dataset1', 'year', 'roundno', 'Nscores', 'Sscores', 'latuseNAD83', 'longuseNAD83']]
        station = station.drop(columns=extra_cols).dropna(axis=0)
        log(slug_wilderness, 'CYAN', str(which_wilderness) + ' with ' + str(len(station)) + ' scores')
        sstation = station.drop(columns=['Nscores'])
        sstation1 = (sstation.groupby(['year', 'roundno', 'latuseNAD83', 'longuseNAD83'], as_index=False).agg({'Sscores' : ['size', 'mean']}))
        sstation1.columns = sstation1.columns.droplevel(0)
        sstation5 = sstation.assign(to_sum=sstation.Sscores.gt(0).astype(int)).groupby(['latuseNAD83', 'longuseNAD83']).to_sum.sum()
        sstation4 = (sstation.groupby(['roundno', 'latuseNAD83', 'longuseNAD83'], as_index=False).agg({'Sscores' : ['size', 'mean']}))
        sstation4.columns = sstation4.columns.droplevel(0)
        sstation2 = (sstation.groupby(['year', 'roundno'], as_index=False).agg({'Sscores' : ['size', 'mean']}))
        sstation2.columns = sstation2.columns.droplevel(0)
        sstation3 = sstation.copy()
        sstation3.roundno = sstation3.roundno.str[0:4]
        sstation3 = (sstation3.groupby(['roundno'], as_index=True).agg({'Sscores' : ['size', 'mean']}))
        sstation3.columns = sstation3.columns.droplevel(0)

        x_vals = sstation3.index.values
        y_vals = sstation3['mean'].values

        if len(x_vals) > 2:
            x_vals = numpy.array2string(x_vals).replace('\'', '')
            y_vals = numpy.array2string(y_vals)

            x_vals = x_vals.replace('[', '').replace(']', '')
            y_vals = y_vals.replace('[', '').replace(']', '')

            m, b, endy, p_value, cols = trend(x_vals, y_vals, ['tab:green', 'tab:gray', 0.5])

            fig1 = matplotlib.pyplot.gcf()
            width = 13
            fig1.set_size_inches(width, width/1.618, forward=True)
            x_vals = [int(value) for value in x_vals.split()]
            xmin = min(x_vals)
            xmax = max(x_vals)
            y_vals = [float(i) for i in y_vals.split()]
            ymax = max(y_vals)
            ytop = ymax+2
            if ymax <= 1:
                ytop = ((ymax*100)+2)/100
            matplotlib.pyplot.axis([xmin-1, xmax+1, 0, ytop])
            matplotlib.pyplot.xticks(x_vals)

            matplotlib.pyplot.suptitle(which_wilderness + '\nLichen S-score Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax), y=.95)
            txt = 'latest s-score = ' + float_formatter(endy) + '\navg s-score trend = ' + float_formatter(m) + '\ntrend p-value = ' + p_formatter(p_value)
            matplotlib.pyplot.gcf().text(0.8, 0.9, txt, fontsize=8, fontdict=mono)

            fig1.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-lichen-graph.png')
            fig1.clf()
            matplotlib.pyplot.clf()
            matplotlib.pyplot.cla()
            matplotlib.pyplot.close()
        else:
            log(slug_wilderness, 'CYAN', str(which_wilderness) + ' samples in ' + str(len(x_vals)) + ' round')

        station['geometry'] = geopandas.points_from_xy(station.longuseNAD83, station.latuseNAD83)
        plots = geopandas.GeoDataFrame(station, crs={'init': 'epsg:4326'})
        if not plots.empty:
            plots.to_file(driver='ESRI Shapefile', filename=out_dir + plots_file)
            plots_1mi = plots.copy()
            plots_1mi.to_crs({'proj':'cea'})
            plots_1mi.dataset1 = plots_1mi.dataset1.str[0:3]
            plots_1mi['bd'] = 0.0001
            plots_1mi.loc[plots_1mi['dataset1'] == 'FIA', 'bd'] = .01609344

            plots_1mi['geometry'] = plots_1mi.geometry.buffer(plots_1mi.bd)
            print(plots_1mi)
            plots.to_crs(epsg=4326)
            plots_1mi.to_file(driver='ESRI Shapefile', filename=out_dir + plots_1mi_file)

            width = 13
            axis = awilderness.plot(color='none', edgecolor='black', linewidth=2.0, alpha=0.9, figsize=(width, width/1.618))
            plots_1mi.plot(ax=axis, color='tab:green', edgecolor='tab:green', alpha=0.1)
            plots.plot(ax=axis, color='tab:green', edgecolor='tab:green', alpha=0.7)
            xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
            ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
            matplotlib.pyplot.suptitle(which_wilderness + '\nLichen plot locations')
            axis.set_xlim(xlim)
            axis.set_ylim(ylim)
            matplotlib.pyplot.axis('off')
            fig1 = matplotlib.pyplot.gcf()
            fig1.savefig(out_dir + slug_wilderness + '-lichen-plots.png')
            awilderness_box = awilderness_1mi.copy()
            awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
            xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
            ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
            axis.set_xlim(xlim2)
            axis.set_ylim(ylim2)
            #try_add_basemap(slug_wilderness, axis, awilderness.crs)
            axis.set_xlim(xlim)
            axis.set_ylim(ylim)
            #fig1.savefig(out_dir + slug_wilderness + '-lichen-plots-base.png')
            fig1.clf()
            matplotlib.pyplot.clf()
            matplotlib.pyplot.cla()
            matplotlib.pyplot.close()
