import django
import geopandas
import pandas

from settings import *
from utils import *

def cols_to_plot(years_x, observations_y, predicted_y, ccaa, width):
    pyplot.scatter(years_x, observations_y, color=ccaa[1], alpha=ccaa[3], marker='x', s=40)
    pyplot.plot(years_x, predicted_y, color=ccaa[0], alpha=ccaa[2], linewidth=2, label=None)

def wetdep(which_wilderness, ns):
    slug_wilderness = django.utils.text.slugify(which_wilderness)
    out_dir = base_dir + slug_wilderness + '\\'
    awilderness_file = slug_wilderness + '.' + out_ext
    empty_file_out = out_dir + slug_wilderness + '-wet' + ns + '-empty.txt'

    if ns == 'n':
        nsname = 'nitrogen'
    elif ns == 's':
        nsname = 'sulfur'

    awilderness = geopandas.read_file(out_dir + awilderness_file)
    wilderness_designation_year = awilderness['Designated'].iloc[0][0:4]

    dropdown_xml_file = 'C:\\_\\cda_data_nat-20200326\\wetdep-dropdown-data.xml'
    dropdown_csv_file = 'C:\\_\\cda_data_nat-20200326\\wetdep-dropdown-data.csv'

    drops = pandas.read_csv(dropdown_csv_file)
    renames = {'value': 'st', 'value3': 'fo', 'name5': 'wilderness', 'value6': 'wi'}
    cut = drops.rename(index=str, columns=renames)
    extra_cols = [e for e in cut.columns if e not in ['st', 'fo', 'wi', 'wilderness', ]]
    cut = cut.drop(columns=extra_cols)
    cut['slug'] = cut['wilderness'] + ' Wilderness'
    cut['path'] = cut['st'] + '\\' + cut['fo'] + '\\' + cut['wi'] + '\\'
    cols = ['path', 'slug']
    cut = cut[cols].dropna().reset_index(drop=True)

    arow = cut[cut['slug'] == which_wilderness]
    apath = arow['path'].values
    wetfolder = 'C:\\_\\webcam.srs.fs.fed.us\\results'

    if ns == 'n':
        wetn_csv = wetfolder + '\\' + apath + 'dep\\TotNit.csv'
    elif ns == 's':
        wetn_csv = wetfolder + '\\' + apath + 'dep\\sulfate.csv'

    if not wetn_csv:
        log(slug_wilderness, 'CYAN', str(which_wilderness) + ' ' + ns + ' wetdep list empty')
    else:
        if not os.path.exists(wetn_csv[0]):
            log(slug_wilderness, 'CYAN', str(which_wilderness) + ' ' + ns + ' wetdep empty')
            with open(empty_file_out, 'a'):
                os.utime(empty_file_out, None)
        else:
            wetn = pandas.read_csv(wetn_csv[0])
            wetn = wetn.loc[wetn['Year'] >= int(wilderness_designation_year)]
            wetn_minyr = wetn['Year'].min()
            wetn_maxyr = wetn['Year'].max()
            wetn_minyr5 = wetn_minyr + 5
            wetn_minyr10 = wetn_minyr + 10
            wetn_minyr15 = wetn_minyr + 15
            wetn_minyr20 = wetn_minyr + 20
            wetn_minyr25 = wetn_minyr + 25
            wetn_minyr30 = wetn_minyr + 30
            wetn_minyr35 = wetn_minyr + 35
            wetn_minyr40 = wetn_minyr + 40

            jsd = {}
            if wetn_minyr5 < wetn_maxyr:
                wetn5 = wetn[wetn.Year.between(wetn_minyr, wetn_minyr5)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(wetn5['Year'], wetn5[' Mean'])
                wetj = {'minyr': wetn_minyr, 'maxyr': wetn_minyr5, 'trend': trend_text, 'p': p_value}
                jsd["wet5"] = wetj
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:blue', 'tab:gray', 0.5, 1.0], 13)
                txt = str(wetn_minyr) + '-' + str(wetn_minyr5) + ' : ' + trend_text + ' ' + '(p=' + p_formatter(p_value) + ')'
            if wetn_minyr10 < wetn_maxyr:
                wetn10 = wetn[wetn.Year.between(wetn_minyr, wetn_minyr10)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(wetn10['Year'], wetn10[' Mean'])
                wetj = {'minyr': wetn_minyr, 'maxyr': wetn_minyr10, 'trend': trend_text, 'p': p_value}
                jsd["wet10"] = wetj
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:blue', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(wetn_minyr) + '-' + str(wetn_minyr10) + ' : ' + trend_text + ' ' + '(p=' + p_formatter(p_value) + ')'
            if wetn_minyr15 < wetn_maxyr:
                wetn15 = wetn[wetn.Year.between(wetn_minyr, wetn_minyr15)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(wetn15['Year'], wetn15[' Mean'])
                wetj = {'minyr': wetn_minyr, 'maxyr': wetn_minyr15, 'trend': trend_text, 'p': p_value}
                jsd["wet15"] = wetj
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:blue', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(wetn_minyr) + '-' + str(wetn_minyr15) + ' : ' + trend_text + ' ' + '(p=' + p_formatter(p_value) + ')'
            if wetn_minyr20 < wetn_maxyr:
                wetn20 = wetn[wetn.Year.between(wetn_minyr, wetn_minyr20)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(wetn20['Year'], wetn20[' Mean'])
                wetj = {'minyr': wetn_minyr, 'maxyr': wetn_minyr20, 'trend': trend_text, 'p': p_value}
                jsd["wet20"] = wetj
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:blue', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(wetn_minyr) + '-' + str(wetn_minyr20) + ' : ' + trend_text + ' ' + '(p=' + p_formatter(p_value) + ')'
            if wetn_minyr25 < wetn_maxyr:
                wetn25 = wetn[wetn.Year.between(wetn_minyr, wetn_minyr25)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(wetn25['Year'], wetn25[' Mean'])
                wetj = {'minyr': wetn_minyr, 'maxyr': wetn_minyr25, 'trend': trend_text, 'p': p_value}
                jsd["wet25"] = wetj
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:blue', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(wetn_minyr) + '-' + str(wetn_minyr25) + ' : ' + trend_text + ' ' + '(p=' + p_formatter(p_value) + ')'
            if wetn_minyr30 < wetn_maxyr:
                wetn30 = wetn[wetn.Year.between(wetn_minyr, wetn_minyr30)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(wetn30['Year'], wetn30[' Mean'])
                wetj = {'minyr': wetn_minyr, 'maxyr': wetn_minyr30, 'trend': trend_text, 'p': p_value}
                jsd["wet30"] = wetj
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:blue', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(wetn_minyr) + '-' + str(wetn_minyr30) + ' : ' + trend_text + ' ' + '(p=' + p_formatter(p_value) + ')'
            if wetn_minyr35 < wetn_maxyr:
                wetn35 = wetn[wetn.Year.between(wetn_minyr, wetn_minyr35)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(wetn35['Year'], wetn35[' Mean'])
                wetj = {'minyr': wetn_minyr, 'maxyr': wetn_minyr35, 'trend': trend_text, 'p': p_value}
                jsd["wet35"] = wetj
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:blue', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(wetn_minyr) + '-' + str(wetn_minyr35) + ' : ' + trend_text + ' ' + '(p=' + p_formatter(p_value) + ')'
            if wetn_minyr40 < wetn_maxyr:
                wetn40 = wetn[wetn.Year.between(wetn_minyr, wetn_minyr40)]
                m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(wetn40['Year'], wetn40[' Mean'])
                wetj = {'minyr': wetn_minyr, 'maxyr': wetn_minyr40, 'trend': trend_text, 'p': p_value}
                jsd["wet40"] = wetj
                cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
                cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:blue', 'tab:gray', 0.5, 1.0], 13)
                txt = txt + '\n' + str(wetn_minyr) + '-' + str(wetn_minyr40) + ' : ' + trend_text + ' ' + '(p=' + p_formatter(p_value) + ')'

            wetnx = wetn['Year']
            wetny = wetn[' Mean']
            x = wetnx
            y = wetny
            m, b, endy, p_value, trend_text, mkr_p_value, mkr_trend_text, cols = trender(x, y)
            wetj = {'minyr': wetn_minyr, 'maxyr': wetn_maxyr, 'trend': trend_text, 'p': p_value}
            jsd["wet_full"] = wetj
            cols = pandas.DataFrame({'years_x': cols[:, 0], 'observations_y': cols[:, 1], 'l_predicted_y': cols[:, 2], 't_predicted_y': cols[:, 3], 'o_predicted_y': cols[:, 4]})
            cols_to_plot(cols['years_x'], cols['observations_y'], cols['o_predicted_y'], ['tab:blue', 'tab:gray', 1.0, 1.0], 13)

            ax = pyplot.gca()
            plotmax = max([max(cols['l_predicted_y']), max(cols['observations_y'])])
            pyplot.ylim(0, plotmax)
            pyplot.axis('tight')
            pyplot.xticks(cols['years_x'])
            width = 13
            pyplot.gcf().set_size_inches(width, width/1.618, forward=True)
            pyplot.setp(ax.get_xticklabels()[::2], visible=False)
            ax.annotate(txt, xy=(1, 1), xytext=(-12, -12), xycoords='axes fraction', fontsize=8, family='monospace', textcoords='offset points', ha='right', va='top', bbox=dict(facecolor='white', edgecolor='black', pad=5.0))
            pyplot.suptitle(which_wilderness + '\n' + nsname.title() + ' Wet Deposition Trends from ' + year_formatter(wetn_minyr) + ' to ' + year_formatter(wetn_maxyr), y=.95)

            fig1 = pyplot.gcf()
            if len(x) >= 21:
                ax = fig1.gca()
                temp = ax.xaxis.get_ticklabels()
                temp = list(set(temp) - set(temp[::2]))
                for label in temp:
                    label.set_visible(False)
            fig1.savefig(out_dir + slug_wilderness + '-wetdep-' + ns + '.png')
            fig1.clf()
            pyplot.clf()
            pyplot.cla()
            pyplot.close()
            extra_cols = [e for e in cols.columns if e not in ['years_x', 'observations_y', 'o_predicted_y']]
            cols = cols.drop(columns=extra_cols)
            cols.to_csv(out_dir + slug_wilderness + '-wetdep-' + ns + '.csv')
            log(slug_wilderness, 'GREEN', str(which_wilderness) + ' ' + ns + ' wetdep written')

            jsd = [jsd]

            jsc = ''.join(str(v) for v in jsd).replace('\'', '\"')
            with open(out_dir + 'index-wetdep-' + ns + '.json', 'w') as static_file:
                static_file.write(jsc)
