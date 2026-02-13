#!/bin/bash

# Change the directory to hailo-apps to correctly source the environment
cd hailo-apps
source setup_env.sh

# Cleanup any existing process on port 8000
echo "Ensuring port 8000 is free..."
fuser -k 8000/tcp 2>/dev/null || true

# Run the app.py which is in the parent directory
# PYTHONPATH is set by setup_env.sh to include the current dir (hailo-apps).
# We need to make sure python can find app.py and imports.
python ../app.py "$@"
