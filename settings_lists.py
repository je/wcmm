

def test_wilderness_list():
    wilderness_list = []
    #wilderness_list.append('Absaroka-Beartooth Wilderness') # typical
    wilderness_list.append('Barbours Creek Wilderness')
    # roadcore collection
    wilderness_list.append('North Fork John Day Wilderness')
    # mixed collection at dev_ln in 408 awilderness_devx.to_file(driver=out_driver, filename=out_dir + awilderness_devx_file)
    # empty at 664 inout = geopandas.overlay(inroads, outroads, how='intersection')
    wilderness_list.append('Round Island Wilderness')
    wilderness_list.append('El Toro Wilderness')
    # off grids
    return wilderness_list

def alaska_wilderness_list():
    wilderness_list = []
    wilderness_list.append('Chuck River Wilderness')
    wilderness_list.append('Coronation Island Wilderness')
    wilderness_list.append('Endicott River Wilderness')
    wilderness_list.append('Karta River Wilderness')
    wilderness_list.append('Kootznoowoo Wilderness')
    wilderness_list.append('Kuiu Wilderness')
    wilderness_list.append('Maurille Islands Wilderness')
    wilderness_list.append('Misty Fiords National Monument Wilderness')
    wilderness_list.append('Petersburg Creek-Duncan Salt Chuck Wilderness')
    wilderness_list.append('Pleasant/Lemusurier/Inian Islands Wilderness')
    wilderness_list.append('Russell Fjord Wilderness')
    wilderness_list.append('South Baranof Wilderness')
    wilderness_list.append('South Etolin Wilderness')
    wilderness_list.append('South Prince of Wales Wilderness')
    wilderness_list.append('Stikine-LeConte Wilderness')
    wilderness_list.append('Tebenkof Bay Wilderness')
    wilderness_list.append('Tracy Arm-Fords Terror Wilderness')
    wilderness_list.append('Warren Island Wilderness')
    wilderness_list.append('West Chichagof-Yakobi Wilderness')
    return wilderness_list

def pilot_wilderness_list():
    wilderness_list = []
    wilderness_list.append('Agua Tibia Wilderness') # wa 17964.28961 oa 13133.61312 ia 10540.38769
    wilderness_list.append('Anaconda Pintler Wilderness') # wa 158753.6039 oa 144899.4844 ia 60206.26354
    wilderness_list.append('Ashdown Gorge Wilderness')
    wilderness_list.append('Boundary Waters Canoe Area Wilderness')
    wilderness_list.append('Box-Death Hollow Wilderness')
    wilderness_list.append('Bucks Lake Wilderness')
    wilderness_list.append('Cohutta Wilderness')
    wilderness_list.append('Columbine-Hondo Wilderness')
    wilderness_list.append('Cottonwood Forest Wilderness')
    wilderness_list.append('Cruces Basin Wilderness')
    wilderness_list.append('Desolation Wilderness')
    wilderness_list.append('Ellicott Rock Wilderness')
    wilderness_list.append('Greenhorn Mountain Wilderness')
    wilderness_list.append('Indian Heaven Wilderness')
    wilderness_list.append('James River Face Wilderness')
    wilderness_list.append('Kuiu Wilderness')
    wilderness_list.append('La Garita Wilderness')
    wilderness_list.append('Latir Peak Wilderness')
    wilderness_list.append('Linville Gorge Wilderness')
    wilderness_list.append('Lost Creek Wilderness')
    wilderness_list.append('Mission Mountains Wilderness')
    wilderness_list.append('Mount Adams Wilderness')
    wilderness_list.append('Mount Evans Wilderness')
    wilderness_list.append('Petersburg Creek-Duncan Salt Chuck Wilderness')
    wilderness_list.append('Pine Valley Mountain Wilderness')
    wilderness_list.append('Saint Mary\'s Wilderness')
    wilderness_list.append('Tebenkof Bay Wilderness')
    wilderness_list.append('Trapper Creek Wilderness')
    wilderness_list.append('West Elk Wilderness')
    wilderness_list.append('Wheeler Peak Wilderness')
    wilderness_list = sorted(list(set(wilderness_list).difference(alaska_wilderness_list())))
    return wilderness_list

