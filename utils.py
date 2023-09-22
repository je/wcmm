""" Utility functions. """

import os
from datetime import datetime

import colorama
import numpy
import pymannkendall_ as pymannkendall
import scipy
import shapely.geometry
import statsmodels.api as sm
from matplotlib import pyplot  # , colors
from osgeo import osr, ogr
from sklearn import linear_model
from pylint import lint
from pylint.reporters.text import TextReporter

from settings import *


# from _topojson import topojson
# import topojson


def uopen(*args, **kwargs):
    return open(*args, encoding="UTF-8", **kwargs)


def run_pylint(filename):
    file_py = "/Volumes/PATRIOT/wcmm/" + filename + ".py"
    lint_txt = base_dir + "_lint" + slash + filename + ".txt"
    ARGS = ["--output=" + lint_txt]
    arun = lint.Run([filename] + ARGS, exit=False)
    ascore = arun.linter.stats.global_note  # pylint score out of 10
    print(f"{ascore:2.4f}" + " ... " + filename)


def log(slug_wilderness, slug_agency, color, txt):
    if slug_wilderness is None:
        if not os.path.exists(base_dir + "_log" + slash):
            os.makedirs(base_dir + "_log" + slash)
        with uopen(
            base_dir + "_log" + slash + str(datetime.now().strftime("%Y%m%d")) + ".txt",
            "a",
        ) as logfile:
            logfile.write(
                str(datetime.now().strftime("%Y%m%d_%H%M")) + " " + txt + "\n"
            )
    elif slug_agency is None:
        with uopen(
            base_dir + slug_wilderness + slash + slug_wilderness + ".txt", "a"
        ) as logfile:
            logfile.write(
                str(datetime.now().strftime("%Y%m%d_%H%M")) + " " + txt + "\n"
            )
    else:
        with uopen(
            base_dir
            + slug_agency
            + slash
            + slug_wilderness
            + slash
            + slug_wilderness
            + ".txt",
            "a",
        ) as logfile:
            logfile.write(
                str(datetime.now().strftime("%Y%m%d_%H%M")) + " " + txt + "\n"
            )
    if color == "GREEN":
        print(
            colorama.Fore.GREEN
            + str(datetime.now().strftime("%Y%m%d_%H%M"))
            + colorama.Style.BRIGHT
            + " "
            + txt
        )
    if color == "CYAN":
        print(
            colorama.Fore.CYAN
            + str(datetime.now().strftime("%Y%m%d_%H%M"))
            + colorama.Style.BRIGHT
            + " "
            + txt
        )
    if color == "RED":
        print(
            colorama.Fore.RED
            + str(datetime.now().strftime("%Y%m%d_%H%M"))
            + colorama.Style.BRIGHT
            + " "
            + txt
        )
    if color == "WHITE":
        print(
            colorama.Fore.WHITE
            + str(datetime.now().strftime("%Y%m%d_%H%M"))
            + colorama.Style.BRIGHT
            + " "
            + txt
        )


def lines_poly(shp, clip_obj):
    poly = clip_obj.geometry.unary_union
    spatial_index = shp.sindex
    bbox = poly.bounds
    sidx = list(spatial_index.intersection(bbox))
    shp_sub = shp.iloc[sidx]
    clipped = shp_sub.copy()
    clipped["geometry"] = shp_sub.intersection(poly)
    final_clipped = clipped[clipped.geometry.notnull()]
    return final_clipped


def trend(x_list, y_list, cca):
    x_split = x_list.split()
    x_split = x_split[::-1]
    y_split = y_list.split()
    y_split = y_split[::-1]
    x_vals = [int(value) for value in x_split]
    y_vals = [float(value) for value in y_split]
    endy = y_vals[-1]

    xmin = min(x_vals)
    xmax = max(x_vals)
    x_array = numpy.array(x_vals)
    big_x = x_array[:, numpy.newaxis]

    y_array = numpy.array(y_vals)
    big_y = y_array[:, numpy.newaxis]

    pyplot.scatter(x_vals, y_vals, color=cca[1], marker="x", s=40)
    line_x = numpy.array([xmin, xmax])

    lm = linear_model.TheilSenRegressor()
    lm.fit(big_x, big_y.ravel())
    params = numpy.append(lm.intercept_, lm.coef_)
    predictions = lm.predict(big_x)

    y_pred = lm.predict(line_x.reshape(2, 1))

    newX = numpy.append(numpy.ones((len(big_x), 1)), big_x, axis=1)
    MSE = (sum((big_y.ravel() - predictions) ** 2)) / (len(newX) - len(newX[0]))

    var_b = MSE * (numpy.linalg.inv(numpy.dot(newX.T, newX)).diagonal())
    sd_b = numpy.sqrt(var_b)
    ts_b = params / sd_b
    p_values = [
        2 * (1 - scipy.stats.t.cdf(numpy.abs(i), (len(newX) - 1))) for i in ts_b
    ]
    sd_b = numpy.round(sd_b, 3)
    ts_b = numpy.round(ts_b, 3)
    p_values = numpy.round(p_values, 20)
    params = numpy.round(params, 4)

    p_value = p_values[1]

    years = []
    for row in x_vals:
        years.append(row)
    y_theil = []
    m = (y_pred[1] - y_pred[0]) / (xmax - xmin)
    b = y_pred[0] - (m * xmin)
    for row in x_vals:
        y_theil.append(m * row + b)
    cols = numpy.column_stack([years, y_vals])
    cols = numpy.column_stack([cols, y_theil])
    pyplot.plot(line_x, y_pred, color=cca[0], alpha=cca[2], linewidth=2, label=None)

    ymax = max(y_vals)
    pmax = max(y_pred)
    plotmax = max([pmax, ymax])
    pyplot.ylim(0, plotmax)

    width = 13
    pyplot.axis("tight")
    pyplot.xticks(x_vals)
    fig2 = pyplot.gcf()
    fig2.set_size_inches(width, width / 1.618, forward=True)
    return [m, b, endy, p_value, cols]


