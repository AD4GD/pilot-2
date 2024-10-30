from abc import ABC, abstractmethod
import os 
class ImpedanceConfigProcessor(ABC):
    
    def __init__(self, config:dict, config_impedance:dict, params_placeholder:dict, impedance_stressors:dict, year:int, *args) -> None:
        super().__init__()
        self.config = config
        self.config_impedance = config_impedance
        self.output_dir = os.path.normpath(self.config.get('output_dir'))
        self.parent_dir = os.path(os.getcwd())
        self.params_placeholder = params_placeholder
        self.impedance_stressors = impedance_stressors
        self.year = year
       
       
    @abstractmethod
    def update_impedance_config(self, *args, **kwargs) -> tuple[dict,dict]:
        """Updates the impedance configuration file with stressors and default decay parameters.
        
        Returns:
            impedance_dictionaries (tuple): Tuple containing two dictionaries:
                - Impedance_stressors (dict) The dictionary of stressors, mapping stressor raster path to YAML alias.
                - Impedance_configuration (dict): The updated configuration file mapping stressors to default decay parameters.
        """
        ...
