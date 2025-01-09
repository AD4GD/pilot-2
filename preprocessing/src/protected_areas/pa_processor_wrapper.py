import os
import json
import requests
import subprocess
from .pa_processor import PAProcessor

class PAProcessorWrapper:
    """
    This class retrieves and processes protected areas for multiple countries and utilizes the PA processor class to merge them into individual GeoJSON files for each country.
    """

    def __init__(self, countries:list[str], api_url:str, token:str, marine:str, output_dir:str) -> None:
        """
        Initialize the PA_Processor_Wrapper class.

        Args:
            countries (list): A list of country codes.
            api_url (str): The API endpoint URL.
            token (str): The API token.
            marine (str): The marine area boolean value.
            output_dir (str): The path to the directory where the GeoJSON files will be saved.
        """
        self.api_url = api_url
        self.token = token
        self.marine = marine
        self.countries = countries
        self.output_dir = output_dir
        self.processors = {country: PAProcessor(country) for country in countries}

    def process_all_countries(self) -> None:
        """
        Fetches all PAs for each country and processes them into a single GeoJSON file.
        """
        all_protected_area_geojson = []
        for country in self.countries:
            page = 0
            url = self.api_url.format(country=country, token=self.token, marine=self.marine)
            url += f"&page={page}"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                continue
            data = response.json()
            protected_areas = data["protected_areas"]
            if len(protected_areas) == 0:
                print(f"No protected areas found for {country}")
                break
            else:
                all_protected_area_geojson.append(data)
                page += 1
                continue
        # combine all the protected areas into a single feature collection / GeoJSON
        for data in all_protected_area_geojson:
            self.processors[country].add_PA_to_feature_collection(data["protected_areas"]) 

    def save_all_country_geoJSON(self) -> list[str]:
        """
        Saves all country GeoJSON files to the export directory.

        Returns:
            geojson_filepaths (list): A list of file paths to the saved GeoJSON files.
        """
        
        geojson_filepaths = []
        for country in self.countries:
            geojson_filepaths.append(self.processors[country].save_to_file(self.output_dir))
        return geojson_filepaths
    

    def merge_geojsons_to_geopackage(self, geojson_filepaths:list[str], output_file:str = "merged_protected_areas.gpkg") -> str:
        """
        Merges all GeoJSON files into a single GeoPackage file with different layers for each country.

        Args:
            geojson_filepaths (list): A list of GeoJSON file paths.
            output_file (str): The name of the output GeoPackage file.
        
        Returns:
            str: The path to the merged GeoPackage file.
        """
        # define the output merged GeoPackage file
        gpkg = os.path.join(self.output_dir, output_file)
        # remove GeoPackage if it already exists
        if os.path.exists(gpkg):
            os.remove(gpkg)

       # loop through the GeoJSON files and convert them to a geopackage
        for geojson_file in geojson_filepaths:
            # writes layer name as the first name from geojson files
            layer_name = os.path.splitext(os.path.basename(geojson_file))[0]
            # use ogr2ogr to convert GeoJSON to GeoPackage
            subprocess.run([
                "ogr2ogr", "-f", "GPKG", "-append", "-nln", layer_name, gpkg, geojson_file
            ]) 

        return gpkg