def trend2(x_list, y_list, cca):
    x_split = x_list.split()
    x_split = x_split[::-1]
    y_split = y_list.split()
    y_split = y_split[::-1]
    x_vals = [int(value) for value in x_split]
    y_vals = [float(value) for value in y_split]
    endy = y_vals[-1]
    xmin = min(x_vals)
    xmax = max(x_vals)
    x_array = numpy.array(x_vals)
    big_x = x_array[:, numpy.newaxis]

    y_array = numpy.array(y_vals)
    big_y = y_array[:, numpy.newaxis]

    pyplot.scatter(x_vals, y_vals, color=cca[1], marker="x", s=40)
    line_x = numpy.array([xmin, xmax])

    lm = linear_model.TheilSenRegressor()
    lm.fit(big_x, big_y.ravel())
    params = numpy.append(lm.intercept_, lm.coef_)
    predictions = lm.predict(big_x)

    y_pred = lm.predict(line_x.reshape(2, 1))

    newX = numpy.append(numpy.ones((len(big_x), 1)), big_x, axis=1)
    MSE = (sum((big_y.ravel() - predictions) ** 2)) / (len(newX) - len(newX[0]))

    var_b = MSE * (numpy.linalg.inv(numpy.dot(newX.T, newX)).diagonal())
    sd_b = numpy.sqrt(var_b)
    ts_b = params / sd_b
    p_values = [
        2 * (1 - scipy.stats.t.cdf(numpy.abs(i), (len(newX) - 1))) for i in ts_b
    ]
    sd_b = numpy.round(sd_b, 3)
    ts_b = numpy.round(ts_b, 3)
    p_values = numpy.round(p_values, 20)
    params = numpy.round(params, 4)

    p_value = p_values[1]

    years = []
    for row in x_vals:
        years.append(row)
    y_theil = []
    m = (y_pred[1] - y_pred[0]) / (xmax - xmin)
    b = y_pred[0] - (m * xmin)
    for row in x_vals:
        y_theil.append(m * row + b)

    cols = numpy.column_stack([years, y_vals])  # x y
    cols = numpy.column_stack([cols, y_theil])  # x y yp_theil
    if m > 0 and p_value <= 0.05:
        trend_text = "increasing"
    elif m < 0 and p_value <= 0.05:
        trend_text = "decreasing"
    else:
        trend_text = "flat"

    if len(y_vals) < 2:
        m_ = None
        b_ = None
        endy_ = y_vals[0]
        p_value_ = None
        trend_text_ = None
    else:
        lr = scipy.stats.linregress(years, y_vals)
        m_ = lr[0]
        b_ = lr.intercept
        endy_ = y_vals[-1]
        p_value_ = lr[3]
        if m_ > 0 and p_value_ <= 0.05:
            trend_text_ = "increasing"
        elif m_ < 0 and p_value_ <= 0.05:
            trend_text_ = "decreasing"
        else:
            trend_text_ = "flat"
        cols_ = numpy.column_stack([years, y_vals])  # x y
        y_lr = []
        for row in years:
            y_lr.append(m_ * row + b_)
        cols_ = numpy.column_stack([cols_, y_lr])  # x y yp_ols

        print(m)  # -0.02097188747687362
        print(m_)  # 0.0234497862976867
        print(b)  # 52.53574048597397
        print(b_)  # -37.2892822022046
        print(endy)  # 8.296277046203613
        print(endy_)  # 8.296277046203613
        print(p_value)  # 0.7863119445461875
        print(p_value_)  # 0.7510488092136175
        print(trend_text)
        print(trend_text_)
        print(cols)
        print(cols_)
        # quit()

        pyplot.plot(years, y_lr, color=cca[0], alpha=cca[2], linewidth=2, label=None)

        ymax = max(y_vals)
        pmax = max(y_lr)
        plotmax = max([pmax, ymax])
        pyplot.ylim(0, plotmax)

        width = 13
        pyplot.axis("tight")
        pyplot.xticks(years)
        fig2 = pyplot.gcf()
        fig2.set_size_inches(width, width / 1.618, forward=True)
    return [m_, b_, endy_, p_value_, trend_text_, cols_]


