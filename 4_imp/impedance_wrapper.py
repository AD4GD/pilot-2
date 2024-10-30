from impedance_config_processor import Impedance_config_processor
import warnings
from utils import load_yaml, save_yaml

class ImpedanceWrapper():
    def __init__(self,
        types: str = None,
        decline_type: str = 'exp_decline', # 'exp_decline' or 'prop_decline'
        lambda_decay: float = 500,
        k_value: float = 500,
        config_path:str="config.yaml", 
        config_impedance_path:str="config_impedance.yaml"
    ):
        
        # Load the configuration files
        self.config = load_yaml(config_path)
        self.config_impedance_path = config_impedance_path
        self.config_impedance = load_yaml(self.config_impedance_path)
        
        # Define the dictionary template for the configuration YAML file (for each stressor). We are using variables defined above.
        self.params_placeholder = {
            'types': types, # specify whether category of stressors has particular types different in parameters (for example, primary and secondary roads)
            'decline_type': decline_type,  # user will choose from 'exp_decline' and 'prop_decline'
            'exp_decline': {
                'lambda_decay': lambda_decay  # placeholder for exponential decay value
            },
            'prop_decline': {
                'k_value': k_value  # placeholder for proportional decline value
            }
        }
        
        # process all years
        self.years = self.config.get('year', None)
        if self.years is None:
            warnings.warn("Year variable is null or not found in the configuration file.")
            self.years = []
        elif isinstance(self.years, int):
            self.years = [self.years]
        else:
            # cast to list
            self.years = [int(year) for year in self.years]

        # 1. Process the impedance configuration (initial setup + lulc & osm stressors)
        # e.g. impedance_stressors = {'primary': '/data/data/output/roads_primary_2018.tif'}
        impedance_stressors = self.process_impedance_config()

        #2. Prompt user to update the configuration file #TODO add function to do this automatically
        print("Please update the configuration file for impedance dataset:")

        # 2.1. Or validate after manual update 
        # TODO unimplemented
        # self.validate_config_impedance() 

        #3.0 Calculate impedance
        # initialise variables with outputs of the effects from all rasters
        max_result = None
        cumul_result = None

        # 4.0 update impdance with decayed effect

        # 5.0 Clean up

    
    def process_impedance_config(self):
        """
        Process the impedance configuration (initial setup + lulc & osm stressors)

        Returns:
            impedance_stressors (dict): dictionary for stressors, mapping stressor raster path to YAML alias
        """
        # initialize the dictionary for stressors, which contains mapping stressor raster path to YAML alias
        impedance_stressors = {} 

        icp = Impedance_config_processor(year=self.years[0], params_placeholder=self.params_placeholder, config_path=config_path, config_impedance_path=config_impedance_path)
        icp.setup_config_impedance()
        impedance_stressors, self.config_impedance = icp.process_stressors()
        # save the updated configuration file
        save_yaml(self.config_impedance, self.config_impedance_path)

        return impedance_stressors
