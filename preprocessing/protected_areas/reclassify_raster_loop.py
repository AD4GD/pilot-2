from osgeo import gdal
import numpy as np
import csv
import os
import subprocess
gdal.UseExceptions()

# specify function to reclassify LULC by mapping dictionary and obtaining impedance raster data
def reclassify_raster(input_raster, output_raster, reclass_table):
    # read reclassification table
    reclass_dict = {}
    with open(reclass_table, 'r', encoding='utf-8-sig') as csvfile:  # handle UTF-8 with BOM
        reader = csv.DictReader(csvfile)
        # initialize a flag to indicate if any row contains decimal values
        has_decimal_values = False
        
        next(reader, None) # skip headers for looping
        for row in reader:
            try:
                impedance_rounded_str = row['impedance']
                if '.' in impedance_rounded_str:  # check if impedance contains decimal values
                    has_decimal_values = True
                    break  # exit the loop if any row contains decimal values
            except ValueError:
                print("Invalid data format in reclassification table.")
            continue

        # reset file pointer to read from the beginning
        csvfile.seek(0)

        # read classification table again and define mapping for decimal and integer values
        next(reader, None) # skip headers for looping
        if has_decimal_values:
            data_type = 'Float32'
            for row in reader:
                try:
                    lulc = int(row['lulc'])
                    impedance = float(row['impedance'])
                    reclass_dict[lulc] = impedance
                except ValueError:
                    print("Invalid data format in reclassification table_2. Problematic row:", row)
                    continue
        else:
            data_type = 'Int32'
            for row in reader:
                try:
                    lulc = int(row['lulc'])
                    impedance = int(row['impedance'])
                    reclass_dict[lulc] = impedance
                except ValueError:
                    print("Invalid data format in reclassification table_3.")
                    continue
  
        if has_decimal_values:
            print("LULC impedance is characterized by decimal values.")
            # update reclassification dictionary to align nodata values with one positive value (Graphab requires positive value as no_data value)
            # assuming nodata value is 9999 (or 9999.00 if estimating decimal values)
            reclass_dict.update({-2147483647: 9999.00, -32768: 9999.00, 0: 9999.00}) # minimum value for int16, int32 and 0 are assigned with 9999.00 (nodata)
        else:
            print("LULC impedance is characterized by integer values only.")
            # update dictionary again
            reclass_dict.update({-2147483647: 9999, -32768: 9999, 0: 9999}) # minimum value for int16, int32 and 0 are assigned with 9999.00 (nodata)
    
    print ("Mapping dictionary used to classify impedance is:", reclass_dict)

    # open input raster
    dataset = gdal.Open(input_raster)
    if dataset is None:
        print("Could not open input raster.")
        return

    # get raster info
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize

    # initialize output raster
    driver = gdal.GetDriverByName("GTiff")
    if has_decimal_values:
        output_dataset = driver.Create(output_raster, cols, rows, 1, gdal.GDT_Float32)
    else:
        output_dataset = driver.Create(output_raster, cols, rows, 1, gdal.GDT_Int32)
    #TODO - to add condition on Int32 if integer values are revealed
    output_dataset.SetProjection(dataset.GetProjection())
    output_dataset.SetGeoTransform(dataset.GetGeoTransform())

    # reclassify each pixel value
    input_band = dataset.GetRasterBand(1)
    output_band = output_dataset.GetRasterBand(1)
    # read the entire raster as a NumPy array
    input_data = input_band.ReadAsArray()

    '''REDUNDNANT BLOCK ON ASSIGNING NULL VALUES
    # identify nodata values in the input raster
    # nodata_mask = (input_data == None) 
    '''

    # apply reclassification using dictionary mapping
    output_data = np.vectorize(reclass_dict.get)(input_data)

    '''REDUNDNANT BLOCK ON ASSIGNING NULL VALUES
    # Reassign nodata values to their original values in the output raster
    # output_data[nodata_mask] = None
    # Write the reclassified data to the output raster
    '''

    output_band.WriteArray(output_data)

    '''FOR CHECKS
    print (f"input_data_shape is': {input_data.shape}")
    print (f"output_data_shape is': {output_data.shape}")
    '''

    # close datasets
    dataset = None
    output_dataset = None

    return (data_type)

if __name__ == "__main__":
    input_folder = r'lulc_pa'
    output_folder = r'impedance_pa'
    reclass_table = "reclassification.csv"
    
    # list all TIFF files in input folder
    tiff_files = [f for f in os.listdir(input_folder) if f.endswith('.tif')]
    # create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    # loop through each input file
    for tiff_file in tiff_files:
        input_raster_path = os.path.join(input_folder, tiff_file)
        print (tiff_file)
        # modify the output raster filename to ensure it's different from the input raster filename
        output_filename = "impedance_" + tiff_file
        output_raster_path = os.path.join(output_folder, output_filename)

        # call function and capture data_type for compression - Float32 or Int32
        data_type = reclassify_raster(input_raster_path, output_raster_path, reclass_table)    
        print ("Data type used to reclassify LULC as impedance is",data_type) 
        
        # compression using 9999 as nodata
        compressed_raster_path = os.path.splitext(output_raster_path)[0] + '_compr.tif'
        subprocess.run(['gdal_translate', output_raster_path, compressed_raster_path,'-a_nodata', '9999', '-ot', data_type, '-co', 'COMPRESS=LZW'])

        # as soon as gdal_translate doesn't support rewriting, we should delete non-compressed GeoTIFFs...
        os.remove(output_raster_path)
        # ...and rename compressed file in the same way as the original GeoTIFF
        os.rename(compressed_raster_path, output_raster_path)

        print("Reclassification complete for:", input_raster_path + "\n------------------------------------")
