from warnings import warn
from osgeo import gdal, ogr
import yaml
import os
from subprocess import Popen, PIPE


def load_yaml(path:str) -> dict:
        """
        Load a yaml file from the given path to a dictionary

        Args:
            path (str): path to the yaml file

        Returns:
            dict: dictionary containing the yaml file content
        """
        with open(path , 'r') as file:
            return yaml.safe_load(file)
        
def save_yaml(data:dict, path:str) -> None:
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
        print("Updated YAML configuration saved to:", path)
    

def get_max_from_tif(ds) -> float:
    """
    Extracts the maximum value from a GDAL raster dataset using GDAL's internal functions.
    
    INPUT (arguments):
        impedance_ds (gdal.Dataset): GDAL dataset object representing the raster.
    
    OUTPUT (returns):
        float: The maximum value in the raster.
    """
    # Check if the dataset is valid
    if ds is None:
        raise ValueError("The dataset is invalid or couldn't be opened.")
    # get the first raster band (assuming a single-band raster)
    band = ds.GetRasterBand(1)
    if band is None:
        raise ValueError("The raster band could not be retrieved.")
    
    # get the statistics for the band: min, max, mean, std_dev
    stats = band.GetStatistics(True, True)  # (approx_ok=True, force=True)
    # the maximum value is the second item in the stats list
    max_value = stats[1]
    # clean up
    ds = None
    return max_value

def extract_layer_names(gpkg_path:str) -> list:
    # open and read geopackage
    vector_data = ogr.Open(gpkg_path, update=0)  # update=0 means read-only mode
    layer_count = vector_data.GetLayerCount() # get the number of layers
    layers = [] # initialise list with layer names

    # extract layer names
    for i in range(layer_count):
        layer = vector_data.GetLayerByIndex(i)
        layer_name = layer.GetName()
        layers.append(layer_name)
    
    return layers


def extract_attribute_values(vector_gpkg:str, layer_name:str=None, attribute:str="highway") -> list:
    """
    Extract all unique attribute values from a vector GeoPackage file.
    
    Args:
        vector_gpkg (str): path to the vector GeoPackage file
        attribute (str): attribute name to extract unique values from
        
    Returns:
    list: list of unique attribute values
    """

    # open the vector data source
    data_source = ogr.Open(vector_gpkg)
    if data_source is None:
        raise RuntimeError(f"Failed to open the vector file: {vector_gpkg}")

    # get the layer from the data source (use first if not specified)
    if layer_name is None:
        layer_name = data_source.GetLayer(0).GetName()
        print(f"Layer name not specified. Using the first layer: {layer_name}")
    layer = data_source.GetLayerByName(layer_name)
    print(f"Layer name: {layer_name}")

    # get unique values of the attribute
    values = layer.GetNextFeature()
    unique_values = set()
    while values:
        value = values.GetField(attribute)
        unique_values.add(value)
        values = layer.GetNextFeature()

    return unique_values


def merge_tiffs_into_vrt(self, tiffs:list, output_path:str):
    """
    Merge multiple raster datasets into a single VRT file.

    Args:
        tiffs (list): list of paths to the raster datasets
        output_path (str): path to the output VRT file

    Returns:
        None
    """
    # write the list to a new file (path to the file is ../data/list_of_tiff_files.txt)
    tiffs_filepaths = output_path.replace('.vrt', '_tiffs.txt')
    with open(tiffs_filepaths, "w") as f:
        for item in tiffs:
            f.write(item + "\n")

    gdal_command = f"""gdalbuildvrt -input_file_list {tiffs_filepaths} {output_path}"""
    proc = Popen(gdal_command, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    # remove the list of tiff files
    os.remove(tiffs_filepaths)

    if proc.returncode != 0:
        print(proc.returncode)
        print("STDERR:", stderr.decode())
        raise Exception("Error creating VRT")
    

def find_stressor_params(config_dict:dict, search_key:str):
        """
        Recursively search for the stressor parameters in the nested dictionary (eg, railways) and return the dictionary of parameters.
        """
        if isinstance(config_dict, dict):
            # Check if in_key is present at the current level
            if search_key in config_dict:
                return config_dict[search_key]
            # Recurse through each key-value pair in the dictionary
            for key, value in config_dict.items():
                stressor_params = find_stressor_params(value, search_key)
                if stressor_params is not None:
                    return stressor_params
        return None 