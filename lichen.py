import django
import geopandas
import pandas

from settings import *
from utils import *

def lichen(which_wilderness):
    lichen_dir = 'C:\\_\\cda_data\\_lichen\\'
    xls = 'MegaDbPLOT_2020_11_23.xlsx'
    lichen_xls = lichen_dir + xls

    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    awilderness_1mi_file = slug_wilderness + '-buffer.' + out_ext
    plots_file = slug_wilderness + '-lichen-plots.' + out_ext
    plots_1mi_file = slug_wilderness + '-lichen-plots-buffer.' + out_ext
    empty_file_out = out_dir + slug_wilderness + '-lichen-empty.txt'

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    awilderness_1mi = geopandas.read_file(out_dir + awilderness_1mi_file)
    wilderness_designation_year = awilderness['Designated'].iloc[0][0:4]
    stations = pandas.read_excel(open(lichen_xls, 'rb'), sheet_name='Full PlotDB')

    station = stations[stations['wilderns'] == which_wilderness].copy(deep=True)
    extra_cols = [e for e in station.columns if e not in ['wilderns', 'dataset1', 'year', 'roundno', 'n_airscore', 's_airscore', 'c', 'longuseNAD83','latuseNAD83']]
    station = station.drop(columns=extra_cols).dropna(axis=0)
    station['plot_id'] = station['latuseNAD83'].astype(str) + station['longuseNAD83'].astype(str)
    station['hash'] = station.plot_id.map(hash)
    station['plot_id'] = pandas.factorize(station['plot_id'])[0]
    extra_cols = [e for e in station.columns if e not in ['roundno', 'plot_id', 'n_airscore', 's_airscore']]
    s = station.groupby(['roundno','plot_id',]).mean().add_suffix('_avg').reset_index()
    d ={'n_airscore': ['mean'], 's_airscore': ['mean']}
    station["n_airscore"] = pandas.to_numeric(station["n_airscore"])
    station["s_airscore"] = pandas.to_numeric(station["s_airscore"])
    s = station.groupby(['roundno','plot_id','latuseNAD83','longuseNAD83']).agg(d).reset_index()
    s.columns = ['_'.join(col) for col in s.columns.values]

    station['geometry'] = geopandas.points_from_xy(station.longuseNAD83, station.latuseNAD83)
    plots = geopandas.GeoDataFrame(station, crs='EPSG:4326')
    if not plots.empty:
        plots_1mi = plots.copy()
        plots_1mi.dataset1 = plots_1mi.dataset1.str[0:3]
        plots_1mi['bd'] = 0.0001
        plots_1mi.loc[plots_1mi['dataset1'] == 'FIA', 'bd'] = .01609344

        plots_1mi['geometry'] = plots_1mi.geometry.buffer(plots_1mi.bd)

        width = 13
        awilderness = awilderness.to_crs(plots.crs)
        awilderness_1mi = awilderness_1mi.to_crs(plots.crs)
        axis = awilderness.plot(color='none', edgecolor='black', linewidth=2.0, alpha=0.9, figsize=(width, width/1.618))
        awilderness_1mi.plot(ax=axis, color='black', edgecolor='black', alpha=0.05)
        plots_1mi.plot(ax=axis, color='tab:cyan', edgecolor='tab:cyan', alpha=0.2)
        plots.plot(ax=axis, color='tab:cyan', edgecolor='tab:cyan', alpha=1)
        xlim = ([awilderness_1mi.total_bounds[0], awilderness_1mi.total_bounds[2]])
        ylim = ([awilderness_1mi.total_bounds[1], awilderness_1mi.total_bounds[3]])
        pyplot.suptitle('Lichen plot locations near ' + which_wilderness)
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        pyplot.axis('off')
        fig1 = pyplot.gcf()
        pyplot.subplots_adjust(top = 0.95, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
        pyplot.margins(0,0)
        fig1.savefig(out_dir + slug_wilderness + '-lichen-plots.png')
        awilderness_box = awilderness_1mi.copy()
        awilderness_box['geometry'] = awilderness_box.geometry.buffer(.1609344)
        xlim2 = ([awilderness_box.total_bounds[0], awilderness_box.total_bounds[2]])
        ylim2 = ([awilderness_box.total_bounds[1], awilderness_box.total_bounds[3]])
        axis.set_xlim(xlim2)
        axis.set_ylim(ylim2)
        try_add_basemap(slug_wilderness, axis, awilderness.crs)
        axis.set_xlim(xlim)
        axis.set_ylim(ylim)
        fig1.savefig(out_dir + slug_wilderness + '-lichen-plots-base.png')
        fig1.clf()
        pyplot.clf()
        pyplot.cla()
        pyplot.close()

    if station.empty:
        log(slug_wilderness, 'CYAN', slug_wilderness + ' lichen empty')
        with open(empty_file_out, 'a'):
            os.utime(empty_file_out, None)
    else:
        extra_cols = [e for e in station.columns if e not in ['wilderns', 'dataset1', 'year', 'roundno', 'n_airscore', 's_airscore', 'latuseNAD83', 'longuseNAD83']]
        station = station.drop(columns=extra_cols).dropna(axis=0)
        station.to_csv(out_dir + 'lichen-plots-all.csv')
        log(slug_wilderness, 'CYAN', slug_wilderness + ' with ' + str(len(station)) + ' lichen scores')
        station['plot_id'] = station['latuseNAD83'].astype(str) + station['longuseNAD83'].astype(str)
        for poln in ['n', 's']:
            pscores = poln + '_airscore'
            extra_cols = [e for e in station.columns if e not in ['wilderns', 'dataset1', 'plot_id', 'latuseNAD83', 'longuseNAD83', 'year', 'roundno', pscores ]]
            sstation = station.drop(columns=extra_cols)
            rounds = sstation['roundno'].drop_duplicates()
            plots = sstation['plot_id'].drop_duplicates()
            sstation['roundyr'] = sstation['roundno']
            sstation.roundyr = sstation.roundno.str[0:4]
            sstation['roundyr'] = pandas.to_numeric(sstation['roundyr'])
            sstation[pscores] = pandas.to_numeric(sstation[pscores])
            fig1 = pyplot.gcf()
            width = 13
            fig1.set_size_inches(width, width/1.618, forward=True)
            x_valsf = sstation['roundyr']
            y_valsf = sstation[pscores]
            xmin = min(x_valsf)
            xmax = max(x_valsf)
            ymax = max(y_valsf)
            ytop = ymax+2
            if ymax <= 1:
                ytop = ((ymax*100)+2)/100
            pyplot.axis([xmin-1, xmax+1, 0, ytop])
            pyplot.xticks(x_valsf)
            x_valsf = sstation['roundyr'].drop_duplicates()
            xvf = x_valsf.tolist()
            df = pandas.DataFrame()

            for plot in plots:
                g = sstation[sstation['plot_id'].isin([plot])]
                grounds = pandas.merge(rounds, g, on=['roundno'], how='outer')
                grounds = grounds[grounds[pscores].notna()]
                grounds.roundno = grounds.roundno.str[0:4]
                grounds['roundno'] = pandas.to_numeric(grounds['roundno'])
                grounds[pscores] = pandas.to_numeric(grounds[pscores])
                xv = grounds['roundno'].tolist()
                if xv == xvf:
                    df = df.append(grounds)
                    print('adding ' + str(xvf))

                gmax = grounds['roundno'].max()
                gmin = grounds['roundno'].min()

                x_vals = grounds['roundno']
                y_vals = grounds[pscores]

                if len(x_vals) > 1 and len(xvf) == len(xv) and gmax != gmin:
                    m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(x_vals, y_vals)

                    cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                    cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:blue', 'tab:gray', 0.5, 1.0], 13)
                    #cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:green', 'tab:gray', 0.5, 1.0], 13) # no theil-sen in lichen

                    pyplot.suptitle(which_wilderness + '\nLichen ' + poln + '-score Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax), y=.95)
                    txt = 'trend = ' + trend_text + '\ntrend slope = ' + float_formatter(m) + '\ntrend p-value = ' + p_formatter(p_value)
                    axis = pyplot.gca()

            fig1.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-lichen-' + poln + '-graph-all.png')
            if df.empty:
                log(slug_wilderness, 'CYAN', slug_wilderness + ' no sites with 2 or more samples')
            else:
                sstation1 = (df.groupby(['roundno', 'latuseNAD83', 'longuseNAD83'], as_index=False).agg({pscores : ['size', 'mean']}))
                sstation1.columns = sstation1.columns.droplevel(0)
                if poln == 's':
                    sstation5 = sstation.assign(to_sum=sstation.s_airscore.gt(0).astype(int)).groupby(['roundno', 'latuseNAD83', 'longuseNAD83']).to_sum.sum()
                elif poln == 'n':
                    sstation5 = sstation.assign(to_sum=sstation.n_airscore.gt(0).astype(int)).groupby(['roundno', 'latuseNAD83', 'longuseNAD83']).to_sum.sum()
                sstation3 = sstation.copy()
                sstation3.roundno = sstation3.roundno.str[0:4]
                sstation3['PLOT'] = sstation3['latuseNAD83'].astype(str) + sstation3['longuseNAD83'].astype(str)
                sstation3['RDPLOT'] = sstation3['roundno'].astype(str) + sstation3['PLOT'].astype(str)
                sstation3 = (sstation3.groupby(['RDPLOT', 'dataset1', 'roundno', 'wilderns', 'latuseNAD83', 'longuseNAD83', 'PLOT'], as_index=False).agg({pscores : ['size', 'mean']}))
                sstation3.columns = sstation3.columns.droplevel(1)
                sstation3.columns = ['RDPLOT', 'dataset1', 'roundno', 'wilderns', 'latuseNAD83', 'longuseNAD83', 'PLOT', 'size', 'score']
                sstation35 = sstation3[sstation3.groupby(['PLOT']).PLOT.transform('count') > 1]
                plot_table = sstation35[['RDPLOT', 'roundno', 'score']]
                pt = plot_table.pivot(index='RDPLOT', columns='roundno', values='score')
                pt['PLOT'] = pt.index.str[4:]
                pt = pt.reset_index().drop(columns='RDPLOT')
                pt.to_csv(out_dir + 'lichen-' + poln + '-table.csv')
                pt2 = pt.sort_values(by=['PLOT']).ffill().groupby(['PLOT']).last().reset_index()
                pt2 = pt2.dropna(how='any')
                ptm = pt2.mean()

                ptm.to_json(out_dir + 'index-lichen-' + poln + '-tablem.json', orient='index')
                pt2.to_json(out_dir + 'index-lichen-' + poln + '-table.json', orient='index')
                jsd = [{
                    "pollutant": poln,
                    }]

                sstation3g = (sstation35.groupby(['roundno'], as_index=True).agg({'score' : ['size', 'mean']}))
                sstation3g.columns = sstation3g.columns.droplevel(0)

                sstation3g = sstation3g.reset_index()
                sstation3g = sstation3g.sort_values('roundno', ascending=False)
                sstation3g['roundno'] = pandas.to_numeric(sstation3g['roundno'])
                sstation3g['mean'] = pandas.to_numeric(sstation3g['mean'])

                x_vals = sstation3g['roundno']
                y_vals = sstation3g['mean']

                if len(x_vals) > 1:
                    m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(x_vals, y_vals)
                    fig1 = pyplot.gcf()
                    width = 13
                    fig1.set_size_inches(width, width/1.618, forward=True)
                    xmin = min(x_vals)
                    xmax = max(x_vals)
                    ymax = max(y_vals)
                    ytop = ymax+2
                    if ymax <= 1:
                        ytop = ((ymax*100)+2)/100
                    pyplot.axis([xmin-1, xmax+1, 0, ytop])
                    pyplot.xticks(x_vals)

                    cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                    cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:red', 'black', 0.5, 1.0], 13)
                    #cols_to_plot(cols['years_x'], cols['observations_y'], cols['t_predicted_y'], ['tab:red', 'black', 0.5, 1.0], 13) # no theil-sen in lichen

                    pyplot.suptitle(which_wilderness + '\nLichen ' + poln + '-score Trend from ' + year_formatter(xmin) + ' to ' + year_formatter(xmax), y=.95)
                    txt = 'trend = ' + trend_text + '\ntrend slope = ' + float_formatter(m) + '\ntrend p-value = ' + p_formatter(p_value)
                    axis = pyplot.gca()
                    axis.annotate(txt, xy=(1, 1), xytext=(-12, -12), xycoords='axes fraction', fontsize=8, family='monospace', textcoords='offset points', ha='right', va='top', bbox=dict(facecolor='white', edgecolor='black', pad=5.0))
                    fig1.savefig(base_dir + '\\' + slug_wilderness + '\\' + slug_wilderness + '-lichen-' + poln + '-graph.png')
                    fig1.clf()
                    pyplot.clf()
                    pyplot.cla()
                    pyplot.close()

                    jsd = [{
                        "pollutant": poln,
                        "yr_min": year_formatter(xmin),
                        "yr_max": year_formatter(xmax),
                        "endy": float_formatter(endy),
                        "trend_text": trend_text,
                        "m": float_formatter(m),
                        "p": p_formatter(p_value)
                        }]

                    for index, row in sstation3g.iterrows():
                        k = row.roundno
                        v = row.mean
                    jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
                    with open(out_dir + 'index-lichen-' + poln + '.json', 'w') as static_file:
                        static_file.write(jsc)

                else:
                    log(slug_wilderness, 'CYAN', slug_wilderness + ' no samples in round ' + str(len(x_vals)))


