# This script is able to consume multiple values from the lists from the configuration file (any combinations of years with filenames of raster datasets)

import yaml
import warnings
import os
import sys
from itertools import product  # import product for Cartesian product of lists
import requests
import json
import matplotlib.pyplot as plt
import pandas as pd
from io import StringIO
import re

# import from external module
from reprojection import RasterTransform

# load filename and year from the configuration file
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

years = config.get('year')
if not isinstance(years, list):
    years = [years]

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
parent_dir = os.getcwd()  # Automatically extract current folder to avoid hard-coded path.
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

        # Naming the bounding box (without year)
        template_name = f"bbox_{os.path.splitext(os.path.basename(template))[0]}"

        if 'ukceh' in template_name.lower():
            bbox_name = f"UK_UKCEH_LCM"
        else:
            bbox_name = f"Catalonia_MUCSC"
        
        print(f"Bounding box for {bbox_name}: {bbox}")

        # Append bbox with name to parameters
        bbox_params.append(f"{bbox_name}:{bbox}")

    except Exception as e:
        print(f"Failed to transform {lulc_path}: {e}")

    # hard-coded names of bounding boxes
    

# join bounding box parameters into a single string with '|'
bboxes = '|'.join(bbox_params)

print(f"Bounding boxes to retrieve OSM historical data are: {bboxes}")

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


# define parameters
params_list = [
    {
    # 1.1. To compare 'water'='river' and 'waterway'='riverbank' (deprecated) tags
    "bboxes": bboxes,
    "format": "csv",
    "showMetadata": "true",
    "time": "2010-01-01/2024-01-01/P1M", # consumes a few formats of timestamp. Means: start date, end date, timestep - 1 month
    "filter": "water=river",
    "groupByKey": "water",
    "groupByValues": "river"
    },
    {
    # 1.2. To compare 'water'='river' and 'waterway'='riverbank' (deprecated) tags
    "bboxes": bboxes,
    "format": "csv",
    "showMetadata": "true",
    "time": "2010-01-01/2024-01-01/P1M", # consumes a few formats of timestamp. Means: start date, end date, timestep - 1 month
    "filter": "waterway=riverbank",
    "groupByKey": "waterway",
    "groupByValues": "riverbank"
    },
    {
    # 2.1. To compare  "natural=water and water=reservoir" and 'waterway'='riverbank' (deprecated) tags
    "bboxes": bboxes,
    "format": "csv",
    "showMetadata": "true",
    "time": "2010-01-01/2024-01-01/P1M", # consumes a few formats of timestamp. Means: start date, end date, timestep - 1 month
    "filter": "natural=water and water=reservoir",
    "groupByKey": "water",
    "groupByValues": "reservoir"
    },
    {
    # 2.2. To compare  "natural=water and water=reservoir" and 'waterway'='riverbank' (deprecated) tags
    "bboxes": bboxes,
    "format": "csv",
    "showMetadata": "true",
    "time": "2010-01-01/2024-01-01/P1M", # consumes a few formats of timestamp. Means: start date, end date, timestep - 1 month
    "filter": "landuse=reservoir",
    "groupByKey": "water",
    "groupByValues": "reservoir"
    }
]

# function to generate filename from filter and URL type
def generate_filename(filter_value, url_type):
    # extract key-value pairs from the filter (e.g., water=river -> water_river)
    filter_key_value = filter_value.replace("=", "_")
    # remove any non-alphanumeric characters and spaces
    filename = re.sub(r'\W+', '_', filter_key_value)
    # combine URL type with filename and add a file extension
    filename = f"{url_type}_{filename}.csv"
    return filename

# define the output directory
output_dir = "ohsome_output"
os.makedirs(output_dir, exist_ok=True)

# dictionary to store data grouped by url_type (count of features, length of features, area of features)
data_by_url_type = {
    'count': [],
    'length': [],
    'area': []
}

# loop through each set of parameters and send request
responses = []  # store responses needed for further processing
for url_type, url in urls.items(): # looping over a dictionary with URLS
    for params in params_list: # loop over each set of parameters
        filter_value = params.get("filter", "")
        # generate the title based on the filter
        title = params.get("filter", "Plot")
        filename = generate_filename(filter_value, url_type) # create a filename from the filter specifications and url type (area, count, length)
        filepath = os.path.join(output_dir, filename)
        
        print(f"Sending request to {url}")
        print(f"Derived filename: {filepath}")
        
        # send the POST request
        response = requests.post(url, params=params)
        print(f"Response status code: {response.status_code}")

        # handle response
        if response.status_code == 200:
            print("Request successful")
            # save response to a file with the derived filename
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(response.text)
            print(f"Saved response to {filepath}")

            # load the response content into a dataframe, skipping metadata rows
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data, delimiter=';',skiprows=5)  # skip the first 5 rows of metadata

            # ensure timestamp is in datetime format
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # store the dataframe and associated label (title)
            data_by_url_type[url_type].append((df, title))

        else:
            print(f"Failed to retrieve data from {url}: {response.status_code}")


# plotting the data for each url_type
for url_type, data_list in data_by_url_type.items():
    plt.figure(figsize=(12, 8))
    
    for df, title in data_list:
        # plot each combination of bboxes and filter value
        for col in df.columns[1:]:  # skip the 'timestamp' column
            plt.plot(df['timestamp'], df[col], linestyle='--', label=f"{title} | {col}") # placeholders for bboxes and filters
    
    plt.xlabel('Time')
    plt.ylabel(f'{url_type.capitalize()} of features')
    plt.title(f'{url_type.capitalize()} over time')
    plt.grid(True)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


"""
# loop through each parameter set, send POST request, and plot the data
for params in params_list:
    title = params.pop("title")  # Extract the plot title from the parameters
    response = requests.post(url, params=params)  # Send the POST request
    
    if response.status_code == 200:
        # Load the response content into a pandas DataFrame
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        
        # Check if the expected columns are in the DataFrame
        if 'timestamp' in df.columns and 'count' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])  # Ensure timestamp is in datetime format
            
            # Plot the data
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


# To export to CSV

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


# WORKS!
# TODO - postprocessing - plots



