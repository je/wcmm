import django
import geopandas
import pandas

from settings import *
from utils import *

def visibility(which_wilderness):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    empty_file_out = out_dir + slug_wilderness + '-vis-empty.txt'

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    wilderness_designation_year = awilderness['Designated'].iloc[0][0:4]
    stations = pandas.read_excel(open(vis_stations, 'rb'))
    station = stations[stations['WILDERNESS_NAME'] == which_wilderness]
    if station.empty:
        log(slug_wilderness, 'RED', str(which_wilderness) + ' visibility empty')
        with open(empty_file_out, 'a'):
            os.utime(empty_file_out, None)
    else:
        site = station['IMPROVE_SITE_CODE'].values[0]
        data = pandas.read_csv(vis_data)
        datum = data[data['site'] == site]
        datum = datum.dropna(axis=1)
        extra_cols = [e for e in datum.columns if '_DV' not in e]
        extra_cols = [value for value in extra_cols if value != 'site']
        datum = datum.drop(columns=extra_cols)
        xlist = ''
        datum['y_total'] = ''
        for col in list(datum):
            if col not in ('site', 'c', 'y_total', 'x_total', 'm', 'b', 'endy', 'p_value', 'acres'):
                yearcol = int(col[3:5])
                if yearcol > 90:
                    yearcol = str(1900 + yearcol)
                elif yearcol <= 90:
                    yearcol = str(2000 + yearcol)
                xlist = xlist + yearcol + ' '
                datum['y_total'] = datum['y_total'] + datum[col].astype(str) + ' '
        datum['x_total'] = xlist
        xlist = ''
        datum['y'] = ''
        for col in list(datum):
            if col not in ('site', 'c', 'y', 'x', 'y_total', 'x_total', 'm', 'b', 'endy', 'p_value', 'acres'):
                yearcol = int(col[3:5])
                if yearcol > 90:
                    yearcol = str(1900 + yearcol)
                elif yearcol <= 90:
                    yearcol = str(2000 + yearcol)
                if int(yearcol) >= int(wilderness_designation_year) + 4:
                    xlist = xlist + yearcol + ' '
                    datum['y'] = datum['y'] + datum[col].astype(str) + ' '
        datum['x'] = xlist

        if datum.empty:
            log(slug_wilderness, 'RED', str(which_wilderness) + ' visibility data empty')
            with open(empty_file_out, 'a'):
                os.utime(empty_file_out, None)
        else:
            if not datum['x_total'].values[0] == datum['x'].values[0]:
                x_vals0 = datum['x_total'].values[0]
                y_vals0 = datum['y_total'].values[0]
                x_vals0 = ' '.join(x_vals0.split(' ')[::-1])
                y_vals0 = ' '.join(y_vals0.split(' ')[::-1])
                m0, b0, endy0, p_value0, cols0 = trend(x_vals0, y_vals0, ['tab:blue', 'tab:gray', 0.5])

                x_vals = datum['x'].values[0]
                y_vals = datum['y'].values[0]
                x_vals = ' '.join(x_vals.split(' ')[::-1])
                y_vals = ' '.join(y_vals.split(' ')[::-1])
                m, b, endy, p_value, cols = trend(x_vals, y_vals, ['tab:red', 'tab:gray', 1])

                fig1 = matplotlib.pyplot.gcf()
                width = 13
                fig1.set_size_inches(width, width/1.618, forward=True)
                x_vals0 = [int(value) for value in x_vals0.split()]
                xmin0 = min(x_vals0)
                xmax0 = max(x_vals0)
                y_vals0 = [float(i) for i in y_vals0.split()]
                ymax0 = max(y_vals0)
                ytop0 = ymax0+2
                if ymax0 <= 1:
                    ytop0 = ((ymax0*100)+2)/100
                matplotlib.pyplot.axis([xmin0-1, xmax0+1, 0, ytop0])
                matplotlib.pyplot.xticks(x_vals0)

                x_vals = [int(value) for value in x_vals.split()]
                xmin = min(x_vals)
                xmax = max(x_vals)

                matplotlib.pyplot.suptitle(which_wilderness + '\nVisibility Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax), y=.95)
                txt = 'latest avg dv = ' + float_formatter(endy) + '\navg dv trend = ' + float_formatter(m) + '\ntrend p-value = ' + p_formatter(p_value)
                matplotlib.pyplot.gcf().text(0.8, 0.9, txt, fontsize=8, fontdict=mono)

                fig1.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-visibility-graph-extended.png')
                fig1.clf()
                matplotlib.pyplot.clf()
                matplotlib.pyplot.cla()
                matplotlib.pyplot.close()

            x_vals = datum['x'].values[0]
            y_vals = datum['y'].values[0]
            x_vals = ' '.join(x_vals.split(' ')[::-1])
            y_vals = ' '.join(y_vals.split(' ')[::-1])
            m, b, endy, p_value, cols = trend(x_vals, y_vals, ['tab:red', 'tab:gray', 1])

            numpy.savetxt(out_dir + slug_wilderness + '-visibility-' + site.replace(" ", "") + '.csv', cols, delimiter=',', fmt=['%4.0f', '%.4f', '%.4f'], header='year,5yr-moving-avg-dv,trend', comments='')

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

            ymax = max(y_vals)
            ypred = []
            for x in x_vals:
                ypred.append(m*x+b)
            pmax = max(ypred)
            plotmax = max([pmax, ymax])
            print(ymax)
            print(ypred)
            print(pmax)
            print(plotmax)
            matplotlib.pyplot.ylim(0, plotmax)
            ytop = plotmax

            matplotlib.pyplot.axis([xmin-1, xmax+1, 0, ytop])
            matplotlib.pyplot.xticks(x_vals)
            matplotlib.pyplot.ylim(0, plotmax)

            matplotlib.pyplot.suptitle(which_wilderness + '\nVisibility Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax), y=.95)
            txt = 'latest avg dv = ' + float_formatter(endy) + '\navg dv trend = ' + float_formatter(m) + '\ntrend p-value = ' + p_formatter(p_value)
            print(p_value)
            matplotlib.pyplot.gcf().text(0.8, 0.9, txt, fontsize=8, fontdict=mono)

            fig1.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-visibility-graph.png')
            fig1.clf()
            matplotlib.pyplot.clf()
            matplotlib.pyplot.cla()
            matplotlib.pyplot.close()

            jsd = [{
                "yr_min": year_formatter(xmin),
                "yr_max": year_formatter(xmax),
                "endy": float_formatter(endy),
                "m": float_formatter(m),
                "p": p_formatter(p_value)
                }]
            jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
            with open(out_dir + 'index-vis.json', 'w') as static_file:
                static_file.write(jsc)

