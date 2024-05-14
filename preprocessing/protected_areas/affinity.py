from osgeo import gdal
import numpy as np
import os
import subprocess

impedance_dir = 'impedance_pa'
affinity_dir = 'affinity'
# create the affinity directory if it doesn't exist
if not os.path.exists(affinity_dir):
    os.makedirs(affinity_dir)

impedance_files = os.listdir(impedance_dir)
print (impedance_files)

# loop through each TIFF file in impedance_dir
for impedance_file in impedance_files:
    if impedance_file.endswith('.tif'):
        # construct full paths for impedance and affinity files
        impedance_path = os.path.join(impedance_dir, impedance_file)
        affinity_path = os.path.join(affinity_dir, impedance_file.replace('impedance', 'affinity'))

        # open impedance file
        ds = gdal.Open(impedance_path)

        if ds is None:
            print(f"Failed to open impedance file: {impedance_file}")
            continue

        # get raster band
        band = ds.GetRasterBand(1)
        # read raster band as a NumPy array
        data = band.ReadAsArray()
        # reverse values with condition (if it is 9999 leave it, otherwise make it reversed)
        reversed_data = np.where(data == 9999, data, 1 / data)

        # write reversed data to affinity file
        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(affinity_path, ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_Float32)
        out_ds.GetRasterBand(1).WriteArray(reversed_data)

        # copy georeferencing info
        out_ds.SetGeoTransform(ds.GetGeoTransform())
        out_ds.SetProjection(ds.GetProjection())

        # close files
        ds = None
        out_ds = None

        print(f"Affinity computed for: {impedance_file}")

        # compression
        compressed_raster_path = os.path.splitext(affinity_path)[0] + '_compr.tif'
        subprocess.run(['gdal_translate', affinity_path, compressed_raster_path,'-a_nodata', '9999', '-ot', 'Float32', '-co', 'COMPRESS=LZW'])
    
        # as soon as gdal_translate doesn't support rewriting, we should delete non-compressed GeoTIFFs...
        os.remove(affinity_path)
        # ...and rename COG in the same way as the original GeoTIFF
        os.rename(compressed_raster_path, affinity_path)
        print(f"Affinity file is successfully compressed.", end="\n------------------------------------------\n")

print("All LULC affinities have been successfully computed.")
