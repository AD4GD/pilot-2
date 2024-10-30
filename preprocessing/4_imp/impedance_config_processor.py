import os
import yaml
import warnings
import geopandas as gpd
import numpy as np
import copy
from typing import Optional, Iterator

# NOTE: this should be split into two classes: 
# one for the configuration file setup (which can be in a Wrapper)
# and one for the lulc stressor processor
# then vector stressor processor

from lulc_impedance_processor import Lulc_impedance_processor
from osm_impedance_processor import Osm_impedance_processor
from utils import save_yaml

class Impedance_config_processor(): 

    def __init__(self, year:int, params_placeholder:dict, config:dict, config_impedance:dict):
        """
        Initialize the Impedance class with the configuration file paths and other parameters.

        Args:
            config_path (str): The path to the main configuration file. Default is 'config.yaml'.
            config_impedance_path (str): The path to the impedance configuration file. Default is 'config_impedance.yaml'.
            params_placeholder (dict): The dictionary template for the configuration YAML file (for each stressor).
            impedance_stressors_dict (dict): The dictionary for stressors, mapping stressor raster path to YAML alias.
        Returns:
            None
        """
        # self.params_placeholder = params_placeholder 
        # self.impedance_stressors_dict = impedance_stressors_dict
        self.config = config
        self.params_placeholder = params_placeholder
        self.year = year
        
        self.impedance_stressors = {} # initialize the dictionary for stressors, which contains mapping stressor raster path to YAML alias
        # TODO remove since it is called in wrapper
        # self.config_impedance = self.setup_config_impedance()
        # self.impedance_stressors = self.process_stressors()


    def setup_config_impedance(self) -> None:
        """
        Handle the initial setup of the configuration file for impedance
        """
        # ensure 'initial_lulc' exists and handle 'enabled' field logic (various cases)
        if self.config_impedance.get('initial_lulc', None) is None:
            # create 'initial_lulc' with 'enabled' set to 'false' if it doesn't exist or is None
            self.config_impedance['initial_lulc'] = {'enabled': 'false'}
        else:
            # if 'enabled' doesn't exist in 'initial_lulc', add it and set to 'false'
            if self.config_impedance['initial_lulc'].get('enabled', None) is None:
                self.config_impedance['initial_lulc']['enabled'] = 'false'

        #NOTE: FOR DEBUGGING
        print("Initial structure of the configuration file for impedance dataset:")
        print(yaml.dump(self.config_impedance, default_flow_style=False))
        print("-" * 40)

        return self.config_impedance
    
    def process_stressors(self):
        """
        Process the stressors for lulc and osm data
        """
        lip = Lulc_impedance_processor(self.config, self.config_impedance, self.params_placeholder, self.impedance_stressors, self.year)
        self.impedance_stressors, self.config_impedance = lip.update_impedance_config()
        oip = Osm_impedance_processor(self.config, self.config_impedance, self.params_placeholder, self.impedance_stressors, self.year)
        self.impedance_stressors, self.config_impedance = oip.update_impedance_config()

        return self.impedance_stressors, self.config_impedance
