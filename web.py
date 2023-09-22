""" Functions for pulling versioned data from distant websites prior to
analysis, and for collecting files and building web pages once trends are
done.
"""

import csv
import json
import traceback
from shutil import copyfile
from urllib.parse import urlparse
from urllib.request import urlretrieve

import dateutil.parser as dparser
import geopandas
import pandas
import requests
import topojson
from bs4 import BeautifulSoup  # , SoupStrainer
from django.template.loader import get_template
from django.utils.text import slugify

from utils import *


def get_nwps():  # failures
    # queryURL = 'https://attains.epa.gov/attains-public/api/assessments?organizationId=' + row.organizationid + '&assessmentUnitIdentifier=' + row.assessmentunitidentifier + '&reportingCycle=' + str(year)
    queryURL = "https://services1.arcgis.com/ERdCHt0sNM6dENSD/ArcGIS/rest/services/Wilderness_Areas_in_the_United_States/FeatureServer/0/query?where=Designated+IS+NOT+NULL&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=&returnGeometry=true&returnCentroid=false&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=html&token="
    cycle_json = "nwps.json"
    response = requests.get(queryURL)
    print(response)
    json = response.json()
    recs = json["items"]
    if not recs:
        log(None, None, "WHITE", "no records")
    else:
        with uopen(base_dir + cycle_json, "wb") as outf:
            outf.write(response.content)
        log(None, None, "CYAN", " writing " + cycle_json)


def get_slug(row):
    return slugify(row["name"])


def get_agency(row):  # ['BLM', 'FS', 'FWS', 'NPS']
    if row["Agency"] == "FS":
        agency = "1"
    if row["Agency"] == "BLM":
        agency = "2"
    if row["Agency"] == "FWS":
        agency = "3"
    if row["Agency"] == "NPS":
        agency = "4"
    return agency


def get_date_from_dyear(row):
    # print(row['Designated'])
    if row["Designated"] >= 1960 and row["Designated"] <= 9999:
        return str(row["Designated"]) + "-01-01"


def get_agency_name_state(row):
    # print(row['Designated'])
    return row["Agency"] + " " + row["state"] + " " + row["name"]


def get_name_state(row):
    if row.name.isin(nwps_agency_name.name):
        row["name"] = row["name"] + row["state"]
        print(row["state"] + " " + row["name"])
        return row["state"] + " " + row["name"]
    else:
        return row["name"]


def get_name_plus_id(row):
    # print(row['Designated'])
    if row["unique"] is False:
        print(row["name"] + " " + str(row["id"]))
        return row["name"] + " " + str(row["id"])
    else:
        return row["name"]


def nwps_wilderness_json():
    nwps_json = data_dir + slash + "_wilderness" + slash + "nwps-2022-12-15.json"
    nwps_gdf = geopandas.read_file(nwps_json)
    # print(nwps_gdf.columns)
    renames = {
        "NAME": "name",
        "STATE": "state",
        "Acreage": "acreage",
        "Description": "description",
        "Comment": "comment",
    }
    nwps_gdf = nwps_gdf.rename(index=str, columns=renames)
    extra_cols = [
        e
        for e in nwps_gdf.columns
        if e
        not in [
            "WID",
            "name",
            "Designated",
            "Agency",
            "state",
            "acreage",
            "description",
            "comment",
            "geometry",
        ]
    ]

    nwps_gdf = nwps_gdf.drop(columns=extra_cols)
    nwps_gdf["name"] = nwps_gdf["name"].str.replace(" Wilderness", "")
    a = nwps_gdf["Agency"].unique()
    nwps_gdf["agency"] = nwps_gdf.apply(get_agency, axis=1)
    nwps_wid = nwps_gdf[nwps_gdf[["WID"]].duplicated()]
    nwps_agency_name = nwps_gdf[nwps_gdf[["Agency", "name"]].duplicated()]

    # nwps_gdf['name'] = nwps_gdf.apply(get_name_state, axis=1)
    # nwps_gdf['name']=nwps_gdf['name'].isin().astype(int)
    # print(nwps_wid.head)
    # print(nwps_agency_name.head)
    # quit()

    nwps_gdf["agency_name_state"] = nwps_gdf.apply(get_agency_name_state, axis=1)
    # nwps_gdf['unique'] = ~nwps_gdf['agency_name'].duplicated(keep=False)
    # nwps_df['name'] = nwps_df.apply(get_name_plus_id, axis=1)
    # print(nwps_gdf.head)
    nwps_gdf = nwps_gdf.dissolve(
        by="agency_name_state",
        aggfunc={
            "name": "first",
            "Designated": "min",
            "agency": "first",
            "Agency": "first",
            "state": "first",
            "acreage": "sum",
            "description": "first",
            "comment": "first",
        },
    )
    # nwps_gdf = nwps_gdf.unstack().reset_index().drop('level_0', axis=1)
    print(nwps_gdf.head)

    # nwps_df.insert(0, 'id', range(1, 1 + len(nwps_df)))

    to_geojson = 1
    if to_geojson:
        nwps_gdf["dd"] = nwps_gdf.apply(get_date_from_dyear, axis=1)
        nwps_gdf = nwps_gdf.drop(columns=["agency"])
        nwps_gdf["a"] = nwps_gdf["Agency"]
        nwps_geojson = base_dir + "_nwps-2022-12-16.geojson"
        nwps_gdf = nwps_gdf.drop(
            columns=["Agency", "description", "comment", "Designated"]
        )
        nwps_gdf.to_file(nwps_geojson, driver="GeoJSON", index=False)
        # topo = topojson.Topology(wilderness_fixture, wilderness_fixture + '.packed', quantization=1e6, simplify=0.0001)
        with uopen(nwps_geojson) as wg:
            wj = json.load(wg)
        topo = topojson.Topology(wj, nwps_geojson + ".packed")
        with uopen(nwps_geojson + ".packed", "w") as static_file:
            static_file.write(str(topo))
        quit()

    nwps_gdf["wkt"] = nwps_gdf.geometry.to_wkt()
    # print(nwps_gdf.crs)
    srid = "SRID=4326;"
    nwps_df = pandas.DataFrame(nwps_gdf)
    # nwps_dfc = nwps_df.stack().reset_index()
    print(nwps_df.head)
    print(nwps_df.columns)
    # nwps_dfc = nwps_dfc.sort_values('name', ascending=False)
    # nwps_df.to_csv(base_dir + '_nwps_up-2022-12-16.csv')
    # quit()

    nwps_df.insert(0, "id", range(1, 1 + len(nwps_df)))
    nwps_df["geom"] = srid + nwps_df["wkt"]
    nwps_df["created"] = "2022-12-15 15:35:55"
    nwps_df["modified"] = "2022-12-15 15:35:55"
    nwps_df["author"] = 1
    nwps_df["name"] = nwps_df["name"].str.replace(" Wilderness", "")
    nwps_df["designation_date"] = nwps_df.apply(get_date_from_dyear, axis=1)
    nwps_df["delist_date"] = ""
    nwps_df["remarks"] = ""

    print(nwps_df.head)

    # nwps_df.to_json(base_dir + '_junk-2022-12-16.json', orient='records')
    # dups = nwps_df[nwps_df['unique'] == 'False']
    # print(dups.head)
    # quit()

    nwps_df["slug"] = nwps_df.apply(get_slug, axis=1)
    nwps_df = nwps_df.drop(columns=["wkt", "geometry", "Designated"])
    nwps_df = nwps_df[
        [
            "id",
            "created",
            "modified",
            "author",
            "name",
            "slug",
            "designation_date",
            "remarks",
            "state",
            "comment",
            "acreage",
            "description",
            "agency",
            "geom",
        ]
    ]
    print(nwps_df.head)
    print(nwps_df.columns)
    cut_json = 1
    if cut_json:
        cut1 = nwps_df[:200]
        print(cut1.head)
        cut2 = nwps_df[200:400]
        print(cut2.head)
        cut3 = nwps_df[400:500]
        print(cut3.head)
        cut4 = nwps_df[500:600]
        print(cut4.head)
        cut5 = nwps_df[600:700]
        print(cut5.head)
        cut6 = nwps_df[700:800]
        print(cut6.head)
        cut7 = nwps_df[800:900]
        print(cut7.head)
        # cut8 = nwps_df[800:]
        # print(cut8.head)
        cut1.to_json(base_dir + "_nwps_up1-2022-12-16.json", orient="records")
        cut2.to_json(base_dir + "_nwps_up2-2022-12-16.json", orient="records")
        cut3.to_json(base_dir + "_nwps_up3-2022-12-16.json", orient="records")
        cut4.to_json(base_dir + "_nwps_up4-2022-12-16.json", orient="records")
        cut5.to_json(base_dir + "_nwps_up5-2022-12-16.json", orient="records")
        cut6.to_json(base_dir + "_nwps_up6-2022-12-16.json", orient="records")
        cut7.to_json(base_dir + "_nwps_up7-2022-12-16.json", orient="records")
        # cut8.to_json(base_dir + '_nwps_up8-2022-12-16.json', orient='records')
    nwps_df.to_json(base_dir + "_nwps_up-2022-12-16.json", orient="records")
    # with uopen(nwps_json , 'w') as file:
    #    file.write(nwps_df.to_json())

    # nwps_df = nwps_df[['id','created','modified','author','name','slug','designation_date','remarks','state','comment','acreage','description','agency','geom']]
    # topo = topojson.Topology(out_shp, out_dir + filename + '.json.packed')
    # topo.to_json(out_dir + filename + '.json.packed')

    # topo = topojson.Topology(wilderness_fixture, wilderness_fixture + '.packed', quantization=1e6, simplify=0.0001)
    quit()

    wilderness_fixture = base_dir + "_wilderness_areas-2022-12-16.json"
    topbit = "[\n"
    with uopen(wilderness_fixture, "w+") as outfile:
        outfile.write(topbit)
    pkey = 1
    created = datetime.utcnow().isoformat()[:-7] + "Z"
    for i, row in nwps_df.iterrows():
        comma = ",\n"
        if pkey == 1:
            comma = ""
        pkey = pkey + 1
        fields = (
            '{\n        "geom": "'
            + str(row["geom"])
            + '",\n        "name": "'
            + str(row["name"])
            + '",\n        "slug": "'
            + str(row["slug"])
            + '",\n        "agency": "'
            + row["agency"]
            + '",\n        "comment": "'
            + str(row["comment"])
            + '",\n        "state": "'
            + str(row["state"])
            + '",\n        "description": "'
            + str(row["description"])
            + '",\n        "designation_date": '
            + row["designation_date"]
            + ',\n        "delist_date": '
            + row["delist_date"]
            + ',\n        "remarks": '
            + row["remarks"]
            + ',\n        "acreage": '
            + str(row["acreage"])
            + ',\n        "created": "'
            + str(created)
            + '",\n        "modified": null,\n        "author": '
            + str(row["author"])
            + "\n    }\n"
        )
        record = (
            comma
            + '{\n    "model": "wcmd.wilderness_area",\n    "pk": '
            + str(pkey)
            + ',\n    "fields": '
            + fields
            + "}"
        )
        with uopen(wilderness_fixture, "a") as outfile:
            outfile.write(record)
    endbit = "\n]"
    with uopen(wilderness_fixture, "a") as outfile:
        outfile.write(endbit)
    log(None, None, "GREEN", wilderness_fixture + " fixture written")