def trend2_map(x_list, y_list, cca):

    # x_list = [2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006]
    # y_list = [0.4921320393, 0.4485062093, 0.4785704492, 0.5799515845, 0.4318211788, 0.5892534651, 0.5541802599, 0.4207925377, 0.4470462941, 0.4843444263, 0.3555758837, 0.4735326792, 0.4311118409, 0.4865506047, 0.4254581905]

    # x_list = [5, 23, 25, 48, 17, 8, 4, 26, 11, 19, 14, 35, 29, 4, 23]
    # y_list = [80, 78, 60, 53, 85, 84, 73, 79, 81, 75, 68, 72, 58, 92, 65]

    dictionary = dict(zip(x_list, y_list))
    # dictionary = dict(sorted(dictionary.items()))

    # dictionary = dict(kv for kv in dictionary.items() if kv[0] >= int(wilderness_designation_year))
    print(dictionary)
    # quit()

    x_list = list(dictionary.keys())
    y_list = list(dictionary.values())

    x = numpy.asarray(x_list)
    y = numpy.asarray(y_list)
    X = statsmodels.api.add_constant(x, prepend=False)

    mod = statsmodels.api.OLS(y, X)
    # mod = statsmodels.api.OLS(spector_data.endog, spector_data.exog)
    res = mod.fit()
    print(res.summary())
    p_values = res.summary2().tables[1]["P>|t|"]
    txt1 = p_values.x1
    xmin = min(x_list)
    xmax = max(x_list)

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    txt2 = p_value
    print(slope)
    if txt1 > 0.05:
        trend = "stable"
    elif slope > 0:
        trend = "increasing"
    elif slope < 0:
        trend = "decreasing"
    txt = trend + " trend (signifigance: p=" + p_formatter(txt1) + ")"

    pred_ols = res.get_prediction()

    mean = pred_ols.summary_frame()["mean"]
    mean_l = pred_ols.summary_frame()["mean_ci_lower"]
    mean_u = pred_ols.summary_frame()["mean_ci_upper"]
    iv_l = pred_ols.summary_frame()["obs_ci_lower"]
    iv_u = pred_ols.summary_frame()["obs_ci_upper"]
    beta = [0, 1]

    x_vals = [int(value) for value in x_split]
    y_vals = [float(value) for value in y_split]

    years = []
    for row in x_vals:
        years.append(row)
    y_ols = []
    m = (pred_ols[1] - pred_ols[0]) / (xmax - xmin)
    b = pred_ols[0] - (m * xmin)
    for row in x_vals:
        y_ols.append(m * row + b)
    cols = numpy.column_stack([years, y_vals])
    cols = numpy.column_stack([cols, y_ols])

    jsd = [
        {
            "yr_min": year_formatter(xmin),
            "yr_max": year_formatter(xmax),
            "endy": float_formatter(intercept),
            "m": float_formatter(slope),
            "trend": trend,
            "p": p_formatter(p_value),
        }
    ]
    return [slope, intercept, endy, p_value, trend, cols]


def trend3(x_list, y_list, cca):
    x_list = [int(i) for i in x_list.split()]
    y_list = [float(i) for i in y_list.split()]
    print(x_list)
    print(y_list)
    dictionary = dict(zip(x_list, y_list))
    # dictionary = dict(sorted(dictionary.items()))

    x_list = list(dictionary.keys())
    y_list = list(dictionary.values())

    x = numpy.asarray(x_list)
    y = numpy.asarray(y_list)
    X = sm.add_constant(x, prepend=False)

    mod = sm.OLS(y, X)
    # mod = sm.OLS(spector_data.endog, spector_data.exog)
    res = mod.fit()
    print(res.summary())
    p_values = res.summary2().tables[1]["P>|t|"]
    txt1 = p_values.x1

    from scipy import stats

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    txt2 = p_value
    print(slope)
    if txt1 > 0.05:
        trend = "stable"
    elif slope > 0:
        trend = "increasing"
    elif slope < 0:
        trend = "decreasing"
    txt = trend + " trend (signifigance: p=" + str(txt1) + ")"

    pred_ols = res.get_prediction()

    mean = pred_ols.summary_frame()["mean"]
    mean_l = pred_ols.summary_frame()["mean_ci_lower"]
    mean_u = pred_ols.summary_frame()["mean_ci_upper"]
    iv_l = pred_ols.summary_frame()["obs_ci_lower"]
    iv_u = pred_ols.summary_frame()["obs_ci_upper"]
    beta = [0, 1]

    pyplot.plot(x, y, color=cca[0], alpha=cca[2], linewidth=2, label=None)

    cols = numpy.column_stack([x, y])
    # cols = numpy.column_stack([cols, y_theil])
    endy = y[0]
    ymax = max(y)
    pmax = max(res.fittedvalues)
    plotmax = max([pmax, ymax])
    pyplot.ylim(0, plotmax)

    width = 13
    pyplot.axis("tight")
    pyplot.xticks(x)
    fig2 = pyplot.gcf()
    fig2.set_size_inches(width, width / 1.618, forward=True)
    return [slope, intercept, endy, p_value, trend, cols]


