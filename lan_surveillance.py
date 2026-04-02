import os
import cv2
import time
import threading
import datetime
import subprocess
import numpy as np
from flask import Flask, render_template, Response, request, redirect, url_for, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'viora_security_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

SECURITY_PASSWORD = os.environ.get("SECURITY_PASSWORD", "admin123")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "static", "sounds")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(SOUNDS_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

alarm_triggered = False
detection_active = False
alarm_countdown = None
camera = None
frame_count = 0
previous_frame = None
motion_detected = False

def log_event(event_type, details):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    log_entry = f"[{timestamp}] {event_type} | IP: {client_ip} | UA: {user_agent} | Details: {details}\n"
    
    log_file = os.path.join(LOG_DIR, "security.log")
    with open(log_file, "a") as f:
        f.write(log_entry)
    
    socketio.emit('log_event', {'event': event_type, 'details': details, 'time': timestamp})

def play_alarm_sound():
    sound_file = os.path.join(SOUNDS_DIR, "alarm.mp3")
    if os.path.exists(sound_file):
        try:
            subprocess.Popen(["mpg123", "-q", sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    else:
        try:
            subprocess.Popen(["speaker-test", "-t", "sine", "-f", "440", "-l", "3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

def draw_overlay(frame, text, position=(10, 30), color=(0, 255, 0), font_scale=0.7, thickness=2):
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

def detect_motion(current_frame):
    global previous_frame, motion_detected
    
    if previous_frame is None:
        previous_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        previous_frame = cv2.GaussianBlur(previous_frame, (21, 21), 0)
        return False
    
    gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
    frame_delta = cv2.absdiff(previous_frame, gray)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    motion_detected = len(contours) > 0
    
    for contour in contours:
        if cv2.contourArea(contour) > 500:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(current_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
    
    previous_frame = gray
    return motion_detected

def find_available_camera():
    """Try multiple camera indices to find an available camera"""
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"📷 Found camera at index {i}")
            return cap
        cap.release()
    return None

def generate_frames():
    global camera, frame_count, alarm_triggered, detection_active
    
    if camera is None:
        print("🔍 Searching for available camera...")
        camera = find_available_camera()
        if camera is None:
            print("❌ No camera found!")
            return
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        frame_count += 1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if detection_active and not alarm_triggered:
            if detect_motion(frame):
                log_event("MOTION_DETECTED", "Movement detected in camera view")
                socketio.emit('motion_detected', {'timestamp': timestamp})
        
        if alarm_triggered:
            draw_overlay(frame, "🚨 ALARM TRIGGERED", (10, 30), (0, 0, 255), 1, 2)
        
        draw_overlay(frame, f"VIORA SECURITY - {timestamp}", (10, frame.shape[0] - 20), (0, 255, 0), 0.6, 1)
        
        if frame_count % 30 == 0:
            log_event("HEARTBEAT", "Camera feed active")
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def countdown_thread():
    global alarm_countdown
    for i in range(10, -1, -1):
        alarm_countdown = i
        socketio.emit('countdown', {'seconds': i})
        socketio.sleep(1)
    
    if alarm_triggered:
        socketio.emit('alarm_triggered', {'message': 'BREACH DETECTED'})
        play_alarm_sound()
        log_event("ALARM", "Alarm triggered - breach detected")

@app.route('/')
def index():
    log_event("PAGE_VIEW", "Accessed security dashboard")
    return render_template('surveillance.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/raw_feed')
def raw_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/security', methods=['POST'])
def security():
    global alarm_triggered, alarm_countdown
    password = request.form.get('password')
    
    if password == SECURITY_PASSWORD:
        alarm_triggered = False
        alarm_countdown = None
        socketio.emit('alarm_defused', {'message': 'Alarm defused successfully'})
        log_event("DEFUSED", f"Alarm defused from IP: {request.remote_addr}")
        return redirect(url_for('index'))
    
    log_event("FAILED_DEFUSE", f"Wrong password attempt from IP: {request.remote_addr}")
    return redirect(url_for('index'))

@app.route('/start_detection', methods=['POST'])
def start_detection():
    global detection_active
    detection_active = True
    socketio.emit('detection_started', {'message': 'Motion detection activated'})
    log_event("DETECTION_STARTED", "Motion detection enabled")
    return redirect(url_for('index'))

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    global detection_active
    detection_active = False
    socketio.emit('detection_stopped', {'message': 'Motion detection stopped'})
    log_event("DETECTION_STOPPED", "Motion detection disabled")
    return redirect(url_for('index'))

@app.route('/manual_alarm', methods=['POST'])
def manual_alarm():
    global alarm_triggered
    alarm_triggered = True
    log_event("MANUAL_ALARM", f"Manual alarm triggered from IP: {request.remote_addr}")
    socketio.start_background_task(countdown_thread)
    return redirect(url_for('index'))

@app.route('/stop_alarm', methods=['POST'])
def stop_alarm():
    global alarm_triggered, alarm_countdown, detection_active
    alarm_triggered = False
    alarm_countdown = None
    detection_active = False
    log_event("ALARM_STOPPED", "Alarm manually stopped")
    return redirect(url_for('index'))

@app.route('/test_mode', methods=['POST'])
def test_mode():
    global alarm_triggered
    alarm_triggered = True
    log_event("TEST_MODE", "Test mode triggered")
    socketio.start_background_task(countdown_thread)
    return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    return jsonify({
        'alarm_triggered': alarm_triggered,
        'alarm_countdown': alarm_countdown,
        'detection_active': detection_active,
        'motion_detected': motion_detected,
        'frame_count': frame_count,
        'log_file': os.path.join(LOG_DIR, "security.log")
    })

@app.route('/api/logs')
def api_logs():
    log_file = os.path.join(LOG_DIR, "security.log")
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = f.readlines()[-50:]
        return jsonify({'logs': logs})
    return jsonify({'logs': []})

if __name__ == '__main__':
    port = int(os.environ.get('SECURITY_PORT', 5001))
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
