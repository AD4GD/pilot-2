# This script is retrieving the subset of Open Street Map data which is meaningful for enriching raster land-use/land-cover (LULC) data based on the extent of raster data. 

import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon
from osgeo import gdal
import pyproj
import osmnx as ox
from pyproj import CRS

# to measure time to run code
import time

# starting to measure running time
start_time = time.time()

# directly specifying that gdal expections should be used
gdal.UseExceptions()

# overpy and overpass are installed through the command propmpt "pip install requests" after activating conda environment
# !geopandas and pandas must be installed this way (to provide compatible versions):
# conda install -c conda-forge geopandas pandas

parent_dir = os.getcwd()
child_dir = r'data\input\lulc'
# define output_dir in input\ folder as the output of this code is using for further preprocessing
output_dir = r'data\input\vector'

# TO SPECIFY INPUT RASTER DATA
## specifying the file names. We should specify the last available version of LULC because open-access APIs do not provide historical data from OSM.
lulc = 'lulc_2022.tif'

## specifying the path to these files through the path variables
lulc = os.path.join(parent_dir,child_dir,lulc)

## to load the raster file and get its extent and cell size
raster = gdal.Open(lulc)
if raster is not None:
    inp_lyr = raster.GetRasterBand(1)  # get the first band
    x_min_cart, x_max_cart, y_min_cart, y_max_cart = raster.GetGeoTransform()[0], raster.GetGeoTransform()[0] + raster.RasterXSize * raster.GetGeoTransform()[1], raster.GetGeoTransform()[3] + raster.RasterYSize * raster.GetGeoTransform()[5], raster.GetGeoTransform()[3]
    '''
    cellsize = raster.GetGeoTransform()[1]  # assuming the cell size is constant in both x and y directions
    x_ncells = int((x_max - x_min) / cellsize)
    y_ncells = int((y_max - y_min) / cellsize)
    '''
    # close the raster  to keep memory empty
    raster = None

## CONVERSION TO GEOGRAPHICAL COORDINATES as Nominatim API accepts only coordinates in geographical coordinate

## defining function to transform
transform_cart_to_geog = pyproj.Transformer.from_crs(
    pyproj.CRS('EPSG:32631'),  # UTM Zone 31N
    pyproj.CRS('EPSG:4326')   # WGS84 geographic
)

## running function
x_min, y_min = transform_cart_to_geog.transform(x_min_cart, y_min_cart)
x_max, y_max = transform_cart_to_geog.transform(x_max_cart, y_max_cart)


## to print the Cartesian coordinates before transformation
print("Before CRS transformation:")
print("x_min_cart:", x_min_cart)
print("x_max_cart:", x_max_cart)
print("y_min_cart:", y_min_cart)
print("y_max_cart:", y_max_cart)

## to print the transformed geographical coordinates
print("After CRS transformation:")
print("x_min:", x_min)
print("x_max:", x_max)
print("y_min:", y_min)
print("y_max:", y_max)

## to check the bounding box of input raster
print (x_min,y_min,x_max,y_max)

# 1. to extract ROADS through osmnx
bbox = [x_max, x_min, y_max, y_min]

## to fetch roads within the bounding box
tags = {'highway': ['motorway','trunk', 'primary', 'secondary', 'tertiary', 'motorway_link','trunk_link','primary_link','secondary_link','tertiary_link']}
gdf_roads = ox.features_from_bbox(*bbox, tags=tags)

'''
# to check lists in columns of dataframes
for col in gdf_roads.columns:
    if any(isinstance(val, list) for val in gdf_roads[col]):
        print('Column: {0}, has a list in it'.format(col))
'''
'''
# to print available columns
print(gdf_roads.dtypes)
'''

## to drop columns that are builded as lists because they're causing troubles while exporting geopackages
columns_to_drop = []
for col in gdf_roads.columns:
    if any(isinstance(val, list) for val in gdf_roads[col]):
        columns_to_drop.append(col)

