import os
import sys
import re
import requests
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import certifi
import logging
import urllib3
import yaml
import json
import warnings
from itertools import product  # import product for Cartesian product of lists


"""
TITLE: OSM features life cycle (?) (https://wiki.openstreetmap.org/wiki/Comparison_of_life_cycle_concepts#start_date_and_opening_date)

INPUT
- Input raster datasets to extract spatial extent of area analysed (GeoTIFF)

OUTPUT 
- Plots with comparison of usage of particular OSM tags throughout years (for Catalonia and Northern England) for features that have been described by different tags (by area, count, length).

NOTES
This script is able to consume multiple values from the lists from the configuration file (any combinations of years with filenames of raster datasets)
User-friendly alternative to analyse historical usage of OSM keys can be found here: https://taghistory.raifer.tech

ISSUES AND LIMITATIONS:
- Experienced outage of ohsome API servers (Error 503) on 07/10/2024.
- Unfortunately, ohsome API filter syntax does not support pattern matching like typical SQL queries.
It was experienced while trying to extract all mentions of 'abandoned' roads (not only 'highway=abandoned' but also 'highway=primary;abandoned')
Visualisation is accessed here: https://taghistory.raifer.tech/#***/highway/abandoned&***/highway/primary%3Babandoned&***/highway/secondary%3Babandoned&***/highway/tertiary%3Babandoned&***/highway%3Aabandoned/&***/disused%3Ahighway/
"""

# setup logging
logging.basicConfig(level=logging.INFO) # for more verbosity use 'DEBUG'
logger = logging.getLogger(__name__)

# custom TLS Adapter to enforce TLSv1.2
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = ssl.create_default_context()
        ctx.options |= ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1  # enforce TLSv1.2+
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx
        )

session = requests.Session()
session.mount('https://', TLSAdapter())

# import from external module
from reprojection import RasterTransform

# load filename and year from the configuration file
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

years = config.get('year')
if not isinstance(years, list):
    years = [years]
print (f"Yearstamps of input raster datasets:{years}")

if not years or any(year is None for year in years):
    warnings.warn("Year variable is not found or is None in the configuration file.")

lulc_templates = config.get('lulc')
if not isinstance(lulc_templates, list):
    lulc_templates = [lulc_templates]

if not lulc_templates or any(lulc is None for lulc in lulc_templates):
    warnings.warn("LULC template is not found or is None in the configuration file.")

# generate lulc filenames for each combination of lulc template and year
lulc_year_combinations = [(template.format(year=year), template, year) for template, year in product(lulc_templates, years)]

print(f"Input rasters to be used for processing: {', '.join([name for name, _, _ in lulc_year_combinations])}")

# specify parent directory
parent_dir = os.getcwd()  # automatically extract current folder to avoid hard-coded path.
print(f"Parent directory: {parent_dir}")

# add Python path to search for scripts, modules
sys.path.append(parent_dir)

# specify paths
lulc_dir = config.get('lulc_dir')
impedance_dir = config.get('impedance_dir')
vector_dir = config.get('vector_dir')
output_dir = config.get('output_dir')

# create the output directory if it does not exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Created directory: {output_dir}")

# initialize bounding box parameter string for the further request
bbox_params = []

# process each lulc derived from different years
for lulc, template, year in lulc_year_combinations:
    lulc_path = os.path.join(parent_dir, lulc_dir, lulc)

    # normalize paths (to avoid mixing of backslashes and forward slashes)
    lulc_path = os.path.normpath(lulc_path)
    print(f"Path to the input raster dataset: {lulc_path}")

    # call external module to reproject input raster dataset (from config)
    try:
        x_min, y_min, x_max, y_max = RasterTransform(lulc_path).bbox_to_WGS84()  # transform raster to WGS84
        bbox = f"{x_min},{y_min},{x_max},{y_max}"

        # naming the bounding box (without year)
        template_name = f"bbox_{os.path.splitext(os.path.basename(template))[0]}"

        # TODO - replace with more flexible name (hardcoded now)
        if 'ukceh' in template_name.lower():
            bbox_name = f"UK_UKCEH_LCM"
        else:
            bbox_name = f"Catalonia_MUCSC"
        
        print(f"Bounding box for {bbox_name}: {bbox}")

        # append bbox with name to parameters
        bbox_params.append(f"{bbox_name}:{bbox}")

    except Exception as e:
        print(f"Failed to transform {lulc_path}: {e}")

    # hard-coded names of bounding boxes
    
# join bounding box parameters into a single string with '|'
bboxes = '|'.join(bbox_params)

print(f"Bounding boxes to retrieve OSM historical data are: {bboxes}")
print("-" * 40)

# define API endpoints
# group by a few areas and tags for number of features, length and area
urls = {
    "count": 'https://api.ohsome.org/v1/elements/count/groupBy/boundary/groupBy/tag', # number of features
    "length": 'https://api.ohsome.org/v1/elements/length/groupBy/boundary/groupBy/tag', # length of linear features
    "area": 'https://api.ohsome.org/v1/elements/area/groupBy/boundary/groupBy/tag' # area of polygonal features
}

