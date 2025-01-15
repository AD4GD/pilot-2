import os
import warnings
from raster_metadata import RasterMetadata

#local imports
from text_matching import LULCCodes

class LULCDataPreprocessor():
    """
    Preprocesses LULC raster data for rasterization, 
    which includes mapping LULC codes with auxiliary data and extracting raster metadata.
    """
    def __init__(self, config:dict, lulc_filepath:str, working_dir:str):
        """
        Initializes the LULC data preprocessor. Maps LULC codes to OSM features and extracts raster metadata.

        Args:
            config (dict): configuration file
            lulc_filepath (str): path to the LULC raster dataset
            working_dir (str): current directory
        """
        self.config = config
        impedance_file = self.config.get('impedance', None)
        impedance_dir = self.config.get('impedance_dir', None)

        if impedance_file is not None and impedance_dir is not None:
            # define path
            impedance_file = os.path.join(working_dir,impedance_dir,impedance_file)
            print(f"Using auxiliary tabular data from {impedance_file}.")
        else:
            warnings.warn("auxiliary tabular data was not provided.")

        # map LULC codes to OSM features 
        self.lulc_codes = self.lulc_mapping(impedance_file)
        self.raster_metadata = RasterMetadata.from_raster(lulc_filepath)

    def lulc_mapping(self, impedance_file:str) -> dict:
        """
        Map LULC codes to OSM features using either user-defined mapping or text-matching tool with the impedance file.

        Args:
            impedance_file (str): path to the impedance file
        
        Returns:
            dict: dictionary containing LULC codes and corresponding OSM features
        """
        # find out from config file if user wants define LULC codes on their own, or use text-matching tool
        user_matching = self.config.get('user_matching')
      
        # if user defines mapping on their own
        if user_matching.lower() == 'true': # case-insensitive condition
            # access variables and subvariables from the confiration file
            lulc_codes = self.config.get('lulc_codes', {})
            # print codes of areas from OSM corresponding with LULC codes from input raster dataset
            print("User-specified mapping of LULC codes and OSM features is used.")
            print("LULC dictionary:", lulc_codes)

        # if user defines mapping from text-matching tool
        elif user_matching.lower() == 'false': # case-insensitive condition
            # call the function and capture the result
            lulc_codes = LULCCodes.codes_from_impedance(self.config, impedance_file)
            # print codes of areas from OSM corresponding with LULC codes from input raster dataset
            print("Text matching tool used to map LULC codes and corresponding OSM features.")
            print("LULC dictionary:", lulc_codes)
        else:
            raise ValueError("User did not specify mapping between OSM features and LULC types.")
        
        return lulc_codes