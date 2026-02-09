import cv2
import numpy as np
from picamera2 import Picamera2
from ultralytics import YOLO

# 1. Load the YOLOv8 Nano model (Smallest and fastest for Pi)
print("Loading YOLOv8 model...")
model = YOLO('yolov8n.pt')

# 2. Initialize the Camera (using libcamera, NOT OpenCV)
picam2 = Picamera2()

# Configure the camera:
# - 640x480 is the standard training size for YOLO.
# - "format": "RGB888" gives us a standard image array.
config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)

# 3. Start the Camera
picam2.start()

# Enable Continuous Auto-Focus (Focus Mode 2 = Continuous)
picam2.set_controls({"AfMode": 2, "AfRange": 0})

print("Starting detection... Press 'q' to quit.")

try:
    while True:
        # 4. Capture the frame as a NumPy array (directly from hardware)
        # This blocks until a new frame is ready.
        image_rgb = picam2.capture_array()

        # 5. Convert RGB to BGR
        # Picamera gives RGB, but OpenCV (used for display) and YOLO expect BGR.
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        # 6. Run YOLOv8 Inference
        # stream=True makes it run faster for video loops
        results = model(image_bgr, stream=True, verbose=False)

        # 7. Draw the bounding boxes
        # We iterate through the results generator to get the plotted frame
        for r in results:
            # plot() returns the BGR numpy array with boxes drawn
            annotated_frame = r.plot()

            # 8. Display the frame
            cv2.imshow('YOLOv8 Detection', annotated_frame)

        # 9. Quit on 'q' key press
        if cv2.waitKey(1) == ord('q'):
            break

except KeyboardInterrupt:
    pass

finally:
    # Cleanup
    picam2.stop()
    cv2.destroyAllWindows()
    print("Cleaned up.")