# other options
"""
url = 'https://api.ohsome.org/v1/elementsFullHistory/geometry'
url = 'https://api.ohsome.org/v1/elements/count'
url = 'https://api.ohsome.org/v1/elements/count/groupBy/boundary'
"""      

# define comparison pairs for OSM tags (each comparison illustrated on separate figure)
comparison_pairs = [
    ["water=river","waterway=riverbank"],
    ["natural=water and water=reservoir","landuse=reservoir"]
]

# define parameters
params_list = [
    {
    # 1.1. To compare 'water=river' and 'waterway=riverbank' (deprecated) tags
    "bboxes": bboxes,
    "format": "csv",
    "showMetadata": "true",
    "time": "2010-01-01/2024-01-01/P1M", # consumes a few formats of timestamp. Means: start date, end date, timestep - 1 month
    "filter": "water=river",
    "groupByKey": "water",
    "groupByValues": "river"
    },
    {
    # 1.2. To compare 'water=river' and 'waterway=riverbank' (deprecated) tags
    "bboxes": bboxes,
    "format": "csv",
    "showMetadata": "true",
    "time": "2010-01-01/2024-01-01/P1M", # consumes a few formats of timestamp. Means: start date, end date, timestep - 1 month
    "filter": "waterway=riverbank",
    "groupByKey": "waterway",
    "groupByValues": "riverbank"
    },
    {
    # 2.1. To compare  'natural=water and water=reservoir' and 'waterway=riverbank' (deprecated) tags
    "bboxes": bboxes,
    "format": "csv",
    "showMetadata": "true",
    "time": "2010-01-01/2024-01-01/P1M", # consumes a few formats of timestamp. Means: start date, end date, timestep - 1 month
    "filter": "natural=water and water=reservoir",
    "groupByKey": "natural", # only one key is allowed, but grouping is not relevant for us
    "groupByValues": "water"
    },
    {
    # 2.2. To compare  'natural=water and water=reservoir' and 'waterway=riverbank' (deprecated) tags
    "bboxes": bboxes,
    "format": "csv",
    "showMetadata": "true",
    "time": "2010-01-01/2024-01-01/P1M", # consumes a few formats of timestamp. Means: start date, end date, timestep - 1 month
    "filter": "landuse=reservoir",
    "groupByKey": "landuse",
    "groupByValues": "reservoir"
    }
]

# another pair of deprecated tags can't be analysed through ohsome api (does not support pattern matching)
"""
    {
    # 3.1. To compare  'abandoned:highway=*' and 'highway=abandoned' (deprecated) tags
    "bboxes": bboxes,
    "format": "csv",
    "showMetadata": "true",
    "time": "2010-01-01/2024-01-01/P1M", # consumes a few formats of timestamp. Means: start date, end date, timestep - 1 month
    "filter": "abandoned:highway=*",
    "groupByKey": "abandoned:highway",
    "groupByValues": "*",

    },
    {# 3.2. To compare  'abandoned:highway=*' and 'highway=abandoned' (deprecated) tags
    "bboxes": bboxes,
    "format": "csv",
    "showMetadata": "true",
    "time": "2010-01-01/2024-01-01/P1M", # consumes a few formats of timestamp. Means: start date, end date, timestep - 1 month
    "filter": "highway=abandoned", # but ohsome API doesn't support pattern matching (%abandoned%) and it is not possible to extract values like 'primary;abandoned'
    "groupByKey": "highway",
    "groupByValues": "abandoned"
    }
"""

# function to generate filename
def generate_filename(filter_value, url_type):
    filter_key_value = filter_value.replace("=", "_")
    filename = re.sub(r'\W+', '_', filter_key_value)
    filename = f"{url_type}_{filename}.csv"
    return filename

# define the output directory
output_dir = "ohsome_output"
os.makedirs(output_dir, exist_ok=True)

# initialise dictionary to store data
data_by_url_type = {
    'count': [],
    'length': [],
    'area': []
}


# loop through URLs and parameters
for url_type, url in urls.items(): # loop over dictionary with ohsome endpoints
    for params in params_list: # loop over list with dictionaries of parameters for ohsome requests
        filter_value = params.get("filter", "") # for example, 'water=river'
        title = params.get("filter", "Plot") 
        filename = generate_filename(filter_value, url_type) # for example 'area_landuse_reservoir'
        filepath = os.path.join(output_dir, filename)
        
        logger.info(f"Sending request to {url}")
        logger.info(f"Derived filename: {filepath}")
        
        try:
            response = session.post(url, data=params, timeout=600)  # use 'data' instead of 'params'
            full_url = f"{url}?" + "&".join([f"{key}={value}" for key, value in params.items()])
            logger.debug(f"Full URL: {full_url}")
            logger.info(f"Response status code: {response.status_code}") 
            
            if response.status_code == 200:
                logger.info("Request successful")
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(response.text)
                logger.info(f"Saved response to {filepath}")
                logger.info("-" * 40)
                
                csv_data = response.text # get text of response                 
                df = pd.read_csv(StringIO(csv_data), delimiter=';', skiprows=5)  # skip the first 5 rows if needed
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                data_by_url_type[url_type].append((df, title)) # append it to df with title (pointing out tags)
            else:
                logger.error(f"Failed to retrieve data from {url}: {response.status_code}")
                logger.error("-" * 40)
        except requests.exceptions.SSLError as ssl_err:
            logger.error(f"SSL error occurred: {ssl_err}")
            logger.error("-" * 40)
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request exception: {req_err}")
            logger.error("-" * 40)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            logger.error("-" * 40)

