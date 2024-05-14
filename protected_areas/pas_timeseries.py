import geopandas as gpd
import os
import subprocess
import rasterio

# load geopackage with protected areas
gdf = gpd.read_file("pas_upd.gpkg")
# to check column names use:
# print(gdf.columns)

# define input folder
input_folder = r'lulc'
# assign output folder
output_dir = ('pas_timeseries')
# create output folder if it doesn't exist - only needed for exporting as gpkgs
os.makedirs(output_dir, exist_ok=True)

# defining year stamp
## list all TIFF files in input folder
tiff_files = [f for f in os.listdir(input_folder) if f.endswith('.tif')]
## extract year stamps from filenames (removes the first part before _ and the part after .)
year_stamps = [int(f.split('_')[1].split('.')[0]) for f in tiff_files]
print("Considered timestamps of LULC data are:",year_stamps)

# extract extent of LULC data
## define function
def extract_ext_res(file_path):
    with rasterio.open(file_path) as src:
        extent = src.bounds
        res = src.transform[0]  # assuming the res is the same for longitude and latitude
    return extent, res

## execute function
if tiff_files:
    file_path = os.path.join(input_folder, tiff_files[0])  # choose the first TIFF file (it shouldn't matter which LULC file to extract extent because they must have the same extent)
    extent, res = extract_ext_res(file_path)
    min_x = extent.left
    max_x = extent.right
    min_y = extent.bottom
    max_y = extent.top
    
    print("Extent of LULC files:")
    print("Minimum X Coordinate:", min_x)
    print("Maximum X Coordinate:", max_x)
    print("Minimum Y Coordinate:", min_y)
    print("Maximum Y Coordinate:", max_y)
    print("Spatial resolution (pixel size):", res)
else:
    print("No LULC files found in the input folder.")

# TODO - redefine null values from LULC data as 0 or something else?

# create an empty dictionary to store subsets
subsets_dict = {}
# loop through each year_stamp and create subsets
for year_stamp in year_stamps:
    # filter Geodataframe based on the year_stamp
    subset = gdf[gdf['STATUS_YR'] <= year_stamp]
    
    # store subset in the dictionary with year_stamp as key
    subsets_dict[year_stamp] = subset

    # print key-value pairs of subsets 
    print(f"Protected areas are filtered according to year stamps of LULC and PAs' establishment year: {year_stamp}")

    # ADDITIONAL BLOCK IF EXPORT TO GEOPACKAGE IS NEEDED (currently needed as rasterizing vector data is not possible with geodataframes)
    ## save filtered subset to a new GeoPackage
    subset.to_file(os.path.join(output_dir,f"pas_{year_stamp}.gpkg"), driver='GPKG')
    print(f"Filtered protected areas are written to:",os.path.join(output_dir,f"pas_{year_stamp}.gpkg"))

print ("---------------------------")

# define rasterize command as a list of arguments
## list all subsets of protected areas by the year of establishment
pas_yearstamps = [f for f in os.listdir(output_dir) if f.endswith('.gpkg')]
pas_yearstamp_rasters = [f.replace('.gpkg', '.tif') for f in pas_yearstamps]


# loop through each input file
for pas_yearstamp, pas_yearstamp_raster in zip(pas_yearstamps, pas_yearstamp_rasters):
    pas_yearstamp_path = os.path.join(output_dir, pas_yearstamp)
    pas_yearstamp_raster_path = os.path.join(output_dir, pas_yearstamp_raster)
    # TODO - to make paths more clear and straightforward

    # rasterize
    pas_rasterize = [
        "gdal_rasterize",
        ##"-l", "pas__merged", if you need to specify the layer
        "-burn", "100", ## assign code starting from "100" to all LULC types
        "-init", "0",
        "-tr", str(res), str(res), #spatial res from LULC data
        "-a_nodata", "-2147483647", # !DO NOT ASSIGN 0 values with non-data values as it will mask them out in raster calculator
        "-te", str(min_x), str(min_y), str(max_x), str(max_y), # minimum x, minimum y, maximum x, maximum y coordinates of LULC raster
        "-ot", "Int32",
        "-of", "GTiff",
        "-co", "COMPRESS=LZW",
        pas_yearstamp_path,
        pas_yearstamp_raster_path
        ]

    # execute rasterize command
    try:
        subprocess.run(pas_rasterize, check=True)
        print("Rasterizing of protected areas has been successfully completed for", pas_yearstamp)
    except subprocess.CalledProcessError as e:
        print(f"Error rasterizing protected areas: {e}")

'''
# REDUNDANT BLOCK FOR COMPRESSION (immplemented in gdal_rasterize directly)
for pas_yearstamp_raster in pas_yearstamp_rasters:
    output_path = os.path.join(output_dir, pas_yearstamp_raster) #construct path for inputs
    compressed_raster_path = os.path.splitext(output_path)[0] + '_compr.tif' #construct path for compressed files
    subprocess.run(['gdal_translate', output_path, compressed_raster_path,'-a_nodata', '9999', '-ot', 'Int32', '-co', 'COMPRESS=LZW'], check=True)
    print (pas_yearstamp_raster,"has been successfully compressed.")
    
    # as soon as gdal_translate doesn't support rewriting, we should delete non-compressed GeoTIFFs...
    os.remove(output_path)
    # ...and rename COG in the same way as the original GeoTIFF
    os.rename(compressed_raster_path, output_path)
'''






