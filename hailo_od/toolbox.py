"""
Minimal toolbox for Hailo object detection: input init, preprocess, visualize, labels.
No hailo_apps dependency.
"""
import json
import os
import time
import queue
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable, Generator
import cv2
import numpy as np

# Default paths relative to this package
_THIS_DIR = Path(__file__).resolve().parent
VIDEO_SUFFIXES = (".mp4", ".avi", ".mov", ".mkv")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")
CAMERA_RESOLUTION_MAP = {"sd": (640, 480), "hd": (1280, 720), "fhd": (1920, 1080)}
DEFAULT_COCO_LABELS_PATH = str(_THIS_DIR / "coco_labels.txt")


def load_json_file(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_images_opencv(images_path: str) -> List[np.ndarray]:
    path = Path(images_path)

    def read_rgb(p: Path):
        img = cv2.imread(str(p))
        if img is not None:
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return None

    if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
        img = read_rgb(path)
        return [img] if img is not None else []
    if path.is_dir():
        images = [
            read_rgb(img)
            for img in path.glob("*")
            if img.suffix.lower() in IMAGE_EXTENSIONS
        ]
        return [img for img in images if img is not None]
    return []


def validate_images(images: List[np.ndarray], batch_size: int) -> None:
    if not images:
        raise ValueError("No valid images found in the specified path.")
    if len(images) % batch_size != 0:
        raise ValueError(
            "The number of input images should be divisible by the batch size."
        )


def divide_list_to_batches(
    images_list: List[np.ndarray], batch_size: int
) -> Generator[List[np.ndarray], None, None]:
    for i in range(0, len(images_list), batch_size):
        yield images_list[i : i + batch_size]


def id_to_color(idx: int) -> np.ndarray:
    np.random.seed(idx)
    return np.random.randint(0, 255, size=3, dtype=np.uint8)


def get_labels(labels_path: Optional[str]) -> List[str]:
    if labels_path is None or not os.path.exists(labels_path):
        labels_path = DEFAULT_COCO_LABELS_PATH
    if not os.path.exists(labels_path):
        # Fallback: COCO 80 classes inline
        return [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
            "truck", "boat", "traffic light", "fire hydrant", "stop sign", "parking meter",
            "bench", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear",
            "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase",
            "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
            "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
            "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
            "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut",
            "cake", "chair", "couch", "potted plant", "bed", "dining table", "toilet",
            "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
            "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
            "scissors", "teddy bear", "hair drier", "toothbrush",
        ]
    with open(labels_path, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def default_preprocess(image: np.ndarray, model_w: int, model_h: int) -> np.ndarray:
    img_h, img_w = image.shape[0], image.shape[1]
    scale = min(model_w / img_w, model_h / img_h)
    new_w, new_h = int(img_w * scale), int(img_h * scale)
    image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    padded = np.full((model_h, model_w, 3), (114, 114, 114), dtype=np.uint8)
    x_off = (model_w - new_w) // 2
    y_off = (model_h - new_h) // 2
    padded[y_off : y_off + new_h, x_off : x_off + new_w] = image
    return padded


def preprocess_from_cap(
    cap: Any,
    batch_size: int,
    input_queue: queue.Queue,
    width: int,
    height: int,
    preprocess_fn: Callable[[np.ndarray, int, int], np.ndarray],
    framerate: Optional[float] = None,
) -> None:
    frames, processed_frames = [], []
    cam_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    skip = max(1, int(round(cam_fps / float(framerate)))) if framerate and framerate > 0 else 1
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % skip != 0:
            continue
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame)
        processed_frames.append(preprocess_fn(frame, width, height))
        if len(frames) == batch_size:
            input_queue.put((frames, processed_frames))
            frames, processed_frames = [], []


def preprocess_images(
    images: List[np.ndarray],
    batch_size: int,
    input_queue: queue.Queue,
    width: int,
    height: int,
    preprocess_fn: Callable[[np.ndarray, int, int], np.ndarray],
) -> None:
    for batch in divide_list_to_batches(images, batch_size):
        input_queue.put(
            (list(batch), [preprocess_fn(im, width, height) for im in batch])
        )


def preprocess(
    images: Optional[List[np.ndarray]],
    cap: Optional[Any],
    framerate: Optional[float],
    batch_size: int,
    input_queue: queue.Queue,
    width: int,
    height: int,
    preprocess_fn: Optional[Callable] = None,
) -> None:
    fn = preprocess_fn or default_preprocess
    if cap is None:
        preprocess_images(images, batch_size, input_queue, width, height, fn)
    else:
        preprocess_from_cap(cap, batch_size, input_queue, width, height, fn, framerate)
    input_queue.put(None)


def resize_frame_for_output(
    frame: np.ndarray, resolution: Optional[Tuple[int, int]]
) -> np.ndarray:
    if resolution is None:
        return frame
    _, target_h = resolution
    h, w = frame.shape[:2]
    if h == 0 or w == 0:
        return frame
    scale = target_h / float(h)
    new_w, new_h = int(round(w * scale)), target_h
    return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)


