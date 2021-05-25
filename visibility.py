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
        datum1 = data[data['site'] == site]
        datum = datum1[datum1['impairment_Group'] == 90]
        datum = datum.dropna(axis=1)
        extra_cols = [e for e in datum.columns if '_DV' not in e]
        extra_cols = [value for value in extra_cols if value != 'site']
        datum = datum.drop(columns=extra_cols)
        xlist = ''
        datum['y_total'] = ''
        for col in list(datum):
            if col not in ('site', 'c', 'y_total', 'x_total', 'm', 'b', 'endy', 'p_value', 'trend_text', 'acres'):
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
            if col not in ('site', 'c', 'y', 'x', 'y_total', 'x_total', 'm', 'b', 'endy', 'p_value', 'trend_text', 'acres'):
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
            if not datum['x_total'].values[0] == datum['x'].values[0]: # extended graph
                x_vals0 = datum['x_total'].values[0]
                y_vals0 = datum['y_total'].values[0]

                x_vals0 = [int(i) for i in x_vals0.split()]
                y_vals0 = [float(i) for i in y_vals0.split()]
                df= pandas.DataFrame()
                df['years_x'] = x_vals0
                df['observations_y'] = y_vals0

                df = df.reset_index()
                df = df.sort_values('years_x', ascending=False)
                df['years_x'] = pandas.to_numeric(df['years_x'])
                df['observations_y'] = pandas.to_numeric(df['observations_y'])
                x_vals0 = df['years_x']
                y_vals0 = df['observations_y']
                m0, b0, endy0, p_value0, trend_text0, mkr_p_value0, mkr_trend_text0, cols = trender(x_vals0, y_vals0)

                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 't_predicted_y': cols[:, 3]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'tab:gray', 0.5, 1.0], 13)

                x_vals = datum['x'].values[0]
                y_vals = datum['y'].values[0]
                x_vals = [int(i) for i in x_vals.split()]
                y_vals = [float(i) for i in y_vals.split()]
                df= pandas.DataFrame()
                df['years_x'] = x_vals
                df['observations_y'] = y_vals

                df = df.reset_index()
                df = df.sort_values('years_x', ascending=False)
                df['years_x'] = pandas.to_numeric(df['years_x'])
                df['observations_y'] = pandas.to_numeric(df['observations_y'])
                x_vals = df['years_x']
                y_vals = df['observations_y']
                numpy.savetxt(out_dir + slug_wilderness + '-visibility-' + site.replace(" ", "") + '-all.csv', cols, delimiter=',', fmt=['%4.0f', '%.4f', '%.4f'], header='year,5yr-moving-avg-dv,trend', comments='')

                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(x_vals, y_vals)
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 't_predicted_y': cols[:, 3]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'tab:gray', 0.5, 1.0], 13)

                fig1 = pyplot.gcf()
                width = 13
                fig1.set_size_inches(width, width/1.618, forward=True)
                xmin0 = min(x_vals0)
                xmax0 = max(x_vals0)
                ymax0 = max(y_vals0)
                ytop0 = ymax0+2
                if ymax0 <= 1:
                    ytop0 = ((ymax0*100)+2)/100
                pyplot.axis([xmin0-1, xmax0+1, 0, ytop0])
                pyplot.xticks(x_vals0)

                xmin = min(x_vals)
                xmax = max(x_vals)

                ax = fig1.gca()
                if len(x_vals) >= 23:
                    temp = ax.xaxis.get_ticklabels()
                    temp = list(set(temp) - set(temp[::2]))
                    for label in temp:
                        label.set_visible(False)

                pyplot.suptitle(which_wilderness + '\nVisibility Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax), y=.95)
                txt = 'latest avg dv = ' + float_formatter(endy) + '\navg dv trend = ' + mkr_trend_text +  '\n\ntrend p-value = ' + p_formatter(mkr_p_value)
                ax.annotate(txt, xy=(1, 1), xytext=(-12, -12), xycoords='axes fraction', fontsize=8, family='monospace', textcoords='offset points', ha='right', va='top', bbox=dict(facecolor='white', edgecolor='black', pad=5.0))

                fig1.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-visibility-graph-extended.png')
                log(slug_wilderness, 'GREEN', slug_wilderness + '-visibility-graph-extended.png saved')
                fig1.clf()
                pyplot.clf()
                pyplot.cla()
                pyplot.close()

            x_vals = datum['x'].values[0]
            y_vals = datum['y'].values[0]
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
            vis_minyr = df['years_x'].min()
            vis_maxyr = df['years_x'].max()
            vis_minyr5 = vis_minyr + 5
            vis_minyr10 = vis_minyr + 10
            vis_minyr15 = vis_minyr + 15
            vis_minyr20 = vis_minyr + 20
            vis_minyr25 = vis_minyr + 25
            vis_minyr30 = vis_minyr + 30
            vis_minyr35 = vis_minyr + 35
            vis_minyr40 = vis_minyr + 40

            if vis_minyr5 < vis_maxyr:
                vis5 = df[df.years_x.between(vis_minyr, vis_minyr5)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(vis5['years_x'], vis5['observations_y'])
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'o_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'tab:gray', 0.5, 1.0], 13)
                txt = str(vis_minyr) + '-' + str(vis_minyr5) + ' : ' + mkr_trend_text + ' ' + '(p=' + p_formatter(mkr_p_value) + ')'
            if vis_minyr10 < vis_maxyr:
                vis10 = df[df.years_x.between(vis_minyr, vis_minyr10)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(vis10['years_x'], vis10['observations_y'])
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'o_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(vis_minyr) + '-' + str(vis_minyr10) + ' : ' + mkr_trend_text + ' ' + '(p=' + p_formatter(mkr_p_value) + ')'
            if vis_minyr15 < vis_maxyr:
                vis15 = df[df.years_x.between(vis_minyr, vis_minyr15)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(vis15['years_x'], vis15['observations_y'])
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'o_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(vis_minyr) + '-' + str(vis_minyr15) + ' : ' + mkr_trend_text + ' ' + '(p=' + p_formatter(mkr_p_value) + ')'
            if vis_minyr20 < vis_maxyr:
                vis20 = df[df.years_x.between(vis_minyr, vis_minyr20)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(vis20['years_x'], vis20['observations_y'])
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'o_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(vis_minyr) + '-' + str(vis_minyr20) + ' : ' + mkr_trend_text + ' ' + '(p=' + p_formatter(mkr_p_value) + ')'
            if vis_minyr25 < vis_maxyr:
                vis25 = df[df.years_x.between(vis_minyr, vis_minyr25)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(vis25['years_x'], vis25['observations_y'])
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'o_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(vis_minyr) + '-' + str(vis_minyr25) + ' : ' + mkr_trend_text + ' ' + '(p=' + p_formatter(mkr_p_value) + ')'
            if vis_minyr30 < vis_maxyr:
                vis30 = df[df.years_x.between(vis_minyr, vis_minyr30)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(vis30['years_x'], vis30['observations_y'])
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'o_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(vis_minyr) + '-' + str(vis_minyr30) + ' : ' + mkr_trend_text + ' ' + '(p=' + p_formatter(mkr_p_value) + ')'
            if vis_minyr35 < vis_maxyr:
                vis35 = df[df.years_x.between(vis_minyr, vis_minyr35)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(vis35['years_x'], vis35['observations_y'])
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'o_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(vis_minyr) + '-' + str(vis_minyr35) + ' : ' + mkr_trend_text + ' ' + '(p=' + p_formatter(mkr_p_value) + ')'
            if vis_minyr40 < vis_maxyr:
                vis40 = df[df.years_x.between(vis_minyr, vis_minyr40)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(vis40['years_x'], vis40['observations_y'])
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'o_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(vis_minyr) + '-' + str(vis_minyr40) + ' : ' + mkr_trend_text + ' ' + '(p=' + p_formatter(mkr_p_value) + ')'

            vis_full = df[df.years_x.between(vis_minyr, vis_maxyr)]
            m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(vis_full['years_x'], vis_full['observations_y'])
            cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'o_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3]})
            cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'tab:gray', 1.0, 1.0], 13)
            txt = txt + '\n' + str(vis_minyr) + '-' + str(vis_maxyr) + ' : ' + mkr_trend_text + ' ' + '(p=' + p_formatter(mkr_p_value) + ')'

            if 'o_predicted_y' in cols.columns:
                cols = cols.drop(columns=['o_predicted_y'])
            numpy.savetxt(out_dir + slug_wilderness + '-visibility-' + site.replace(" ", "") + '.csv', cols, delimiter=',', fmt=['%4.0f', '%.4f', '%.4f'], header='year,5yr-moving-avg-dv,trend', comments='')

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
            ypred = []
            for x in x_vals:
                ypred.append(m*x+b)
            pmax = max(ypred)
            plotmax = max([pmax, ymax])
            ytop = plotmax

            pyplot.xticks(x_vals)
            pyplot.xlim(xmin-1, xmax+1)

            ax = fig1.gca()
            if len(x_vals) >= 23:
                temp = ax.xaxis.get_ticklabels()
                temp = list(set(temp) - set(temp[::2]))
                for label in temp:
                    label.set_visible(False)

            pyplot.suptitle(which_wilderness + '\nVisibility Trends from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax) + ' at ' +  site, y=.95)
            ax.annotate(txt, xy=(1, 1), xytext=(-12, -12), xycoords='axes fraction', fontsize=8, family='monospace', textcoords='offset points', ha='right', va='top', bbox=dict(facecolor='white', edgecolor='black', pad=5.0))

            fig1.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-visibility-graph.png')
            ax.set_xlabel('Year')
            ax.set_ylabel('5-year average of 20% most impaired days, deciviews')
            fig1.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-visibility-graph-labels.png')
            fig1.clf()
            pyplot.clf()
            pyplot.cla()
            pyplot.close()
            log(slug_wilderness, 'GREEN', slug_wilderness + '-visibility-graph.png saved')

            jsd = [{
                "yr_min": year_formatter(xmin),
                "yr_max": year_formatter(xmax),
                "endy": float_formatter(endy),
                "trend_text": mkr_trend_text,
                "m": float_formatter(m),
                "p": p_formatter(mkr_p_value)
                }]
            jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
            with open(out_dir + 'index-vis.json', 'w') as static_file:
                static_file.write(jsc)

