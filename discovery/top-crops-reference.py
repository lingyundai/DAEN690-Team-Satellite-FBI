# 1. Make sure usda cdl 2023 data is downloaded and unzipped
# 2. Download and unzip the michigan shapefile (tl_2023_26063_edges) from https://catalog.data.gov/dataset/tiger-line-shapefile-2023-county-huron-county-mi-all-lines
# 3. Running code should generate a .csv sheet in your downloads folder
# 4. Once you've generated the excel sheet, use the crop metadata in unzipped file to identify crops

import rasterio
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.mask import mask

# File paths for cdl and michigan shapefile
cdl_path = "C:/Users/monic/Downloads/2023_30m_cdls/2023_30m_cdls.tif"
shapefile_path = "C:/Users/monic/Downloads/tl_2023_26063_edges/tl_2023_26063_edges.shp"



# Load the shapefile and drop TFIDL column
gdf = gpd.read_file(shapefile_path).drop(columns=["TFIDL"], errors="ignore")

# Check coordinate system mismatch + convert shapefile to match raster crs
with rasterio.open(cdl_path) as src:
    if gdf.crs != src.crs:
        gdf = gdf.to_crs(src.crs)

# Filter for Huron County's unique county code (FIPS = 063)
huron_county = gdf[gdf['COUNTYFP'] == '063']

# Save filtered shapefile
huron_county.to_file("C:/Users/monic/Downloads/huron_county.shp")



# Open USDA CDL Raster
with rasterio.open(cdl_path) as src:
    out_image, out_transform = mask(src, huron_county.geometry, crop=True)
    cdl_array = out_image[0]

# Count unique crop counts in Huron County
unique, counts = np.unique(cdl_array, return_counts=True)
crop_counts = pd.DataFrame({"Crop_Code": unique, "Pixel_Count": counts})

# Outline valid crop codes (1-55, 56-65, 78-203) - specifically cropland and not general land
valid_crop_codes = crop_counts["Crop_Code"].isin(range(1, 56)) | \
                   crop_counts["Crop_Code"].isin(range(66, 78)) | \
                   crop_counts["Crop_Code"].isin(range(204, 255))

crop_counts = crop_counts[valid_crop_codes]



# Sort & get top 5 crops (to change to top 10, 15, etc. just edit head)
top_crops = crop_counts.sort_values("Pixel_Count", ascending=False).head(5)

# Save to CSV
top_crops.to_csv("C:/Users/monic/Downloads/huron_top_crops.csv", index=False)