def more():
    fig, ax = pyplot.subplots(figsize=(8, 6))

    ax.plot(
        x,
        y,
        color="black",
        linestyle="none",
        marker="o",
        markerfacecolor="black",
        label="observed",
    )
    # ax.plot(x, mean, "b--.", label="true")
    ax.plot(x, res.fittedvalues, "r--", label="OLS trend")
    ax.plot(x, mean_u, "b--")
    ax.plot(x, mean_l, "b--")
    ax.plot(x, iv_u, "g--")
    ax.plot(x, iv_l, "g--")
    ax.legend(loc="best")
    ax.annotate(
        txt,
        xy=(0.9, 0.9),
        xytext=(-200, -0),
        xycoords=("figure fraction", "figure fraction"),
        textcoords="offset points",
        bbox={"facecolor": "white", "edgecolor": "black", "pad": 5.0},
        size=8,
        family="monospace",
        ha="left",
        va="bottom",
    )
    pyplot.show()


def trend_test():
    tdata = [
        8.015265464782715,
        3.227195978164673,
        3.217073917388916,
        11.468589782714844,
        4.155986785888672,
        9.9461088180542,
        3.653317928314209,
        3.270510911941528,
        2.896094083786011,
        3.279099941253662,
        2.279714107513428,
        2.495779991149902,
        5.651147842407227,
        2.597424983978271,
        2.94126296043396,
        3.546931028366089,
        3.980052947998047,
        3.911618947982788,
        6.089375019073486,
    ]
    ssr = pymannkendall.sens_slope(tdata)
    print(ssr)
    mkr = pymannkendall.original_test(tdata)
    print(mkr)


# preprocessing
def __preprocessing(x):
    x = numpy.asarray(x).astype(float)
    dim = x.ndim

    if dim == 1:
        c = 1

    elif dim == 2:
        (n, c) = x.shape

        if c == 1:
            dim = 1
            x = x.flatten()

    else:
        print("Please check your dataset.")

    return x, c


# missing values analysis
def __missing_values_analysis(x, method="skip"):
    if method.lower() == "skip":
        if x.ndim == 1:
            x = x[~numpy.isnan(x)]

        else:
            x = x[~numpy.isnan(x).any(axis=1)]

    n = len(x)

    return x, n


# vectorization approach to calculate mk score, S
def __mk_score(x, n):
    s = 0

    demo = numpy.ones(n)
    for k in range(n - 1):
        s = (
            s
            + numpy.sum(demo[k + 1 : n][x[k + 1 : n] > x[k]])
            - numpy.sum(demo[k + 1 : n][x[k + 1 : n] < x[k]])
        )

    return s


# standardized test statistic Z
def __z_score(s, var_s):
    if s > 0:
        z = (s - 1) / numpy.sqrt(var_s)
    elif s == 0:
        z = 0
    elif s < 0:
        z = (s + 1) / numpy.sqrt(var_s)

    return z


# original Mann-Kendal's variance S calculation
def __variance_s(x, n):
    # calculate the unique data
    unique_x = numpy.unique(x)
    g = len(unique_x)

    # calculate the var(s)
    if n == g:  # there is no tie
        var_s = (n * (n - 1) * (2 * n + 5)) / 18

    else:  # there are some ties in data
        tp = numpy.zeros(unique_x.shape)
        demo = numpy.ones(n)
        # print(demo)
        for i in range(g):
            # print(x)
            # print(unique_x[i])
            # print(x == unique_x[i])
            # print(demo[x == unique_x[i]])
            tp[i] = numpy.sum(demo[x == unique_x[i]])
            # print(tp[i])
        # print(tp)

        var_s = (
            n * (n - 1) * (2 * n + 5) - numpy.sum(tp * (tp - 1) * (2 * tp + 5))
        ) / 18

    return var_s


# calculate the p_value
from scipy.stats import norm


def __p_value(z, alpha):
    # two tail test
    p = 2 * (1 - norm.cdf(abs(z)))
    h = abs(z) > norm.ppf(1 - alpha / 2)
    # print('ppf=' + str(norm.ppf(0.975)))

    if (z < 0) and h:
        trend = "decreasing"
    elif (z > 0) and h:
        trend = "increasing"
    else:
        trend = "no trend"

    return p, h, trend