gdf_roads=gdf_roads.drop(columns=columns_to_drop)

## to filter columns in the geodataframe
## to be modified - slice columns in this dataframes instead of filtering .loc[row_indexer,col_indexer]
filtered_columns = ['geometry','name','width','highway','level','bridge']  # specifying columns needed
gdf_roads_filtered = gdf_roads[filtered_columns]

## transforming text in the'width' columnn into numerical one
gdf_roads_filtered['width'] = pd.to_numeric(gdf_roads_filtered['width'], errors='coerce')  
## to convert to numeric, coerce errors to NaN - to omit all non-numerical values persisting in this column

## to filter roads by 'level' being equal to 0 or NULL
gdf_water_lines_filtered = gdf_roads_filtered[
    (gdf_roads_filtered['level'] == 0) | 
    (gdf_roads_filtered['level'].isnull())
]

## to filter only lines and multilines
gdf_roads_filtered = gdf_roads_filtered[gdf_roads_filtered['geometry'].geom_type.isin(['LineString', 'MultiLineString'])]

## reproject geodataframe to EPSG 25831
gdf_roads_filtered = gdf_roads_filtered.to_crs(CRS.from_epsg(25831))
print(gdf_roads_filtered)

## to export geodataframe as a single geopackage
output_path = os.path.join(output_dir,"roads.gpkg")
try:
    gdf_roads_filtered.to_file(output_path, driver='GPKG')
    print("Roads have been exported from OSM to:", output_path)
except Exception as e:
    print("Export of roads from OSM has failed:", e)
output_path = None

'''# OTHER OPTION TO EXPORT GEODATAFRAME AS A TEMPORARY GEOPACKAGE
# to export geodataframe as a temporary geopackage
temp_dir = tempfile.gettempdir()
temp_file_path = os.path.join(parent_dir, temp_dir, 'vector_roads.gpkg')
try:
    gdf_roads_filtered.to_file(temp_file_path, driver='GPKG')
    print("Roads have been exported from OSM to:", temp_file_path)
except Exception as e:
    print("Export of roads from OSM has failed:", e)
'''

print ("-------------------------")

# 2. to extract WATER BODIES through osmnx

## to fetch water features within the bounding box
tags = {'natural': 'water'}
gdf_water_bodies = ox.features_from_bbox(*bbox, tags=tags)

'''
# to check lists in columns of dataframes as lists cause issues for creating geopackage files
for col in gdf_water_bodies.columns:
    if any(isinstance(val, list) for val in gdf_water_bodies[col]):
        print('Column: {0}, has a list in it'.format(col))
'''

'''
# to print available columns
print(gdf_water_bodies.dtypes)
'''

## to drop columns that are builded as lists because they're causing troubles while exporting geopackages
columns_to_drop = []
for col in gdf_water_bodies.columns:
    if any(isinstance(val, list) for val in gdf_water_bodies[col]):
        columns_to_drop.append(col)

gdf_water_bodies=gdf_water_bodies.drop(columns=columns_to_drop)

## to filter columns in the geodataframe
filtered_columns = ['geometry','name','natural','water','height']  # specify columns needed (other attributes are not useful to enrich LULC data)
gdf_water_filtered = gdf_water_bodies[filtered_columns]

## to filter only polygons and myltipolygons
gdf_water_filtered = gdf_water_filtered[gdf_water_filtered['geometry'].geom_type.isin(['Polygon', 'MultiPolygon'])]

## reproject geodataframe to EPSG 25831
gdf_water_filtered = gdf_water_filtered.to_crs(CRS.from_epsg(25831))

print(gdf_water_filtered)

## to export geodataframe as a single geopackage
output_path = os.path.join(output_dir,"water_bodies.gpkg")
try:
    gdf_water_filtered.to_file(output_path, driver='GPKG')
    print("Water bodies have been exported from OSM to:", output_path)
