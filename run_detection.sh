#!/bin/bash

# Change to the hailo-apps directory to source the environment setup correctly
cd hailo-apps
source setup_env.sh

# Run the detection app (which is in the parent directory)
# PYTHONPATH includes the parent directory now because we are running from hailo-apps
# but setup_env.sh adds PROJECT_ROOT (hailo-apps) to PYTHONPATH. 
# We need to ensure the parent directory is also in PYTHONPATH or just run it.
# Actually, setup_env.sh adds PWD to PYTHONPATH.
# If we cd into hailo-apps, PWD is .../hailo-apps. 
# That allows importing hailo_apps.
# But detection.py is in ../detection.py
python ../detection.py "$@"
