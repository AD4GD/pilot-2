import rasterio
import numpy as np
import os
import pandas as pd


input_dir = 'data\input\lulc'

lulc = 'lulc_albera_ext_2022.tif'
factor = 'srtm.tif'
# 'aspect_srtm.tif' for slope aspect

lulc_code = 22 # vineyards

os.chdir("preprocessing/src")
print(os.getcwd())

lulc_path = os.path.join(input_dir, lulc)
lulc_path = os.path.normpath(lulc_path)
factor_path = os.path.join(input_dir, factor)
factor_path = os.path.normpath(factor_path)

# Load binary raster
with rasterio.open(lulc_path) as src1:
    binary_raster = src1.read(1)  # Read the first band
    binary_transform = src1.transform
    binary_nodata = src1.nodata
    binary_raster_proc = np.where(binary_raster == lulc_code, binary_raster, np.nan)
    binary_raster = np.nan_to_num(binary_raster_proc, nan=0)  # Replace NaN (NoData) with 0


# Load continuous raster
with rasterio.open(factor_path) as src2:
    continuous_raster = src2.read(1)
    continuous_transform = src2.transform
    continuous_nodata = src2.nodata

# Mask NoData values
if binary_nodata is not None:
    binary_raster = np.where(binary_raster == binary_nodata, np.nan, binary_raster)

if continuous_nodata is not None:
    continuous_raster = np.where(continuous_raster == continuous_nodata, np.nan, continuous_raster)


from rasterio.warp import reproject, Resampling


# Example: Aligning the continuous raster to match the binary raster
aligned_continuous = np.empty_like(binary_raster, dtype=np.float32)  # Ensure it's float for NaN handling
reproject(
    source=continuous_raster,
    destination=aligned_continuous,
    src_transform=continuous_transform,
    dst_transform=binary_transform,
    src_crs=src2.crs,
    dst_crs=src1.crs,
    resampling=Resampling.nearest,
    src_nodata=continuous_nodata,  # Handle NoData in source
    dst_nodata=binary_nodata,      # Propagate NoData to destination
)

aligned_continuous = np.where(binary_raster == binary_nodata, binary_nodata, aligned_continuous)

# Define the output path for the reprojected raster
output_path = os.path.join(input_dir, 'reproj_cont_raster.tif')

# Open the output file in write mode and save the reprojected raster
with rasterio.open(output_path, 'w', driver='GTiff',
                   count=1, dtype=aligned_continuous.dtype,
                   width=aligned_continuous.shape[1], height=aligned_continuous.shape[0],
                   crs=src1.crs, transform=binary_transform, nodata=binary_nodata) as dst:
    dst.write(aligned_continuous, 1)  # Write data to the first band

print(f"Reprojected raster saved as: {output_path}")

# Flatten arrays
binary_flat = binary_raster.flatten()
df_binary_describe = pd.DataFrame(binary_flat)
print(df_binary_describe.describe())

continuous_flat = continuous_raster.flatten()
df_cont_describe = pd.DataFrame(continuous_flat)
print(df_cont_describe.describe())

# Filter out NaN values
binary_values = binary_flat
continuous_values = continuous_flat

from scipy.stats import pearsonr, spearmanr, kendalltau, pointbiserialr

# Pearson correlation
pearson_corr, p_value = pearsonr(binary_values, continuous_values)

# Spearman correlation
spearman_corr, p_value_spearman = spearmanr(binary_values, continuous_values)

kendall_corr, p_value_kendall = kendalltau(binary_values, continuous_values)
point_biserial_corr, p_value_pb = pointbiserialr(binary_values, continuous_values)


print(f"Pearson Correlation: {pearson_corr}, p-value: {p_value}")
print(f"Spearman Correlation: {spearman_corr}, p-value: {p_value_spearman}")
print(f"Kendall Tau Correlation: {kendall_corr}, p-value: {p_value_kendall}")
print(f"Point-Biserial Correlation: {point_biserial_corr}, p-value: {p_value_pb}")


import matplotlib.pyplot as plt

# Scatter plot
plt.scatter(binary_values, continuous_values, alpha=0.5)
plt.xlabel(lulc)
plt.ylabel(factor)
plt.title("Scatter Plot of Raster Correlation")
plt.show()