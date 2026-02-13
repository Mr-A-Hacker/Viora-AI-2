import sys
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib
import cv2
import hailo
import multiprocessing
import queue

from hailo_apps.python.core.common.hailo_logger import get_logger
from hailo_apps.python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.python.pipeline_apps.detection.detection_pipeline import GStreamerDetectionApp
from hailo_apps.python.core.gstreamer.gstreamer_helper_pipelines import (
    SOURCE_PIPELINE,
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    TRACKER_PIPELINE,
    USER_CALLBACK_PIPELINE,
    DISPLAY_PIPELINE,
)
from hailo_apps.python.core.common.buffer_utils import get_numpy_from_buffer

hailo_logger = get_logger(__name__)

# -----------------------------------------------------------------------------------------------
# Robust get_caps_from_pad implementation
# -----------------------------------------------------------------------------------------------
def robust_get_caps_from_pad(pad: Gst.Pad):
    """
    Robustly extracts width, height, and format from the GStreamer pad caps.
    Handles different structure objects returned by GStreamer bindings.
    """
    caps = pad.get_current_caps()
    if not caps:
        hailo_logger.warning("No caps found on pad.")
        return None, None, None

    structure = caps.get_structure(0)
    if not structure:
        return None, None, None

    width, height, format = None, None, None

    try:
        # Try different ways to access structure fields
        if hasattr(structure, 'get_value'):
            format = structure.get_value("format")
            width = structure.get_value("width")
            height = structure.get_value("height")
        elif hasattr(structure, 'get_string') and hasattr(structure, 'get_int'):
            # Some bindings use get_string/get_int
            success_w, width = structure.get_int("width")
            success_h, height = structure.get_int("height")
            if not success_w or not success_h:
                 # Try property access if get_int fails
                 width = structure.width if hasattr(structure, "width") else None
                 height = structure.height if hasattr(structure, "height") else None
            
            format = structure.get_string("format")
            if not format and hasattr(structure, "format"):
                format = structure.format
        else:
            # Fallback to direct attribute access (common in some gi versions)
            if hasattr(structure, "width"): width = structure.width
            if hasattr(structure, "height"): height = structure.height
            if hasattr(structure, "format"): format = structure.format

        # Sanity check and fallback parsing if needed
        if width is None or height is None:
             import re
             caps_str = caps.to_string()
             w_match = re.search(r'width=\(int\)(\d+)', caps_str)
             h_match = re.search(r'height=\(int\)(\d+)', caps_str)
             f_match = re.search(r'format=\(string\)([A-Z0-9]+)', caps_str)
             if w_match: width = int(w_match.group(1))
             if h_match: height = int(h_match.group(1))
             if f_match: format = f_match.group(1)

        return format, width, height
    except Exception as e:
        hailo_logger.error(f"Error parsing caps: {e}")
        return None, None, None

import threading
import time
import copy

# -----------------------------------------------------------------------------------------------
# Shared State for Integration
# -----------------------------------------------------------------------------------------------
class SharedState:
    def __init__(self):
        self.frame = None
        self.detections = []
        self.lock = threading.Lock()

    def update(self, frame, detections):
        with self.lock:
            self.frame = frame
            self.detections = detections

    def get_latest(self):
        with self.lock:
            return self.frame, self.detections

shared_state = SharedState()

# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.use_frame = True # Force frame usage for integration

# -----------------------------------------------------------------------------------------------
# User-defined callback function
# -----------------------------------------------------------------------------------------------
def app_callback(element, buffer, user_data):
    if buffer is None:
        return Gst.PadProbeReturn.OK

    pad = element.get_static_pad("src")
    format, width, height = robust_get_caps_from_pad(pad)
    
    # DEBUG: Print caps info occasionally
    print(f"DEBUG: app_callback detected caps: Fmt={format}, W={width}, H={height}")

    frame = None
    if user_data.use_frame and format is not None and width is not None and height is not None:
        frame = get_numpy_from_buffer(buffer, format, width, height)
    else:
        # Check if we are failing to get caps
        if user_data.use_frame:
             print(f"WARNING: Missing caps info. Fmt={format}, W={width}, H={height}")

    # Get detections
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    detection_list = []
    for detection in detections:
        label = detection.get_label()
        confidence = detection.get_confidence()
        bbox = detection.get_bbox()
        
        detection_list.append({
            "label": label,
            "confidence": confidence,
            "bbox": [bbox.xmin(), bbox.ymin(), bbox.xmax(), bbox.ymax()]
        })

    # Update shared state
    if frame is not None:
        # NOTE: Frame is RGB. If you need BGR for OpenCV elsewhere, convert it there.
        # For web streaming (MJPEG), RGB is often converted to JPEG which is fine.
        shared_state.update(frame, detection_list)

    return Gst.PadProbeReturn.OK

