import geopandas as gpd
import rasterio
import os
import subprocess
import numpy as np
from raster_metadata import RasterMetadata

class PARasterizer:
    """
    This class is responsible for filtering protected areas based on the year of establishment and rasterizing them.
    """

    def __init__(self, gpkg_filepath:str, input_dir:str,output_dir:str) -> None:
        """
        Initialize the PARasterizer class.

        Args:
            gpkg_filepath (str): The path to the GeoPackage file containing all the protected areas.
            input_dir (str): The path to the directory containing the LULC files.
            output_dir (str): The path to the output directory.
        """
        self.gdf = gpd.read_file(gpkg_filepath)
        self.input_folder = input_dir
        self.output_dir = output_dir
        # create output directory if it does not exist
        os.makedirs(output_dir, exist_ok=True)

        # Extract raster metadata
        tiff_files = [f for f in os.listdir(input_dir) if f.endswith('.tif')]
        if tiff_files:
            # choose the first TIFF file (it shouldn't matter which LULC file to extract extent because they must have the same extent)
            file_path = os.path.join(input_dir, tiff_files[0])  
            self.lulc_metadata = RasterMetadata.from_raster(raster_path=file_path)
            print(self.lulc_metadata)
        else:
            raise ValueError("No LULC files found in the input folder.")

        # extract the year from the filename (last block before the file extension with '-' separator
        self.year_stamps = [f.split('_')[-1].split('.')[0] for f in tiff_files]
        print("Considered timestamps of LULC data are:","".join(str(self.year_stamps)))
            
    def reproject_pa_data(self, target_crs:str, filter_by_year:bool=True) -> None:
        """
        Reprojects the protected areas to the same CRS as the LULC raster dataset, and filters them based on the year of establishment into separate GeoPackage files.

        Args:
            target_crs (str): The target CRS to reproject the protected areas.
            filter_by_year (bool): Filter protected areas by the year of establishment (default is True).

        Returns:
            None: prints the path/paths to the saved GeoPackage file.
        """

        if filter_by_year:
            # create an empty dictionary to store subsets
            subsets_dict = {}
            # loop through each year_stamp and create subsets
            for year_stamp in self.year_stamps:
                # filter Geodataframe based on the year_stamp
                subset = self.gdf[self.gdf['year'] <= np.datetime64(str(year_stamp))]

                # store subset in the dictionary with year_stamp as key
                subsets_dict[year_stamp] = subset

                # print key-value pairs of subsets 
                print(f"Protected areas are filtered according to year stamps of LULC and PAs' establishment year: {year_stamp}")

                # reproject geodataframe to the CRS of input rastser dataset
                subset = subset.to_crs(target_crs)

                # ADDITIONAL BLOCK IF EXPORT TO GEOPACKAGE IS NEEDED (currently needed as rasterizing vector data is not possible with geodataframes)
                ## save filtered subset to a new GeoPackage
                subset.to_file(os.path.join(self.output_dir,f"pas_{year_stamp}.gpkg"), driver='GPKG')
                print(f"Filtered protected areas are written to:",os.path.join(self.output_dir,f"pas_{year_stamp}.gpkg"))

            print ("---------------------------")
        else:
            # reproject geodataframe to the CRS of input raster dataset
            self.gdf = self.gdf.to_crs(target_crs)
            # save the reprojected geodataframe to a new GeoPackage
            self.gdf.to_file(os.path.join(self.output_dir, "pa.gpkg"), driver='GPKG')
            print(f"Protected areas are written to:",os.path.join(self.output_dir, "pa.gpkg"))
        
    def rasterize_pa(self, lulc_metadata:RasterMetadata, vector_filepath:str, output_filepath:str):
        """
        Rasterizes the vector data (protected areas) to the same extent and resolution as the LULC raster dataset.

        Args:
            lulc_metadata (RasterMetadata): The metadata of the LULC raster dataset.
            vector_filepath (str): The path to the vector file (GeoPackage).
            output_filepath (str): The path to the output raster file.

        Returns:
            None: prints the path to the saved raster file.
        """

        epsg = "EPSG:" + str(lulc_metadata.crs_info['epsg'])
        gdal_cmd = [
            "gdal_rasterize",
            ##"-l", "pas__merged", if you need to specify the layer
            "-burn", "100", ## assign code starting from "100" to all LULC types
            "-init", "0",
            "-tr", str(abs(lulc_metadata.xres)), str(abs(lulc_metadata.yres)), #spatial res from LULC data (use absolute values to avoid negative res)
            "-a_srs", epsg, #output crs from LULC data
            "-a_nodata", "-2147483647", # !DO NOT ASSIGN 0 values with non-data values as it will mask them out in raster calculator
            "-te", str(lulc_metadata.x_min), str(lulc_metadata.y_min), str(lulc_metadata.x_max), str(lulc_metadata.y_max), # minimum x, minimum y, maximum x, maximum y coordinates of LULC raster
            "-ot", "Int32",
            "-of", "GTiff",
            "-co", "COMPRESS=LZW",
            vector_filepath,
            output_filepath
            ]
        
        print(gdal_cmd)
        # execute rasterize command
        try:
            subprocess.run(gdal_cmd, check=True)
            print("Rasterizing of protected areas has been successfully completed for", vector_filepath)
        except subprocess.CalledProcessError as e:
            print(f"Error rasterizing protected areas: {e}")
        
        

    def rasterize_pa_geopackage(self, lulc_metadata:RasterMetadata, pa_to_yearly_rasters:bool=True , keep_intermediate_gpkg:bool=False) -> None:
        """
        Rasterizes the protected areas to the same extent and resolution as the LULC raster dataset.

        Args:
            lulc_metadata (RasterMetadata): The metadata of the LULC raster dataset.
            pa_to_yearly_rasters (bool): Rasterize all subsets of protected areas by the year of establishment (default is True).
            keep_intermediate_gpkg (bool): Keep intermediate GeoPackage files (default is False).
        
        """
        # if rasterize_all_years is True, rasterize all subsets of protected areas by the year of establishment
        if pa_to_yearly_rasters:
            # list all subsets of protected areas by the year of establishment (input files)
            pa_years = [f for f in os.listdir(self.output_dir) if f.endswith('.gpkg')]
            # list all rasterized subsets of protected areas by the year of establishment (output files)
            pa_yearly_rasters = [f.replace('.gpkg', '.tif') for f in pa_years]

            # loop through each pa subset and rasterize it
            for reprojected_pa, output_path in zip(pa_years, pa_yearly_rasters):
                pas_yearstamp_path = os.path.join(self.output_dir, reprojected_pa)
                pas_yearstamp_raster_path = os.path.join(self.output_dir, output_path)
                self.rasterize_pa(lulc_metadata, pas_yearstamp_path, pas_yearstamp_raster_path)

        # if rasterize_all_years is False, rasterize the one reprojected pa file.
        else:
            # rasterize the one reprojected pa file.
            reprojected_pa = os.path.join(self.output_dir, "pa.gpkg") # (input file)
            reprojected_pa_raster = os.path.join(self.output_dir, "pa.tif") # (output file)
            self.rasterize_pa(lulc_metadata, reprojected_pa, reprojected_pa_raster)
            
        if not keep_intermediate_gpkg:
            os.remove(pas_yearstamp_path)
            print(f"Intermediate GeoPackage {reprojected_pa} has been removed.")