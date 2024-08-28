import os
from osgeo import ogr
import warnings

class VectorTransform:
    def __init__(self, directory):
        self.directory = directory

    def geom_valid(self):
        """
        Checks the validity of geometries in all Geopackage files within the specified directory.

        Returns:
        - None: Prints out the validity status of the geometries.
        """
        for filename in os.listdir(self.directory):
            if filename.lower().endswith('.gpkg'):
                file_path = os.path.join(self.directory, filename)
                
                # open geopackage file
                data_source = ogr.Open(file_path)
                
                if data_source is None:
                    print(f"Failed to open GeoPackage: {file_path}")
                    continue

                # get the number of layers in Geopackage
                num_layers = data_source.GetLayerCount()
                # initialize counters for invalid geometries
                invalid_features = 0
                # initialize list to write down IDs of invalid geometries
                invalid_features_list = []
                # initialize flag for geometry validity
                any_invalid_geometry = False
                
                # iterate through each layer
                for i in range(num_layers):
                    layer = data_source.GetLayerByIndex(i)
                    layer_name = layer.GetName()
                    # calculate the total number of features in the layer
                    total_features = layer.GetFeatureCount()
                    
                    # iterate through each feature in the layer
                    for feature in layer:
                        total_features += 1 # increment the number of total fearu
                        geometry = feature.GetGeometryRef()
                        if not geometry.IsValid():
                            invalid_features += 1
                            
                            any_invalid_geometry = True
                            invalid_features_list.append(feature.GetFID())
                            """print(f"Invalid geometry found in file '{filename}', layer '{layer_name}':")"""
                            # print(f"Feature ID: {feature.GetFID()}")
                            """print(f"Geometry: {geometry.ExportToWkt()}")""" # to print geometry - dropped, as provides massive text

                    # output validity status
                    if any_invalid_geometry:
                        # calculate share of invalid geometries
                        share_invalid = (invalid_features / total_features) * 100 # if invalid_features > 0:
                        # raise warning
                        warning_message = (
                            f"At least one geometry in GeoPackage '{filename}' (layer '{layer_name}') is invalid. It might bring extra omissions in the further processing.\n"
                            f"Share of invalid geometries in GeoPackage '{filename}', layer '{layer_name}': {share_invalid:.4f}%.\n"
                            f"IDs of invalid features are: {invalid_features_list}."
                        )
                        warnings.warn(warning_message)
                        print("-"*40)  # separator for readability
                    else:
                        print(f"Good news! All vector geometries in GeoPackage '{filename}' (layer '{layer_name}') are valid.")
                        print("-"*40)  # separator for readability

                    # show the share of invalid geometries in each layer
                                         
                # close Geopackage
                data_source = None

# Example usage:
# vector_transform = VectorTransform(directory)
# vector_transform.geom_valid()