# -----------------------------------------------------------------------------------------------
# Improved Picamera Thread with Robust Cleanup
# -----------------------------------------------------------------------------------------------
def robust_picamera_thread(pipeline, video_width, video_height, video_format, picamera_config=None):
    hailo_logger.info("robust_picamera_thread started")
    appsrc = pipeline.get_by_name("app_source")
    if appsrc is None:
        hailo_logger.error("app_source not found in pipeline")
        return

    appsrc.set_property("is-live", True)
    appsrc.set_property("format", Gst.Format.TIME)
    
    # Retry mechanism for camera acquisition
    max_retries = 3
    picam2 = None
    
    for attempt in range(max_retries):
        try:
            from picamera2 import Picamera2
            picam2 = Picamera2()
            
            if picamera_config is None:
                # Use a reliable configuration
                main = {"size": (1280, 720), "format": "RGB888"}
                lores = {"size": (video_width, video_height), "format": "RGB888"}
                controls = {"FrameRate": 30}
                config = picam2.create_preview_configuration(main=main, lores=lores, controls=controls)
            else:
                config = picamera_config

            picam2.configure(config)
            picam2.start() 
            hailo_logger.info("Camera acquired and started successfully.")
            break
        except Exception as e:
            hailo_logger.warning(f"Failed to acquire camera (attempt {attempt+1}/{max_retries}): {e}")
            if picam2:
                try:
                    picam2.stop()
                    picam2.close()
                except:
                    pass
                picam2 = None
            time.sleep(1.0) # Wait before retry

    if picam2 is None:
        hailo_logger.error("Could not acquire camera after retries.")
        # Signal error or exit?
        return

    try:
        # Configuration successful, proceed with loop
        lores_stream = config["lores"]
        format_str = "RGB" if lores_stream["format"] == "RGB888" else video_format
        width, height = lores_stream["size"]
        
        appsrc.set_property(
            "caps",
            Gst.Caps.from_string(
                f"video/x-raw, format={format_str}, width={width}, height={height}, framerate=30/1, pixel-aspect-ratio=1/1"
            ),
        )

        frame_count = 0
        while True:
            # Check if app is still running (using global flag or weakref if possible, 
            # but for now we rely on pipeline state)
            
            # Non-blocking capture if possible, but capture_array is blocking.
            # We trust that GStreamer flow return will tell us when to stop.
            try:
                # Add a small timeout to allow checking for exit signals if supported by lib
                # But picamera2 capture_array doesn't support timeout natively in all versions?
                # It waits for a request.
                frame_data = picam2.capture_array("lores")
            except Exception as e:
                hailo_logger.warning(f"Capture error: {e}")
                break

            if frame_data is None:
                hailo_logger.warning("Frame capture returned None")
                break

            frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
            buffer = Gst.Buffer.new_wrapped(frame.tobytes())
            buffer_duration = Gst.util_uint64_scale_int(1, Gst.SECOND, 30)
            buffer.pts = frame_count * buffer_duration
            buffer.duration = buffer_duration
            
            try:
                ret = appsrc.emit("push-buffer", buffer)
                if ret != Gst.FlowReturn.OK:
                    hailo_logger.info(f"Pipeline stopped accepting buffers ({ret}). Stopping camera thread.")
                    break
            except Exception as e:
                hailo_logger.error(f"Error pushing buffer: {e}")
                break

            frame_count += 1
            
    finally:
        hailo_logger.info("Closing camera resources...")
        if picam2:
            try:
                picam2.stop()
                picam2.close()
            except Exception as e:
                hailo_logger.error(f"Error closing camera: {e}")
        hailo_logger.info("Camera thread exited.")