def sens(endog, exog):

    # null hypothesis (H0) assumes there is no trend in the series
    # alternative hypothesis (H1) assumes there is a trend in the series

    # Mann Kendall is a trend test to give you trend statistics by which
    # you can calculate p value and z value etc. and by Sen's slope you
    # can calculate magnitude of change in a variable. for example the
    # amount of increase or decrease in rainfall over period.

    X1 = numpy.asarray(exog)
    Y1 = numpy.asarray(endog)
    x = X1.reshape(len(X1), 1)
    y = Y1.reshape(len(Y1), 1).ravel()
    # log(None, 'GREEN', ' ' + str(x)) # first year

    lr = scipy.stats.linregress(exog, endog)
    print(lr)
    quit()

    x, c = __preprocessing(Y1)
    # print(x)
    # print(c)
    x, n = __missing_values_analysis(x, method="skip")
    # print(x)
    # print(n)
    s = __mk_score(x, n)
    var_s = __variance_s(x, n)
    z = __z_score(s, var_s)
    alpha = 0.05
    p, h, trend = __p_value(z, alpha)
    print(p)
    print(h)
    print(trend)
    # quit()

    X1 = numpy.asarray(exog)
    Y1 = numpy.asarray(endog)
    x = X1.reshape(len(X1), 1)
    y = Y1.reshape(len(Y1), 1).ravel()
    print(endog)
    print(Y1)
    print(y)
    endog = y
    s_pmk = pymannkendall.sens_slope(endog)
    s_pmk_intreal = s_pmk.intercept - (x * s_pmk.slope)
    s_pmk_pline = s_pmk.slope * X1 + s_pmk_intreal[0][0]
    s_pmk_result = pymannkendall.original_test(endog)
    log(None, None, "GREEN", "sen slope      " + str(s_pmk.slope))
    log(None, None, "GREEN", "intercept nom  " + str(s_pmk.intercept))
    log(None, None, "GREEN", "intercept year " + str(s_pmk_intreal[0][0]))
    log(None, None, "GREEN", "predicted line " + str(s_pmk_pline))
    log(None, None, "GREEN", "result trend " + str(s_pmk_result.trend))
    log(None, None, "GREEN", "result h     " + str(s_pmk_result.h))
    log(None, None, "GREEN", "result p     " + str(s_pmk_result.p))
    log(None, None, "GREEN", "result z     " + str(s_pmk_result.z))
    log(None, None, "GREEN", "result Tau   " + str(s_pmk_result.Tau))
    log(None, None, "GREEN", "result s     " + str(s_pmk_result.s))
    log(None, None, "GREEN", "result var_s " + str(s_pmk_result.var_s))
    log(None, None, "GREEN", "result slope " + str(s_pmk_result.slope))
    log(None, None, "GREEN", "result int   " + str(s_pmk_result.intercept))

    s_scipy_s = scipy.stats.mstats.theilslopes(endog, exog)
    s_scipy_pred = s_scipy_s[1] + (s_scipy_s[0] * x)
    s_scipy_pline = s_scipy_s[0] * X1 + s_scipy_s[1]
    s_scipy_result = scipy.stats.mstats.kendalltau(endog, exog)
    log(None, None, "CYAN", "sen slope      " + str(s_scipy_s[0]))
    log(None, None, "CYAN", "intercept nom  " + str(s_scipy_pred[0][0]))
    log(None, None, "CYAN", "intercept year " + str(s_scipy_s[1]))
    log(None, None, "CYAN", "predicted line " + str(s_scipy_pline))
    log(None, None, "CYAN", "result       " + str(s_scipy_result))
    log(None, None, "CYAN", "result trend " + str(s_scipy_result.trend))
    log(None, None, "CYAN", "result h     " + str(s_scipy_result.h))
    log(None, None, "CYAN", "result p     " + str(s_scipy_result.pvalue))
    log(None, None, "CYAN", "result z     " + str(s_scipy_result.z))
    log(None, None, "CYAN", "result Tau   " + str(s_scipy_result.correlation))
    log(None, None, "CYAN", "result s     " + str(s_scipy_result.s))
    log(None, None, "CYAN", "result var_s " + str(s_scipy_result.var_s))
    log(None, None, "CYAN", "result slope " + str(s_scipy_result.slope))
    log(None, None, "CYAN", "result int   " + str(s_scipy_result.intercept))

    from sklearn.linear_model import TheilSenRegressor

    s_sklearn = TheilSenRegressor().fit(x, y)
    s_sklearn_pred = s_sklearn.intercept_ + (s_sklearn.coef_ * x)
    s_sklearn_pline = s_sklearn.coef_[0] * X1 + s_sklearn.intercept_
    log(None, None, "RED", "sen slope      " + str(s_sklearn.coef_[0]))
    log(None, None, "RED", "intercept nom  " + str(s_sklearn_pred[0][0]))
    log(None, None, "RED", "intercept year " + str(s_sklearn.intercept_))
    log(None, None, "RED", "predicted line " + str(s_sklearn_pline))

    # Once you've fit your model using whatever method you like, you can
    # compute the Pearson correlation on your data using your linear model.

    tsr = TheilSenRegressor()
    tsr2 = tsr.fit(x, y)
    params = numpy.append(tsr.intercept_, tsr.coef_)

    y_theil = []
    y_pred = tsr.predict(x)  # (line_x.reshape(2, 1))
    m = (y_pred[1] - y_pred[0]) / (max(x) - min(x))
    b = y_pred[0] - (m * min(x))
    endy = y[-1]
    for row in x:
        y_theil.append(m * row + b)

    X = x
    yt = y_theil
    m_ = numpy.nanmedian(y)
    n_ = numpy.median(numpy.arange(len(endog)))
    intercept = m_ - n_ * s_pmk.slope  # or median(x) - (n-1)/2 *slope
    # print(str(m_))
    # print(str(n_))
    # print(str(intercept))

    ols_model = sm.OLS(yt, X)
    ols_results = ols_model.fit()
    print(ols_results.params)
    X2 = sm.add_constant(X)
    ols_model = sm.OLS(yt, X2)
    ols_results = ols_model.fit()
    print(ols_results.params)
    quit()

    liney = s_pmk.slope * X1 + s_pmk.intercept
    print(liney)

    ols_model = sm.OLS(liney, x)
    ols_results = ols_model.fit()
    print(ols_results.summary())
    print(ols_results.pvalues)
    print(ols_results.pvalues[0])
    print(ols_results.params)

    # compute the weighted 𝑟2 where the weights are those coming from your fitting routine.
    # s_sklearn_score = s_sklearn.score(x, y)
    # print(s_sklearn_score)

    quit()


