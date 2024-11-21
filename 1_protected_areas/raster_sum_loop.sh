#!/bin/bash

# Set directory with LULC files
lulc_path="lulc"
# Set directory with temporary LULC files with reassigned null values
lulc_0_path="lulc_0"
# Output directory - save to parent directory with input LULC datasets
lulc_upd_compr_path="$(dirname "$(pwd)")/data/input/lulc"
# previous version - in subnested directory: lulc_upd_compr_path="lulc_pa"

# Create these directories if they don't exist
mkdir -p "$lulc_0_path" 
mkdir -p "$lulc_upd_compr_path"

# List all LULC files in the directory
lulc_files=("$lulc_path"/*.tif)

# Set directory with PA files
pa_path="pas_timeseries"
pa_files=("$pa_path"/*.tif)

# Assign no-data values through the loop over LULC folder
for lulc_file in "$lulc_path"/*.tif; do    
    lulc_file_0="$lulc_0_path/$(basename "$lulc_file" .tif)_0.tif"
    # Print input and output filenames
    echo "Input filename: $lulc_file"
    echo "Output filename: $lulc_file_0"
    gdal_translate -a_nodata none -co COMPRESS=LZW -co TILED=YES "$lulc_file" "$lulc_file_0"
done

# Loop through each LULC file
for lulc_file_0 in "$lulc_0_path"/*.tif; do
    filename=$(basename "$lulc_file_0")
    filename_without_extension="${filename%.*}"
    last_six="${filename_without_extension: -6}"
    lulc_year="${last_six%'_0'}"  # Remove '_0' suffix

    # Validate extracted year
    if [[ "$lulc_year" =~ ^[0-9]{4}$ ]]; then
        echo "LULC year: $lulc_year"
    else
        echo "No valid year found in: $lulc_file_0 ($lulc_year)"
        continue
    fi

    # Loop through each PA file
    for pa_file in "$pa_path"/*.tif; do
        # Extract last four characters from PA file name (year)
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
    
            # Set paths for compressed updated LULC file
            lulc_upd_compr_file="${lulc_upd_file##*/}"
            lulc_upd_compr_file="${lulc_upd_compr_file%_0_upd.tif}"
            echo "After removing _0: $lulc_upd_compr_file"
            lulc_upd_compr_file="$lulc_upd_compr_path/${lulc_upd_compr_file##*/}_pa.tif"
            echo "Compressed LULC is uploaded to: $lulc_upd_compr_file"

            # Compress and set no data values
            gdal_translate -a_nodata -2147483647 -co COMPRESS=LZW -co TILED=YES "$lulc_upd_file" "$lulc_upd_compr_file"

            # Remove non-compressed updated LULC file
            rm "$lulc_upd_file"
          
            # Break the loop once a matching PA file is found
            break
        fi
    done
done

# Remove the intermediate lulc_0 directory
rm -r "$lulc_0_path"