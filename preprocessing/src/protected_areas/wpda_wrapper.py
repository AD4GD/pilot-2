# external imports
import os

# local imports
from protected_areas.wdpa_preprocessor import WDPAPreprocessor
from protected_areas.pa_processor_wrapper import PAProcessorWrapper
from protected_areas.pa_rasterizer import PARasterizer
from protected_areas.update_land_impedance import UpdateLandImpedance
from protected_areas.landscape_affinity_estimator import LandscapeAffinityEstimator
from protected_areas.lulc_pa_raster_sum import LulcPaRasterSum
from utils import load_yaml


class WDPAWrapper():
    """
    This class is responsible for preprocessing the input data for the ingesting protected areas data from WDPA API.
    The input LULC raster bounding box is extracted and used to fetch the unique ISO 3166-1 alpha-3 country code from the ohsome API.
    """

    def __init__(self, working_dir:str,config_path:str, verbose:bool) -> None:
        """
        Initialize the WDPAWrapper class

        Args:
            working_dir (str): path to the current/working directory
            config_path (str): path to the configuration file
            verbose (bool): verbose output
        """

        self.working_dir = working_dir
        self.config = load_yaml(config_path)
        self.verbose = verbose

        self.pa_input_dir = os.path.abspath(os.path.join(working_dir, "data","input","protected_areas"))
        os.makedirs(self.pa_input_dir, exist_ok=True)
        self.pa_output_dir = os.path.abspath(os.path.join(working_dir, "data","output","protected_areas"))
        os.makedirs(self.pa_output_dir, exist_ok=True)
        self.pa_output_data_dir = os.path.join(self.pa_output_dir, "pa_data")
        os.makedirs(self.pa_output_data_dir, exist_ok=True)

    def get_lulc_country_codes(self) -> dict:
        """
        Fetch the country codes for the LULC rasters

        Returns:
            dict: A dictionary of unique ISO3 country codes.
        """
        # initialize the WDPAPreprocessor class
        lulc_ccp = WDPAPreprocessor(self.config, self.working_dir, self.verbose)
        # fetch the unique country codes from input LULC raster data
        lulc_country_codes = set().union(*dict(lulc_ccp.fetch_lulc_country_codes(self.pa_output_dir)).values())
        return lulc_country_codes
    
    def protected_area_to_merged_geopackage(self, lulc_country_codes:dict, output_file:str ="merged_pa.gpkg", skip_fetch:bool=False) -> str:
        """
        For each unique country code, fetch and process the protected areas and merge them into a single GeoPackage file.
        API used fetches most up to date protected areas.

        Args:
            lulc_country_codes (dict): A dictionary of unique country codes.
            output_file (str): The name of the output GeoPackage file.
        
        Returns:
            str: The path to the merged GeoPackage file.
        """
        # initialize the PA_Processor_Wrapper class
        response_dir = os.path.join(self.pa_input_dir, "wdpa_data")
        os.makedirs(response_dir, exist_ok=True)
        # list to store the names of the GeoJSON files
        geojson_filepaths = []

        Pa_processor = PAProcessorWrapper(
            lulc_country_codes, 
            self.config['api_url'],
            self.config['token'],
            self.config['marine'],
            response_dir
        )
        if skip_fetch:
            geojson_filepaths = [os.path.join(response_dir, file) for file in os.listdir(response_dir)]
        else:
            Pa_processor.process_all_countries()
            geojson_filepaths = Pa_processor.save_all_country_geoJSON()

        # merge all the GeoJSON files into a single GeoPackage file
        gpkg = Pa_processor.merge_geojsons_to_geopackage(geojson_filepaths, output_file)
        # print(f"GeoPackage file created: {gpkg}")
        return gpkg
    
    def rasterize_protected_areas(self, merged_gpkg:str, lulc_dir:str, pa_to_yearly_rasters:bool=True) -> None:
        """
        Rasterize the protected areas by year of establishment.

        Args:
            merged_gpkg (str): The file name to the merged GeoPackage file.
            lulc_dir (str): The path to the directory containing the LULC raster data.
            pa_to_yearly_rasters (bool): Rasterize the protected areas by year of establishment (default is True).
        Returns:
            None
        """
        # Change this to false to use PAs from all years.
        gpkg = os.path.join(self.pa_output_data_dir, merged_gpkg)
        raster_output_dir = os.path.join(self.pa_output_dir, "pa_rasters")
        os.makedirs(raster_output_dir, exist_ok=True)

        rp = PARasterizer(gpkg, lulc_dir ,raster_output_dir)
        rp.reproject_pa_data(rp.lulc_metadata.crs_info["epsg"],filter_by_year=pa_to_yearly_rasters)
        rp.rasterize_pa_geopackage(rp.lulc_metadata, pa_to_yearly_rasters=True ,keep_intermediate_gpkg=False) 

    def sum_lulc_pa_rasters(self,input_path:str="data/input",output_path:str="data/output", lulc_path:str="lulc", lulc_with_null_path:str="lulc_temp", pa_path:str="pa_rasters", lulc_upd_compr_path:str="lulc_pa") -> None:
        """
        Sum the LULC and PA raster data.

        Args:
            input_path (str): The path to the input directory.
            output_path (str): The path to the output directory.
            lulc_path (str): The path to the LULC raster data.
            lulc_with_null_path (str): The path to the LULC raster data with zeros.
            lulc_upd_compr_path (str): The path to the combined LULC and PA raster data.
            pa_path (str): The path to the PA raster data.
        
        Returns:
            None
        """

        lprs = LulcPaRasterSum(input_path,output_path,lulc_path, lulc_with_null_path, pa_path, lulc_upd_compr_path)
        lprs.assign_no_data_values()
        lprs.combine_pa_lulc()

    def compute_affinity(self, affinity_dir:str='affinity') -> None:
        """
        Compute the affinity between the protected areas.

        Args:
            affinity_dir (str): The path to the directory where the affinity data will be saved.

        Returns:
            None
        """
        os.makedirs(affinity_dir, exist_ok=True)
        impedance_dir = os.path.join(self.working_dir, self.config["impedance_dir"])
        
        lae = LandscapeAffinityEstimator(impedance_dir, affinity_dir)
        lae.compute_affinity(os.listdir(impedance_dir))


    def reclassify_raster_with_impedance(self) -> None:
        """
        Reclassify the raster data with impedance values.
        
        Returns:
            None
        """
        uli = UpdateLandImpedance(self.config)
        uli.update_impedance()


# Example usage
if __name__ == "__main__":
    working_dir = os.getcwd()
    config_path = os.path.join(working_dir, "config", "config.yaml")
    wp = WDPAWrapper(working_dir,config_path, verbose=True)
    country_codes = wp.get_lulc_country_codes()
    print(f"Country protected areas to fetch: {country_codes}")
