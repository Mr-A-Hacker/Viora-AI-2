import time
import cv2
import numpy as np
from picamera2 import Picamera2, Preview
from picamera2.devices import Hailo

# --- CONFIGURATION ---
# We use the exact same model file that 'rpicam-still' was using in the background.
# The JSON you used points to this specific file for the Hailo-8L.
MODEL_FILE = "/usr/share/hailo-models/yolov8s.hef" 

# --- PARSING FUNCTION ---
# The Hailo-8L outputs data in a specific format. This function extracts the boxes.
def extract_detections(results, width, height, threshold=0.5):
    detections = []
    # The Picamera2 Hailo wrapper returns a dictionary or list depending on the model
    # For the official YOLOv8 model, it returns a list of detection objects.
    
    for detection in results:
        # Each detection has: [ymin, xmin, ymax, xmax, score, class_id]
        # or it is an object with attributes. The wrapper standardizes this:
        score = detection['score']
        if score < threshold:
            continue

        # Coordinates are normalized (0.0 to 1.0)
        ymin, xmin, ymax, xmax = detection['ymin'], detection['xmin'], detection['ymax'], detection['xmax']
        label = detection['label']
        
        # Convert to pixels
        x0 = int(xmin * width)
        y0 = int(ymin * height)
        x1 = int(xmax * width)
        y1 = int(ymax * height)
        
        detections.append((label, score, x0, y0, x1, y1))
        
    return detections

# --- MAIN SCRIPT ---

try:
    # 1. Load the Hailo Chip with the system model
    print(f"Loading Hailo model from: {MODEL_FILE}")
    with Hailo(MODEL_FILE) as hailo:
        
        # 2. Setup Camera
        picam2 = Picamera2()
        
        # We need two streams: 
        # 'main': High resolution for you to see (1280x720)
        # 'lores': Square resolution for the AI (640x640 is required for YOLOv8)
        config = picam2.create_preview_configuration(
            main={"size": (1280, 720), "format": "XRGB8888"},
            lores={"size": (640, 640), "format": "RGB888"}
        )
        picam2.configure(config)
        picam2.start()

        # 3. Enable Continuous Auto-Focus
        picam2.set_controls({"AfMode": 2, "AfRange": 0})
        
        print("Camera running! Press 'q' to quit.")

        while True:
            # 4. Capture the AI frame (lores)
            # This waits for the next frame from the camera
            frame_ai = picam2.capture_array('lores')
            
            # 5. Run Inference
            # This sends the image to the Hailo chip and gets results instantly
            results = hailo.run(frame_ai)

            # 6. Get the display frame
            # We assume 'main' is synced closely enough with 'lores'
            frame_display = picam2.capture_array('main')
            
            # Convert to OpenCV format (BGR)
            frame_display = cv2.cvtColor(frame_display, cv2.COLOR_RGB2BGR)
            h, w, _ = frame_display.shape

            # 7. Draw boxes
            detections = extract_detections(results, w, h)
            
            for label, score, x0, y0, x1, y1 in detections:
                # Green Box
                cv2.rectangle(frame_display, (x0, y0), (x1, y1), (0, 255, 0), 2)
                
                # Label with confidence
                text = f"{label}: {int(score*100)}%"
                cv2.putText(frame_display, text, (x0, y0-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # 8. Show output
            cv2.imshow("Hailo-8L Python Detection", frame_display)
            
            if cv2.waitKey(1) == ord('q'):
                break

except Exception as e:
    print(f"\nError: {e}")
    if "No such file" in str(e):
        print("\nFix: The system model file wasn't found.")
        print("Try installing the full assets: sudo apt install rpicam-apps hailo-models")

finally:
    try:
        picam2.stop()
    except:
        pass
    cv2.destroyAllWindows()