
## Satellite Image Field Boundary Identification (FBI) and Field Acreage Calculation (FAC) using Computer Vision

Project Goals

- Identify Field Boundaries in Sentinel 2 data.

- Calculate field acreage using the boundaries above.

## Setup

Setup Hopper -

Request account, finish tutorials to activate account: https://wiki.orc.gmu.edu/mkdocs/Getting_an_ORC_Account/

Use ORC documentation as source of truth: https://wiki.orc.gmu.edu/mkdocs/Hopper_Quick_Start_Guide/



Setup Cyberduck -

To run our code, the code needs to exist on Hopper. Cyberduck is an user interface that makes managing files in your directory on Hopper easier.

Download: https://cyberduck.io/download/

Click "Open Connection" -> Select SFTP -> Server: hopper.orc.gmu.edu -> Enter username and password -> will see directory /home/[NetID] (this is where your files are stored)


Setup in VSCode -

https://wiki.orc.gmu.edu/mkdocs/Running_VSCode/#installing-the-remote-development-extension-in-vscode







## Useful Commands

```
ssh [NetID]@hopper.orc.gmu.edu     # Connect to Hopper
module load python               # Load Python environment
module list                     # Show loaded modules

# Start interactive session (most common way, more parameters can be added based on needs)
salloc --ntasks=1 --nodes=1 --partition=normal --time=1:00:00

# Job information
squeue -u ldai2                 # View your jobs
sacct -X                        # View job history
scancel <job_id>               # Cancel a job
exit                           # Exit current session

# Submit batch job
sbatch reserve_cores.slurm      # Submit a job script

pip list --user                 # List installed packages
pip install --user <package>    # Install new package

# For AWS access
export AWS_NO_SIGN_REQUEST=YES  # Enable public AWS access

# Run Jupyter notebook
ipython your_notebook.ipynb     # Run notebook from command line

# List S3 contents
aws s3 ls --no-sign-request s3://sentinel-cogs/sentinel-s2-l2a-cogs/[path]
```

## Run Script on Hopper
*** NEVER FORCE A PUSH, IF THERE IS MERGE CONFLICT PLEASE PING THE TEAM ***

1.Connect to Hopper on Cyberduck

2.Copy paste the relevant files in your directory (/home/[NetID])

3. In VSCode -
```
ssh [NetID]@hopper.orc.gmu.edu
salloc --ntasks=1 --nodes=1 --partition=normal --time=1:00:00 --mem=30gb (parameters are example)
module load python
export AWS_NO_SIGN_REQUEST=YES
ipython [script-file-name]
```

If script creates file, file can be found in your directory on Hopper.





