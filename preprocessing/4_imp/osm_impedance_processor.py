
from utils import load_yaml
from osgeo import gdal
import os
import copy
import yaml
from interfaces.ImpedanceConfigProcessor import ImpedanceConfigProcessor

class Osm_impedance_processor(ImpedanceConfigProcessor):
    def __init__(self, config_impedance:dict, config:dict, params_placeholder:dict, impedance_stressors:dict, year:int,
            osm_stressor_path:str="stressors.yaml"
        ):
        """
        Initialize the Impedance class with the configuration file paths and other parameters.
        """
        super().__init__(config, config_impedance, params_placeholder, impedance_stressors)

        # additional directories
        self.vector_dir = self.config.get('vector_dir')

        # load road/railway types from the configuration file form the 3rd notebook
        self.osm_stressor_path = osm_stressor_path

        # # get the maximum value from the impedance raster dataset
        # if impedance_tif is not None:
        #     impedance_ds = gdal.Open(impedance_tif) # open raster impedance dataset
        #     impedance_max = get_max_from_tif(impedance_ds) # call function from above
        #     print (f"Impedance raster GeoTIFF dataset used is {impedance_tif}") # debug
        #     print (f"Maximum value of impedance dataset: {impedance_max}") # debug
        #     # close the dataset
        #     impedance_ds = None
        # else:
        #     raise FileNotFoundError(f"Impedance raster GeoTIFF dataset '{impedance_tif}' is not found! Please check the configuration file.") # stop execution

    def update_impedance_config(self):
        """
        - Updates the impedance configuration file with OSM stressors and default decay parameters.
        - Updates the impedance stressors dictionary with the OSM stressors and their raster paths.

        Returns:
            tuple: Tuple containing two dictionaries:
                - Impedance_stressors (dict) The dictionary of stressors, mapping stressor raster path to YAML alias.
                - Impedance_configuration (dict): The updated configuration file mapping stressors to default decay parameters.
        """
        
        osm_stressors = load_yaml(self.osm_stressor_path)
        self.config_impedance = self.prepare_config_impendance_file(osm_stressors)
        # add the OSM stressors to the impedance configuration file
        for osm_stressor_feature,osm_feature_subtypes in osm_stressors.items():
            for osm_feature_subtype in osm_feature_subtypes:
                raster_path = os.path.normpath(os.path.join(self.parent_dir,self.output_dir,f'{osm_stressor_feature}_{osm_feature_subtype}_{year}.tif'))
                self.impedance_stressors[osm_feature_subtype] = raster_path

        return self.impedance_stressors, self.config_impedance
    
    def prepare_config_impendance_file(self, osm_stressors:dict):
        """
        Inserts the OSM stressors and subtypes (for example the 'road' OSM feature has a subtype 'motorway') into the impedance configuration file.
        
        - Format of the osm_stressor_dict:
        { 
            roads: ['trunk', 'motorway', 'primary', 'secondary', 'tertiary'] # road types to be extracted from OSM
            railways: ['rail', 'light_rail', 'subway'] # railway types to be extracted from OSM
        }

        Args:
            osm_stressor_dict (dict): dictionary of OSM stressors and their subtypes
        Returns:
            dict: updated configuration file with OSM stressors and subtypes

            
        """
        vector = self.config_impedance.get('vector', {}) # access the vector section in YAML
  
        for osm_stressor_feature, osm_stressor_feature_subtypes in osm_stressors.items(): 
            print(f"Processing {osm_stressor_feature}...")

            # 1. create or update the key for each osm_stressor_feature in 'vector'
            if osm_stressor_feature not in vector:
                vector[osm_stressor_feature] = {}  # initialize the osm_stressor_feature as an empty dictionary
                
            # define the 'types' key for each osm_stressor as an empty dictionary (will be updated later)
            vector[osm_stressor_feature]['types'] = {}  # initialize 'types' as an empty dictionary

            # check if the subtypes variable contains more than one object)
            if len(osm_stressor_feature_subtypes) > 1:
                # update the types in the vector for the current osm_stressor
                vector[osm_stressor_feature]['types'] = True # Update types with True
                # loop through each subtype in the dynamic variable
                for stressor_subtype in osm_stressor_feature_subtypes:
                    # write params_placeholder to vector for each type
                    vector[osm_stressor_feature][stressor_subtype] = copy.deepcopy(self.params_placeholder)
            else:
                # update the types in the vector for the current osm_stressor
                vector[osm_stressor_feature]['types'] = None # update types with empty value
                vector[osm_stressor_feature] = copy.deepcopy(self.params_placeholder)
                
        # update the 'vector' section back into the main config_impedance
        self.config_impedance['vector'] = vector

        return self.config_impedance
