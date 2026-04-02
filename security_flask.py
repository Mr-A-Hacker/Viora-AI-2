import os
import subprocess
import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECURITY_SECRET", "secret123")
socketio = SocketIO(app, cors_allowed_origins="*")

SECURITY_PASSWORD = os.environ.get("SECURITY_PASSWORD", "admin123")
ALARM_COUNTDOWN_SECONDS = 10
alarm_triggered = False
alarm_countdown = None
detection_active = False

def play_alarm_sound():
    try:
        sound_file = os.path.join(os.path.dirname(__file__), "static/sounds/alarm.mp3")
        if os.path.exists(sound_file):
            subprocess.Popen(["mpg123", "-q", sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["speaker-test", "-t", "sine", "-f", "440", "-l", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def countdown_thread():
    global alarm_countdown
    for i in range(ALARM_COUNTDOWN_SECONDS, -1, -1):
        alarm_countdown = i
        socketio.emit('countdown', {'seconds': i})
        socketio.sleep(1)
    if alarm_triggered:
        socketio.emit('alarm_triggered', {'message': 'BREACH DETECTED'})
        threading.Thread(target=play_alarm_sound, daemon=True).start()

@app.route('/')
def index():
    return render_template('security_dashboard.html')

@app.route('/raw_feed')
def raw_feed():
    return "Camera feed would display here"

@app.route('/video_feed')
def video_feed():
    return "Video feed would display here"

@app.route('/security', methods=['POST'])
def security():
    password = request.form.get('password')
    global alarm_triggered, alarm_countdown
    if password == SECURITY_PASSWORD:
        alarm_triggered = False
        alarm_countdown = None
        socketio.emit('alarm_defused', {'message': 'Alarm defused'})
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/start_detection', methods=['POST'])
def start_detection():
    global detection_active
    detection_active = True
    socketio.emit('detection_started', {'message': 'Motion detection active'})
    return redirect(url_for('index'))

@app.route('/manual_alarm', methods=['POST'])
def manual_alarm():
    global alarm_triggered
    alarm_triggered = True
    socketio.start_background_task(countdown_thread)
    return redirect(url_for('index'))

@app.route('/stop_alarm', methods=['POST'])
def stop_alarm():
    global alarm_triggered, alarm_countdown, detection_active
    alarm_triggered = False
    alarm_countdown = None
    detection_active = False
    return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    return jsonify({
        'alarm_triggered': alarm_triggered,
        'alarm_countdown': alarm_countdown,
        'detection_active': detection_active
    })

if __name__ == '__main__':
    port = int(os.environ.get('SECURITY_PORT', 5001))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