# -----------------------------------------------------------------------------------------------
# Custom GStreamer Application to fix RGB issue and threading/args quirks
# -----------------------------------------------------------------------------------------------
class CustomGStreamerDetectionApp(GStreamerDetectionApp):
    def __init__(self, app_callback, user_data, headless=False):
        # PATCH: Temporarily mock signal.signal to avoid ValueError in thread
        import signal
        original_signal = signal.signal
        
        def mock_signal(sig, handler):
            hailo_logger.warning(f"Skipping signal registration for {sig} in background thread")
        
        signal.signal = mock_signal
        
        self.force_headless = headless
        
        # We still need to clean sys.argv for GStreamerApp if --headless remains
        if "--headless" in sys.argv:
            sys.argv.remove("--headless")

        try:
             super().__init__(app_callback, user_data)
        finally:
             signal.signal = original_signal

    def run(self):
        # Override run to use our robust_picamera_thread
        from hailo_apps.python.core.common.defines import RPI_NAME_I
        
        hailo_logger.debug("Running CustomGStreamerDetectionApp main loop")
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.bus_call, self.loop)

        self._connect_callback()

        hailo_display = self.pipeline.get_by_name("hailo_display")
        if hailo_display is None and not getattr(self.options_menu, "ui", False):
            hailo_logger.warning("hailo_display not found in pipeline")

        # Disable QoS to prevent frame drops
        from hailo_apps.python.core.gstreamer.gstreamer_common import disable_qos
        disable_qos(self.pipeline)

        if self.options_menu.use_frame:
            from hailo_apps.python.core.gstreamer.gstreamer_common import display_user_data_frame
            hailo_logger.debug("Starting display_user_data_frame process")
            display_process = multiprocessing.Process(
                target=display_user_data_frame, args=(self.user_data,)
            )
            display_process.start()

        if self.source_type == RPI_NAME_I:
            hailo_logger.debug("Starting robust_picamera_thread")
            picam_thread = threading.Thread(
                target=robust_picamera_thread,
                args=(self.pipeline, self.video_width, self.video_height, self.video_format),
            )
            self.threads.append(picam_thread)
            picam_thread.start()

        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_latency(self.pipeline_latency * Gst.MSECOND)
        self.pipeline.set_state(Gst.State.PLAYING)

        if self.watchdog_enabled and not self.watchdog_running:
            self.watchdog_running = True
            self.watchdog_thread = threading.Thread(target=self._watchdog_monitor, daemon=True)
            self.watchdog_thread.start()

        if self.options_menu.dump_dot:
            GLib.timeout_add_seconds(3, self.dump_dot_file)

        self.loop.run()

        try:
            hailo_logger.debug("Cleaning up after loop exit")
            self.user_data.running = False
            self.pipeline.set_state(Gst.State.NULL)
            if self.options_menu.use_frame:
                display_process.terminate()
                display_process.join()
            for t in self.threads:
                t.join()
        except Exception as e:
            hailo_logger.error(f"Error during cleanup: {e}")
        finally:
            if self.error_occurred:
                hailo_logger.error("Exiting with error")
                # sys.exit(1) # Do not exit the whole process in thread!
            else:
                hailo_logger.info("Exiting successfully")
                # sys.exit(0)

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(
            video_source=self.video_source,
            video_width=self.video_width,
            video_height=self.video_height,
            frame_rate=self.frame_rate,
            sync=self.sync,
        )
        detection_pipeline = INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.post_process_so,
            post_function_name=self.post_function_name,
            batch_size=self.batch_size,
            config_json=self.labels_json,
            additional_params=self.thresholds_str,
        )
        detection_pipeline_wrapper = INFERENCE_PIPELINE_WRAPPER(detection_pipeline)
        tracker_pipeline = TRACKER_PIPELINE(class_id=1)
        user_callback_pipeline = USER_CALLBACK_PIPELINE()
        
        if self.force_headless:
             display_pipeline = f"fakesink name=hailo_display sync={self.sync}"
        else:
             display_pipeline = DISPLAY_PIPELINE(
                video_sink=self.video_sink, sync=self.sync, show_fps=self.show_fps
            )

        pipeline_string = (
            f"{source_pipeline} ! "
            f"{detection_pipeline_wrapper} ! "
            f"{tracker_pipeline} ! "
            f"videoconvert ! video/x-raw,format=RGB ! "
            f"{user_callback_pipeline} ! "
            f"{display_pipeline}"
        )
        hailo_logger.debug("Pipeline string: %s", pipeline_string)
        return pipeline_string

