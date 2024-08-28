# import yaml
# import os
# already specified in parent Jupyter Notebook

import warnings
import geopandas as gpd

class LulcCodes:
    def __init__(self, road, railway, urban, suburban, water):
        self.lulc_road = road
        self.lulc_railway = railway
        self.lulc_urban = urban
        self.lulc_suburban = suburban
        self.lulc_water = water


def codes(config, impedance_file):
    # define impedance variable
    impedance = config.get('impedance')
    if impedance is not None:
        print(f"Using auxiliary CSV data from {impedance}.")
    else:
        warnings.warn("No valid auxiliary CSV data found.")

    # read impedance through geopandas
    impedance = gpd.read_file(impedance_file)

    # find impedance values matching with built-up areas of human impact on habitats and inland water
    lulc_urban = impedance.loc[impedance['type'].str.contains('urban|built|build|resident|industr|commerc', case=False), 'lulc'].iloc[0]
    lulc_suburban = impedance.loc[impedance['type'].str.contains('suburban|urbanized|urbanised', case=False), 'lulc'].iloc[0]

    lulc_road = impedance.loc[impedance['type'].str.contains(r'\broad|highway', case=False), 'lulc']
    if not lulc_road.empty:
        lulc_road = lulc_road.iloc[0]
    else:
        lulc_road = lulc_urban

    lulc_railway = impedance.loc[impedance['type'].str.contains('rail|train', case=False), 'lulc']
    if not lulc_railway.empty:
        lulc_railway = lulc_railway.iloc[0]
    else:
        lulc_railway = lulc_suburban

    lulc_water = impedance.loc[impedance['type'].str.contains('continental water|inland water|freshwater', case=False), 'lulc']
    if not lulc_water.empty:
        lulc_water = lulc_water.iloc[0]
    else:
        lulc_water = impedance.loc[impedance['type'].str.contains('water|aqua|river', case=False), 'lulc'].iloc[0]

    # create an instance of LulcCodes
    result = LulcCodes(lulc_road, lulc_railway, lulc_urban, lulc_suburban, lulc_water)
    
    return result