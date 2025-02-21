import subprocess
import os
from rich import print

class LulcPaRasterSum():

    def __init__(self, 
        input_path:str,
        output_path:str,
        lulc_path:str, 
        lulc_with_null_path:str,
        pa_path:str, 
        lulc_upd_compr_path:str
    ):
        """
        Initialize the combine_rasters class

        Args:
            input_path (str): The path to the input directory.
            output_path (str): The path to the output directory.
            lulc_path (str): The path to the LULC raster data.
            lulc_with_zeros_path (str): The path to the LULC raster data with zeros.
            lulc_upd_compr_path (str): The path to the combined LULC and PA raster data.
            pa_path (str): The path to the PA raster data.

        """
        
        self.lulc_path = os.path.join(input_path, lulc_path)
        self.lulc_with_null_path = self.make_directory_if_not_exists(os.path.join(input_path,"protected_areas", lulc_with_null_path))

        self.lulc_upd_compr_path = self.make_directory_if_not_exists(os.path.join(output_path, "protected_areas", lulc_upd_compr_path))
        self.pa_path = self.make_directory_if_not_exists(os.path.join(output_path,"protected_areas", pa_path))

    def make_directory_if_not_exists(self, path:str):
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
    
    def assign_no_data_values(self):
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
            print(f"[green] No data values assigned complete for file: {file} [green]")

    def combine_pa_lulc(self, keep_temp_files:bool=False):
        """
        Combine the LULC and PA raster data

        Args:
            keep_temp_files (bool): Keep the temporary files

        Returns:
            None
        """
        null_assgined_lulc_files = os.listdir(self.lulc_with_null_path)
        for lulc_file_with_null in null_assgined_lulc_files:
            year = lulc_file_with_null.split("_")[-2].split(".")[0]
            # check if matching year pa file exists
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
                print(f"[green] Raster sum complete for year: {year} [green]")
            else:
                raise FileNotFoundError(f"PA file for year {year} does not exist")
            
        # remove the temp files directory
        if keep_temp_files == False:
            subprocess.run(f"rm -rf {self.lulc_with_null_path}", shell=True)


# Example usage
if __name__ == "__main__":
    lprs = LulcPaRasterSum("data/input","data/output",'lulc_albera_ext_concat_{year}.tif', "lulc_temp", "pa_rasters", "lulc_pa")
    lprs.assign_no_data_values()
    lprs.combine_pa_lulc()