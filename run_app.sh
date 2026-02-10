#!/bin/bash

# 1. Define where the hailo-apps repo is
REPO_DIR="./hailo-apps"

# 2. Activate the virtual environment
if [ -f "$REPO_DIR/venv_hailo_apps/bin/activate" ]; then
    source "$REPO_DIR/venv_hailo_apps/bin/activate"
else
    echo "Error: Could not find virtual environment in $REPO_DIR/venv_hailo_apps/"
    exit 1
fi

# 3. Add the hailo-apps folder to Python's search path
export PYTHONPATH=$PYTHONPATH:$(pwd)/$REPO_DIR

# --- AUTOFOCUS PATCH START ---
# Dynamically locate the gstreamer_app.py file inside the venv
TARGET_FILE=$(python -c "import hailo_apps.python.core.gstreamer.gstreamer_app as app; print(app.__file__)")

# Check if the file exists and hasn't been patched yet
if [ -f "$TARGET_FILE" ]; then
    if ! grep -q "AfMode" "$TARGET_FILE"; then
        echo "🔧 Patching Hailo library to enable Autofocus..."
        # Safely replace the FrameRate control with FrameRate + AfMode
        sed -i 's/"FrameRate": 30/"FrameRate": 30, "AfMode": 2/' "$TARGET_FILE"
        echo "✅ Patch applied!"
    else
        echo "⚡ Autofocus already enabled."
    fi
else
    echo "⚠️ Warning: Could not find gstreamer_app.py to patch."
fi
# --- AUTOFOCUS PATCH END ---

# 4. Run your custom application
echo "Starting Pocket AI..."
python object_detection.py --input rpi