def measures_json():
    _json = data_dir + "_wilderness" + slash + "measures_short.json"
    _gdf = pandas.read_json(_json)
    print(_gdf.columns)
    _gdf.insert(0, "id", range(1, 1 + len(_gdf)))
    _gdf["created"] = "2022-12-15 15:35:55"
    _gdf["modified"] = "2022-12-15 15:35:55"
    _gdf["author"] = 1
    # _gdf['name'] = ""
    # _gdf['fullname'] = ""
    _gdf["slug"] = _gdf.apply(get_slug, axis=1)
    _gdf["remarks"] = ""
    _gdf["agency"] = 1
    # _gdf['required'] = ""
    _gdf["reported_as"] = ""
    _gdf.to_csv(
        base_dir + "_measures_up-2022-12-16.csv",
        quotechar='"',
        index=False,
        quoting=csv.QUOTE_ALL,
    )


def pull_edw_links():
    rev_date = str(datetime.now().strftime("%Y%m%d_%H%M"))
    out_dir = data_dir  # + rev_date + slash
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    urlbase = "https://data.fs.usda.gov/geodata/edw/"
    url = urlbase + "datasets.php"
    page = requests.get(url)
    data = page.text
    soup = BeautifulSoup(data, features="html.parser")
    df = pandas.DataFrame()
    for link in soup.find_all("a"):
        ll = link.get("href")
        if ll is not None:
            lf = urlbase + ll
            if ".gdb.zip" in lf:
                lparent = link.find_parent("td")
                # lrefresh = lparent.select('p')
                lrefresh = lparent.find_all("p")[-1].get_text()
                if "Date of last refresh" in lrefresh:
                    r_date = dparser.parse(lrefresh, fuzzy=True)
                    print(r_date)
                    ldf = pandas.DataFrame([[lf, r_date]], columns=["link", "new_date"])
                    df = df.append(ldf)
                else:
                    print("skipping " + lf)
    df = df.sort_values("link", ascending=False)
    df.to_csv(out_dir + rev_date + "-links.csv")
    # if not os.path.exists(data_dir + 'current.csv'):
    #    df.to_csv(data_dir + 'current.csv')
    print("links pulled")


def pull_edw_local():
    # rev_date = str(datetime.now().strftime('%y%m%d_%h%M'))
    rev_date = str(datetime.now().strftime("%Y%m%d_%H%M"))
    out_dir = data_dir  # + rev_date + slash

    # lfs = [f for f in os.listdir(out_dir) if f.endswith('-links.csv')]
    # dds = [f for f in os.scandir(out_dir) if f.is_dir()]
    # dfs = [f for f in os.scandir(out_dir) if f.is_file()]
    dfs = [
        os.path.join(root, name)
        for root, dirs, files in os.walk(out_dir)
        for name in files
        if name.endswith((".gdb.zip"))
    ]
    df = pandas.DataFrame({"path": dfs})
    # df['shortpath'] = df['path'].str.replace(data_dir, ' ', regex=True)
    # df = pandas.DataFrame(df.row.str.split('\\',1).tolist(),columns = ['date','file'])
    df[["base", "old_date", "file"]] = df["path"].str.rsplit(slash, 2, expand=True)
    df = df[["old_date", "file"]]

    lfs = [f for f in os.listdir(out_dir) if f.endswith("-links.csv")]
    lfs = sorted(lfs, reverse=True)
    current = lfs[0]
    current = pandas.read_csv(out_dir + current)
    current[["path", "file"]] = current["link"].str.rsplit("/", 1, expand=True)
    current = current[["new_date", "file", "link"]]
    # current = pandas.read_csv(out_dir + current)
    # current = current.rename(index=str, columns={'new_date': 'old_date'})
    result = current.merge(df, on="file", how="outer")
    result = result[["old_date", "new_date", "file", "link"]]
    result = result.sort_values("old_date").groupby("file").tail(1)
    print(result.head)
    result.to_csv(out_dir + rev_date + "-check.csv")
    check = pandas.read_csv(out_dir + rev_date + "-check.csv")
    dif = check.loc[check["new_date"] != check["old_date"]]


def pull_edw_data():
    out_dir = data_dir
    if not os.path.exists(out_dir):
        print("no path")
        quit()
    lfs = [f for f in os.listdir(out_dir) if f.endswith("-links.csv")]
    lfs = sorted(lfs, reverse=True)
    current = lfs[0]
    print("current: " + current)
    current = pandas.read_csv(out_dir + current)
    current[["path", "file"]] = current["link"].str.rsplit("/", 1, expand=True)
    current = current[["new_date", "file", "link"]]
    checks = [f for f in os.listdir(out_dir) if f.endswith("-check.csv")]
    checks = sorted(checks, reverse=True)
    check = checks[0]
    print("check: " + check)
    check = pandas.read_csv(out_dir + check)
    # quit()

    for index, row in check.iterrows():
        new_date = row["new_date"]
        if pandas.isnull(new_date):
            print("blank date entry for " + row["file"])
        else:
            if not os.path.exists(data_dir + new_date + slash):
                os.makedirs(data_dir + new_date + slash)
                print("creating folder " + new_date)
            url = row["link"]
            a = urlparse(url)
            filename = os.path.basename(a.path)
            # print(new_date + ' update to ' + filename)
            if not os.path.exists(data_dir + new_date + slash + filename):
                log(None, None, "GREEN", "downloading " + filename)
                file = urlretrieve(url, data_dir + new_date + slash + filename)
            else:
                log(None, None, "CYAN", "skipping " + filename)
                pass
    dif = check.loc[check["new_date"] != check["old_date"]]


def get_gdb_rev(gdb_name, rev_date):
    gdb_name = gdb_name
    rev_datetime = datetime.strptime(rev_date, "%Y-%m-%d")
    print(rev_date + " " + gdb_name)
    dfs = [
        os.path.join(root, name)
        for root, dirs, files in os.walk(data_dir)
        for name in files
        if name == gdb_name
    ]
    df = pandas.DataFrame({"path": dfs})
    df["folder"] = df["path"].str.replace(gdb_name, "", regex=False)
    df["parent"] = df["folder"].str.split(slash).str[-2]
    df["date"] = pandas.to_datetime(df["parent"])
    youngest = max(dt for dt in df["date"] if dt < rev_datetime)
    dfn = df[df["date"] == youngest]["path"]
    path = dfn.values[0]
    return path