def trend_test2(endog, exog):
    from scipy import stats
    import time
    import pandas
    import matplotlib.pyplot as plt

    start_time = time.time()
    tdata = [
        8.015265464782715,
        3.227195978164673,
        3.217073917388916,
        11.468589782714844,
        4.155986785888672,
        9.9461088180542,
        3.653317928314209,
        3.270510911941528,
        2.896094083786011,
        3.279099941253662,
        2.279714107513428,
        2.495779991149902,
        5.651147842407227,
        2.597424983978271,
        2.94126296043396,
        3.546931028366089,
        3.980052947998047,
        3.911618947982788,
        6.089375019073486,
    ]
    years = [
        2000,
        2001,
        2002,
        2003,
        2004,
        2005,
        2006,
        2007,
        2008,
        2009,
        2010,
        2011,
        2012,
        2013,
        2014,
        2015,
        2016,
        2017,
        2018,
    ]
    tdata = [
        0.07900000000000001,
        0.083,
        0.079,
        0.07400000000000001,
        0.073,
        0.075,
        0.07300000000000001,
        0.07,
        0.07300000000000001,
        0.07200000000000001,
        0.07100000000000001,
        0.059000000000000004,
        0.068,
        0.067,
        0.063,
        0.061000000000000026,
        0.064,
        0.058,
        0.062,
        0.064,
        0.062,
    ]  # ocala ymca
    years = [
        1998,
        1999,
        2000,
        2001,
        2002,
        2003,
        2004,
        2005,
        2006,
        2007,
        2008,
        2009,
        2010,
        2011,
        2012,
        2013,
        2014,
        2015,
        2016,
        2017,
        2018,
    ]
    tdf = pandas.DataFrame(({"year": years, "v": tdata}))
    tdf = pandas.DataFrame(({"year": exog, "v": endog}))
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        tdf["year"], tdf["v"]
    )
    print("The p-value between the 2 variables is measured as " + str(p_value) + "\n")
    print(
        "Least squares linear model coefficients, intercept = "
        + str(intercept)
        + ". Slope = "
        + str(slope)
        + "\n"
    )
    regressLine = intercept + tdf["year"] * slope
    res = stats.theilslopes(tdf["v"], tdf["year"], 0.95)
    print(
        "Thiel-Sen linear model coefficients, intercept = "
        + str(res[1])
        + ". Slope = "
        + str(res[0])
        + "\n"
    )
    plt.clf()
    plt.scatter(tdf["year"], tdf["v"], s=3, label="Allele frequency")
    plt.plot(tdf["year"], regressLine, label="Least squares regression line")
    plt.plot(
        tdf["year"],
        res[1] + res[0] * tdf["year"],
        "r-",
        label="Theil-Sen regression line",
    )
    # Add Theil-Sen confidence intervals
    plt.plot(
        tdf["year"],
        res[1] + res[2] * tdf["year"],
        "r--",
        label="Theil-Sen 95% confidence interval",
    )
    plt.plot(tdf["year"], res[1] + res[3] * tdf["year"], "r--")
    plt.legend(loc="upper left")
    plt.xlabel("Year")
    plt.ylabel("trend")
    plt.savefig("pythonRegress.png")
    end_time = time.time()
    print("Elapsed time = " + str(end_time - start_time) + " seconds")


