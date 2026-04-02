#!/usr/bin/env python3
"""
AI-Powered Security Camera System
Motion detection, TTS alerts, alarm, and live video feed over LAN.
"""
import eventlet
eventlet.monkey_patch()

import os
import sys
import json
import time
import threading
import logging
import subprocess
import datetime
from pathlib import Path
from collections import deque

import cv2
import numpy as np
import psutil
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, session, send_from_directory
from flask_socketio import SocketIO, emit

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECURITY_SECRET', 'MR-A-TACTICAL-KEY-2024')
app.config['SECURITY_PASSWORD'] = os.environ.get('SECURITY_PASSWORD', 'admin1')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

RECORDINGS_DIR = PROJECT_ROOT / 'recordings'
CAPTURES_DIR = PROJECT_ROOT / 'captures'
SOUNDS_DIR = PROJECT_ROOT / 'static' / 'sounds'
RECORDINGS_DIR.mkdir(exist_ok=True)
CAPTURES_DIR.mkdir(exist_ok=True)

CONFIG = {
    'MOTION_THRESHOLD': 500,
    'MOTION_SENSITIVITY': 25,
    'ALARM_COOLDOWN': 10,
    'RECORD_ON_DETECTION': True,
    'PRE_RECORD_SECONDS': 3,
}

state = {
    'armed': False,
    'alarm_triggered': False,
    'alarm_defused': False,
    'motion_detected': False,
    'recording': False,
    'last_trigger_time': 0,
    'awaiting_response': False,
    'detection_active': False,
}

pre_record_buffer = deque(maxlen=30)
recording_writer = None
recording_start_time = None
recording_filename = None
motion_prev_frame = None
camera = None
frame_count = 0

# --- TTS using PocketAudio ---
tts = None
try:
    from tts_piper import PocketAudio
    tts = PocketAudio()
    logger.info("PocketAudio TTS loaded")
except Exception as e:
    logger.warning(f"PocketAudio TTS not available: {e}")


