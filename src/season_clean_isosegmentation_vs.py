import os
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from skimage.morphology import remove_small_objects, remove_small_holes, opening, rectangle
from skimage.measure import label, regionprops

# 1. Reference image
ref_image_path = "C:/Users/monic/Downloads/19_clipped.tif"

# 2. Output directory for realigned bands
ndvi_output_dir = "C:/Users/monic/Downloads/season_clean_ndvi/"
os.makedirs(ndvi_output_dir, exist_ok=True)

# 3. Sentinel-2 band folders for april-august + ndvi bands
date_folders = {
    "20190403": "C:/Users/monic/Downloads/2019 Sentinel-2 Bands/4 - April/S2B_17TLJ_20190403_1_L2A",
    "20190508": "C:/Users/monic/Downloads/2019 Sentinel-2 Bands/5 - May/S2A_17TLJ_20190508_1_L2A",
    "20190627": "C:/Users/monic/Downloads/2019 Sentinel-2 Bands/6 - June/S2A_17TLJ_20190627_1_L2A",
    "20190714": "C:/Users/monic/Downloads/2019 Sentinel-2 Bands/7 - July/S2A_17TLJ_20190714_L2A",
    "20190801": "C:/Users/monic/Downloads/2019 Sentinel-2 Bands/8 - August/S2B_17TLJ_20190801_1_L2A"
}

B04 = "B04.tif" # red
B08 = "B08.tif" # nir

# 4. Load reference image
with rasterio.open(ref_image_path) as ref:
    ref_crs = ref.crs
    ref_transform = ref.transform
    ref_width = ref.width
    ref_height = ref.height
    ref_profile = ref.profile.copy()

# 5. Function to align other sentinel images and bands to reference image (July)
def align_band(input_path, output_path):
    with rasterio.open(input_path) as src:
        output_meta = src.meta.copy()
        output_meta.update({
            "crs": ref_crs,
            "transform": ref_transform,
            "width": ref_width,
            "height": ref_height
        })
        with rasterio.open(output_path, "w", **output_meta) as dst:
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=ref_transform,
                dst_crs=ref_crs,
                resampling=Resampling.bilinear
            )

# 6. Function to compute NDVI for all months
def compute_ndvi(red_path, nir_path, out_path):
    with rasterio.open(red_path) as red_src, rasterio.open(nir_path) as nir_src:
        red = red_src.read(1).astype(np.float32)
        nir = nir_src.read(1).astype(np.float32)
        ndvi = (nir - red) / (nir + red + 1e-10)
        ndvi[np.isnan(ndvi)] = 0 # If pixel is NaN, then 0
        profile = red_src.profile.copy()
        profile.update(dtype=rasterio.float32, count=1)
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(ndvi, 1)

# 7. Align red and NIR bands
for date in sorted(date_folders.keys()):
    folder = date_folders[date]
    red_input = os.path.join(folder, B04)
    nir_input = os.path.join(folder, B08)

    red_aligned = os.path.join(ndvi_output_dir, f"aligned_B04_{date}.tif")
    nir_aligned = os.path.join(ndvi_output_dir, f"aligned_B08_{date}.tif")

    align_band(red_input, red_aligned)
    align_band(nir_input, nir_aligned)

# 8. Load and align SWIR bands (July) for road and building filtering
swir_path = os.path.join(date_folders["20190714"], "B11.tif")
swir2_path = os.path.join(date_folders["20190714"], "B12.tif")
aligned_swir = os.path.join(ndvi_output_dir, "aligned_B11_20190714.tif")
aligned_swir2 = os.path.join(ndvi_output_dir, "aligned_B12_20190714.tif")
align_band(swir_path, aligned_swir)
align_band(swir2_path, aligned_swir2)

with rasterio.open(aligned_swir) as swir_src, rasterio.open(aligned_swir2) as swir2_src:
    swir = swir_src.read(1).astype(np.float32)
    swir2 = swir2_src.read(1).astype(np.float32)

# 9. Build NDVI stack and compute NDVI from aligned bands
ndvi_stack = []
for date in sorted(date_folders.keys()):
    red_aligned = os.path.join(ndvi_output_dir, f"aligned_B04_{date}.tif")
    nir_aligned = os.path.join(ndvi_output_dir, f"aligned_B08_{date}.tif")
    ndvi_output = os.path.join(ndvi_output_dir, f"ndvi_{date}.tif")

    compute_ndvi(red_aligned, nir_aligned, ndvi_output)

    with rasterio.open(ndvi_output) as src:
        ndvi_stack.append(src.read(1))

ndvi_stack = np.stack(ndvi_stack, axis=-1)

# 10. NDVI features to use for cropland mask base - max for max NDVI value and std for difference in NDVI over months
ndvi_max = np.max(ndvi_stack, axis=-1)
ndvi_std = np.std(ndvi_stack, axis=-1)

# 11. Calculate NDBI using July NDVI
dates_sorted = sorted(date_folders.keys())
ndvi_july = ndvi_stack[:, :, dates_sorted.index("20190714")]
ndbi = (swir - ndvi_july) / (swir + ndvi_july + 1e-10)

# 12. Final cropland mask logic
mask = (
    (ndvi_max > 0.25) &
    (ndvi_std > 0.02) &
    (swir > np.percentile(swir, 60)) &
    (swir2 > np.percentile(swir2, 68)) &
    (ndbi > 0)
)

# 13. Morphological cleanup
mask = remove_small_objects(mask.astype(bool), min_size=1000)
mask = remove_small_holes(mask, area_threshold=5000)
mask = mask.astype(np.uint8)

mask = opening(mask, rectangle(3, 6)) # For roads
mask = opening(mask, rectangle(6, 3)) # for roads

# 14. Aspect ratio filtering for thin roads and skinny shapes
labeled_mask = label(mask) # Label connected regions in the mask
new_mask = np.zeros_like(mask, dtype=bool) # Make an empty boolean mask

for region in regionprops(labeled_mask): # Loop thru each connected region in labeled_mask to add/skip objects
    if region.area < 5000: # skips very small fields - not put in new_mask
        continue
    top_row, left_col, bottom_row, right_col = region.bbox # Bounding box in CV image processing - rectangular area drawn around objects
    height = bottom_row - top_row
    width = right_col - left_col
    if height == 0 or width == 0: # Skips pixels, shapes one row tall or one col wide, division by zero errors
        continue
    aspect_ratio = max(height, width) / min(height, width) # If tall and skinny, max()/min() will account
    if aspect_ratio < 15.0: # Skips the skinny shapes - regular fields are typical (1-10)
        new_mask[labeled_mask == region.label] = True

mask = new_mask.astype(np.uint8)

# 15. Save final mask
output_path = "C:/Users/monic/Downloads/season_clean_cropland_mask.tif"
mask_profile = ref_profile.copy()
mask_profile.update(dtype=rasterio.uint8, count=1)

with rasterio.open(output_path, "w", **mask_profile) as dst:
    dst.write(mask, 1)

print(f"Saved season_clean cropland mask to: {output_path}")
