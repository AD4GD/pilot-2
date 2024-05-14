from osgeo import gdal, ogr, gdal_array
import pandas as pd
import numpy as np
import os
import csv

# specify path to input tiff and txt files
path = r'c:\Users\kriukovv\Documents\Graphab\outputs'
tif_path = os.path.join(path, 'patches_2022.tif')
txt_path = os.path.join(path, 'delta-IIC_thresh_2355.0_cost_2355_2022.txt')
output_tif_path = os.path.join(path, 'IIC_2022.tif')

# open tiff file
tif_dataset = gdal.Open(tif_path, gdal.GA_ReadOnly)
if tif_dataset is None:
    print("Error: Could not open the TIFF file.")
    exit()

# read the values from txt file
csv_values = {}
with open(txt_path, 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='\t')
    next(csv_reader)  # skip the header row
    next(csv_reader)  # skip the second line because it shows the initial value of delta index
    for row in csv_reader:
        id_value = int(row[0])
        csv_values[id_value] = float(row[1]) 

# get the raster band from the TIFF file
tif_band = tif_dataset.GetRasterBand(1)
tif_data = tif_band.ReadAsArray()

# create a new band with values from the txt file
new_band_data = np.array([[csv_values.get(int(value), 0) for value in row] for row in tif_data])

# create a new TIFF file with the original band and the new band
driver = gdal.GetDriverByName('GTiff')
output_tif_dataset = driver.Create(output_tif_path, tif_dataset.RasterXSize, tif_dataset.RasterYSize, 2, gdal.GDT_Float32)
output_tif_dataset.GetRasterBand(1).WriteArray(tif_data)
output_tif_dataset.GetRasterBand(2).WriteArray(new_band_data.astype(np.float64))  # Ensure float64 data type

# set georeferencing information
output_tif_dataset.SetGeoTransform(tif_dataset.GetGeoTransform())
output_tif_dataset.SetProjection(tif_dataset.GetProjection())

# close the datasets
tif_dataset = None
output_tif_dataset = None

print("New TIFF file created successfully.")