def open_edw_data(rev_date):  # not happening yet
    out_dir = data_dir
    check = pandas.read_csv(out_dir + rev_date + "-check.csv")
    # short = check[['new_date','file']]
    # short.to_csv(out_dir + rev_date + '-short.csv')
    dif = check.loc[check["new_date"] != check["old_date"]]
    gdb_list = [
        dev_pt_gdb_as_list,
        dev_ln_gdb_as_list,
        dev_pl_gdb_as_list,
        road_ln_gdb_as_list,
        gdb_as_list,
    ]

    print(gdb_list)
    quit()

    for gdb in gdbs_as_list:
        pass

    print(check.head)
    print(dif.head)
    quit()


def pull_data_states():  # not happening yet
    rev_date = str(datetime.now().strftime("%Y%m%d_%H%M"))
    out_dir = water_dir
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    epa_page = ""
    # get epa files here

    states_wiki_page = (
        "https://en.wikipedia.org/wiki/List_of_U.S._state_and_territory_abbreviations"
    )
    page = requests.get(states_wiki_page)
    data = page.text
    soup = BeautifulSoup(data, features="html.parser")
    df = pandas.DataFrame()

    # table = soup.find_all('table')
    # df = pandas.read_html(str(table))[0]
    # print(df.head)
    # print(df[1])
    # quit()
    # df[['name','code']] = df[df[[0,1]]]
    # print(df.columns)
    # quit()

    for caption in soup.find_all("caption"):
        ll = caption.get_text().strip()
        if (
            ll
            == "Codes and abbreviations for U.S. states, federal district, territories, and other regions"
        ):
            trs = caption.find_parent("table")
            trh = trs.find_all("th")
            print(trh)
        # tag=soup.find("span", {"class":"google-src-text"})
        # print(trd)
    quit()

    for tr in soup.find_all("tr"):
        ll = td.get_text().strip()
        if ll == "United States of America":
            print(ll)
            rows = [row for row in soup.findAll("tr") if not irow.find("td")]
            tr = td.findNext("tr")
            print(tr)
            quit()
            trs = td.find_parent("table").findAll("tr")[10:]
            # trs = caption.find_parent('table').findAll('tr')
            # foundtd = caption.find('td',text='Name and status of region')
            # print(foundtd)
            # quit()
            # trs = foundtext.findNext('table')
    quit()
    for caption in soup.find_all("caption"):
        ll = caption.get_text().strip()
        if (
            ll
            == "Codes and abbreviations for U.S. states, federal district, territories, and other regions"
        ):
            trs = caption.find_parent("table").findAll("tr")[10:]
            trs = caption.find_parent("table").findAll("tr")
            foundtd = caption.find("td", text="Name and status of region")
            print(foundtd)
            quit()
            # trs = foundtext.findNext('table')
            # print(trs)
            # print(tbody)
            # quit()
            for tr in trs:
                # for tr in caption.find_parent('table').findAll('tr'):
                print(tr.get_text().strip())
                # quit()
                # for td in tr.findChildren('td'):
                #    print(td.get_text().strip())
                #    if td.get_text().strip() == 'Name and status of region':
                #        print(td)
                # quit()

            # lrefresh = lparent.select('p')
            lrefresh = lparent.find_all("p")[-1].get_text()
            r_date = dparser.parse(lrefresh, fuzzy=True)
            ldf = pandas.DataFrame([[lf, r_date]], columns=["link", "new_date"])
            df = df.append(ldf)
    quit()
    df = df.sort_values("caption", ascending=False)
    df.to_csv(out_dir + rev_date + "-links.csv")
    # if not os.path.exists(data_dir + 'current.csv'):
    #    df.to_csv(data_dir + 'current.csv')
    print("links pulled")

    state_pages = pandas.DataFrame()
    states_list = []
    ldf = pandas.DataFrame([[lf, r_date]], columns=["state", "page"])
    df = df.append(ldf)
    df = df.sort_values("link", ascending=False)
    df.to_csv(out_dir + rev_date + "-links.csv")

    urlbase = "https://data.fs.usda.gov/geodata/edw/"
    url = urlbase + "datasets.php"
    page = requests.get(url)
    data = page.text
    soup = BeautifulSoup(data, features="html.parser")


