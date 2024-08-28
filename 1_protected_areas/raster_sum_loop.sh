# to run it in Anaconda prompt on local machine (Windows):
# "C:\Users\kriukovv\AppData\Local\Programs\Git\bin\sh.exe" raster_sum_loop.sh (use your local path for bash.exe)
# if it doesn't work, try "C:\Users\kriukovv\AppData\Local\Programs\Git\bin\bash.exe" raster_sum_loop.sh
# to set directory with lulc files
lulc_path="lulc"
# to set directory with temporary lulc files with reassigned null values
lulc_0_path="lulc_0"
#create this directory if doesn't exist
mkdir -p "$lulc_0_path"

lulc_upd_compr_path="lulc_pa"

# to list all lulc files in the directory
lulc_files=("$lulc_path"/*.tif)

# to set directory with pa files
pa_path="pas_timeseries"
pa_files=("$pa_path"/*.tif)

# ASSIGN no data values through the loop over LULC folder
for lulc_file in "$lulc_path"/*.tif; do    
    lulc_file_0="$lulc_0_path/$(basename "$lulc_file" .tif)_0.tif"
    # Print input and output filenames
    echo "Input filename: $lulc_file"
    echo "Output filename: $lulc_file_0"
    gdal_translate -a_nodata none -co COMPRESS=LZW -co TILED=YES "$lulc_file" "$lulc_file_0"
done

# loop through each LULC file
for lulc_file_0 in "$lulc_0_path"/*.tif; do
    # extract last four characters from LULC file name (year)
    lulc_year=$(basename "$lulc_file_0" | cut -c 6-9)
    echo "LULC year: $lulc_year"

    # loop through each PA file
    for pa_file in "$pa_path"/*.tif; do
        # extract last four characters from PA file name (year)
        pa_year=$(basename "$pa_file" | cut -c 5-8)
        echo "PA year: $pa_year"

        # Check if LULC and PA files have matching years
        if [ "$lulc_year" = "$pa_year" ]; then
            # Process files
            lulc_upd_file="${lulc_file_0##*/}"
            lulc_upd_file="${lulc_upd_file%.tif}_upd"
            lulc_upd_file="$lulc_upd_path/${lulc_upd_file}.tif"
            gdal_calc.py --overwrite --calc  "A+B" --format GTiff --type Int32 -A "$lulc_file_0" --A_band 1 -B "$pa_file" --outfile "$lulc_upd_file" --NoDataValue=-2147483647 
            echo "Updated LULC is uploaded to: $lulc_upd_file"
    
            # set paths for compressed updated LULC file
            lulc_upd_compr_file="${lulc_upd_file##*/}"
            lulc_upd_compr_file="${lulc_upd_compr_file%_0_upd.tif}"
            echo "After removing _0: $lulc_upd_compr_file"
            lulc_upd_compr_file="$lulc_upd_compr_path/${lulc_upd_compr_file##*/}_pa.tif"
            echo "Compressed LULC is uploaded to: $lulc_upd_compr_file"

            # compress and set no data values
            gdal_translate -a_nodata -2147483647 -co COMPRESS=LZW -co TILED=YES "$lulc_upd_file" "$lulc_upd_compr_file"

            # remove non-compressed updated LULC file
            # rm "$lulc_upd_file"
          
            # break the loop once a matching PA file is found
            break
        fi
    done
done

# remove the intermediate lulc_0 directory
rm -r "$lulc_0_path"