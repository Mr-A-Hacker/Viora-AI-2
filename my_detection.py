import gi
import sys
import os

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# ---------------------------------------------------------------------------------------
# USER CONFIGURATION
# ---------------------------------------------------------------------------------------
# UPDATE THIS PATH to point to the model file inside your hailo-apps folder
HEF_PATH = "hailo-apps/resources/models/hailo8/yolov8m.hef" 

# Arducam/RPi Camera usually uses libcamerasrc
SOURCE_ELEMENT = "libcamerasrc ! video/x-raw, width=640, height=480, format=NV12"

# ---------------------------------------------------------------------------------------
# PIPELINE SETUP
# ---------------------------------------------------------------------------------------
def get_pipeline_string():
    """
    Constructs the GStreamer pipeline string.
    Flow: Camera -> Resize -> HailoNet (Inference) -> HailoFilter (Post-proc) -> Overlay -> Screen
    """
    # Check if HEF file exists
    if not os.path.exists(HEF_PATH):
        print(f"ERROR: HEF file not found at {HEF_PATH}")
        print("Please check your hailo-apps/resources folder and update HEF_PATH in the script.")
        sys.exit(1)

    pipeline = (
        f'{SOURCE_ELEMENT} ! '
        f'videoscale ! video/x-raw, width=640, height=640 ! '  # Resize to model input size
        f'queue leaky=no max-size-buffers=30 max-size-bytes=0 max-size-time=0 ! '
        
        # Inference (The Brain)
        f'hailonet hef-path={HEF_PATH} ! '
        
        # Post-processing (Decodes the raw numbers into boxes)
        # We use the default libyolo post-processing provided by Hailo
        f'hailofilter so-path=/usr/lib/aarch64-linux-gnu/hailo/tappas/post_processes/libyolo_hailortpp_post.so '
        f'config-path=./hailo-apps/resources/yolov6n.json qos=false ! '
        
        f'queue leaky=no max-size-buffers=30 max-size-bytes=0 max-size-time=0 ! '
        
        # Draw the bounding boxes
        f'hailooverlay ! '
        
        # Display on screen
        f'videoconvert ! fpsdisplaysink video-sink=autovideosink text-overlay=false sync=false'
    )
    return pipeline

# ---------------------------------------------------------------------------------------
# CUSTOM LOGIC (The "Pocket AI" part)
# ---------------------------------------------------------------------------------------
def probe_callback(pad, info, user_data):
    """
    This function runs for EVERY frame. 
    This is where you put your custom logic (e.g., "If person detected, send alert").
    """
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Note: To read actual detection data (classes, boxes) here requires 
    # parsing the GstHailoMeta. This is advanced, but for now, 
    # we just prove the loop is running.
    # print("Frame processed...") 
    
    return Gst.PadProbeReturn.OK

# ---------------------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------------------
def main():
    Gst.init(None)
    
    pipeline_str = get_pipeline_string()
    print(f"Building Pipeline: {pipeline_str}")
    
    pipeline = Gst.parse_launch(pipeline_str)
    
    # Connect to the bus to catch errors
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    
    def bus_call(bus, message, loop):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End-of-stream")
            loop.quit()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}: {debug}")
            loop.quit()
        return True

    loop = GLib.MainLoop()
    bus.connect("message", bus_call, loop)

    # Attach our custom callback (probe) to the inference source pad
    # This allows us to intercept data right after the AI finishes
    hailonet = pipeline.get_by_name("hailonet0") # GStreamer auto-names elements if not named
    if hailonet:
        pad = hailonet.get_static_pad("src")
        pad.add_probe(Gst.PadProbeType.BUFFER, probe_callback, None)

    # Start the pipeline
    pipeline.set_state(Gst.State.PLAYING)
    print("Pocket AI Running... Press Ctrl+C to stop.")
    
    try:
        loop.run()
    except KeyboardInterrupt:
        pass

    # Clean up
    pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    main()