except Exception as e:
    print("Export of water bodies from OSM has failed:", e)
output_path = None


'''# OTHER OPTION TO EXPORT GEODATAFRAME AS A TEMPORARY GEOPACKAGE
temp_dir = tempfile.gettempdir()
temp_file_path = os.path.join(parent_dir, temp_dir, 'water_bodies.gpkg')

try:
    gdf_water_filtered.to_file(temp_file_path, driver='GPKG')
    print("Water bodies have been exported from OSM to:", temp_file_path)
except Exception as e:
    print("Export of water bodies from OSM has failed:", e)
'''

print ("-------------------------")

# 3. to extract WATER LINES through osmnx

## to fetch water lines within the bounding box
tags = {'waterway': ['river', 'stream', 'canal', 'drain', 'ditch']}
gdf_water_lines = ox.features_from_bbox(*bbox, tags=tags)

'''
# to check lists in columns of dataframes
for col in gdf_water_lines.columns:
    if any(isinstance(val, list) for val in gdf_water_lines[col]):
        print('Column: {0}, has a list in it'.format(col))
'''
'''
# to print available columns
print(gdf_water_lines.dtypes)
'''

## to drop columns that are builded as lists because they're causing troubles while exporting geopackages
columns_to_drop = []
for col in gdf_water_lines.columns:
    if any(isinstance(val, list) for val in gdf_water_lines[col]):
        columns_to_drop.append(col)

gdf_water_lines=gdf_water_lines.drop(columns=columns_to_drop)

## to filter columns in the geodataframe
filtered_columns = ['geometry','name','width','tunnel','intermittent','level','bridge','seasonal','highway']  # specify columns needed
gdf_water_lines_filtered = gdf_water_lines[filtered_columns]

## to filter only lines and multilines
gdf_water_lines_filtered = gdf_water_lines_filtered[gdf_water_lines_filtered['geometry'].geom_type.isin(['LineString', 'MultiLineString'])]

print(gdf_water_lines_filtered)

## to filter water lines by 'level' being equal to 0 or NULL
gdf_water_lines_filtered = gdf_water_lines_filtered[
    (gdf_water_lines_filtered['level'] == 0) | 
    (gdf_water_lines_filtered['level'].isnull())
]

## reproject geodataframe to EPSG 25831
gdf_water_lines_filtered = gdf_water_lines_filtered.to_crs(CRS.from_epsg(25831))

## to export geodataframe as a single geopackage
output_path = os.path.join(output_dir,"water_lines.gpkg")
try:
    gdf_water_lines_filtered.to_file(output_path, driver='GPKG')
    print("Waterways have been exported from OSM to:", output_path)
except Exception as e:
    print("Export of waterways from OSM has failed:", e)
output_path = None

'''
# OTHER OPTION TO EXPORT GEODATAFRAME AS A TEMPORARY GEOPACKAGE
temp_dir = tempfile.gettempdir()
temp_file_path = os.path.join(parent_dir, temp_dir, 'water_lines.gpkg')

try:
    gdf_water_lines_filtered.to_file(temp_file_path, driver='GPKG')
    print("Waterways have been exported from OSM to:", temp_file_path)
except Exception as e:
    print("Export of waterways from OSM has failed:", e)
'''
print ("-------------------------")

# 4. to extract RAILWAYS through osmnx
## to fetch railways within the bounding box
tags = {'railway': ['rail', 'light_rail', 'narrow_gauge']}
gdf_railways = ox.features_from_bbox(*bbox, tags=tags)

'''
# to check lists in columns of dataframes
for col in gdf_railways.columns:
    if any(isinstance(val, list) for val in gdf_railways[col]):
        print('Column: {0}, has a list in it'.format(col))
'''
'''
# print available columns
print(gdf_railways.dtypes)
'''