# -----------------------------------------------------------------------------------------------
# Multiprocessing Support
# -----------------------------------------------------------------------------------------------
detection_process = None
monitor_thread = None
stop_event = multiprocessing.Event()
frame_queue = None

def run_detection_process(frame_queue, stop_event):
    """
    Runs the detection app in a separate process.
    """
    # Set proctitle for easier identification
    try:
        import setproctitle
        setproctitle.setproctitle("pocket-ai-detection")
    except ImportError:
        pass

    hailo_logger.info("Starting Detection Process.")
    
    # Ensure correct args for the process
    if "--input" not in sys.argv:
        sys.argv.extend(["--input", "rpi"])
    
    # DO NOT add --use-frame to sys.argv here.
    # This ensures options_menu.use_frame is False, preventing the display process from spawning
    # inside CustomGStreamerDetectionApp.run().
    # We still get frames in our callback because user_data.use_frame is manually set to True below.

    # Define a custom callback that pushes to the queue
    def process_callback(element, buffer, user_data):
        if buffer is None:
             return Gst.PadProbeReturn.OK

        pad = element.get_static_pad("src")
        format, width, height = robust_get_caps_from_pad(pad)

        frame = None
        # Always capture frame if we have valid format, width, height, regardless of user_data.use_frame
        # This is because we disabled --use-frame to prevent display process from spawning,
        # but we still need frames for the queue.
        if format and width and height:
            frame = get_numpy_from_buffer(buffer, format, width, height)

        # Get detections
        roi = hailo.get_roi_from_buffer(buffer)
        detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

        detection_list = []
        for detection in detections:
            bbox = detection.get_bbox()
            detection_list.append({
                "label": detection.get_label(),
                "confidence": detection.get_confidence(),
                "bbox": [bbox.xmin(), bbox.ymin(), bbox.xmax(), bbox.ymax()]
            })

        if frame is not None:
            # Push to queue (non-blocking, drop if full)
            if not frame_queue.full():
                try:
                    frame_queue.put_nowait((frame, detection_list))
                except queue.Full:
                    pass
            #else:
            #    hailo_logger.warning("Frame queue full. Skipping frame.")
        else:
             hailo_logger.warning(f"Frame is None! Caps: Fmt={format}, W={width}, H={height}, UseFrame={user_data.use_frame}")
        
        return Gst.PadProbeReturn.OK

    # Initialize App
    user_data = user_app_callback_class()
    user_data.use_frame = True # Explicitly enable frame capture for callback
    app = CustomGStreamerDetectionApp(process_callback, user_data, headless=True)

    # Monitor thread to check stop_event and quit loop gracefully
    def monitor_stop_signal():
        while True:
            if stop_event.is_set():
                hailo_logger.info("Stop event received in process. Shutting down app.")
                # Call shutdown from the main loop thread to avoid signal issues
                GLib.idle_add(app.shutdown)
                break
            time.sleep(0.5)

    stop_monitor = threading.Thread(target=monitor_stop_signal, daemon=True)
    stop_monitor.start()

    # Run Loop
    try:
        app.run()
    except Exception as e:
        hailo_logger.error(f"Process Exception: {e}")
    finally:
        hailo_logger.info("Detection Process Exiting.")

