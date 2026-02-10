import sys
import time
import hailo

# -----------------------------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------------------------
try:
    from hailo_apps.python.pipeline_apps.detection.detection_pipeline import GStreamerDetectionApp
    from hailo_apps.python.core.common.hailo_logger import get_logger
    from hailo_apps.python.core.gstreamer.gstreamer_app import app_callback_class
except ImportError:
    print("Error: Could not import hailo_apps. Did you run ./run_app.sh?")
    sys.exit(1)

hailo_logger = get_logger(__name__)

# -----------------------------------------------------------------------------------------------
# 2. Custom Logic with FPS Calculation
# -----------------------------------------------------------------------------------------------
class PocketAI_Callback(app_callback_class):
    def __init__(self):
        super().__init__()
        # Variables for FPS calculation
        self.frame_count = 0
        self.start_time = time.time()
        self.fps = 0.0

def app_callback(element, buffer, user_data):
    """
    Runs on every frame.
    """
    if buffer is None:
        return

    # --- FPS CALCULATION ---
    user_data.frame_count += 1
    # Update FPS every 30 frames to avoid jitter
    if user_data.frame_count % 30 == 0:
        end_time = time.time()
        duration = end_time - user_data.start_time
        if duration > 0:
            user_data.fps = 30.0 / duration
        user_data.start_time = end_time # Reset timer
    # -----------------------

    # Get the detections
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    # Gather found objects
    found_objects = []
    for detection in detections:
        label = detection.get_label()
        confidence = detection.get_confidence()
        
        # Filter noise
        if confidence > 0.50:
            found_objects.append(f"{label} ({confidence:.0%})")

    # Print Status (FPS + Objects)
    # We use \r to overwrite the line so it looks like a clean dashboard
    objects_str = ", ".join(found_objects) if found_objects else "Scanning..."
    print(f"\rFPS: {user_data.fps:.1f} | Visible: {objects_str} " + " "*20, end="", flush=True)

    return

# -----------------------------------------------------------------------------------------------
# 3. Main
# -----------------------------------------------------------------------------------------------
def main():
    print("Starting Pocket AI...")
    
    user_data = PocketAI_Callback()
    
    # Initialize the app
    app = GStreamerDetectionApp(app_callback, user_data)
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == "__main__":
    main()