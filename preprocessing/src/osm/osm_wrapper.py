import os 
from osm.osm_preprocessor import OSMPreprocessor
from osm.osm_geojson_to_gpkg import OSMGeojsonToGpkg
from utils import load_yaml, read_years_from_config
import shutil
import timing

class OSMWrapper():

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
        self.osm_output_data_dir = os.path.abspath(os.path.join(working_dir, "data","output","osm_data"))
        os.makedirs(self.osm_output_data_dir, exist_ok=True)
        self.input_dir = os.path.abspath(os.path.join(working_dir, "data","input"))
        self.lulc_dir = os.path.abspath(os.path.join(self.input_dir, 'lulc'))
        self.vector_dir = os.path.abspath(os.path.join(self.input_dir, 'vector'))
        os.makedirs(self.vector_dir, exist_ok=True)
        self.gpkg_dir = os.path.join(self.osm_output_data_dir, 'gpkg_temp')
        self.years = read_years_from_config(self.config)
        

    def osm_to_geojson(self, years:list, skip_fetch:bool):
        """
        Handles fetching OSM data for all the years in the configuration file and convert them to geojson files.

        Args:
            years (list): a list of years to process (From the OSMPreprocessor class)
            skip_fetch (bool): whether to skip fetching OSM data or not
        """
        osmp = OSMPreprocessor(self.config, self.lulc_dir, self.osm_output_data_dir, self.verbose, years)
        for year in years:
            # build the queries for the year
            queries = osmp.overpass_query_builder(year, bbox= osmp.bbox)
            
            # fetch the OSM data for the year
            if skip_fetch == False:
                intermediate_jsons = osmp.fetch_osm_data(queries=queries, year=year)
                if self.verbose:
                    [print(f"Created JSON file: {intermediate_json}, ") for intermediate_json in intermediate_jsons]
            else:
                #read all json files with the year in the name
                intermediate_jsons = [os.path.join(self.osm_output_data_dir, file) for file in os.listdir(self.osm_output_data_dir) if f'{year}.json' in file]

            # convert the intermediate JSON files to GeoJSON files
            osmp.convert_to_geojson(queries=queries, year=year)
            # fix invalid geometries in the GeoJSON files
            osmp.fix_invalid_geometries(queries=queries,year=year,overwrite_original=False)

    def osm_to_merged_gpkg(self, years:list):
        """
        Converts the OSM GeoJSON files to GeoPackage files and merges them into a single GeoPackage file.

        Args:
            years (list): a list of years to process (From the OSMPreprocessor class)

        Returns:
            None: Writes the GeoPackage files to the output directory
        
        """
        for year in years:
            ogtg = OSMGeojsonToGpkg(self.osm_output_data_dir,self.gpkg_dir,target_epsg=4326, year=year, file_ending='geojson')
            output_file = os.path.join(self.gpkg_dir, f'osm_merged_{year}.gpkg') # year added from OSM_PreProcessor class 
            fixed_gpkg_path = os.path.join(self.gpkg_dir, f'osm_merged_{year}_fixed.gpkg')
            ogtg.merge_gpkg_files(output_file, year)
            gpkg_path = ogtg.fix_geometries_in_gpkg(output_file, fixed_gpkg_path)
            #Move file to vector_dir for next notebook
            shutil.move(gpkg_path, os.path.join(self.vector_dir, f'osm_merged_{year}.gpkg'))

    
    def delete_temp_files(self, delete_geojsons:bool, delete_gpkg_files:bool):
        """
        Delete all intermediate GeoJSON files to save disk space.
        
        Args:
            delete_geojsons (bool): whether to delete GeoJSON files
            delete_gpkg_files (bool): whether to delete GeoPackage files
        Returns:
            None: Deletes all intermediate GeoJSON files from osm data directory
        """
        # delete all GeoJSON files
        if delete_geojsons:
            for file in os.listdir(self.osm_output_data_dir):
                if file.endswith('.geojson'):
                    os.remove(os.path.join(self.osm_output_data_dir, file))
            print(f"Deleted all GeoJSON files from {self.osm_output_data_dir}")
        
        if delete_gpkg_files:
            for file in os.listdir(self.gpkg_dir):
                if file.endswith('.gpkg') and 'osm_merged' not in file:
                    os.remove(os.path.join(self.gpkg_dir, file))
            print(f"Deleted all GeoPackage files from {self.gpkg_dir}")


if __name__ == "__main__":
    osm = OSMWrapper(os.getcwd(), "./config/config.yaml", verbose=True)
    osm.osm_to_geojson(osm.years, skip_fetch=True)
    osm.osm_to_merged_gpkg(osm.years)
    # osm.delete_temp_files(True, True)
    print("OSM data processing complete.")