def shps_to_geojsons_to_topojsons(which_wilderness):
    slug_wilderness = slugify(which_wilderness)
    out_dir = static_dir + "wcm" + slash + slug_wilderness + slash + "map" + slash
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    tails = ["", "-ntdep-grid", "-stdep-grid"]
    shp_list = [slug_wilderness + s + ".shp" for s in tails]
    in_dir = base_dir + slug_wilderness + slash
    for ashp in shp_list:
        filename = os.path.splitext(ashp)[0]
        if not os.path.exists(in_dir + ashp):
            print(
                colorama.Fore.WHITE
                + str(datetime.now().strftime("%Y%m%d_%H%M"))
                + colorama.Style.NORMAL
                + " "
                + ashp
                + " skipped"
            )
        else:
            in_shp = geopandas.read_file(in_dir + ashp)
            # in_shp['geometry'] = in_shp.geometry.apply(cast_to_multigeometry)
            gdf_to_multigeometry(in_shp)
            if filename == slug_wilderness:
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e
                    not in [
                        "WILDERNESS",
                        "NAME",
                        "DESIGNATED",
                        "BASELINE",
                        "UPDATED",
                        "geometry",
                    ]
                ]
                renames = {
                    "WILDERNESS": "number",
                    "NAME": "name",
                    "DESIGNATED": "year_designated",
                    "BASELINE": "year_baseline",
                    "UPDATED": "updated",
                }
            if filename == slug_wilderness + "-wcc":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e
                    not in [
                        "WATERSHED_",
                        "WATERSHE_1",
                        "WATERSHE_2",
                        "acres",
                        "geometry",
                    ]
                ]
                renames = {
                    "WATERSHED_": "number",
                    "WATERSHE_1": "name",
                    "WATERSHE_2": "wcc",
                }
            if filename == slug_wilderness + "-streams":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e not in ["REACHCODE", "miles", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-lakes":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["REACHCODE", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-ntdep-grid":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e
                    not in [
                        "c",
                        "20200",
                        "20190",
                        "20180",
                        "20170",
                        "20160",
                        "20150",
                        "20140",
                        "20130",
                        "20120",
                        "20110",
                        "20100",
                        "20090",
                        "20080",
                        "20070",
                        "20060",
                        "20050",
                        "20040",
                        "20030",
                        "20020",
                        "20010",
                        "20000",
                        "y",
                        "x",
                        "m",
                        "b",
                        "endy",
                        "p_value",
                        "geometry",
                    ]
                ]
                renames = {
                    "20200": "2020",
                    "20190": "2019",
                    "20180": "2018",
                    "20170": "2017",
                    "20160": "2016",
                    "20150": "2015",
                    "20140": "2014",
                    "20130": "2013",
                    "20120": "2012",
                    "20110": "2011",
                    "20100": "2010",
                    "20090": "2009",
                    "20080": "2008",
                    "20070": "2007",
                    "20060": "2006",
                    "20050": "2005",
                    "20040": "2004",
                    "20030": "2003",
                    "20020": "2002",
                    "20010": "2001",
                    "20000": "2000",
                }
            if filename == slug_wilderness + "-stdep-grid":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e
                    not in [
                        "c",
                        "20200",
                        "20190",
                        "20180",
                        "20170",
                        "20160",
                        "20150",
                        "20140",
                        "20130",
                        "20120",
                        "20110",
                        "20100",
                        "20090",
                        "20080",
                        "20070",
                        "20060",
                        "20050",
                        "20040",
                        "20030",
                        "20020",
                        "20010",
                        "20000",
                        "y",
                        "x",
                        "m",
                        "b",
                        "endy",
                        "p_value",
                        "geometry",
                    ]
                ]
                renames = {
                    "20200": "2020",
                    "20190": "2019",
                    "20180": "2018",
                    "20170": "2017",
                    "20160": "2016",
                    "20150": "2015",
                    "20140": "2014",
                    "20130": "2013",
                    "20120": "2012",
                    "20110": "2011",
                    "20100": "2010",
                    "20090": "2009",
                    "20080": "2008",
                    "20070": "2007",
                    "20060": "2006",
                    "20050": "2005",
                    "20040": "2004",
                    "20030": "2003",
                    "20020": "2002",
                    "20010": "2001",
                    "20000": "2000",
                }
            if filename == slug_wilderness + "-rem-out-fin":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-in-fin":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            cut = in_shp.drop(columns=extra_cols).rename(index=str, columns=renames)
            cut = cut[cut["geometry"].notna()]
            out_shp = cut.to_crs(epsg=4326)
            # out_shp.to_file(out_dir + filename + '.json', driver="GeoJSON")
            # topojson.Topology(out_dir + filename + '.json', out_dir + filename + '.json.packed', quantization=1e6, simplify=0.0001)
            try:
                topo = topojson.Topology(out_shp, out_dir + filename + ".json.packed")
                topo.to_json(out_dir + filename + ".json.packed")
                # print(out_dir)
                print(
                    colorama.Fore.GREEN
                    + str(datetime.now().strftime("%Y%m%d_%H%M"))
                    + colorama.Style.BRIGHT
                    + " "
                    + filename
                    + ".json.packed created"
                )
                # quit()
                if os.path.exists(out_dir + filename + ".json"):
                    os.remove(out_dir + filename + ".json")
            except Exception:
                print(
                    colorama.Fore.RED
                    + str(datetime.now().strftime("%Y%m%d_%H%M"))
                    + colorama.Style.BRIGHT
                    + " "
                    + ashp
                    + " topojson fail"
                )
                traceback.print_exc()
                out_shp.to_file(out_dir + filename + ".json", driver="GeoJSON")
                print(
                    colorama.Fore.YELLOW
                    + str(datetime.now().strftime("%Y%m%d_%H%M"))
                    + colorama.Style.BRIGHT
                    + " "
                    + filename
                    + ".json created"
                )

    tails = ["", "-wcc", "-streams", "-lakes", "-rem-out-fin", "-rem-in-fin"]
    shp_list = [slug_wilderness + s + ".shp" for s in tails]
    in_dir = base_maps_dir + slug_wilderness + slash

    for ashp in shp_list:
        filename = os.path.splitext(ashp)[0]
        if not os.path.exists(in_dir + ashp):
            print(
                colorama.Fore.WHITE
                + str(datetime.now().strftime("%Y%m%d_%H%M"))
                + colorama.Style.NORMAL
                + " "
                + ashp
                + " skipped"
            )
        else:
            in_shp = geopandas.read_file(in_dir + ashp)
            # in_shp['geometry'] = in_shp.geometry.apply(cast_to_multigeometry)
            gdf_to_multigeometry(in_shp)
            if filename == slug_wilderness:
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e
                    not in [
                        "WILDERNESS",
                        "NAME",
                        "DESIGNATED",
                        "BASELINE",
                        "UPDATED",
                        "geometry",
                    ]
                ]
                renames = {
                    "WILDERNESS": "number",
                    "NAME": "name",
                    "DESIGNATED": "year_designated",
                    "BASELINE": "year_baseline",
                    "UPDATED": "updated",
                }
            if filename == slug_wilderness + "-wcc":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e
                    not in [
                        "WATERSHED_",
                        "WATERSHE_1",
                        "WATERSHE_2",
                        "acres",
                        "geometry",
                    ]
                ]
                renames = {
                    "WATERSHED_": "number",
                    "WATERSHE_1": "name",
                    "WATERSHE_2": "wcc",
                }
            if filename == slug_wilderness + "-streams":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e not in ["REACHCODE", "miles", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-lakes":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["REACHCODE", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-ntdep-grid":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e
                    not in [
                        "c",
                        "20200",
                        "20190",
                        "20180",
                        "20170",
                        "20160",
                        "20150",
                        "20140",
                        "20130",
                        "20120",
                        "20110",
                        "20100",
                        "20090",
                        "20080",
                        "20070",
                        "20060",
                        "20050",
                        "20040",
                        "20030",
                        "20020",
                        "20010",
                        "20000",
                        "y",
                        "x",
                        "m",
                        "b",
                        "endy",
                        "p_value",
                        "geometry",
                    ]
                ]
                renames = {
                    "20200": "2020",
                    "20190": "2019",
                    "20180": "2018",
                    "20170": "2017",
                    "20160": "2016",
                    "20150": "2015",
                    "20140": "2014",
                    "20130": "2013",
                    "20120": "2012",
                    "20110": "2011",
                    "20100": "2010",
                    "20090": "2009",
                    "20080": "2008",
                    "20070": "2007",
                    "20060": "2006",
                    "20050": "2005",
                    "20040": "2004",
                    "20030": "2003",
                    "20020": "2002",
                    "20010": "2001",
                    "20000": "2000",
                }
            if filename == slug_wilderness + "-stdep-grid":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e
                    not in [
                        "c",
                        "20200",
                        "20190",
                        "20180",
                        "20170",
                        "20160",
                        "20150",
                        "20140",
                        "20130",
                        "20120",
                        "20110",
                        "20100",
                        "20090",
                        "20080",
                        "20070",
                        "20060",
                        "20050",
                        "20040",
                        "20030",
                        "20020",
                        "20010",
                        "20000",
                        "y",
                        "x",
                        "m",
                        "b",
                        "endy",
                        "p_value",
                        "geometry",
                    ]
                ]
                renames = {
                    "20200": "2020",
                    "20190": "2019",
                    "20180": "2018",
                    "20170": "2017",
                    "20160": "2016",
                    "20150": "2015",
                    "20140": "2014",
                    "20130": "2013",
                    "20120": "2012",
                    "20110": "2011",
                    "20100": "2010",
                    "20090": "2009",
                    "20080": "2008",
                    "20070": "2007",
                    "20060": "2006",
                    "20050": "2005",
                    "20040": "2004",
                    "20030": "2003",
                    "20020": "2002",
                    "20010": "2001",
                    "20000": "2000",
                }
            if filename == slug_wilderness + "-rem-out-fin":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-in-fin":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            cut = in_shp.drop(columns=extra_cols).rename(index=str, columns=renames)
            cut = cut[cut["geometry"].notna()]
            out_shp = cut.to_crs(epsg=4326)
            try:
                # topojson.Topology(out_shp, out_dir + filename + '.json.packed')
                topo = topojson.Topology(out_shp, out_dir + filename + ".json.packed")
                topo.to_json(out_dir + filename + ".json.packed")
                if os.path.exists(out_dir + filename + ".json"):
                    os.remove(out_dir + filename + ".json")
                print(
                    colorama.Fore.GREEN
                    + str(datetime.now().strftime("%Y%m%d_%H%M"))
                    + colorama.Style.BRIGHT
                    + " "
                    + filename
                    + ".json.packed created"
                )
            except Exception:
                print(
                    colorama.Fore.RED
                    + str(datetime.now().strftime("%Y%m%d_%H%M"))
                    + colorama.Style.BRIGHT
                    + " "
                    + ashp
                    + " topojson fail"
                )
                traceback.print_exc()
                out_shp.to_file(out_dir + filename + ".json", driver="GeoJSON")
                print(
                    colorama.Fore.GREEN
                    + str(datetime.now().strftime("%Y%m%d_%H%M"))
                    + colorama.Style.BRIGHT
                    + " "
                    + filename
                    + ".json created"
                )


