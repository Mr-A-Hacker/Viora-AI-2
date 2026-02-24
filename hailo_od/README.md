# Hailo object detection (standalone)

Self-contained implementation based on [hailo-apps object_detection](https://github.com/hailo-ai/hailo-apps/tree/main/hailo_apps/python/standalone_apps/object_detection). No need to clone the hailo-apps repo.

## Requirements

- **Hailo device** (Hailo-8, Hailo-8L, or Hailo-10) with driver and **PyHailoRT** installed.
  - Install the `.whl` from the [Hailo Developer Zone](https://hailo.ai/developer-zone/), e.g.:
    ```bash
    pip install hailort-*.whl
    ```
- **Pip packages** (from project root):
  ```bash
  pip install -r requirements.txt
  ```
  This adds: `lap`, `cython_bbox`, `PyYAML`. You already have `opencv-python`, `numpy`, `scipy`.

## Supported models

HEF files that include **HailoRT postprocess** (YOLO NMS), e.g.:

- YOLOv5, YOLOv6, YOLOv7, YOLOv8, YOLOv9, YOLOv10, YOLOv11
- YOLOx, SSD, CenterNet

## Run

From the project root:

```bash
# USB camera
python object_detection.py -n path/to/model.hef -i usb

# Raspberry Pi camera
python object_detection.py -n path/to/model.hef -i rpi

# With tracking and motion trails
python object_detection.py -n path/to/model.hef -i usb --track --draw-trail

# Video or image
python object_detection.py -n path/to/model.hef -i video.mp4 -s -o output
python object_detection.py -n path/to/model.hef -i image.jpg -o output
```

Options: `-b` batch size, `-l` labels file, `--camera-resolution sd|hd|fhd`, `--show-fps`, `-f` frame rate.

## Config

Edit `hailo_od/config.json` to change score threshold, max boxes, and tracker parameters.
