import rasterio
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import MiniBatchKMeans
from rasterio.warp import calculate_default_transform, reproject, Resampling
from skimage.morphology import remove_small_objects, remove_small_holes

# Input and output paths for sentinel-2 image and band processing
image_path = "/home/mlim8/19_clipped.tif"
s2_folder = "/home/mlim8/S2A_17TLJ_20190714_L2A/"
red_band_path = s2_folder + "B04.tif"
nir_band_path = s2_folder + "B08.tif"
swir_band_path = s2_folder + "B11.tif"  # SWIR1 for filtering non-vegetation areas
swir2_band_path = s2_folder + "B12.tif"  # SWIR2 for filtering out built-up areas like roads and buildings
aligned_red_path = "/home/mlim8/k4whole_aligned_B04.tif"
aligned_nir_path = "/home/mlim8/k4whole_aligned_B08.tif"
aligned_swir_path = "/home/mlim8/k4whole_aligned_B11.tif"
aligned_swir2_path = "/home/mlim8/k4whole_aligned_B12.tif"
ndvi_path = "/home/mlim8/k4whole_NDVI.tif"
output_path = "/home/mlim8/k4whole_segmented_cropland.tif"

# Load 19_clipped.tif to get spatial reference
with rasterio.open(image_path) as src:
    ref_crs = src.crs
    ref_transform = src.transform
    ref_width, ref_height = src.width, src.height
    profile = src.profile.copy()

# Function to align a band to 19_clipped.tif
def align_band(input_band_path, output_band_path):
    with rasterio.open(input_band_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, ref_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update({"crs": ref_crs, "transform": ref_transform, "width": ref_width, "height": ref_height})
        
        with rasterio.open(output_band_path, "w", **kwargs) as dst:
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=ref_transform,
                dst_crs=ref_crs,
                resampling=Resampling.bilinear
            )

# Align Red, NIR, SWIR1, and SWIR2 bands
align_band(red_band_path, aligned_red_path)
align_band(nir_band_path, aligned_nir_path)
align_band(swir_band_path, aligned_swir_path)
align_band(swir2_band_path, aligned_swir2_path)

# Compute NDVI
with rasterio.open(aligned_red_path) as red_src, rasterio.open(aligned_nir_path) as nir_src:
    red = red_src.read(1).astype(np.float32)
    nir = nir_src.read(1).astype(np.float32)
    ndvi = (nir - red) / (nir + red + 1e-10)
    ndvi[np.isnan(ndvi)] = 0
    
    profile.update(dtype=rasterio.float32, count=1)
    with rasterio.open(ndvi_path, "w", **profile) as dst:
        dst.write(ndvi, 1)

# Load SWIR1 and SWIR2 bands for filtering
with rasterio.open(aligned_swir_path) as swir_src, rasterio.open(aligned_swir2_path) as swir2_src:
    swir = swir_src.read(1).astype(np.float32)
    swir2 = swir2_src.read(1).astype(np.float32)

# Compute NDBI (normalized difference built-up index - filters developed/built-up urban areas)
ndbi = (swir - nir) / (swir + nir + 1e-10)

# Apply NDVI + SWIR1 + SWIR2 + NDBI filtering
cropland_mask = (ndvi >= 0.45) & (swir < np.percentile(swir, 75)) & (swir2 < np.percentile(swir2, 80)) & (ndbi < 0)  # Remove built-up areas

# Apply morphological filtering to remove small holes
cropland_mask = remove_small_holes(cropland_mask, area_threshold=5000)

# Extract cropland pixels
cropped_ndvi = ndvi[cropland_mask]

# Flatten cropped data for clustering
features = cropped_ndvi.reshape(-1, 1)

# Normalize features (ndvi)
scaler = MinMaxScaler()
features_scaled = scaler.fit_transform(features)

# Apply Mini-Batch K-means clustering
kmeans = MiniBatchKMeans(n_clusters=4, batch_size=10000, random_state=42)
labels = kmeans.fit_predict(features_scaled)

# Reconstruct segmented tile, keeping only cropland
segmented_tile = np.zeros_like(ndvi, dtype=np.uint8)
segmented_tile[cropland_mask] = labels + 1

# Apply morphological filtering to remove small objects
segmented_tile = remove_small_objects(segmented_tile.astype(bool), min_size=1000).astype(np.uint8)


# Save the segmented cropland .tif output
profile.update(dtype=rasterio.uint8, count=1, height=segmented_tile.shape[0], width=segmented_tile.shape[1])

with rasterio.open(output_path, 'w', **profile) as dst:
    dst.write(segmented_tile.astype(rasterio.uint8), 1)

print(f"Segmented cropland saved: {output_path}")