def b_shps_to_geojsons_to_topojsons(which_wilderness):
    slug_wilderness = slugify(which_wilderness)
    out_dir = static_dir + "wcm" + slash + slug_wilderness + slash + "map" + slash
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    tails = []
    shp_list = [slug_wilderness + s + ".shp" for s in tails]
    in_dir = base_dir + slug_wilderness + slash

    for ashp in shp_list:
        filename = os.path.splitext(ashp)[0]
        if not os.path.exists(in_dir + ashp):
            print(
                colorama.Fore.WHITE
                + str(datetime.now().strftime("%Y%m%d_%H%M"))
                + colorama.Style.NORMAL
                + " "
                + ashp
                + " skipped"
            )
        else:
            in_shp = geopandas.read_file(in_dir + ashp)
            # in_shp['geometry'] = in_shp.geometry.apply(cast_to_multigeometry)
            gdf_to_multigeometry(in_shp)
            extra_cols = []
            renames = {}
            if filename == slug_wilderness:
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e not in ["WILDERNESS", "NAME", "geometry"]
                ]
                renames = {
                    "WILDERNESS": "number",
                    "NAME": "name",
                }
            if filename == slug_wilderness + "-streams-around":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e not in ["REACHCODE", "miles", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-lakes-around":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["REACHCODE", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-streamsb-around":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e not in ["REACHCODE", "miles", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-lakesb-around":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["REACHCODE", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-rem-in-roadcore2":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-out-roadcore2":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-in-devln":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-out-devln":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-in-devpt":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-out-devpt":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-in-devpl":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-out-devpl":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            cut = in_shp.drop(columns=extra_cols).rename(index=str, columns=renames)
            cut = cut[cut["geometry"].notna()]
            out_shp = cut.to_crs(epsg=4326)
            # out_shp.to_file(out_dir + filename + '.json', driver="GeoJSON")
            try:
                topojson.Topology(out_shp, out_dir + filename + ".json.packed")
                if os.path.exists(out_dir + filename + ".json"):
                    os.remove(out_dir + filename + ".json")
                print(
                    colorama.Fore.GREEN
                    + str(datetime.now().strftime("%Y%m%d_%H%M"))
                    + colorama.Style.BRIGHT
                    + " "
                    + filename
                    + ".json.packed created"
                )

            except Exception:
                print(
                    colorama.Fore.RED
                    + str(datetime.now().strftime("%Y%m%d_%H%M"))
                    + colorama.Style.BRIGHT
                    + " "
                    + ashp
                    + " topojson fail"
                )
                traceback.print_exc()
                out_shp.to_file(out_dir + filename + ".json", driver="GeoJSON")
                print(
                    colorama.Fore.GREEN
                    + str(datetime.now().strftime("%Y%m%d_%H%M"))
                    + colorama.Style.BRIGHT
                    + " "
                    + filename
                    + ".json created"
                )

    tails = [
        "-streams-around",
        "-lakes-around",
        "-streamsb",
        "-lakesb",
        "-streamsb-around",
        "-lakesb-around",
        "-rem-in-roadcore2",
        "-rem-out-roadcore2",
        "-rem-in-devln",
        "-rem-out-devln",
        "-rem-in-devpt",
        "-rem-out-devpt",
        "-rem-in-devpl",
        "-rem-out-devpl",
    ]
    shp_list = [slug_wilderness + s + ".shp" for s in tails]
    in_dir = base_maps_dir + slug_wilderness + slash

    # print(shp_list)

    for ashp in shp_list:
        filename = os.path.splitext(ashp)[0]
        if not os.path.exists(in_dir + ashp):
            print(
                colorama.Fore.WHITE
                + str(datetime.now().strftime("%Y%m%d_%H%M"))
                + colorama.Style.NORMAL
                + " "
                + ashp
                + " skipped"
            )
        else:
            # print('------------------')
            # print(ashp)
            in_shp = geopandas.read_file(in_dir + ashp)
            # print(in_shp.geometry)
            # in_shp['geometry'] = in_shp.geometry.apply(cast_to_multigeometry)
            gdf_to_multigeometry(in_shp)
            extra_cols = []
            renames = {}
            if filename == slug_wilderness:
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e not in ["WILDERNESS", "NAME", "geometry"]
                ]
                renames = {
                    "WILDERNESS": "number",
                    "NAME": "name",
                }
            if filename == slug_wilderness + "-streams-around":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e not in ["REACHCODE", "miles", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-lakes-around":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["REACHCODE", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-streamsb-around":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e not in ["REACHCODE", "miles", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-lakesb-around":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["REACHCODE", "geometry"]
                ]
                renames = {
                    "REACHCODE": "reachcode",
                }
            if filename == slug_wilderness + "-rem-in-roadcore2":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e not in ["NAME_1", "GLOBALID", "acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-out-roadcore2":
                extra_cols = [
                    e
                    for e in in_shp.columns
                    if e not in ["NAME_1", "GLOBALID", "acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-in-devln":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-out-devln":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-in-devpt":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-out-devpt":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-in-devpl":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            if filename == slug_wilderness + "-rem-out-devpl":
                extra_cols = [
                    e for e in in_shp.columns if e not in ["acres", "geometry"]
                ]
                renames = {}
            # print(in_shp.geometry)
            # in_shp.to_file(out_dir + 'test.json', driver="GeoJSON")
            cut = in_shp.drop(columns=extra_cols).rename(index=str, columns=renames)
            cut = cut[cut["geometry"].notna()]
            # print(cut.geometry)
            if cut.crs is None:
                cut.crs = "EPSG:4269"
            out_shp = cut.to_crs(epsg=4326)
            # print(ashp)
            # out_shp = out_shp.reset_index()
            # print(out_shp.head)
            if out_shp.empty:
                print(
                    colorama.Fore.CYAN
                    + str(datetime.now().strftime("%Y%m%d_%H%M"))
                    + colorama.Style.BRIGHT
                    + " "
                    + filename
                    + " empty"
                )
            else:
                # from shapely import wkt
                # out_shp['geometry'] = out_shp['geometry'].astype(str).apply(wkt.loads)
                # out_shp['valid'] = out_shp.is_valid
                # out_shp = out_shp.reset_index()
                # print(out_shp.head)
                # out_shp2 = out_shp.sort_index().explode()
                # out_shp2 = out_shp.reset_index(drop=True).explode()
                # out_shp2 = out_shp.reset_index(level=[0]).explode()
                # print(out_shp2.head)
                # out_shp.to_file(out_dir + 'test.' + out_ext, driver=out_driver)
                print(filename)
                topojson.Topology(out_shp, out_dir + filename + ".json.packed")
                try:
                    topojson.Topology(
                        out_shp, out_dir + filename + ".json.packed"
                    )  # crashy numpy dup check
                    if os.path.exists(out_dir + filename + ".json"):
                        os.remove(out_dir + filename + ".json")
                    print(
                        colorama.Fore.GREEN
                        + str(datetime.now().strftime("%Y%m%d_%H%M"))
                        + colorama.Style.BRIGHT
                        + " "
                        + filename
                        + ".json.packed writing"
                    )

                except Exception:
                    print(
                        colorama.Fore.RED
                        + str(datetime.now().strftime("%Y%m%d_%H%M"))
                        + colorama.Style.BRIGHT
                        + " "
                        + ashp
                        + " topojson fail"
                    )
                    traceback.print_exc()
                    out_shp.to_file(out_dir + filename + ".json", driver="GeoJSON")
                    print(
                        colorama.Fore.YELLOW
                        + str(datetime.now().strftime("%Y%m%d_%H%M"))
                        + colorama.Style.BRIGHT
                        + " "
                        + filename
                        + ".json writing"
                    )


def collect_downloads_nwps(
    which_wilderness,
):  # collect files for wilderness baseline page
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    source_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    out_dir = static_dir + "wcm" + slash + slug_agency + slash + slug_wilderness + slash
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    vis_csvs = [
        fn
        for fn in os.listdir(source_dir)
        if fn.endswith(".csv") and "-visibility-" in fn
    ]
    print(vis_csvs)
    for file in vis_csvs:
        copyfile(source_dir + file, out_dir + file)
    ozone_csvs = [
        fn for fn in os.listdir(source_dir) if fn.endswith(".csv") and "-ozone-" in fn
    ]
    print(ozone_csvs)
    for file in ozone_csvs:
        copyfile(source_dir + file, out_dir + file)
    ozone_pngs = [
        fn
        for fn in os.listdir(source_dir)
        if fn.endswith(".png") and "-ozone-" in fn and "-graph" in fn
    ]
    print(ozone_pngs)
    for file in ozone_pngs:
        copyfile(source_dir + file, out_dir + file)
    file_list = [
        "-303d.png",
        "-lakes.png",
        "-lakes.csv",
        "-streams.png",
        "-streams.csv",
        "-lakes-inventoried.csv",
        "-streams-inventoried.csv",
        "-wcc.png",
        "-wcc.csv",
        "-rem-in-fin.png",
        "-rem-out-fin.png",
        "-waters.png",
        "-ln_in.csv",
        "-ln_in_groups.csv",
        "-pl_in.csv",
        "-pl_in_groups.csv",
    ]
    file_list.extend(
        [
            "-waters-base.png",
            "-lakes-base.png",
            "-streams-base.png",
            "-wcc-base.png",
            "-rem-in-fin-base.png",
            "-rem-out-fin-base.png",
        ]
    )
    file_list.extend(
        [
            "-rem-all-fin.png",
            "-rem-all-fin-base.png",
            "-rem-all-fin-27in.png",
            "-rem-all-fin-27in-base.png",
        ]
    )
    file_list.extend(
        [
            "-ntdep-map-scaled.png",
            "-ntdep.png",
            "-ntdep_trend.png",
            "-ntdep-graph.png",
            "-ntdep.csv",
            "-stdep-map-scaled.png",
            "-stdep.png",
            "-stdep_trend.png",
            "-stdep-graph.png",
            "-stdep.csv",
            "-visibility-graph.png",
        ]
    )
    file_list.extend(
        ["-ozone-stations-13in.png", "-ozone-stations-27in.png", "-ozone.csv"]
    )
    file_list.extend(["-ozone-stations-13in-base.png", "-ozone-stations-27in-base.png"])
    file_list.extend(
        [
            "-lichen-plots.png",
            "-lichen-plots-base.png",
            "-lichen-plots.csv",
            "-lichen-s-plots.png",
            "-lichen-s-plots-labels.png",
            "-lichen-s-plotwise.png",
            "-lichen-s-plotwise-labels.png",
            "-lichen-s-qq-all.png",
            "-lichen-n-plots.png",
            "-lichen-n-plots-labels.png",
            "-lichen-n-plotwise.png",
            "-lichen-n-plotwise-labels.png",
            "-lichen-n-qq-all.png",
        ]
    )
    file_list.extend(
        ["-wetdep-n.png", "-wetdep-n.csv", "-wetdep-s.png", "-wetdep-s.csv"]
    )
    file_list.extend(
        [
            "-map-s.png",
            "-map-sf.png",
            "-mapw-s.png",
            "-mapw-sf.png",
            "-mapw-terrain-sf.png",
        ]
    )
    for file in file_list:
        if not os.path.exists(source_dir + slug_wilderness + file):
            print(
                colorama.Fore.WHITE
                + str(datetime.now().strftime("%Y%m%d_%H%M"))
                + colorama.Style.NORMAL
                + " "
                + slug_wilderness
                + file
                + " skipped"
            )
        else:
            print(
                colorama.Fore.GREEN
                + str(datetime.now().strftime("%Y%m%d_%H%M"))
                + colorama.Style.BRIGHT
                + " "
                + slug_wilderness
                + file
                + " writing"
            )
            copyfile(
                source_dir + slug_wilderness + file, out_dir + slug_wilderness + file
            )

    for file in os.listdir(source_dir):
        if "-lichen-n-qq-" in file:
            print(
                colorama.Fore.GREEN
                + str(datetime.now().strftime("%Y%m%d_%H%M"))
                + colorama.Style.BRIGHT
                + " "
                + file
                + " writing"
            )
            copyfile(source_dir + file, out_dir + file)


def build_wcm_baseline_nwps(which_wilderness):  # build baseline page for a wilderness
    slug_wilderness = slugify(which_wilderness[2])
    slug_agency = slugify(which_wilderness[1])
    source_dir = base_dir + slug_agency + slash + slug_wilderness + slash

    out_dir = static_dir + "wcm" + slash + slug_wilderness + slash
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    vis_csvs = [
        fn for fn in os.listdir(out_dir) if fn.endswith(".csv") and "-visibility-" in fn
    ]
    print(vis_csvs)
    ozone_csvs = [
        fn for fn in os.listdir(out_dir) if fn.endswith(".csv") and "-ozone-" in fn
    ]
    ozone_pngs = [
        fn for fn in os.listdir(out_dir) if fn.endswith(".png") and "-ozone-" in fn
    ]
    file_list = [
        "-303d.png",
        "-lakes.png",
        "-lakes.csv",
        "-streams.png",
        "-streams.csv",
        "-lakes-inventoried.csv",
        "-streams-inventoried.csv",
        "-wcc.png",
        "-wcc.csv",
        "-rem-in-fin.png",
        "-rem-out-fin.png",
        "-waters.png",
        "-ln_in.csv",
        "-ln_in_groups.csv",
        "-pl_in.csv",
        "-pl_in_groups.csv",
    ]
    file_list.extend(
        [
            "-ntdep-map-scaled.png",
            "-ntdep.png",
            "-ntdep_trend.png",
            "-ntdep-graph.png",
            "-ntdep.csv",
            "-stdep-map-scaled.png",
            "-stdep.png",
            "-stdep_trend.png",
            "-stdep-graph.png",
            "-stdep.csv",
            "-visibility-graph.png",
        ]
    )
    file_list.extend(
        ["-ozone-stations-13in.png", "-ozone-stations-27in.png", "-ozone.csv"]
    )
    file_list.extend(
        [
            "-lichen-plots-base.png",
            "-lichen-plots.png",
            "-lichen-n-graph.png",
            "-lichen-s-graph.png",
            "-lichen.csv",
        ]
    )
    file_list.extend(
        [
            "-map-s.png",
            "-map-sf.png",
            "-mapw-s.png",
            "-mapw-sf.png",
            "-mapw-terrain-sf.png",
        ]
    )
    file_list.extend(
        ["-wetdep-n.png", "-wetdep-n.csv", "-wetdep-s.png", "-wetdep-s.csv"]
    )
    ntdep_ext = "-ntdep-graph-extended.png"
    stdep_ext = "-stdep-graph-extended.png"
    vis_ext = "-visibility-graph-extended.png"
    for file in file_list:
        if not os.path.exists(out_dir + slug_wilderness + file):
            print(
                colorama.Fore.WHITE
                + str(datetime.now().strftime("%Y%m%d_%H%M"))
                + colorama.Style.NORMAL
                + " "
                + slug_wilderness
                + file
                + " skipped"
            )
        else:
            print(
                colorama.Fore.WHITE
                + str(datetime.now().strftime("%Y%m%d_%H%M"))
                + colorama.Style.BRIGHT
                + " "
                + slug_wilderness
                + file
                + " added"
            )
    if not vis_csvs:
        context = {"name": which_wilderness[2], "slug": slug_wilderness, "vis_csv": ""}
    else:
        context = {
            "name": which_wilderness[2],
            "slug": slug_wilderness,
            "vis_csv": vis_csvs[0],
        }
    print(ozone_csvs)
    if not ozone_csvs:
        context["ozone_csv"] = ""
    else:
        context["ozone_csv"] = ozone_csvs[0]
    if not ozone_pngs:
        context["ozone_png"] = ""
    else:
        context["ozone_png"] = ozone_pngs[0]
    if not os.path.exists(out_dir + slug_wilderness + ntdep_ext):
        print(
            colorama.Fore.WHITE
            + str(datetime.now().strftime("%Y%m%d_%H%M"))
            + colorama.Style.NORMAL
            + " "
            + slug_wilderness
            + ntdep_ext
            + " skipped"
        )
        context.update({"nt_ext": ""})
    else:
        print(
            colorama.Fore.WHITE
            + str(datetime.now().strftime("%Y%m%d_%H%M"))
            + colorama.Style.BRIGHT
            + " "
            + slug_wilderness
            + ntdep_ext
            + " added"
        )
        context.update({"nt_ext": slug_wilderness + ntdep_ext})
    if not os.path.exists(out_dir + slug_wilderness + stdep_ext):
        print(
            colorama.Fore.WHITE
            + str(datetime.now().strftime("%Y%m%d_%H%M"))
            + colorama.Style.NORMAL
            + " "
            + slug_wilderness
            + stdep_ext
            + " skipped"
        )
        context.update({"st_ext": ""})
    else:
        print(
            colorama.Fore.WHITE
            + str(datetime.now().strftime("%Y%m%d_%H%M"))
            + colorama.Style.BRIGHT
            + " "
            + slug_wilderness
            + stdep_ext
            + " added"
        )
        context.update({"st_ext": slug_wilderness + stdep_ext})
    if not os.path.exists(out_dir + slug_wilderness + vis_ext):
        print(
            colorama.Fore.WHITE
            + str(datetime.now().strftime("%Y%m%d_%H%M"))
            + colorama.Style.NORMAL
            + " "
            + slug_wilderness
            + vis_ext
            + " skipped"
        )
        context.update({"vis_ext": ""})
    else:
        print(
            colorama.Fore.WHITE
            + str(datetime.now().strftime("%Y%m%d_%H%M"))
            + colorama.Style.BRIGHT
            + " "
            + slug_wilderness
            + vis_ext
            + " added"
        )
        context.update({"vis_ext": slug_wilderness + vis_ext})

    try:
        with uopen(source_dir + "index-inout.json") as jsf:
            data = json.load(jsf)
            context.update({"io": data})
    except FileNotFoundError:
        log(slug_wilderness, slug_agency, "RED", "index-inout.json does not exist")
    try:
        with uopen(source_dir + "index-iw.json") as jsf:
            data = json.load(jsf)
            context.update({"iw": data})
    except FileNotFoundError:
        log(slug_wilderness, slug_agency, "RED", "index-iw.json does not exist")
    try:
        with uopen(source_dir + "index-wcc.json") as jsf:
            data = json.load(jsf)
            context.update({"wcc": data})
    except FileNotFoundError:
        log(slug_wilderness, slug_agency, "RED", "index-wcc.json does not exist")
    try:
        with uopen(source_dir + "index-ntdep.json") as jsf:
            data = json.load(jsf)
            context.update({"ntdep": data})
    except FileNotFoundError:
        log(slug_wilderness, slug_agency, "RED", "index-ntdep.json does not exist")
        jsd = [
            {
                "yr_min": "NA",
                "yr_max": "NA",
                "endy": "NA",
                "m": "NA",
                "trend_text": "NA",
                "p": "NA",
            }
        ]
        jsc = "".join(str(v) for v in jsd).replace("'", '"')
        context.update({"ntdep": jsc})
    try:
        with uopen(source_dir + "index-stdep.json") as jsf:
            data = json.load(jsf)
            context.update({"stdep": data})
    except FileNotFoundError:
        log(slug_wilderness, slug_agency, "RED", "index-stdep.json does not exist")
        jsd = [
            {
                "yr_min": "NA",
                "yr_max": "NA",
                "endy": "NA",
                "m": "NA",
                "trend_text": "NA",
                "p": "NA",
            }
        ]
        jsc = "".join(str(v) for v in jsd).replace("'", '"')
        context.update({"stdep": jsc})
    try:
        with uopen(source_dir + "index-vis.json") as jsf:
            data = json.load(jsf)
            context.update({"vis": data})
    except FileNotFoundError:
        log(slug_wilderness, slug_agency, "RED", "index-vis.json does not exist")
        jsd = [
            {
                "yr_min": "NA",
                "yr_max": "NA",
                "endy": "NA",
                "m": "NA",
                "trend_text": "NA",
                "p": "NA",
            }
        ]
        jsc = "".join(str(v) for v in jsd).replace("'", '"')
        context.update({"vis": jsc})
    try:
        with uopen(source_dir + "index-ozone.json") as jsf:
            data = json.load(jsf)
            context.update({"ozone": data})
    except FileNotFoundError:
        log(slug_wilderness, slug_agency, "RED", "index-ozone.json does not exist")
        jsd = [
            {
                "site": "NA",
                "yr_min": "NA",
                "yr_max": "NA",
                "endy": "NA",
                "m": "NA",
                "trend_text": "NA",
                "p": "NA",
            }
        ]
        jsc = "".join(str(v) for v in jsd).replace("'", '"')
        context.update({"ozone": jsc})
    if not os.path.exists(source_dir + slug_wilderness + "-lichen-plots.csv"):
        log(
            slug_wilderness,
            slug_agency,
            "RED",
            slug_wilderness + "-lichen-plots.csv does not exist",
        )
        context.update({"lichen_plots": []})
    else:
        w_plots = pandas.read_csv(source_dir + slug_wilderness + "-lichen-plots.csv")
        # w_plot_list = df[companies_column].tolist()
        w_plot_list = w_plots.reset_index().values.tolist()
        context.update({"lichen_plots": w_plot_list})
        print(w_plot_list)
        # quit()
        try:
            with uopen(source_dir + "index-lichen-N.json") as jsf:
                data = json.load(jsf)
                context.update({"lichen_n": data})
        except FileNotFoundError:
            log(
                slug_wilderness,
                slug_agency,
                "RED",
                "index-lichen-N.json does not exist",
            )
            context.update({"lichen_n": None})
        try:
            with uopen(source_dir + "index-lichen-N-table.json") as jsf:
                data = json.load(jsf)
                context.update({"lichen_n_table": data})
            with uopen(source_dir + "index-lichen-N-tablem.json") as jsf:
                data = json.load(jsf)
                context.update({"lichen_n_tablem": data})
        except FileNotFoundError:
            log(
                slug_wilderness,
                slug_agency,
                "RED",
                "index-lichen-N-table.json does not exist",
            )
            context.update({"lichen_n_table": None})
        try:
            with uopen(source_dir + "index-lichen-S.json") as jsf:
                data = json.load(jsf)
                context.update({"lichen_s": data})
        except FileNotFoundError:
            log(
                slug_wilderness,
                slug_agency,
                "RED",
                "index-lichen-S.json does not exist",
            )
            context.update({"lichen_s": None})
        try:
            with uopen(source_dir + "index-lichen-S-table.json") as jsf:
                data = json.load(jsf)
                context.update({"lichen_s_table": data})
            with uopen(source_dir + "index-lichen-S-tablem.json") as jsf:
                data = json.load(jsf)
                context.update({"lichen_s_tablem": data})
        except FileNotFoundError:
            log(
                slug_wilderness,
                slug_agency,
                "RED",
                "index-lichen-S-table.json does not exist",
            )
            context.update({"lichen_s_table": None})
    try:
        with uopen(source_dir + "index-wetdep-n.json") as jsf:
            data = json.load(jsf)
            context.update({"wetdep_n": data})
    except FileNotFoundError:
        log(slug_wilderness, slug_agency, "RED", "index-wetdep-n.json does not exist")
        jsd = [{"wet_full": "NA"}]
        jsc = "".join(str(v) for v in jsd).replace("'", '"')
        context.update({"wetdep_n": jsc})
    try:
        with uopen(source_dir + "index-wetdep-s.json") as jsf:
            data = json.load(jsf)
            context.update({"wetdep_s": data})
    except FileNotFoundError:
        log(slug_wilderness, slug_agency, "RED", "index-wetdep-s.json does not exist")
        jsd = [{"wet_full": "NA"}]
        jsc = "".join(str(v) for v in jsd).replace("'", '"')
        context.update({"wetdep_s": jsc})

    print(source_dir + "index-wilderness.json")
    with uopen(source_dir + "index-wilderness.json") as jsf:
        data = json.load(jsf)
        release_month = "May 2021"
        context.update({"wilderness": data})
    print(context)
    template = get_template("build_wcm_baseline.html")
    content = template.render(context)
    with uopen(out_dir + "index.html", "w") as static_file:
        static_file.write(content)
    log(
        slug_wilderness,
        slug_agency,
        "CYAN",
        which_wilderness[2] + " baseline index built",
    )

    template = get_template("build_wcm_map.html")
    content = template.render(context)
    with uopen(out_dir + "index-map.html", "w") as static_file:
        static_file.write(content)
    log(slug_wilderness, slug_agency, "CYAN", which_wilderness[2] + " map index built")

    template = get_template("build_wcm_baseline.js")
    content = template.render(context)
    with uopen(out_dir + "data.js", "w") as static_file:
        static_file.write(content)
    log(
        slug_wilderness, slug_agency, "CYAN", which_wilderness[2] + " baseline js built"
    )

    if not os.path.exists(web_dir + slug_wilderness):
        os.makedirs(web_dir + slug_wilderness)

    copyfile(out_dir + "index.html", web_dir + slug_wilderness + slash + "index.html")
    log(
        slug_wilderness,
        slug_agency,
        "CYAN",
        which_wilderness[2] + " baseline index upload ready",
    )

    copyfile(out_dir + "data.js", web_dir + slug_wilderness + slash + "data.js")
    log(
        slug_wilderness,
        slug_agency,
        "CYAN",
        which_wilderness[2] + " baseline js upload ready",
    )


def build_index_():  # build wcm index page
    out_dir = static_dir + "wcm" + slash
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    rev_date = str(datetime.now().strftime("%Y%m%d_%H%M"))
    context = {
        "rev_date": rev_date,
        "wilderness_count": "447",
        "to_date": "2015",
        "admin_email": "admin@wilderness.ordvac.com",
    }
    template = get_template("build_index.html")
    content = template.render(context)
    print("ok")
    with uopen(out_dir + "index.html", "w") as static_file:
        static_file.write(content)
    template = get_template("build_index.js")
    content = template.render(context)
    with uopen(out_dir + "data.js", "w") as static_file:
        static_file.write(content)


class reversor:
    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        return other.obj == self.obj

    def __lt__(self, other):
        return other.obj < self.obj


def build_index(req_list):  # build another wcm index page
    out_dir = static_dir + "wcm" + slash
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    rev_date = str(datetime.now().strftime("%Y%m%d_%H%M"))
    r_list = []
    for r in req_list:
        r.insert(2, slugify(r[1]))
        r = [w.replace(" Wilderness", "") for w in r]
        r_list.append(r)
    req_list = sorted(r_list, key=lambda y: (reversor(y[0]), y[1].lower()))
    ask_list = [x for x in req_list if x[0] != ""]
    add_list = [x for x in req_list if x[0] == ""]
    add_list.extend(ask_list)

    top_list = [
        ["", "", "Automatic Writing"],
        ["", "", "A Child's Garden of State-Sponsored Parking Lot Demographics"],
        ["", "", "Landscape Ontology"],
        ["", "", "Timelines and Regional Trends"],
        ["2023-08-14", "water/fs", "Impaired Waters in ____ Wilderness"],
        ["2023-02-28", "annotated", "Illuminated Manuscripts"],
        ["2023-01-29", "topics/ozone-generator", "Ozone Trend Generator"],
        ["2023-01-18", "topics/mapping-water-quality", "Mapping Water Quality"],
        [
            "2023-01-06",
            "topics/lichen-trending",
            "Air Quality Trends from Lichen Sampling",
        ],
        ["2022-12-27", "topics/best-and-nearest", "Best and Nearest"],
        ["2022-12-21", "topics/wilderness-by-area", "Wilderness by Area"],
        ["2022-12-18", "wcmd", "A Wilderness Character Database"],
        [
            "2022-12-04",
            "topics/measures-scores-and-trends",
            "Measures, Scores, and Trends",
        ],
        [
            "2022-11-30",
            "topics/mktest",
            "Mann-Kendall Test vs Ordinary Linear Regression",
        ],
    ]

    context = {
        "top_list": top_list,
        "req_list": add_list,
        "rev_date": rev_date,
        "wilderness_count": "447",
        "to_date": "2023",
        "admin_email": "admin@wilderness.ordvac.com",
    }
    template = get_template("build_index.html")
    content = template.render(context)
    print("ok")
    with uopen(out_dir + "index.html", "w") as static_file:
        static_file.write(content)
    template = get_template("build_index.js")
    content = template.render(context)
    with uopen(out_dir + "data.js", "w") as static_file:
        static_file.write(content)


def build_impaired_dirs_nwps(req_list):  # build imapired waters pages
    rev_date = str(datetime.now().strftime("%Y%m%d_%H%M"))
    if not os.path.exists(static_dir + "water_html"):
        os.makedirs(static_dir + "water_html")
    if not os.path.exists(static_dir + "water_json"):
        os.makedirs(static_dir + "water_json")
    req4_list = req_list.copy()
    for r in req4_list:
        r.insert(2, slugify(r[1]))
        r.insert(4, slugify(r[3]))
        print(r)

        context = {
            "admin_email": "admin@wilderness.ordvac.com",
        }
        source_dir = base_dir + r[4] + slash + r[2] + slash
        out_dir = static_dir + "water_json" + slash + r[4] + slash + r[2] + slash
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        file_list = []
        file_list.append(r[2] + "-water-tidy.csv")
        file_list.append(r[2] + "_ca_in.json.packed")
        file_list.append(r[2] + "_ln_in.json.packed")
        file_list.append(r[2] + "_pl_in.json.packed")
        file_list.append(r[2] + ".json.packed")
        file_list.append("index-wilderness.json")

        # print(source_dir)
        # print(out_dir)
        # print(file_list)

        for file in file_list:
            copyfile(source_dir + file, out_dir + file)

        out_dir = (
            static_dir
            + "water_html"
            + slash
            + r[4]
            + slash
            + r[2]
            + slash
            + "impaired-streams"
            + slash
        )
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        template = get_template("impaired-streams.html")
        content = template.render(context)
        with uopen(out_dir + "index.html", "w") as static_file:
            static_file.write(content)
        out_dir = (
            static_dir
            + "water_html"
            + slash
            + r[4]
            + slash
            + r[2]
            + slash
            + "impaired-lakes"
            + slash
        )
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        template = get_template("impaired-lakes.html")
        content = template.render(context)
        with uopen(out_dir + "index.html", "w") as static_file:
            static_file.write(content)
        print(r[1])
    print("built")


def build_lichen_dirs_nwps(req_list):  # build lichen pages
    rev_date = str(datetime.now().strftime("%Y%m%d_%H%M"))
    if not os.path.exists(static_dir + "lichen_html"):
        os.makedirs(static_dir + "lichen_html")
    print(req_list)

    for r in req_list:
        r.insert(2, slugify(r[1]))
        r.insert(4, slugify(r[3]))
        print(r)

        context = {
            "admin_email": "admin@wilderness.ordvac.com",
        }
        source_dir = base_dir + r[2] + slash + r[4] + slash
        out_dir = static_dir + "lichen_html" + slash + r[2] + slash + r[4] + slash
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        file_list = []
        file_list.append(r[4] + "-lichen-plots.json")
        file_list.append(r[4] + ".json.packed")
        file_list.append("index-wilderness.json")

        for file in file_list:
            copyfile(source_dir + file, out_dir + file)

        template = get_template("lichen.html")
        content = template.render(context)
        with uopen(out_dir + "index.html", "w") as static_file:
            static_file.write(content)

        print(r[1])
    print("lichen built")


def build_water(req_list):  # build another wcm index page
    out_dir = static_dir + "water_html" + slash
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    rev_date = str(datetime.now().strftime("%Y%m%d_%H%M"))
    r_list = []
    for r in req_list:
        r.insert(2, slugify(r[1]))
        r = [w.replace(" Wilderness", "") for w in r]
        r_list.append(r)
    req_list = sorted(r_list, key=lambda y: (reversor(y[0]), y[1].lower()))
    ask_list = [x for x in req_list if x[0] != ""]
    add_list = [x for x in req_list if x[0] == ""]
    add_list.extend(ask_list)

    top_list = []

    context = {
        "req_list": add_list,
        "rev_date": rev_date,
        "wilderness_count": "447",
        "to_date": "2023",
        "admin_email": "admin@wilderness.ordvac.com",
    }
    template = get_template("water.html")
    content = template.render(context)
    with uopen(out_dir + "index.html", "w") as static_file:
        static_file.write(content)


def build_d(req_list, build_list):  # build new pages
    rev_date = str(datetime.now().strftime("%Y%m%d_%H%M"))
    if not os.path.exists(static_dir + "d"):
        os.makedirs(static_dir + "d")

    if "lichen" in build_list:
        file_list = []
        file_list.append("lichen-airscores-nwps.csv")
        lwa = pandas.read_csv(base_dir + "lichen-airscores-nwps.csv")
        lw = lwa[["a", "w"]].drop_duplicates()
        lw = lw.sort_values(["a", "w"], ascending=True)
        lichen_list = []
        for index, row in lw.iterrows():
            lichen_list.append(
                [
                    "2023-09-05",
                    row["a"],
                    slugify(row["a"]),
                    row["w"],
                    slugify(row["w"]),
                    "je",
                ]
            )
        for r in lichen_list:
            if not os.path.exists(static_dir + "lichen"):
                os.makedirs(static_dir + "lichen")
            out_dir = static_dir + "lichen" + slash + r[2] + slash + r[4] + slash
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            template = get_template("lichen.html")
            content = template.render({})
            with uopen(out_dir + "index.html", "w") as static_file:
                static_file.write(content)

    for r in req_list:
        slug_a = slugify(r[1])
        slug_w = slugify(r[2])
        source_dir = base_dir + slug_a + slash + slug_w + slash
        a_dir = static_dir + "d" + slash + slug_a + slash
        print(source_dir)
        print(a_dir)
        # quit()
        # w_dir = a_dir + slash + r[4] + slash
        if not os.path.exists(a_dir):
            os.makedirs(a_dir)
        for m in build_list:
            if not os.path.exists(a_dir + m):
                os.makedirs(a_dir + m)
            file_list = []
            if m == "w":
                copyfile(
                    source_dir + "index-wilderness.json",
                    a_dir + m + slash + slug_w + "-wcm.json",
                )
                file_list.append(slug_w + ".json.packed")
            elif m == "water":
                file_list = []
                # file_list.append(r[2] + '-water-tidy.csv')
                # file_list.append(r[2] + '_ca_in.json.packed')
                # file_list.append(r[2] + '_ln_in.json.packed')
                # file_list.append(r[2] + '_pl_in.json.packed')
                if not os.path.exists(static_dir + "water"):
                    os.makedirs(static_dir + "water")
                out_dir = (
                    static_dir
                    + "water"
                    + slash
                    + slug_a
                    + slash
                    + slug_w
                    + slash
                    + "impaired-streams"
                    + slash
                )
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                template = get_template("impaired-streams.html")
                content = template.render({})
                with uopen(out_dir + "index.html", "w") as static_file:
                    static_file.write(content)
                out_dir = (
                    static_dir
                    + "water"
                    + slash
                    + slug_a
                    + slash
                    + slug_w
                    + slash
                    + "impaired-lakes"
                    + slash
                )
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                template = get_template("impaired-lakes.html")
                content = template.render({})
                with uopen(out_dir + "index.html", "w") as static_file:
                    static_file.write(content)
            elif m == "ozone":
                pass
            elif m == "visibility":
                pass
            elif m == "tdep_ns":
                pass
            elif m == "lichen":
                pass
            elif m == "remoteness":
                file_list = []
                file_list.append(slug_w + "-rem-in-fin")
                file_list.append(slug_w + "-rem-out-fin")
                file_list.append(slug_w + "-rem-in-roadcore2")
                file_list.append(slug_w + "-rem-in-trails")
                file_list.append(slug_w + "-rem-in-devln")
                file_list.append(slug_w + "-rem-in-devpl")
                file_list.append(slug_w + "-rem-in-devpt")
                file_list.append(slug_w + "-rem-out-roadcore2")
                file_list.append(slug_w + "-rem-out-trails")
                file_list.append(slug_w + "-rem-out-devln")
                file_list.append(slug_w + "-rem-out-devpl")
                file_list.append(slug_w + "-rem-out-devpt")
                file_list.append(slug_w + "_trails")
                file_list.append(slug_w + "_roadcore2")
                file_list.append(slug_w + "_devpt")
                file_list.append(slug_w + "_devln")
                file_list.append(slug_w + "_devpl")
                file_list = [str(x) + ".json.packed" for x in file_list]
                print(file_list)
                if not os.path.exists(static_dir + "remoteness"):
                    os.makedirs(static_dir + "remoteness")
                out_dir = (
                    static_dir + "remoteness" + slash + slug_a + slash + slug_w + slash
                )
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                template = get_template("remoteness.html")
                content = template.render({})
                with uopen(out_dir + "index.html", "w") as static_file:
                    static_file.write(content)
            for file in file_list:
                copyfile(source_dir + file, a_dir + m + slash + file)
        print(r)

        # template = get_template("lichen.html")
        # content = template.render(context)
        # with uopen(out_dir + "index.html", "w") as static_file:
        #    static_file.write(content)


def get_tdep():
    # open page
    # download files
    # extract
    # stack
    pass


def get_wetdep():
    # https://webcam.srs.fs.fed.us/results/dep/ is gone
    pass


def get_ozone():
    # open page
    # download files
    pass


def get_visibility():
    # open copeland page if possible
    # download files
    pass


def get_lichen():
    # geiser box is invitation only
    pass
