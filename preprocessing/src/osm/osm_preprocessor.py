from raster_metadata import RasterMetadata
from reprojection import RasterTransform
import os
import pyproj
import requests
import json
import subprocess
import warnings
from utils import get_lulc_template

class OSMPreprocessor():
    """
    OSM (OpenStreetMap) Pre-Processor class to fetch OSM data for a given set of years and a bounding box.
    Currently only fetches for one year of OSM data.
    """
    def __init__(self, config:dict, lulc_dir:str, output_dir:str, verbose:bool, years:list[int]) -> None:
        """
        Initialize the OSM Pre-Processor class with the configuration file and output directory.

        Args:
            lulc_dir (str): the directory containing the LULC files
            config (dict): The configuration.yaml loaded as a dictionary
            output_dir (str): the output directory to save the intermediate files
            verbose (bool): verbose output
        """
        self.config = config
        self.output_dir = output_dir
        self.years = years

        # create a dictionary of LULC files and corresponding years
        lulc_series = {get_lulc_template(lulc_dir,self.config, year):year for year in self.years}
        
        # We can use the first raster to get the bounding box, as all rasters should have the same extent
        lulc = list(lulc_series.keys())[0]

        if verbose:
            print(f"OSM data is to be retrieved for {self.years} years.")
            print ("-" * 30)
            print(f"Bounding box for the OSM data is to be retrieved from the raster: {lulc}")

        self.bbox = RasterTransform(raster_path=lulc).bbox_to_WGS84(print_details=verbose)
        # convert the bounding box to a string
        self.bbox = ",".join([str(coord) for coord in self.bbox])

    def fetch_osm_data(self,queries:dict, year:int , overpass_url:str = "https://overpass-api.de/api/interpreter") -> list:
        """
        A function to fetch OSM data for a given set of queries and a year.

        Args:
            queries (dict): a dictionary of queries
            year (int): the year of the data
            overpass_url (str): the URL of the Overpass API

        Returns:
            list: a list of intermediate JSON files
        """

        intermediate_jsons = []

        # iterate over the queries and execute them
        for query_name, query in queries.items():
            response = requests.get(overpass_url, params={'data': query})
            print(response)
                
            # if response is successful
            if response.status_code == 200:
                print(f"Query to fetch OSM data for {query_name} in the {year} year has been successful.")
                data = response.json()
                
                # Extract elements from data
                elements = data.get('elements', [])
                
                # Print the number of elements
                print(f"Number of elements in {query_name} in the {year} year: {len(elements)}")
                
                # Print the first 3 elements to verify response
                for i, element in enumerate(elements[:3]):
                    print(f"Element {i+1}:")
                    print(json.dumps(element, indent=2))
                
                # Save the JSON data to a file
                output_file = os.path.join(self.output_dir, f"{query_name}_{year}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print(f"Data has been saved to {output_file}")
                print ("-" * 30)

                # Add the output file name to the list
                intermediate_jsons.append(output_file)
                
            else:
                print(f"Error: {response.status_code} for {query_name} in the {year} year")
                print(response.text)
                print ("-" * 30)

        return intermediate_jsons

    def overpass_query_builder(self, year:int, bbox:str) -> dict[str, str]:
        """
        A function to build the queries for Overpass API for a given year and bounding box, for roads, railways, waterways, and waterbodies.

        Args:
            year (int): the year of the data
            bbox (str): the bounding box to query
        
        Returns:
            dict: a dictionary of queries for roads, railways, waterways, and waterbodies
        """
        #TODO: The data limit is 1GB. Could try split the query into smaller parts (bounding boxes) and run them separately.
        #NOTE: the issue with the above is that you might get IP blocked by the server. So, need to be careful with this.
        query_roads = f"""
        [out:json]
        [maxsize:1073741824]
        [timeout:9000]
        [date:"{year}-12-31T23:59:59Z"]
        [bbox:{bbox}];
        way["highway"~"(motorway|trunk|primary|secondary|tertiary)"];
        /* also includes 'motorway_link',  'trunk_link' etc. because they also restrict habitat connectivity */
        (._;>;);
        out body;
        """
        # '{' characters must be doubled in Python f-string (except for {bbox} because it is a variable)
        # to include statement on paved surfaces use: ["surface"~"(paved|asphalt|concrete|paving_stones|sett|unhewn_cobblestone|cobblestone|bricks|metal|wood)"];
        # it is important to include only paved roads it is important to list all values above, not only 'paved'*/
        # BUT! : 'paved' tag seems to be missing in a lot of features at timestamps from 2010s
        # 'residential' roads are not fetched as these areas are already identified in land-use/land-cover data as urban or residential ones
        # "~" extracts all tags containing this text, for example 'motorway_link'
        
        query_railways = f"""
        [out:json]
        [maxsize:1073741824]
        [timeout:9000]
        [date:"{year}-12-31T23:59:59Z"]
        [bbox:{bbox}];
        way["railway"~"(rail|light_rail|narrow_gauge|tram|preserved)"];
        (._;>;);
        out;
        """
        
        # way["railway"];  # to include features if 'railway' key is found (any value)
        # to include features with values filtered by key. 
        # This statement also includes 'monorail' which are not obstacles for species migration, but these features are extremely rare. Therefore, it was decided not to overcomplicate the query.
        # 31/07/2024 - added filtering on 'preserved' railway during the verification by UKCEH LULC dataset (some railways are marked as 'preserved at older timestamps and 'rail' in newer ones).
    
        query_waterways = f"""
        [out:json]
        [maxsize:1073741824]
        [timeout:9000]
        [date:"{year}-12-31T23:59:59Z"]
        [bbox:{bbox}];
        (
        way["waterway"~"^(river|canal|flowline|tidal_channel)$"];
        way["water"~"^(river|canal)$"];
        );
        /* ^ and $ symbols to exclude 'riverbank' and 'derelict_canal'*/
        /*UPD - second line is added in case if some older features are missing 'way' tag*/
        (._;>;);
        out;
        """

        # Query to bring water features with deprecated tags
        query_waterbodies = f"""
        [out:json]
        [maxsize:1073741824]
        [timeout:9000]
        [date:"{year}-12-31T23:59:59Z"]
        [bbox:{bbox}];
        (
        nwr["natural"="water"];
        nwr["water"~"^(cenote|lagoon|lake|oxbow|rapids|river|stream|stream_pool|canal|harbour|pond|reservoir|wastewater|tidal|natural)$"];
        nwr["landuse"="reservoir"];
        nwr["waterway"="riverbank"];
        /*UPD - second filter was added to catch other water features at all timestamps*/
        /*UPD - third and fourth filters were added to catch other water features at older timestamps*/
        /*it is more reliable to query nodes, ways and relations altogether ('nwr') to fetch the complete polygon spatial features*/
        );
        (._;>;);
        out;
        """
        
        # to include small waterways use way["waterway"~"(^river$|^canal$|flowline|tidal_channel|stream|ditch|drain)"]

        # merge queries into dictonary
        # to include all queries
        return {"roads":query_roads, "railways":query_railways, "waterways":query_waterways, "waterbodies":query_waterbodies}
    

    def convert_to_geojson(self, queries:dict[str,str], year:int):
        """
        A function to convert the intermediate JSON files to GeoJSON files. The GeoJSON files written to the output directory.

        Args:
            queries (dict): a dictionary of queries
            year (int): the year of the data
        """
        for query_name, query in queries.items():
            input_file = os.path.join(self.output_dir, f"{query_name}_{year}.json")
            output_file = os.path.join(self.output_dir, f"{query_name}_{year}.geojson")
            result = subprocess.run(['osmtogeojson', input_file], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Conversion to GeoJSON for {query_name} in the {year} year was successful.")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
            else:
                print(f"Conversion to GeoJSON for {query_name} in the {year} year failed.")
                print(result.stderr)
            

    def fix_invalid_geometries(self, queries:dict[str,str], year:int ,overwrite_original:bool):
        """
        A function to fix invalid geometries in the GeoJSON files

        Args:
            queries (dict): a dictionary of queries
            year (int): the year of the data
            overwrite_original (bool): overwrite the original GeoJSON files (True) or create new ones (False) *_filtered.geojson

        Returns:
            list: a list of fixed GeoJSON files
        """
        geojson_files=[]

        # iterate over the queries and define outputs
        for query_name, query in queries.items():
            geojson_file = os.path.join(self.output_dir, f"{query_name}_{year}.geojson")

            # check if the non-zero GeoJSON files exist
            if os.path.exists(geojson_file) and os.path.getsize(geojson_file) > 0:
                print(f"Conversion to GeoJSON for {query_name} in the {year} year was successful.")
                
                # read the GeoJSONs
                with open(geojson_file, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                    features = geojson_data.get('features', [])
                    print(f"Total features: {len(features)}")
                    
                # determine the geometries to filter based on query_name
                # for roads, railways and waterways extract only lines and multilines
                if query_name in ("roads", "railways", "waterways"):
                    geometry_types = ['LineString', 'MultiLineString']
                    # filter based on geometry types and level - it should be 0 (or null)
                    filtered_features = [
                        feature for feature in geojson_data.get('features', [])
                        if feature['geometry']['type'] in geometry_types
                        and (feature['properties'].get('level') in (None, 0)) # filtering by ground level of infrastructure
                    ]
                # for waterbodies extract only polygons and multipolygons
                elif query_name == "waterbodies":
                    geometry_types = ['Polygon', 'MultiPolygon']
                    # filter based on geometry types only
                    filtered_features = [
                        feature for feature in geojson_data.get('features', [])
                        if feature['geometry']['type'] in geometry_types
                    ]
                # for everything else extract everything that can be found
                else:
                    filtered_features = [
                        feature for feature in geojson_data.get('features', [])
                    ]

                # cast all property keys to lowercase (to avoid issues with case sensitivity for future notebooks)
                filtered_features = [
                    {
                        k: {property_key.lower(): property_value for property_key, property_value in v.items()} if k == "properties" else v
                        for k, v in feature.items()
                    }
                    for feature in filtered_features
                ]
                # create a new GeoJSON structure with filtered features
                filtered_geojson_data = {
                    "type": "FeatureCollection",
                    "features": filtered_features
                }

                print(f"Total features after filtering {query_name} in the {year} year: {len(filtered_features)}")
                print ("-" *30)
                
                # create new file 
                if overwrite_original == False:
                    geojson_file = os.path.join(self.output_dir, f"{query_name}_{year}_filtered.geojson")
                
                # overwrite the original GeoJSON file with the filtered one
                with open(geojson_file, 'w', encoding='utf-8') as f:
                    json.dump(filtered_geojson_data, f, ensure_ascii=False, indent=4)

                # write filenames to the list with intermediate geojsons
                geojson_files.append(geojson_file)
            
            else:
                print(f"Conversion to GeoJSON for {query_name} in the {year} year failed.")
                print ("-" *30)

        return geojson_files