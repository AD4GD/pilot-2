import os
import json
import requests
import warnings
from itertools import product

#local imports
from reprojection import RasterTransform

class WDPAPreprocessor():
    """
    This class is responsible for preprocessing the input data for the ingesting protected areas data from WDPA API.
    The input LULC raster bounding box is extracted and used to fetch the unique ISO 3166-1 alpha-3 country code from the ohsome API.
    Since the LULC rasters have the same extent, we only need to fetch the country codes for one raster.
    """

    def __init__(self, config:dict,  current_dir:str, verbose:bool) -> None:
        """
        Initialize the WDPAPreprocessor

        Args:
            config (dict): dictionary containing the configuration parameters
            current_dir (str): the current directory

        """
        self.current_dir = current_dir
        self.config = config
        self.verbose = verbose

        # read year 
        self.years = self.config.get('year', None)
        if self.years is None:
            warnings.warn("Year variable is null or not found in the configuration file.")
            self.years = []
        elif isinstance(self.years, int):
            self.years = [self.years]
        else:
            # cast to list
            self.years = [int(year) for year in self.years]

        #read lulc
        self.lulc_templates = self.config.get('lulc', None)
        if self.lulc_templates is None:
            raise ValueError("LULC variable is null or not found in the configuration file.")
        elif isinstance(self.lulc_templates, str):
            self.lulc_templates = [self.lulc_templates]
        else:
            # cast to list
            self.lulc_templates = [lulc for lulc in self.lulc_templates]

        # read lulc_dir
        self.lulc_dir = self.config.get('lulc_dir', None)
        if self.lulc_dir is None:
            raise ValueError("LULC directory is null or not found in the configuration file.")

        # get all existing files
        self.lulc_series = self.get_all_existing_files(self.lulc_templates, self.years)

    def get_all_existing_files(self, lulc_templates: list, years: list) -> list[str]:
        """
        Get all existing files based on the list of years and the LULC templates

        Args:
            lulc_templates (list): list of LULC templates (e.g. ['lulc_{year}.tif', 'lulc_{year}_v2.tif'])
            years (list): list of years (e.g. [2015, 2016, 2017])
        Returns:
            list: list of existing files to process (e.g. ['lulc_2015.tif', 'lulc_2016.tif'])
        """

        # generate all possible filenames based on the list of years
        lulc_series = []
        # use itertools,product to create combination of lulc filename and year
        for lulc_template, year in product(lulc_templates, years): 
            try:
                # substitute year in the template
                lulc_file = str(lulc_template).format(year=year)
                # construct the full path to the input raster dataset
                lulc_path = os.path.join(self.current_dir, self.lulc_dir, lulc_file)
                # mormalize the path to ensure it is correctly formatted
                lulc_path = os.path.normpath(lulc_path)
                lulc_series.append(lulc_path)
            except KeyError as e:
                raise ValueError(f"Placeholder {e.args[0]} not found in 'lulc_template'") from e
            
        # Check if files exist and collect existing files
        existing_lulc_series = []
        for lulc_templates in lulc_series:
            if os.path.exists(lulc_templates):
                print(f"Input raster to be used for processing is {lulc_templates}")
                existing_lulc_series.append(lulc_templates)
            else:
                print(f"File does not exist: {lulc_templates}")

        # list all existing filenames to process
        if self.verbose:
            print("\n List of available input raster datasets to process:")
            for lulc_templates in existing_lulc_series:
                print(f"Processing file: {lulc_templates}")

        # update lulc_series with files that exist
        return existing_lulc_series
        
    #NOTE Ohsome API is using openstreetmap data, which may not be the best source to fetch country codes from bounding box with. The GAUL dataset provided by FAO (UN) is a better source for this but it is not available through API.
    def get_country_code_from_bbox(self, bbox:str, output_path:str) -> set:
        """
        This function sends a request to the ohsome API to get the country code from a given bounding box

        Args:
            bbox (str): bounding box in the format 'x_min,y_min,x_max,y_max'. It should be 'lon_min','lat_min',lon_max','lat_max'
            output_path (str): path to save the geojson file

        Returns:
            set: set of unique country codes
        """
        url = 'https://api.ohsome.org/v1/elements/geometry'
        data = {"bboxes": {bbox}, "filter": "boundary=administrative and admin_level=2", "properties": 'tags'}
        response = requests.post(url, data=data)

        
        # check if the request was successful
        if response.status_code == 200:
            response_json = response.json()
            print("Request was successful")
            # extract unique country names, filtering out None values
            # create set to handle only unique names
            unique_country_names = {
                feature['properties'].get('ISO3166-1:alpha3') 
                for feature in response_json.get('features', []) # filter out none values
                if feature['properties'].get('ISO3166-1:alpha3')
            }
    
            # print unique country names
            print(f"Countries covered by the bounding box are (ISO-3 codes): \n{'\n'.join(unique_country_names)}")
            print("-" * 40)

            # save JSON response to GeoJSON
            if output_path is not None:
                with open(os.path.join(output_path,"countries.geojson"), 'w') as f:
                    json.dump(response_json, f, indent=4)
            return unique_country_names
        else:
            raise Exception(f"Error: {response.status_code}")

        # TODO - raise warning if no countries in the respnse but request is successful
        
    def fetch_lulc_country_codes(self, output_path:str) -> dict[set]:
        """
        Fetch the country codes for the LULC raster.
        Since the LULC rasters have the same extent, we only need to fetch the country codes for one raster.

        Args:
            save_geojson (bool): save the geojson file (default is True)
            output_path (str): path to save the geojson file (optional)

        Returns:
            dict: dictionary containing the country codes for each LULC raster
        """
        lulc_country_codes = {}
        lulc = self.lulc_series[0]
        x_min, y_min, x_max, y_max = RasterTransform(lulc).bbox_to_WGS84(print_details=self.verbose)
        bbox = f"{y_min},{x_min},{y_max},{x_max}" # changed! Ohsome API requires: 'lon_min','lat_min',lon_max','lat_max'
        lulc_country_codes[lulc] = self.get_country_code_from_bbox(bbox, output_path)
        return lulc_country_codes