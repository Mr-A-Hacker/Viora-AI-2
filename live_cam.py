import time
from picamera2 import Picamera2, Preview

# 1. Initialize Picamera2
picam2 = Picamera2()

# 2. Configure High Quality Resolution
# rpicam-still uses the full sensor. For a smooth live feed, 
# 1920x1080 (1080p) is the sweet spot between quality and speed.
# You can go higher (e.g., 2304x1296) if you want even more detail.
config = picam2.create_preview_configuration(
    main={"size": (1920, 1080), "format": "XRGB8888"}
)
picam2.configure(config)

# 3. Start the Camera
picam2.start_preview(Preview.QTGL)
picam2.start()

# 4. ENABLE AUTO-FOCUS (The Magic Part)
# AfMode: 0 = Manual, 1 = Auto (One-shot), 2 = Continuous
# AfRange: 0 = Normal, 1 = Macro, 2 = Full
# We set it to Continuous (2) so it always stays sharp.
picam2.set_controls({"AfMode": 2, "AfRange": 0})

print("Camera running in High Quality (1080p) with Auto-Focus.")
print("Press Ctrl+C to stop.")

# 5. Wait / Keep Alive
try:
    while True:
        # We just sleep here to keep the preview window open.
        # The camera hardware handles the focus/exposure in the background.
        time.sleep(1)
except KeyboardInterrupt:
    picam2.stop_preview()
    picam2.stop()