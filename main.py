import sys
import os

# Add the hailo-apps directory to the system path to allow imports
# This assumes main.py is in /home/pocket-ai/Documents/pocket-ai/
# and the hailo-apps repo is in /home/pocket-ai/Documents/pocket-ai/hailo-apps/
current_dir = os.path.dirname(os.path.abspath(__file__))
hailo_apps_path = os.path.join(current_dir, "hailo-apps")
if hailo_apps_path not in sys.path:
    sys.path.append(hailo_apps_path)

# Import the main function from the existing detection.py script
from hailo_apps.python.pipeline_apps.detection.detection import main as detection_main

if __name__ == "__main__":
    # Run the detection application
    # Command line arguments (like --input, --show-fps) are passed through automatically
    detection_main()