# extract all unique filters from params_list
filter_values = {params['filter'] for params in params_list}
# create a color cycle from a color map
colors = plt.cm.get_cmap('tab10', len(filter_values) + 2)  # Get a color map with enough distinct colors
# create a color map for each unique filter value (tag)
color_map = {filter_value: colors(i) for i, filter_value in enumerate(filter_values)}


# plotting the data for each url_type
for url_type, data_list in data_by_url_type.items():  # url_type is area/length/count; data_list is a list of tuples
    print(f"DATA LIST IS: {data_list}")  # debug

    # create a dictionary to group data by title (filter value)
    data_by_title = {}

    # aggregate data by title
    for df, title in data_list:  # title is the filter value, e.g., 'water=river'
        if title not in data_by_title:
            data_by_title[title] = []
        data_by_title[title].append(df)

    # loop over each comparison pair
    for pair in comparison_pairs:
        plt.figure(figsize=(12, 8))

        # loop through the titles in each pair and plot them
        for title in pair:
            if title in data_by_title:  # Check if title exists in data
                # combine the data for the same title by summing 
                combined_df = pd.concat(data_by_title[title]).groupby('timestamp').sum().reset_index()

                # plot each column except for 'timestamp'
                for col in combined_df.columns[1:]:  # skip the 'timestamp' column
                    plt.plot(combined_df['timestamp'], combined_df[col], linestyle='dotted', linewidth=3, label=f"{col} | {title}")  # use title and col as label
                    # to add colour map use ', color=color_map[title]'
        
        # set the labels and title for each plot
        plt.xlabel('Time')
        plt.ylabel(f'{url_type.capitalize()} of features')  # 'Area of features'
        plt.title(f'{url_type.capitalize()} over time for {pair}')  # e.g., 'Area over time for [water=river, waterway=riverbank]'
        plt.grid(True)
        plt.legend(loc='best', bbox_to_anchor=(1, 1))
        plt.xticks(rotation=45)
        plt.tight_layout()  # to adjust labels
        
        # show the plot
        plt.show()

"""
# loop through each parameter set, send POST request, and plot the data
for params in params_list:
    title = params.get("filter", "Plot")  # extract the plot title from the parameters
    response = requests.post(url, params=params, timeout=600)  # send the POST request
    
    if response.status_code == 200:
        # load the response content into a pandas DataFrame
        csv_data = StringIO(response.text) # to simulate a file object
        df = pd.read_csv(csv_data, skiprows=6, sep=';') # skip 6 first rows (metadata)
        
        # check if the expected columns are in dataframe
        if 'timestamp' in df.columns and 'count' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])  # ensure timestamp is in datetime format
            
            # plot 
            plt.figure(figsize=(10, 6))
            plt.plot(df['timestamp'], df['count'], marker='o', linestyle='-', label=params['groupByKey'])
            plt.xlabel('Time')
            plt.ylabel('Count of Features')
            plt.title(title)
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
        else:
            print(f"Unexpected data format in response: {df.columns}")
    else:
        print(f"Failed to retrieve data: {response.status_code}")
"""

"""
data = response.json()

# save the response to a JSON file
with open('ohsome_response.json', 'w') as json_file:
    json.dump(data, json_file)

"""    


# to export to CSV
"""
# function to generate filename from filter
def generate_filename(filter_value):
    # extract key-value pairs from the filter (e.g., water=river -> water_river)
    filter_key_value = filter_value.replace("=", "_")
    # remove any non-alphanumeric characters and spaces
    filename = re.sub(r'\W+', '_', filter_key_value)
    # add a file extension
    filename = f"{filename}.csv"
    return filename

# loop through each parameter set, derive the filename, and send the POST request
for params in params_list:
    filter_value = params.get("filter", "")
    filename = generate_filename(filter_value)
    
    print(f"Derived filename: {filename}")
    
    # send the POST request
    response = requests.post(url, params=params)
    
    # handle response
    if response.status_code == 200:
        print("Request successful")
        # save response to a file with the derived filename
        with open(filename, 'w') as file:
            file.write(response.text)
    else:
        print(f"Failed to retrieve data: {response.status_code}")
"""