def try_add_basemap_(slug_wilderness, axis, crs):
    log(slug_wilderness, None, "ORANGE", slug_wilderness + " basemap skipped")


def try_add_basemap(slug_wilderness, slug_agency, axis, crs):  ## too slow
    crs_epsg = str(crs)
    log(
        slug_wilderness,
        slug_agency,
        "WHITE",
        slug_wilderness + " adding terrain basemap " + crs_epsg,
    )
    try:
        contextily.add_basemap(axis, zoom=14, crs=crs)
        log(
            slug_wilderness,
            slug_agency,
            "CYAN",
            slug_wilderness + " basemap added at zoom 14",
        )
    except:
        log(slug_wilderness, slug_agency, "WHITE", slug_wilderness + " trying zoom 13")
        try:
            contextily.add_basemap(axis, zoom=13, crs=crs)
            log(
                slug_wilderness,
                slug_agency,
                "CYAN",
                slug_wilderness + " basemap added at zoom 13",
            )
        except:
            log(
                slug_wilderness,
                slug_agency,
                "WHITE",
                slug_wilderness + " trying zoom 12",
            )
            try:
                contextily.add_basemap(axis, zoom=12, crs=crs)
                log(
                    slug_wilderness,
                    slug_agency,
                    "CYAN",
                    slug_wilderness + " basemap added at zoom 12",
                )
            except:
                log(
                    slug_wilderness,
                    slug_agency,
                    "WHITE",
                    slug_wilderness + " trying zoom 11",
                )
                try:
                    contextily.add_basemap(axis, zoom=11, crs=crs)
                    log(
                        slug_wilderness,
                        slug_agency,
                        "CYAN",
                        slug_wilderness + " basemap added at zoom 11",
                    )
                except:
                    log(
                        slug_wilderness,
                        slug_agency,
                        "WHITE",
                        slug_wilderness + " trying zoom 10",
                    )
                    try:
                        contextily.add_basemap(axis, zoom=10, crs=crs)
                        log(
                            slug_wilderness,
                            slug_agency,
                            "CYAN",
                            slug_wilderness + " basemap added at zoom 10",
                        )
                    except:
                        log(
                            slug_wilderness,
                            slug_agency,
                            "RED",
                            slug_wilderness + " basemap fail",
                        )


# from shapely.geometry.polygon import Polygon
# from shapely.geometry.multipolygon import MultiPolygon
def gdf_to_multigeometry(gdf):
    gdf["geometry"] = [
        shapely.geometry.multipolygon.MultiPolygon([feature])
        if type(feature) == shapely.geometry.polygon.Polygon
        else feature
        for feature in gdf["geometry"]
    ]
    gdf["geometry"] = [
        shapely.geometry.multilinestring.MultiLineString([feature])
        if type(feature) == shapely.geometry.linestring.LineString
        else feature
        for feature in gdf["geometry"]
    ]
    gdf["geometry"] = [
        shapely.geometry.multipoint.MultiPoint([feature])
        if type(feature) == shapely.geometry.point.Point
        else feature
        for feature in gdf["geometry"]
    ]


def cast_to_multigeometry(geom):
    upcast_dispatch = {
        shapely.geometry.Point: shapely.geometry.MultiPoint,
        shapely.geometry.LineString: shapely.geometry.MultiLineString,
        shapely.geometry.Polygon: shapely.geometry.MultiPolygon,
    }
    caster = upcast_dispatch.get(type(geom), lambda x: x[0])
    return caster([geom])


def graph_objs(foo):
    import objgraph

    fooname = f"{foo=}".split("=")[0]
    objgraph.show_refs(
        [foo],
        filename=base_dir
        + "og-"
        + str(datetime.now().strftime("%Y%m%d_%H%M"))
        + fooname
        + ".png",
    )


def ptest():
    import pandas
    import numpy
    from sklearn.linear_model import LinearRegression

    model = LinearRegression(fit_intercept=True)

    csv_file = (
        base_dir
        + "output"
        + slash
        + "big-gum-swamp-wilderness"
        + slash
        + "big-gum-swamp-wilderness-wetdep-n.csv"
    )
    wet = pandas.read_csv(csv_file)
    x = wet.years_x[:31]  # .sort_values(ascending=False)
    y = wet.observations_y[:31]
    m2 = model.fit(x[:, numpy.newaxis], y)
    print(m2.coef_)

    xfit = numpy.linspace(x.min(), x.max())
    yfit = model.predict(xfit[:, numpy.newaxis])

    import statsmodels.api as sm

    X = x
    y = y

    X2 = sm.add_constant(X)
    est = sm.OLS(y, X2)
    est2 = est.fit()
    print(est2.summary())
    print(est2.pvalues["years_x"])
    print(est2.params)

    import pymannkendall_ as pymannkendall

    ssr = pymannkendall.sens_slope(y)
    mkr = pymannkendall.original_test(y)
    m = ssr
    p_value = mkr.p
    trend_text = mkr.trend
    print(mkr)