def y2019_wilderness_list():
    wilderness_list = []
    wilderness_list.append('Cabinet Mountains Wilderness')
    wilderness_list.append('Mount Sneffels Wilderness') # jstagner
    wilderness_list.append('Uncompahgre Wilderness') # jstagner
    wilderness_list.append('Raggeds Wilderness') # jstagner
    wilderness_list.append('Sangre de Cristo Wilderness')
    wilderness_list.append('Spanish Peaks Wilderness') # mcunningham
    wilderness_list.append('Capitan Mountains Wilderness') # wribbans
    wilderness_list.append('White Mountain Wilderness') # wribbans
    wilderness_list.append('Chama River Canyon Wilderness') # areville / kdeutsch
    wilderness_list.append('Dome Wilderness') # areville / kdeutsch
    wilderness_list.append('Pecos Wilderness') # areville / kdeutsch
    wilderness_list.append('San Pedro Parks Wilderness') # areville / kdeutsch
    wilderness_list.append('Bridger Wilderness') # dcallahan / esulser
    wilderness_list.append('Gros Ventre Wilderness') # dcallahan / esulser
    wilderness_list.append('Teton Wilderness') # dcallahan / esulser
    wilderness_list.append('Jedediah Smith Wilderness')
    wilderness_list.append('Winegar Hole Wilderness')
    wilderness_list.append('Hauser Wilderness') # jzehr
    wilderness_list.append('Pine Creek Wilderness') # jzehr
    wilderness_list.append('San Mateo Canyon Wilderness') # jzehr
    wilderness_list.append('Mokelumne Wilderness')
    wilderness_list.append('Sanhedrin Wilderness') # jzehr
    wilderness_list.append('Cahuilla Mountain Wilderness') # dcallahan / esulser
    wilderness_list.append('San Jacinto Wilderness') # dcallahan / esulser
    wilderness_list.append('Santa Rosa Wilderness') # dcallahan / esulser
    wilderness_list.append('South Fork San Jacinto Wilderness') # dcallahan / esulser
    wilderness_list.append('Emigrant Wilderness') # jzehr
    wilderness_list.append('Granite Chief Wilderness') # jzehr
    wilderness_list.append('Glacier View Wilderness') # adunham
    wilderness_list.append('Goat Rocks Wilderness') # adunham
    wilderness_list.append('Tatoosh Wilderness') # adunham
    wilderness_list.append('Priest Wilderness')
    wilderness_list.append('Ramseys Draft Wilderness')
    wilderness_list.append('Three Ridges Wilderness')
    wilderness_list.append('Thunder Ridge Wilderness')
    wilderness_list.append('Alexander Springs Wilderness')
    wilderness_list.append('Big Gum Swamp Wilderness')
    wilderness_list.append('Billies Bay Wilderness')
    wilderness_list.append('Bradwell Bay Wilderness')
    wilderness_list.append('Juniper Prairie Wilderness')
    wilderness_list.append('Little Lake George Wilderness')
    wilderness_list.append('Mud Swamp/New River Wilderness')
    wilderness_list.append('Middle Prong Wilderness') # kdevarona
    wilderness_list.append('Shining Rock Wilderness') # kdevarona
    wilderness_list.append('East Fork Wilderness')
    wilderness_list.append('Hurricane Creek Wilderness')
    wilderness_list.append('Leatherwood Wilderness')
    wilderness_list.append('Richland Creek Wilderness')
    wilderness_list.append('Upper Buffalo Wilderness')
    wilderness_list.append('Blackjack Springs Wilderness')
    wilderness_list.append('Headwaters Wilderness')
    wilderness_list.append('Porcupine Lake Wilderness')
    wilderness_list.append('Rainbow Lake Wilderness')
    wilderness_list.append('Whisker Lake Wilderness')
    wilderness_list.append('Pleasant/Lemusurier/Inian Islands Wilderness') # kebinger
    wilderness_list.append('Russell Fjord Wilderness') # kebinger
    wilderness_list = sorted(list(set(wilderness_list).difference(alaska_wilderness_list())))
    wilderness_list = sorted(list(set(wilderness_list).difference(y2019_short_wilderness_list())))
    return wilderness_list

def y2019_short_wilderness_list():
    wilderness_list = []
    wilderness_list.append('Mount Sneffels Wilderness') # jstagner
    wilderness_list.append('Uncompahgre Wilderness') # jstagner
    wilderness_list.append('Raggeds Wilderness') # jstagner
    wilderness_list.append('Chama River Canyon Wilderness') # areville
    wilderness_list.append('Dome Wilderness') # areville
    wilderness_list.append('Pecos Wilderness') # areville
    wilderness_list.append('San Pedro Parks Wilderness') # areville
    wilderness_list.append('Hauser Wilderness') # jzehr
    wilderness_list.append('Pine Creek Wilderness') # jzehr
    wilderness_list.append('San Mateo Canyon Wilderness') # jzehr
    wilderness_list.append('Cahuilla Mountain Wilderness') # dcallahan
    wilderness_list.append('San Jacinto Wilderness') # dcallahan
    wilderness_list.append('Santa Rosa Wilderness') # dcallahan
    wilderness_list.append('South Fork San Jacinto Wilderness') # dcallahan
    wilderness_list.append('Spanish Peaks Wilderness') # mcunningham
    wilderness_list = sorted(list(set(wilderness_list).difference(alaska_wilderness_list())))
    return wilderness_list

def other_wilderness_list():
    wilderness = geopandas.read_file(wilderness_gdb)
    wilderness = wilderness.rename(columns={'WILDERNESSNAME': 'NAME'})
    wilderness_list = wilderness['NAME'].tolist()
    wilderness_list = sorted(list(set(wilderness_list).difference(test_wilderness_list())))
    wilderness_list = sorted(list(set(wilderness_list).difference(alaska_wilderness_list())))
    wilderness_list = sorted(list(set(wilderness_list).difference(pilot_wilderness_list())))
    wilderness_list = sorted(list(set(wilderness_list).difference(y2019_wilderness_list())))
    return wilderness_list

def all_wilderness_list():
    wilderness = geopandas.read_file(wilderness_gdb)
    wilderness = wilderness.rename(columns={'WILDERNESSNAME': 'NAME'})
    wilderness_list = wilderness['NAME'].tolist()
    wilderness_list = sorted(list(set(wilderness_list).difference(test_wilderness_list())))
    return wilderness_list