def monitor_queue_loop(q):
    """
    Reads from the multiprocessing queue and updates shared_state.
    Runs in a thread in the MAIN process.
    """
    hailo_logger.info("Queue monitor thread started.")
    while True:
        try:
            # verify process is alive
            if detection_process is None or not detection_process.is_alive():
                break
            
            try:
                # Timeout allows checking liveness
                frame, detections = q.get(timeout=1.0) 
                shared_state.update(frame, detections)
            except queue.Empty:
                hailo_logger.debug("Monitor queue empty.")
                continue
        except Exception as e:
            hailo_logger.error(f"Monitor error: {e}")
            break
    hailo_logger.info("Queue monitor thread exited.")

# Track active users to handle React Strict Mode and rapid navigation
ref_count = 0
shutdown_timer = None
session_lock = threading.Lock()

def start_detection(session_id=None):
    """
    Starts the detection process if not already running.
    Increments a reference count to track active sessions.
    """
    global detection_process, monitor_thread, frame_queue, ref_count, shutdown_timer
    
    with session_lock:
        ref_count += 1
        hailo_logger.info(f"Start requested (session_id={session_id}). Ref count: {ref_count}")
        
        # Cancel any pending shutdown if a new user arrives
        if shutdown_timer is not None:
            hailo_logger.info("Cancelling pending shutdown.")
            shutdown_timer.cancel()
            shutdown_timer = None

    # If process is ALIVE, just return the existing shared state
    if detection_process is not None and detection_process.is_alive():
        hailo_logger.info("Detection process is already running.")
        return shared_state

    hailo_logger.info("Spawning detection process...")
    
    # Reset communication primitives
    stop_event.clear()
    frame_queue = multiprocessing.Queue(maxsize=2)
    
    # Spawn Process
    # daemon=False to allow potential child processes (legacy display app logic)
    detection_process = multiprocessing.Process(
        target=run_detection_process, 
        args=(frame_queue, stop_event),
        daemon=False
    )
    detection_process.start()
    
    # Start Monitor Thread in parent process to update shared_state
    monitor_thread = threading.Thread(
        target=monitor_queue_loop, 
        args=(frame_queue,), 
        daemon=True
    )
    monitor_thread.start()
    
    return shared_state

def stop_detection(session_id=None):
    """
    Decrements reference count. If 0, schedules a delayed shutdown.
    """
    global ref_count, shutdown_timer
    
    with session_lock:
        if ref_count > 0:
            ref_count -= 1
        hailo_logger.info(f"Stop requested (session_id={session_id}). Ref count: {ref_count}")
        
        if ref_count == 0:
            hailo_logger.info("No active users. Scheduling immediate shutdown (100ms)...")
            if shutdown_timer is not None:
                shutdown_timer.cancel()
            shutdown_timer = threading.Timer(0.1, perform_actual_shutdown)
            shutdown_timer.start()
    
    return True

def perform_actual_shutdown():
    """
    Actually kills the process. Called by the shutdown_timer.
    """
    global detection_process, frame_queue, shutdown_timer
    
    with session_lock:
        # Re-check ref_count in case someone started while we were waiting
        if ref_count > 0:
            hailo_logger.info("Shutdown aborted: ref_count increased while waiting.")
            return

        hailo_logger.info("Performing actual shutdown of detection process...")
        
        # Signal graceful exit via stop_event
        stop_event.set()
        
        if detection_process and detection_process.is_alive():
            # Wait for graceful exit
            detection_process.join(timeout=5.0)
            
            if detection_process.is_alive():
                 hailo_logger.warning("Process did not exit gracefully; terminating.")
                 detection_process.terminate()
                 detection_process.join(timeout=2.0)
                 
                 if detection_process.is_alive():
                    hailo_logger.warning("Process did not terminate; killing.")
                    detection_process.kill()
                    detection_process.join()
                
        hailo_logger.info("Detection process stopped.")
        
        detection_process = None
        frame_queue = None
        shutdown_timer = None

def main():
    # Standalone run
    hailo_logger.info("Starting Custom Detection App (Standalone).")
    
    if "--input" not in sys.argv:
        sys.argv.extend(["--input", "rpi"])

    user_data = user_app_callback_class()
    app = CustomGStreamerDetectionApp(app_callback, user_data)
    app.run()

if __name__ == "__main__":
    main()
