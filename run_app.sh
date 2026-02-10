#!/bin/bash

# 1. Define where the hailo-apps repo is
REPO_DIR="./hailo-apps"

# 2. Activate the virtual environment directly
# (This fixes the "directory not found" error)
if [ -f "$REPO_DIR/venv_hailo_apps/bin/activate" ]; then
    source "$REPO_DIR/venv_hailo_apps/bin/activate"
else
    echo "Error: Could not find virtual environment in $REPO_DIR/venv_hailo_apps/"
    exit 1
fi

# 3. Add the hailo-apps folder to Python's search path
# (This allows you to do: from hailo_apps.python... import ...)
export PYTHONPATH=$PYTHONPATH:$(pwd)/$REPO_DIR

# 4. Run your custom application
# We pass --input rpi to force it to try the Raspberry Pi camera
echo "Starting Pocket AI..."
python app.py --input rpi