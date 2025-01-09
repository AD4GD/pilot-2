import subprocess
import os

class LulcPaRasterSum():

    def __init__(self, 
            input_dir:str="data/input/protected_areas",
            output_dir:str="data/output/protected_areas",
            lulc_path:str="lulc", 
            lulc_with_null_path:str="lulc_temp",
            pa_path="pas_timeseries", 
            lulc_upd_compr_path:str="lulc_pa" 
        )-> None:
        """
        Initialize the combine_rasters class

        Args:
            lulc_path (str): The path to the LULC raster data.
            lulc_with_zeros_path (str): The path to the LULC raster data with zeros.
            lulc_upd_compr_path (str): The path to the combined LULC and PA raster data.
            pa_path (str): The path to the PA raster data.

        """
        self.lulc_path = self.make_directory_if_not_exists(os.path.join(input_dir, lulc_path))
        self.lulc_with_null_path = self.make_directory_if_not_exists(os.path.join(input_dir, lulc_with_null_path))
        self.lulc_upd_compr_path = self.make_directory_if_not_exists(os.path.join(output_dir, lulc_upd_compr_path))
        self.pa_path = self.make_directory_if_not_exists(os.path.join(input_dir, pa_path))

    def make_directory_if_not_exists(self, path:str) -> None:
        """
        Make a directory if it does not exist

        Args:
            path (str): The path to the directory

        Returns:
            str: The path to the directory
        """
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    def assign_no_data_values(self) -> None:
        """
        Reassign no data values to the LULC raster data as temporary files
        """
        # loop through the files
        for file in os.listdir(self.lulc_path):
            # get the file path
            file_path = os.path.join(self.lulc_path, file)
            output_path = os.path.join(self.lulc_with_null_path, file.replace(".tif", "_temp.tif"))
            gdal_command = f"""
            gdal_translate -a_nodata none -co COMPRESS=LZW -co TILED=YES {file_path} {output_path}
            """
            subprocess.run(gdal_command, shell=True)
            print(f"Processing complete for file: {file}")

    def combine_pa_lulc(self, keep_temp_files:bool=False) -> None:
        """
        Combine the LULC and PA raster data

        Args:
            keep_temp_files (bool): Keep the temporary files

        Returns:
            None
        """
        null_assgined_lulc_files = os.listdir(self.lulc_with_null_path)
        for lulc_file_with_null in null_assgined_lulc_files:
            year = lulc_file_with_null.split("_")[1].split(".")[0]
            # check if mathcing year pa file exists
            pa_file = os.path.join(self.pa_path, f"pas_{year}.tif")
            if os.path.exists(pa_file):
                lulc_pa_sum_file = os.path.join(self.lulc_upd_compr_path, f"lulc_{year}_pa.tif")
                gdal_command = " ".join([
                    "gdal_calc.py --overwrite --calc 'A+B' --format GTiff",
                    "--type Int32 --NoDataValue=-2147483647",
                    f"-A {os.path.join(self.lulc_with_null_path, lulc_file_with_null)}",
                    f"--A_band 1 -B {pa_file}",
                    f"--outfile {lulc_pa_sum_file}",
                    "--co COMPRESS=LZW --co TILED=YES"
                ])
                subprocess.run(gdal_command, shell=True)
                print(f"Raster sum complete for year: {year}")
            else:
                raise FileNotFoundError(f"PA file for year {year} does not exist")
            
        # remove the temp files directory
        if keep_temp_files == False:
            subprocess.run(f"rm -rf {self.lulc_with_null_path}", shell=True)


# Example usage
if __name__ == "__main__":
    lprs = LulcPaRasterSum()
    lprs.assign_no_data_values()
    lprs.combine_pa_lulc()