def visualize(
    output_queue: queue.Queue,
    cap: Optional[Any],
    save_stream_output: bool,
    output_dir: str,
    callback: Callable,
    fps_tracker: Optional["FrameRateTracker"] = None,
    output_resolution: Optional[Tuple[int, int]] = None,
    framerate: Optional[float] = None,
) -> None:
    image_id = 0
    out = None
    frame_width = frame_height = None

    if cap is not None:
        cv2.namedWindow("Output", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Output", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        base_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
        base_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
        if output_resolution is not None:
            target_w, target_h = output_resolution
        else:
            target_w, target_h = base_width, base_height
        frame_width, frame_height = target_w, target_h
        if save_stream_output:
            os.makedirs(output_dir, exist_ok=True)
            cam_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            final_fps = framerate or (cam_fps if cam_fps > 1 else 30.0)
            out_path = os.path.join(output_dir, "output.avi")
            out = cv2.VideoWriter(
                out_path,
                cv2.VideoWriter_fourcc(*"XVID"),
                final_fps,
                (frame_width, frame_height),
            )

    while True:
        result = output_queue.get()
        if result is None:
            break
        original_frame, inference_result = result[0], result[1]
        if isinstance(inference_result, list) and len(inference_result) == 1:
            inference_result = inference_result[0]
        frame_with_detections = callback(original_frame, inference_result)
        if fps_tracker is not None:
            fps_tracker.increment()
        bgr = cv2.cvtColor(frame_with_detections, cv2.COLOR_RGB2BGR)
        frame_to_show = resize_frame_for_output(bgr, output_resolution)

        if cap is not None:
            cv2.imshow("Output", frame_to_show)
            if save_stream_output and out is not None and frame_width and frame_height:
                out.write(cv2.resize(frame_to_show, (frame_width, frame_height)))
        else:
            os.makedirs(output_dir, exist_ok=True)
            cv2.imwrite(
                os.path.join(output_dir, f"output_{image_id}.png"), frame_to_show
            )
        image_id += 1

        if cv2.waitKey(1) & 0xFF == ord("q"):
            if save_stream_output and out is not None:
                out.release()
            if cap is not None:
                cap.release()
            cv2.destroyAllWindows()
            break

    if cap is not None and save_stream_output and out is not None:
        out.release()


class FrameRateTracker:
    def __init__(self):
        self._count = 0
        self._start_time = None

    def start(self):
        self._start_time = time.time()

    def increment(self, n: int = 1):
        self._count += n

    @property
    def count(self):
        return self._count

    @property
    def elapsed(self):
        return (time.time() - self._start_time) if self._start_time else 0.0

    @property
    def fps(self):
        e = self.elapsed
        return self._count / e if e > 0 else 0.0

    def frame_rate_summary(self):
        return f"Processed {self.count} frames at {self.fps:.2f} FPS"


def init_input_source(
    input_src: str, batch_size: int, resolution: Optional[str]
) -> Tuple[Optional[Any], Optional[List[np.ndarray]]]:
    src = input_src.strip()
    if src == "usb":
        camera_index = int(os.environ.get("CAMERA_INDEX", 0))
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open USB camera index {camera_index}")
        if resolution and resolution in CAMERA_RESOLUTION_MAP:
            w, h = CAMERA_RESOLUTION_MAP[resolution]
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        return cap, None
    if src == "rpi":
        try:
            from picamera2 import Picamera2
            picam2 = Picamera2()
            main = {"size": (1280, 720), "format": "RGB888"}
            config = picam2.create_preview_configuration(main=main)
            picam2.configure(config)
            picam2.start()
            # Simple adapter: expose read() returning RGB
            class RpiCap:
                def __init__(self, p):
                    self._p = p
                def read(self):
                    arr = self._p.capture_array()
                    if arr is None:
                        return False, None
                    if len(arr.shape) == 2:
                        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
                    else:
                        arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
                    return True, arr
                def get(self, prop):
                    if prop == cv2.CAP_PROP_FRAME_WIDTH:
                        return 1280.0
                    if prop == cv2.CAP_PROP_FRAME_HEIGHT:
                        return 720.0
                    if prop == cv2.CAP_PROP_FPS:
                        return 30.0
                    return 0.0
                def release(self):
                    self._p.stop()
                    self._p.close()
            return RpiCap(picam2), None
        except Exception as e:
            raise RuntimeError(f"RPi camera failed: {e}") from e
    if src.startswith(("http://", "https://", "rtsp://")):
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open stream: {src}")
        return cap, None
    if any(src.endswith(s) for s in VIDEO_SUFFIXES):
        if not os.path.exists(src):
            raise FileNotFoundError(f"File not found: {src}")
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {src}")
        return cap, None
    if not os.path.exists(src):
        raise FileNotFoundError(
            f"Invalid input '{src}'. Use usb, rpi, a URL, video path, or image/dir path."
        )
    images = load_images_opencv(src)
    validate_images(images, batch_size)
    return None, images