def trender(years_x, observations_y):
    o = observations_y.values[::-1]
    ssr = pymannkendall.sens_slope(o)
    mkr = pymannkendall.original_test(o)
    m = ssr
    mkr_p_value = mkr.p
    mkr_trend_text = mkr.trend
    if mkr.trend == "no trend":
        mkr_trend_text = "flat"

    # print(years_x.to_string(index=False))
    # print(observations_y.to_string(index=False))
    # print(o)

    lr = scipy.stats.linregress(years_x, observations_y)
    # print(lr)

    length = len(observations_y)
    x = years_x.values.reshape(length, 1)
    y = observations_y.values.reshape(length, 1)

    regr = linear_model.LinearRegression()
    regr2 = regr.fit(x, y.ravel())
    params = numpy.append(regr.intercept_, regr.coef_)

    y_lin = []
    y_pred = regr.predict(x)

    m = (y_pred[1] - y_pred[0]) / (max(x) - min(x))
    b = y_pred[0] - (m * min(x))
    endy = y[-1]
    for row in x:
        y_lin.append(m * row + b)
    cols = numpy.column_stack([x, y])
    cols = numpy.column_stack([cols, y_pred])

    tsr = linear_model.TheilSenRegressor()
    tsr2 = tsr.fit(x, y.ravel())
    params = numpy.append(tsr.intercept_, tsr.coef_)

    y_theil = []
    yt_pred = tsr.predict(x)  # (line_x.reshape(2, 1))
    m = (yt_pred[1] - yt_pred[0]) / (max(x) - min(x))
    b = yt_pred[0] - (m * min(x))
    endy = y[-1]
    for row in x:
        y_theil.append(m * row + b)
    cols = numpy.column_stack([cols, yt_pred])

    X = x
    y = y

    X2 = sm.add_constant(X)
    est = sm.OLS(y, X2)
    est2 = est.fit()
    y_pred = est2.params
    # print(y_pred)
    # quit()

    y_ols = []
    m = y_pred[1]
    b = y_pred[0]
    endy = y[-1]

    # print(numpy.polyfit(x,y,deg=1))
    # print(scipy.stats.linregress(x,y))

    # lr_std_err = lr.intercept_stderr
    # print(lr_std_err)
    # print(est2.summary())
    # print(est2.summary2())
    # quit()
    p_value = est2.pvalues[1]
    if m > 0 and p_value <= 0.05:
        trend_text = "increasing"
    elif m < 0 and p_value <= 0.05:
        trend_text = "decreasing"
    else:
        trend_text = "flat"
    for row in x:
        y_ols.append(m * row + b)
    cols = numpy.column_stack([cols, y_ols])
    m_ = lr[0]
    b_ = lr.intercept
    endy_ = y[-1]
    p_value_ = lr[3]
    if m_ > 0 and p_value_ <= 0.05:
        trend_text_ = "increasing"
    elif m < 0 and p_value_ <= 0.05:
        trend_text_ = "decreasing"
    else:
        trend_text_ = "flat"
    cols_ = numpy.column_stack([x, y])
    y_lr = []
    for row in x:
        y_lr.append(m_ * row + b_)
    cols_ = numpy.column_stack([cols_, y_lr])
    cols_ = numpy.column_stack([cols_, yt_pred])
    cols_ = numpy.column_stack([cols_, y_ols])
    # print(m)
    print(m_)
    # print(b)
    print(b_)
    # print(endy)
    print(endy_)
    # print(p_value)
    print(p_value_)
    # print(trend_text)
    print(trend_text_)
    print(cols)
    # print(cols_)
    # quit()
    # print(trend_text)
    # print(p_value) # nan
    # print(mkr_trend_text)
    # print(mkr_p_value) # 1.0
    return [m_, b_, endy_, p_value_, trend_text_, mkr_p_value, mkr_trend_text, cols_]


def cols_to_plot(years_x, observations_y, predicted_y, ccaa, width):
    width = width
    pyplot.scatter(
        years_x, observations_y, color=ccaa[1], alpha=ccaa[3], marker="x", s=40
    )
    pyplot.plot(
        years_x, predicted_y, color=ccaa[0], alpha=ccaa[2], linewidth=2, label=None
    )


def cols_to_plot2(years_x, observations_y, predicted_y, ccaalm, width):
    width = width
    pyplot.scatter(
        years_x,
        observations_y,
        color=ccaalm[1],
        alpha=ccaalm[3],
        marker=ccaalm[5],
        s=40,
    )
    pyplot.plot(
        years_x,
        predicted_y,
        color=ccaalm[0],
        alpha=ccaalm[2],
        linewidth=ccaalm[4],
        label=None,
    )
