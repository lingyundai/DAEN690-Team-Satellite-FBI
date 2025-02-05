# DAEN690-Team-Satellite-FBI
Satellite Image Field Boundary Identification (FBI) and Field Acreage Calculation (FAC) Using Computer Vision 


Project Goals 

1.Identify Field Boundaries in Sentinel 2 data. 

2.Calculate field acreage using the boundaries above. 



# Working with Hopper and Sentinel-2 Data

## Connecting to Hopper
```bash
ssh [netID]@hopper.orc.gmu.edu
```

## Basic Module Management
```bash
# Load required modules
module load gnu10
module load python

# View currently loaded modules
module list
```

## Slurm Commands for Job Management

### Resource Information
```bash
# View available resources
sinfo

# View your job information
squeue -u [netID]
squeue --me
```

### Job Control
```bash

# Request interactive session
salloc --ntasks=1 --nodes=1 --partition=normal --time=1:00:00

# For GPU nodes
# Use partition=gpuq 

# View job details
sacct -X
seff job_id

# Cancel a running job
scancel job_id

# Exit job/session
exit
```


## Package Management
```bash
# Always load Python module first
module load python

# List installed packages
pip list --user

# Install new packages
pip install --user <package_name>
```

## Running Scripts
```bash
# Set AWS environment variable for public access
export AWS_NO_SIGN_REQUEST=YES

# Run Jupyter notebook
ipython [script_name]

# Suspend process
ctrl+z
```

## Working with AWS S3 Sentinel-2 Data

### Accessing Sentinel-2 Data
The data is stored in the following structure:
```
s3://sentinel-cogs/sentinel-s2-l2a-cogs/[zone]/[latitude]/[longitude]/[year]/[month]/[scene]/
```

### Available Files in Each Scene
- **AOT.tif**: Aerosol Optical Thickness
- **B01-B12.tif**: Different spectral bands
  - B02, B03, B04, B08: 10m resolution
  - B05, B06, B07, B8A, B11, B12: 20m resolution
  - B01, B09: 60m resolution
- **L2A_PVI.tif**: Vegetation Index
- **SCL.tif**: Scene Classification Layer
- **TCI.tif**: True Color Image
- **WVP.tif**: Water Vapor
- **Metadata files**:
  - granule_metadata.xml
  - tileinfo_metadata.json
  - [scene_name].json

### Example AWS S3 Commands
```bash
# List contents of a directory
aws s3 ls --no-sign-request s3://sentinel-cogs/sentinel-s2-l2a-cogs/[path]

# Example path
s3://sentinel-cogs/sentinel-s2-l2a-cogs/9/D/VA/2021/3/S2B_9DVA_20210323_1_L2A/
```
