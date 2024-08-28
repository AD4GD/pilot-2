import os
import numpy as np
from osgeo import gdal

# Directory containing input TIFF files
input_dir = r'C:\Users\kriukovv\Documents\pilot_2\preprocessing\data\input\lulc\lulc_extended'
output_file = r'C:\Users\kriukovv\Documents\pilot_2\preprocessing\data\input\lulc\lulc_extended\lulc_2022_dist.tif'

# Get a list of all TIFF files in the input directory
tiff_files = [f for f in os.listdir(input_dir) if f.endswith('.tif')]

# Open the first file with GDAL to get the GeoTransform, Projection, and dimensions
src_ds = gdal.Open(os.path.join(input_dir, tiff_files[0]))
geo_transform = src_ds.GetGeoTransform()
projection = src_ds.GetProjection()
x_size = src_ds.RasterXSize
y_size = src_ds.RasterYSize

# Create a new dataset with GDAL to hold the output
driver = gdal.GetDriverByName('GTiff')
output_ds = driver.Create(output_file, x_size, y_size, len(tiff_files) * 2, gdal.GDT_Float32)
output_ds.SetGeoTransform(geo_transform)
output_ds.SetProjection(projection)

# Process each input file
for i, tiff_file in enumerate(tiff_files):
    input_path = os.path.join(input_dir, tiff_file)
    
    # Open the input file
    src_ds = gdal.Open(input_path)
    band1 = src_ds.GetRasterBand(1).ReadAsArray()
    
    # Step 1: Create a mask in-memory where the values between 5 and 7 are set to 1 and others to 0
    mask = ((band1 >= 5) & (band1 <= 7)).astype(np.uint8)
    
    # Create an in-memory GDAL dataset for the mask
    mem_driver = gdal.GetDriverByName('MEM')
    mask_ds = mem_driver.Create('', x_size, y_size, 1, gdal.GDT_Byte)
    mask_ds.GetRasterBand(1).WriteArray(mask)
    mask_ds.SetGeoTransform(geo_transform)
    mask_ds.SetProjection(projection)
    
    # Create an in-memory GDAL dataset for the distance output
    distance_ds = mem_driver.Create('', x_size, y_size, 1, gdal.GDT_Float32)
    distance_ds.SetGeoTransform(geo_transform)
    distance_ds.SetProjection(projection)
    
    # Use GDAL to compute the proximity
    gdal.ComputeProximity(mask_ds.GetRasterBand(1), distance_ds.GetRasterBand(1), ["DISTUNITS=GEO"])
    
    # Read the distance data
    distance_band = distance_ds.GetRasterBand(1).ReadAsArray()
    
    # Write the original band and the distance band to the output file
    output_ds.GetRasterBand((i * 2) + 1).WriteArray(band1.astype(np.float32))
    output_ds.GetRasterBand((i * 2) + 2).WriteArray(distance_band)

# Close the datasets
output_ds = None
src_ds = None

print("Processing completed successfully.")