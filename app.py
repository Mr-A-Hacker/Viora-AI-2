import sys
import os

# -----------------------------------------------------------------------------------------------
# 1. Imports from Hailo Apps
# -----------------------------------------------------------------------------------------------
# We need these to access the pre-built pipeline tools
try:
    import hailo
    from hailo_apps.python.pipeline_apps.detection.detection_pipeline import GStreamerDetectionApp
    from hailo_apps.python.core.common.hailo_logger import get_logger
    from hailo_apps.python.core.gstreamer.gstreamer_app import app_callback_class
except ImportError:
    print("Error: Could not import hailo_apps. Did you run ./run_app.sh?")
    sys.exit(1)

# Logger setup
hailo_logger = get_logger(__name__)

# -----------------------------------------------------------------------------------------------
# 2. Define Your Custom Logic
# -----------------------------------------------------------------------------------------------
class PocketAI_Callback(app_callback_class):
    """
    This class holds data you want to keep between frames.
    """
    def __init__(self):
        super().__init__()
        self.person_count = 0

def app_callback(element, buffer, user_data):
    """
    This function runs on EVERY frame processed by the AI.
    """
    if buffer is None:
        return

    # 1. Get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    # 2. Process detections (Your Custom Logic)
    current_frame_people = 0
    for detection in detections:
        label = detection.get_label()
        confidence = detection.get_confidence()
        
        if label == "person" and confidence > 0.5:
            current_frame_people += 1
            # You can add logic here: e.g., "If person detected, turn on LED"
            # print(f"Person detected! Confidence: {confidence:.2f}")

    # 3. Print status only if it changes (to avoid spamming console)
    if current_frame_people != user_data.person_count:
        user_data.person_count = current_frame_people
        print(f"Pocket AI Status: I see {user_data.person_count} person(s).")

    return

# -----------------------------------------------------------------------------------------------
# 3. Main Application Entry Point
# -----------------------------------------------------------------------------------------------
def main():
    print("Initializing Pocket AI Pipeline...")
    
    # Initialize your custom data holder
    user_data = PocketAI_Callback()
    
    # Create the App using Hailo's pre-built class
    # This automatically handles camera inputs, threading, and resizing!
    app = GStreamerDetectionApp(app_callback, user_data)
    
    print("Running! Press Ctrl+C to stop.")
    app.run()

if __name__ == "__main__":
    main()