## to drop columns that are builded as lists because they're causing troubles while exporting geopackages
columns_to_drop = []
for col in gdf_railways.columns:
    if any(isinstance(val, list) for val in gdf_railways[col]):
        columns_to_drop.append(col)

gdf_railways=gdf_railways.drop(columns=columns_to_drop)

## to filter columns in the geodataframe
filtered_columns = ['geometry','name','frequency','bridge','maxspeed','level','gauge','importance','passenger_lines']  # specify columns needed
gdf_railways_filtered = gdf_railways[filtered_columns]

## to filter only lines and multilines
gdf_railways_filtered = gdf_railways_filtered[gdf_railways_filtered['geometry'].geom_type.isin(['LineString', 'MultiLineString'])]

## reproject geodataframe to EPSG 25831
gdf_railways_filtered = gdf_railways_filtered.to_crs(CRS.from_epsg(25831))

## convert the 'gauge' column to integers
##  if ';' is present in the 'gauge' column
if gdf_railways_filtered['gauge'].str.contains(';').any():
    # read gauge as string, drop null values, split the values by ';' and convert them to floats
    gauge_values = gdf_railways_filtered['gauge'].dropna().astype(str).str.split(';').apply(lambda x: [float(val) for val in x])
    # take the maximum value from each list of floats
    gdf_railways_filtered['gauge'] = gauge_values.apply(max)
else:
    # convert the 'gauge' column to floats directly
    gdf_railways_filtered['gauge'] = gdf_railways_filtered['gauge'].astype(float)
print(gdf_railways_filtered)

## TODO - to figure out whether railways should be buffered by different width or not - currently not

## to export geodataframe as a single geopackage
output_path = os.path.join(output_dir,"railways.gpkg")
try:
    gdf_railways_filtered.to_file(output_path, driver='GPKG')
    print("Railways have been exported from OSM to:", output_path)
except Exception as e:
    print("Export of waterways from OSM has failed:", e)
output_path = None

'''
# OTHER OPTION TO EXPORT GEODATAFRAME AS A TEMPORARY GEOPACKAGE
# to export geodataframe as a temporary geopackage
temp_dir = tempfile.gettempdir()
temp_file_path = os.path.join(parent_dir, temp_dir, 'vector_railways.gpkg')

try:
    gdf_railways_filtered.to_file(temp_file_path, driver='GPKG')
    print("Railways have been exported from OSM to:", temp_file_path)
except Exception as e:
    print("Export of railways from OSM has failed:", e)
'''

print ("-------------------------")

# 5. to merge all geopackages into one (single geopackages/geodataframes are better to be used on further preproprocessing steps)

def merge_geodataframes(gdfs, names):
    ## to add a new column "layer_type" to each geodataframe based on its variable name
    for name, gdf in zip(names, gdfs):
        gdf['layer_type'] = name

    ## to concatenate geodataframes
    merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)

    return merged_gdf

## to list geodataframes and their names to merge
input_gdfs = [gdf_roads_filtered, gdf_railways_filtered, gdf_water_lines_filtered, gdf_water_filtered]
## automatically generate corresponding names for the GeoDataFrames
gdf_names = ["gdf_roads_filtered", "gdf_railways_filtered", "gdf_water_lines_filtered", "gdf_water_filtered"]
## print the message and the resulting gdf_names
print(f'Layers to be merged into a single GeoPackage file are: {", ".join(gdf_names)}')

## to call the merge function
merged_gdf = merge_geodataframes(input_gdfs, gdf_names)

## reproject geodataframe to EPSG 25831
merged_gdf = merged_gdf.to_crs(CRS.from_epsg(25831))

## to save the merged GeoDataFrame to a Geopackage
output_geo_package = os.path.join(parent_dir, output_dir, 'osm_merged.gpkg')
merged_gdf.to_file(output_geo_package, driver="GPKG")

## to record the end time
end_time = time.time()
## to calculate the duration
duration = end_time - start_time
## to print executiion time
print("Execution time: {} seconds".format(duration))