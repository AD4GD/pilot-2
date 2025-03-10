import unittest
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch
from enrichment.lulc_enrichment_wrapper import LULCEnrichmentWrapper
from enrichment.vector_data_processor import VectorDataPreprocessor
import sys
import io
from contextlib import redirect_stdout
# from unittest.mock import Mock, patch

# local imports required for the tests
import yaml
#from utils import load_yaml,extract_attribute_values,get_lulc_template,read_years_from_config
from raster_metadata import RasterMetadata
import os
from osgeo import ogr

class TestLulcDataProcessor(TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        #warnings.simplefilter("ignore", ResourceWarning)

        config_path = "./config/config.yaml"
        cls.lew = LULCEnrichmentWrapper(
           working_dir=os.getcwd(),
           config_path=config_path,
           verbose=True
        )

        with open(config_path , 'r') as file:
            cls.config = yaml.safe_load(file)
        cls.working_dir = os.getcwd()
        cls.vector_dir = os.path.join(cls.working_dir,cls.config["case_study_dir"],cls.config['vector_dir'])
        cls.year = 2017
        cls.lulc_filepath = './data/shared/input/lulc/lulc_albera_ext_concat_{year}.tif'.format(year=cls.year)

    def test_prepare_lulc_osm_data(self):
        self.lew.initialise_data_processors([self.year])
        self.assertTrue(os.path.exists(self.lew.vp.vector_railways_buffered))
        self.assertTrue(os.path.exists(self.lew.vp.vector_roads_buffered))

    # NOTE: Requires buffered geopackage files to exist
    @patch.object(VectorDataPreprocessor, "buffer_features")
    def test_rasterize_vector_roads(self, mocked_buffer):
        mocked_buffer.return_value = None
        self.lew.initialise_data_processors([self.year])
        expected_road_types = ['motorway', 'primary', 'secondary', 'tertiary']
        stressor_dict = self.lew.rasterize_vector_roads(
            year = self.year,
            output_dir = self.lew.stressors_dir,
            raster_metadata= self.lew.lp.raster_metadata,
            roads_gpkg = self.lew.vp.vector_roads_buffered,
            burn_value = self.lew.lp.lulc_codes["lulc_road"],
            groupby_roads=True
        )
        # check file exists
        # loop through directory and get all road tiffs
        road_tiffs = [f for f in os.listdir(self.lew.stressors_dir) if "roads" in f]
        self.assertTrue(len(road_tiffs) > 0)
        # check if the road types are as expected
        self.assertEqual(sorted(stressor_dict["roads"]), sorted(expected_road_types))
        
        # clean up - delete the road tiffs
        for road_tiff in road_tiffs:
            os.remove(os.path.join(self.lew.stressors_dir, road_tiff))

    #NOTE Requires osm_merged geopackage file to exist
    @patch.object(VectorDataPreprocessor, "buffer_features")
    def test_rasterize_one_vector_layer(self, mocked_buffer):
        mocked_buffer.return_value = None
        self.lew.initialise_data_processors([self.year])
        output_path = os.path.join(self.lew.stressors_dir, "test_roads.tif")
        self.lew.rasterize_vector_layer(
            self.lew.lp.raster_metadata,
            self.lew.vp.vector_roads_buffered,
            output_path=output_path,
            nodata_value=0,
            burn_value=self.lew.lp.lulc_codes["lulc_road"],
            layer_name="roads"
        )
        self.assertTrue(os.path.exists(output_path))
        os.remove(output_path)
        
    #TODO
    def test_rasterize_vector_layers(self):
        self.rasters_temp = self.lew.rasterize_vector_layers([self.year],save_osm_stressors=True)
    
        self.lew.initialise_data_processors()
        self.lew.rasterize_vector_layers()
        self.assertTrue(os.path.exists(self.lew.vp.raster_roads))
        self.assertTrue(os.path.exists(self.lew.vp.raster_railways))

    def test_merge_lulc_osm_data(self):
        self.lew.initialise_data_processors()
        self.lew.merge_lulc_osm_data()
        self.assertTrue(os.path.exists(self.lew.vp.vector_merged))
