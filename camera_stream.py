import os
import time
import psutil
import multiprocessing
import cv2
import glob
import asyncio
from fastapi import APIRouter, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

# --- Constants from camera_stream.py ---
STREAM_WIDTH = 640
STREAM_HEIGHT = 384
STREAM_FPS = 30
DETECTION_FRAME_INTERVAL = 3

# --- Camera Process Logic ---
def run_stream_process(
    stream_queue: multiprocessing.Queue,
    stop_event: multiprocessing.Event,
    detection_enabled: multiprocessing.Value = None,
    detection_queue: multiprocessing.Queue = None,
    width: int = STREAM_WIDTH,
    height: int = STREAM_HEIGHT,
):
    try:
        from picamera2 import Picamera2
        picam2 = Picamera2()
        main = {"size": (1280, 720), "format": "RGB888"}
        lores = {"size": (width, height), "format": "RGB888"}
        controls = {"FrameRate": STREAM_FPS, "AfMode": 2, "AfRange": 2}
        config = picam2.create_preview_configuration(main=main, lores=lores, controls=controls)
        picam2.configure(config)
        picam2.start()
    except Exception as e:
        print(f"Camera init failed: {e}")
        return

    frame_count = 0
    try:
        while not stop_event.is_set():
            try:
                frame_data = picam2.capture_array("lores")
            except Exception:
                break
            if frame_data is None:
                break

            import cv2
            if len(frame_data.shape) == 2:
                frame = cv2.cvtColor(frame_data, cv2.COLOR_GRAY2RGB)
            elif frame_data.shape[2] == 3:
                frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
            else:
                frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)

            try:
                stream_queue.put_nowait(frame)
            except Exception:
                pass

            if detection_enabled is not None and detection_queue is not None:
                if detection_enabled.value and frame_count % DETECTION_FRAME_INTERVAL == 0:
                    try:
                        detection_queue.put_nowait(frame)
                    except Exception:
                        pass
            frame_count += 1
    finally:
        picam2.stop()
        picam2.close()

# --- Router Logic ---
router = APIRouter()

# Global camera state
camera_process = None
stop_event = multiprocessing.Event()
stream_queue = multiprocessing.Queue(maxsize=1)
detection_enabled = multiprocessing.Value('b', False)
detection_queue = multiprocessing.Queue(maxsize=1)

@router.get("/system/stats")
async def get_stats():
    return {
        "time": time.strftime("%H:%M:%S"),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "temperature": 0
    }

@router.post("/camera/start")
async def start_camera():
    global camera_process, stop_event
    if camera_process and camera_process.is_alive():
        return {"status": "already_running"}
    
    stop_event.clear()
    camera_process = multiprocessing.Process(
        target=run_stream_process,
        args=(stream_queue, stop_event, detection_enabled, detection_queue)
    )
    camera_process.start()
    return {"status": "started"}

@router.post("/camera/stop")
async def stop_camera():
    global camera_process, stop_event
    if camera_process:
        stop_event.set()
        camera_process.join(timeout=2)
        if camera_process.is_alive():
            camera_process.terminate()
        camera_process = None
    return {"status": "stopped"}

def generate_frames():
    while True:
        try:
            frame = stream_queue.get(timeout=1.0)
        except Exception:
            if camera_process and not camera_process.is_alive():
                break
            continue
            
        if frame is None:
            break
        
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        frame = cv2.resize(frame, (480, 800), interpolation=cv2.INTER_LINEAR)
        
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        ret, buffer = cv2.imencode('.jpg', frame_bgr)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@router.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@router.post("/camera/capture")
async def capture_image():
    try:
        frame = stream_queue.get(timeout=2.0)
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        frame = cv2.resize(frame, (480, 800), interpolation=cv2.INTER_LINEAR)
        
        timestamp = int(time.time())
        filename = f"capture_{timestamp}.jpg"
        save_path = os.path.join("captures", filename)
        os.makedirs("captures", exist_ok=True)
        
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(save_path, frame_bgr)
        print(f"Captured: {save_path}")
        return {"status": "success", "filename": filename}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Capture failed: {str(e)}"}

@router.post("/camera/detection/start")
async def start_detection():
    detection_enabled.value = True
    return {"status": "started"}

@router.post("/camera/detection/stop")
async def stop_detection():
    detection_enabled.value = False
    return {"status": "stopped"}

@router.get("/gallery/images")
async def list_gallery_images():
    files = glob.glob("captures/*.jpg")
    files.sort(key=os.path.getmtime, reverse=True)
    images = []
    for f in files:
        filename = os.path.basename(f)
        images.append({
            "filename": filename,
            "url": f"/captures/{filename}"
        })
    return {"status": "success", "images": images}

@router.delete("/gallery/images/{filename}")
async def delete_gallery_image(filename: str):
    file_path = os.path.join("captures", filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "File not found"}

@router.websocket("/ws/detections")
async def detection_websocket(websocket: WebSocket):
    await websocket.accept()
    print("Detection WebSocket connected")
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Detection WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
