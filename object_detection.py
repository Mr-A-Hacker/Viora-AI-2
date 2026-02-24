#!/usr/bin/env python3
"""
Simple real-time object detection: RPi camera at 720p, frame-by-frame.
Inference runs on Hailo-8 HAT. For higher FPS use a smaller model (e.g. yolov11n.hef).
Run: python object_detection.py
     python object_detection.py -n path/to/model.hef
"""
import argparse
import sys
import threading
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hailo_od.hailo_inference import HailoInfer
from hailo_od.toolbox import get_labels, load_json_file, default_preprocess
from hailo_od.object_detection_post_process import inference_result_handler

# Display size (fits on screen, no fullscreen)
DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 540

DEFAULT_HEF = Path(__file__).resolve().parent / "models" / "yolov11l.hef"
CONFIG_PATH = Path(__file__).resolve().parent / "hailo_od" / "config.json"


def main():
    p = argparse.ArgumentParser(description="Real-time object detection (RPi camera 720p)")
    p.add_argument("-n", "--hef-path", type=Path, default=DEFAULT_HEF, help="Path to .hef model")
    args = p.parse_args()
    hef_path = args.hef_path
    if not hef_path.exists():
        print(f"Model not found: {hef_path}")
        print("Usage: python object_detection.py [-n path/to/model.hef]")
        sys.exit(1)

    # RPi camera at 1280x720 (720p)
    try:
        from picamera2 import Picamera2
    except ImportError:
        print("picamera2 required for RPi camera. Install: pip install picamera2")
        sys.exit(1)

    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (1280, 720), "format": "RGB888"}  # 1280x720
    )
    picam2.configure(config)
    picam2.start()

    # Hailo-8 HAT: load model and configure (inference runs on the HAT, not the Pi CPU)
    infer = HailoInfer(str(hef_path), batch_size=1)
    height, width, _ = infer.get_input_shape()
    print(f"Hailo-8: inference on device (HEF: {hef_path.name})")
    print("For higher FPS try a smaller model, e.g. yolov11n.hef or yolov8n.hef")

    labels = get_labels(None)
    config_data = load_json_file(str(CONFIG_PATH)) if CONFIG_PATH.exists() else {
        "visualization_params": {"score_thres": 0.25, "max_boxes_to_draw": 50}
    }

    result_holder = []
    done_event = threading.Event()

    def on_done(completion_info, bindings_list=None):
        if completion_info.exception:
            result_holder.append(("err", completion_info.exception))
        else:
            b = bindings_list[0]
            if len(b._output_names) == 1:
                result_holder.append(("ok", b.output().get_buffer()))
            else:
                result_holder.append(("ok", {
                    n: np.expand_dims(b.output(n).get_buffer(), axis=0)
                    for n in b._output_names
                }))
        done_event.set()

    # Pipeline: capture next frame while Hailo runs (reduces latency)
    next_frame_lock = threading.Lock()
    next_frame_data = [None, None]  # [frame, preprocessed]
    stop_capture = threading.Event()

    def capture_loop():
        while not stop_capture.is_set():
            frame = picam2.capture_array()
            if frame is None:
                break
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            else:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            preprocessed = default_preprocess(frame, width, height)
            with next_frame_lock:
                next_frame_data[0] = frame
                next_frame_data[1] = preprocessed

    capture_thread = threading.Thread(target=capture_loop, daemon=True)
    capture_thread.start()
    time.sleep(0.5)  # let first frame fill

    cv2.namedWindow("Object detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Object detection", DISPLAY_WIDTH, DISPLAY_HEIGHT)

    fps_smooth = 0.0
    infer_ms_smooth = 0.0
    t_prev = time.perf_counter()

    try:
        while True:
            with next_frame_lock:
                frame = next_frame_data[0]
                preprocessed = next_frame_data[1]
            if frame is None or preprocessed is None:
                continue

            # Run inference on Hailo-8 and wait
            result_holder.clear()
            done_event.clear()
            t_infer_start = time.perf_counter()
            infer.run([preprocessed], on_done)
            done_event.wait(timeout=5.0)
            infer_ms = (time.perf_counter() - t_infer_start) * 1000
            infer_ms_smooth = infer_ms_smooth * 0.8 + infer_ms * 0.2

            if not result_holder:
                continue
            kind, raw = result_holder[0]
            if kind == "err":
                continue

            drawn = inference_result_handler(
                frame, raw, labels, config_data, tracker=None, draw_trail=False
            )

            t_now = time.perf_counter()
            dt = t_now - t_prev
            t_prev = t_now
            if dt > 0:
                fps_smooth = fps_smooth * 0.85 + (1.0 / dt) * 0.15

            fps_text = f"FPS: {fps_smooth:.1f}  Hailo: {infer_ms_smooth:.0f}ms"
            cv2.putText(
                drawn, fps_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA
            )

            show = cv2.resize(
                cv2.cvtColor(drawn, cv2.COLOR_RGB2BGR),
                (DISPLAY_WIDTH, DISPLAY_HEIGHT),
                interpolation=cv2.INTER_LINEAR,
            )
            cv2.imshow("Object detection", show)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        stop_capture.set()
        picam2.stop()
        picam2.close()
        infer.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