def speak(text):
    """Speak text using TTS (non-blocking via queue)."""
    if tts:
        try:
            tts.speak(text)
        except Exception as e:
            logger.warning(f"TTS speak error: {e}")
    else:
        try:
            subprocess.Popen(
                ["espeak", text],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception:
            pass


def play_alarm_sound(sound_file="alarm.wav"):
    """Play alarm sound file looping until stopped."""
    sound_path = SOUNDS_DIR / sound_file
    if not sound_path.exists():
        sound_path = SOUNDS_DIR / "alarm.wav"

    # Kill any existing alarm audio first
    _kill_alarm_processes()

    # Try pw-play first (PipeWire), then pygame, then aplay
    try:
        subprocess.Popen(
            ["bash", "-c", f"while true; do pw-play '{sound_path}'; done"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        logger.info(f"Playing alarm with pw-play: {sound_path.name}")
        return
    except Exception:
        pass

    try:
        os.environ['SDL_AUDIODRIVER'] = 'pipewire'
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(str(sound_path))
        pygame.mixer.music.play(-1)
        logger.info(f"Playing alarm with pygame: {sound_path.name}")
        return
    except Exception as e:
        logger.warning(f"pygame alarm failed: {e}")

    try:
        subprocess.Popen(
            ["bash", "-c", f"while true; do aplay '{sound_path}'; done"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        logger.info(f"Playing alarm with aplay: {sound_path.name}")
    except Exception as e:
        logger.error(f"All alarm playback methods failed: {e}")


def _kill_alarm_processes():
    """Kill any running alarm audio processes."""
    for proc in ["pw-play", "aplay"]:
        try:
            subprocess.run(["pkill", "-f", proc], timeout=1, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass


def stop_alarm_sound():
    """Stop alarm sound."""
    _kill_alarm_processes()
    logger.info("Alarm sound stopped")


def play_loud_beep():
    """Play a single loud beep for the 'Get out' alarm."""
    beep_path = SOUNDS_DIR / "alarm.wav"
    try:
        subprocess.Popen(
            ["pw-play", str(beep_path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        try:
            subprocess.Popen(
                ["aplay", str(beep_path)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception:
            pass


# --- Camera ---
def find_camera():
    """Find an available camera."""
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                logger.info(f"Camera found at index {i}")
                return cap
        cap.release()
    logger.error("No camera found!")
    return None


def get_camera():
    """Get or initialize the global camera."""
    global camera
    if camera is None:
        camera = find_camera()
    return camera


# --- Motion Detection ---
def detect_motion(frame):
    """Detect motion in frame using frame differencing. Returns True if motion found."""
    global motion_prev_frame

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if motion_prev_frame is None:
        motion_prev_frame = gray
        return False

    delta = cv2.absdiff(motion_prev_frame, gray)
    thresh = cv2.threshold(delta, CONFIG['MOTION_SENSITIVITY'], 255, cv2.THRESH_BINARY)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    thresh = cv2.dilate(thresh, kernel, iterations=2)
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_found = False
    for c in contours:
        if cv2.contourArea(c) > CONFIG['MOTION_THRESHOLD']:
            motion_found = True
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    motion_prev_frame = gray
    return motion_found


# --- Voice Alert Flow ---
def trigger_voice_alert():
    """
    When motion is detected:
    1. Say "Someone has entered your room"
    2. Ask "Would you like me to sound an alarm?"
    3. Wait for user response via API
    """
    global state

    if state['awaiting_response'] or state['alarm_triggered']:
        return

    state['awaiting_response'] = True
    state['motion_detected'] = True

    socketio.emit('motion_alert', {
        'message': 'Someone has entered your room!',
        'timestamp': datetime.datetime.now().isoformat(),
        'prompt': 'Would you like me to sound an alarm?'
    })

    speak("Someone has entered your room.")
    time.sleep(2)
    speak("Would you like me to sound an alarm?")

    logger.info("Voice alert triggered - awaiting user response")


def sound_the_alarm():
    """Sound the alarm: loud beep + say 'Get out'."""
    global state
    state['alarm_triggered'] = True
    state['alarm_defused'] = False

    socketio.emit('alarm_triggered', {
        'status': 'ACTIVE',
        'message': 'ALARM SOUNDED!'
    })

    # Run TTS and alarm sound in background so HTTP response returns immediately
    def _alarm_thread():
        try:
            speak("Get out!")
        except Exception as e:
            logger.warning(f"TTS alarm error: {e}")
        play_alarm_sound()
        if CONFIG['RECORD_ON_DETECTION'] and not state['recording']:
            start_recording()
        logger.info("ALARM SOUNDED - Get out!")

    threading.Thread(target=_alarm_thread, daemon=True).start()


def trigger_motion_alert():
    """Called when motion is detected. Prevents duplicate triggers."""
    global state
    now = time.time()

    if state['awaiting_response'] or state['alarm_triggered']:
        return
    if now - state['last_trigger_time'] < CONFIG['ALARM_COOLDOWN']:
        return

    state['last_trigger_time'] = now
    threading.Thread(target=trigger_voice_alert, daemon=True).start()


# --- Recording ---
def start_recording():
    global recording_writer, recording_start_time, recording_filename, state
    if state['recording']:
        return

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'recording_{timestamp}.avi'
    filepath = RECORDINGS_DIR / filename

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    recording_writer = cv2.VideoWriter(str(filepath), fourcc, 10.0, (640, 480))
    recording_start_time = time.time()
    recording_filename = filename
    state['recording'] = True
    logger.info(f"Started recording: {filename}")
    socketio.emit('recording_started', {'filename': filename})


def stop_recording():
    global recording_writer, recording_start_time, recording_filename, state
    if not state['recording'] or recording_writer is None:
        return

    recording_writer.release()
    recording_writer = None
    state['recording'] = False
    duration = time.time() - recording_start_time
    logger.info(f"Stopped recording: {recording_filename} ({duration:.1f}s)")
    socketio.emit('recording_stopped', {'filename': recording_filename, 'duration': duration})


def write_frame_to_recording(frame):
    if state['recording'] and recording_writer is not None:
        try:
            recording_writer.write(frame)
        except Exception:
            pass


# --- Video Feed Generator ---
def generate_frames():
    """Generate MJPEG frames for live video feed."""
    global frame_count, state, pre_record_buffer

    cam = get_camera()
    if cam is None:
        # Generate a placeholder frame saying "No Camera"
        while True:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "NO CAMERA FOUND", (150, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            socketio.sleep(0.5)
        return

    while True:
        success, frame = cam.read()
        if not success:
            # Try to re-open camera
            cam.release()
            time.sleep(1)
            cam = find_camera()
            if cam is None:
                continue
            success, frame = cam.read()
            if not success:
                continue

        frame_count += 1
        frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)

        # Motion detection when armed
        if state['armed'] and not state['alarm_triggered']:
            if detect_motion(frame):
                state['motion_detected'] = True
                trigger_motion_alert()
                # Green rectangle already drawn by detect_motion
            else:
                state['motion_detected'] = False

            # Add frame to pre-record buffer
            pre_record_buffer.append(frame.copy())

            # Write frame to recording if active
            if state['recording']:
                write_frame_to_recording(frame)
        else:
            state['motion_detected'] = False

        # Draw timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Draw status overlay
        if state['armed']:
            if state['alarm_triggered']:
                cv2.putText(frame, "ALARM!", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)
            elif state['motion_detected']:
                cv2.putText(frame, "MOTION DETECTED", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            else:
                cv2.putText(frame, "ARMED", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if state['recording']:
            cv2.circle(frame, (frame.shape[1] - 20, 20), 8, (0, 0, 255), -1)

        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        socketio.sleep(0.033)  # ~30fps


# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('security_dashboard.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/arm', methods=['POST'])
def arm_system():
    global state
    state['armed'] = True
    state['alarm_defused'] = False
    state['alarm_triggered'] = False
    state['motion_detected'] = False
    state['awaiting_response'] = False
    speak("Security system armed")
    socketio.emit('system_armed', {'status': 'armed'})
    return jsonify({'status': 'armed'})


@app.route('/disarm', methods=['POST'])
def disarm_system():
    global state
    state['armed'] = False
    state['alarm_defused'] = True
    state['alarm_triggered'] = False
    state['awaiting_response'] = False
    state['motion_detected'] = False
    stop_alarm_sound()

    if state['recording']:
        stop_recording()

    speak("Security system disarmed")
    socketio.emit('system_disarmed', {'status': 'disarmed'})
    return jsonify({'status': 'disarmed'})


@app.route('/defuse', methods=['POST'])
def defuse_alarm():
    global state
    state['alarm_defused'] = True
    state['alarm_triggered'] = False
    state['awaiting_response'] = False
    stop_alarm_sound()

    if state['recording']:
        stop_recording()

    speak("Alarm defused")
    socketio.emit('alarm_defused', {'status': 'DEFUSED'})
    return jsonify({'status': 'defused'})


@app.route('/alarm_response', methods=['POST'])
def alarm_response():
    """Handle user's yes/no response to 'Would you like me to sound an alarm?'"""
    global state
    data = request.get_json() or {}
    answer = data.get('answer', '').lower().strip()

    state['awaiting_response'] = False

    if answer in ['yes', 'y', 'yeah', 'yep', 'sure', 'do it']:
        sound_the_alarm()
        return jsonify({'status': 'alarm_triggered', 'message': 'Alarm is sounding!'})
    else:
        speak("Okay, alarm cancelled.")
        socketio.emit('alarm_cancelled', {'message': 'Alarm cancelled by user'})
        return jsonify({'status': 'cancelled', 'message': 'Alarm cancelled'})


@app.route('/manual_alarm', methods=['POST'])
def manual_alarm():
    sound_the_alarm()
    return jsonify({'status': 'triggered'})


@app.route('/stop_alarm', methods=['POST'])
def stop_alarm():
    global state
    state['alarm_defused'] = True
    state['alarm_triggered'] = False
    state['awaiting_response'] = False
    stop_alarm_sound()

    if state['recording']:
        stop_recording()

    return jsonify({'status': 'stopped'})


@app.route('/start_camera', methods=['POST'])
def start_cam():
    cam = get_camera()
    if cam:
        return jsonify({'status': 'started'})
    return jsonify({'status': 'error', 'message': 'No camera found'})


@app.route('/stop_camera', methods=['POST'])
def stop_cam():
    global camera
    if camera:
        camera.release()
        camera = None
    return jsonify({'status': 'stopped'})


@app.route('/capture', methods=['POST'])
def capture_image():
    cam = get_camera()
    if cam is None:
        return jsonify({'status': 'error', 'message': 'No camera'})

    ret, frame = cam.read()
    if not ret:
        return jsonify({'status': 'error', 'message': 'Failed to capture'})

    frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'capture_{timestamp}.jpg'
    filepath = CAPTURES_DIR / filename
    cv2.imwrite(str(filepath), frame)
    logger.info(f"Captured: {filename}")
    return jsonify({'status': 'success', 'filename': filename})


@app.route('/recordings')
def list_recordings():
    files = sorted(RECORDINGS_DIR.glob('*.avi'), key=lambda x: x.stat().st_mtime, reverse=True)
    recordings = [{
        'filename': f.name,
        'size': f.stat().st_size,
        'time': datetime.datetime.fromtimestamp(f.stat().st_mtime).isoformat()
    } for f in files]
    return jsonify({'recordings': recordings})


@app.route('/recordings/<filename>')
def get_recording(filename):
    return send_from_directory(RECORDINGS_DIR, filename)


@app.route('/captures/<filename>')
def get_capture(filename):
    return send_from_directory(CAPTURES_DIR, filename)


@app.route('/captures')
def list_captures():
    files = sorted(CAPTURES_DIR.glob('*.jpg'), key=lambda x: x.stat().st_mtime, reverse=True)
    captures = [{
        'filename': f.name,
        'url': f'/captures/{f.name}',
        'time': datetime.datetime.fromtimestamp(f.stat().st_mtime).isoformat()
    } for f in files]
    return jsonify({'captures': captures})


@app.route('/api/status')
def api_status():
    return jsonify({
        'armed': state['armed'],
        'alarm_triggered': state['alarm_triggered'],
        'alarm_defused': state['alarm_defused'],
        'motion_detected': state['motion_detected'],
        'awaiting_response': state['awaiting_response'],
        'recording': state['recording'],
        'frame_count': frame_count,
    })


def get_cpu_temp():
    try:
        temps = psutil.sensors_temperatures()
        if 'cpu_thermal' in temps and temps['cpu_thermal']:
            return temps['cpu_thermal'][0].current
        if 'rp1_adc' in temps and temps['rp1_adc']:
            return temps['rp1_adc'][0].current
        for k, v in temps.items():
            if v:
                return v[0].current
    except Exception:
        pass
    return 0


@app.route('/system/stats')
def system_stats():
    return jsonify({
        "time": time.strftime("%I:%M:%S %p"),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "temperature": get_cpu_temp()
    })


@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    global CONFIG
    if request.method == 'POST':
        CONFIG.update(request.json or {})
        return jsonify({'status': 'updated', 'config': CONFIG})
    return jsonify(CONFIG)


@app.route('/manual_alarm_trigger', methods=['POST'])
def manual_alarm_trigger():
    sound_the_alarm()
    return jsonify({'status': 'triggered'})


@socketio.on('connect')
def handle_connect():
    logger.info("Client connected to security dashboard")


@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected")


# --- Start ---
if __name__ == '__main__':
    logger.info("Starting AI Security Camera System...")
    logger.info(f"Dashboard: http://0.0.0.0:5050")
    logger.info(f"Access from other computers: http://<this-ip>:5050")
    socketio.run(app, host='0.0.0.0', port=5050, debug=False, allow_unsafe_werkzeug=True)
