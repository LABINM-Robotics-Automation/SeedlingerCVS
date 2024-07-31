#!/bin/bash
source /home/robot/miniconda3/etc/profile.d/conda.sh

cd /home/robot/seedlinger/SeedlingerCVS
conda activate seedlinger

/home/robot/miniconda3/envs/seedlinger/bin/python server_im_calidad.py