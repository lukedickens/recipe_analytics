#!/bin/bash -l

# Batch script to run an array job under SGE and 
#  transfer the output to Scratch from local.

# Request wallclock time (format hours:minutes:seconds).
#$ -l h_rt=02:00:0

# Request 16 gigabyte of RAM (must be an integer followed by M, G, or T)
#$ -l mem=16G

# Request 10 gigabyte of TMPDIR space (default is 10 GB - remove if cluster is diskless)
#$ -l tmpfs=10G


# Request 1 cores
#$ -pe smp 1

# Set the name of the job.
#$ -N recipe_json_preprocessing

# Set the working directory to somewhere in your scratch space.
# Replace "<your_UCL_id>" with your UCL user ID :)
#$ -wd /home/uczclwf/Scratch/substitution_database_local

# Load the related modules (standard libraries)
module -f unload compilers mpi gcc-libs
module load beta-modules
module load gcc-libs/10.2.0
module load python3/3.9-gnu-10.2.0
module load cuda/11.3.1/gnu-10.2.0
module load cudnn/8.2.1.32/cuda-11.3
module load pytorch/1.11.0/gpu

# Change directories to the location of your script
cd $HOME/Scratch/substitution_database_local

# Activate the virtual environment
# (to make your pip installed libraries available)
source $HOME/virtualenvs/substitution_database/bin/activate

# Run the script
python3 recipe_json_preprocessing.py
