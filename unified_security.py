"""
Unified Security System Integration
Bridges lan_surveillance_system with Mr-A-Hacker-pocket-Ai-version-2 (Viora AI)

Flow:
1. Camera detects human movement -> Notify Viora AI
2. Viora AI speaks: "Someone has entered your room."
3. Viora AI asks: "Do I sound the alarm?"
4. If user says yes -> Trigger alarm on surveillance system
"""
import asyncio
import json
import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

import requests
from flask import Flask
from flask_socketio import SocketIO

PROJECT_ROOT = Path(__file__).resolve().parent

logger = logging.getLogger(__name__)

SURVEILLANCE_PORT = 5051
VIORA_PORT = 8000

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

state = {
    "motion_detected": False,
    "alarm_triggered": False,
    "alarm_answered": False,
    "user_answer": None,
    "surveillance_active": False,
    "awaiting_response": False,
}

_detection_thread = None
_surveillance_process = None


_tts = None
try:
    from tts_piper import PocketAudio
    _tts = PocketAudio()
    logger.info("PocketAudio TTS loaded for unified security")
except Exception as e:
    logger.warning(f"PocketAudio not available: {e}")


def speak(text: str):
    """Speak text via TTS - integrates with Pocket-AI's TTS system."""
    if _tts:
        try:
            _tts.speak(text)
            return
        except Exception as e:
            logger.warning(f"TTS speak error: {e}")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass


def notify_pocket_ai(motion_type: str = "person"):
    """Notify Pocket-AI backend about motion detection via WebSocket or REST."""
    try:
        requests.post(
            f"http://127.0.0.1:{VIORA_PORT}/security/motion_detected",
            json={"type": motion_type, "timestamp": time.time()},
            timeout=5
        )
    except Exception as e:
        logger.warning(f"Failed to notify Pocket-AI: {e}")


def trigger_voice_alert():
    """Trigger the voice alert flow: announce motion, ask about alarm."""
    global state
    
    if state.get("awaiting_response"):
        return
    
    state["awaiting_response"] = True
    state["motion_detected"] = True
    state["alarm_answered"] = False
    state["user_answer"] = None
    
    speak("Someone has entered your room.")
    time.sleep(1)
    speak("Do I sound the alarm?")
    
    state["awaiting_response"] = False


def send_alarm_to_surveillance():
    """Send alarm trigger command to surveillance system."""
    try:
        response = requests.post(
            f"http://127.0.0.1:{SURVEILLANCE_PORT}/manual_alarm",
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to trigger alarm: {e}")
        return False


def stop_alarm_on_surveillance():
    """Stop alarm on surveillance system."""
    try:
        response = requests.post(
            f"http://127.0.0.1:{SURVEILLANCE_PORT}/stop_alarm",
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to stop alarm: {e}")
        return False


def get_surveillance_status():
    """Get current status from surveillance system."""
    try:
        response = requests.get(
            f"http://127.0.0.1:{SURVEILLANCE_PORT}/api/status",
            timeout=5
        )
        return response.json() if response.status_code == 200 else {}
    except:
        return {}


def start_surveillance():
    """Start the surveillance system."""
    global _surveillance_process
    
    if state.get("surveillance_active"):
        return {"status": "already_running"}
    
    try:
        surveillance_path = PROJECT_ROOT / "lan_surveillance.py"
        if surveillance_path.exists():
            _surveillance_process = subprocess.Popen(
                ["/usr/bin/python3", str(surveillance_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(PROJECT_ROOT)
            )
            state["surveillance_active"] = True
            logger.info("Surveillance system started")
            return {"status": "started"}
        else:
            return {"status": "error", "message": "Surveillance file not found"}
    except Exception as e:
        logger.error(f"Failed to start surveillance: {e}")
        return {"status": "error", "message": str(e)}


def stop_surveillance():
    """Stop the surveillance system."""
    global _surveillance_process
    
    if _surveillance_process:
        _surveillance_process.terminate()
        _surveillance_process = None
    
    state["surveillance_active"] = False
    logger.info("Surveillance system stopped")
    return {"status": "stopped"}


@socketio.on('connect')
def handle_connect():
    logger.debug("Client connected to unified security")


@socketio.on('detection_alert')
def handle_detection_alert(data):
    """Handle motion detection alert from surveillance system."""
    logger.info(f"Motion detected: {data}")
    
    state["motion_detected"] = True
    
    socketio.emit('motion_detected', data)
    
    threading.Thread(target=trigger_voice_alert, daemon=True).start()


@socketio.on('alarm_triggered')
def handle_alarm_triggered(data):
    """Handle alarm triggered event."""
    logger.info(f"Alarm triggered: {data}")
    state["alarm_triggered"] = True
    socketio.emit('alarm_status', {"status": "triggered"})


@socketio.on('alarm_defused')
def handle_alarm_defused(data):
    """Handle alarm defused event."""
    logger.info(f"Alarm defused: {data}")
    state["alarm_triggered"] = False
    state["alarm_answered"] = False
    state["user_answer"] = None
    socketio.emit('alarm_status', {"status": "defused"})


@app.route('/api/status')
def api_status():
    """Get unified security system status."""
    surv_status = get_surveillance_status()
    return jsonify({
        **state,
        "surveillance": surv_status
    })


@app.route('/api/motion_detected', methods=['POST'])
def api_motion_detected():
    """API endpoint for motion detection notification."""
    data = request.get_json() or {}
    thread = threading.Thread(target=trigger_voice_alert, daemon=True)
    thread.start()
    return jsonify({"status": "notified"})


@app.route('/api/trigger_alarm', methods=['POST'])
def api_trigger_alarm():
    """Manually trigger the alarm through surveillance system."""
    success = send_alarm_to_surveillance()
    if success:
        state["alarm_triggered"] = True
        speak("Alarm triggered!")
    return jsonify({"status": "success" if success else "error"})


@app.route('/api/stop_alarm', methods=['POST'])
def api_stop_alarm():
    """Stop the alarm."""
    success = stop_alarm_on_surveillance()
    if success:
        state["alarm_triggered"] = False
        speak("Alarm stopped.")
    return jsonify({"status": "success" if success else "error"})


@app.route('/api/user_answer', methods=['POST'])
def api_user_answer():
    """Record user's answer to 'Do I sound the alarm?'"""
    data = request.get_json() or {}
    answer = data.get("answer", "").lower()
    
    state["alarm_answered"] = True
    state["user_answer"] = answer
    
    if answer in ["yes", "yeah", "sure", "yep", "do it", "trigger"]:
        speak("Sounding the alarm!")
        send_alarm_to_surveillance()
        return jsonify({"status": "alarm_triggered", "action": "triggered"})
    else:
        speak("Alarm cancelled.")
        return jsonify({"status": "alarm_cancelled", "action": "cancelled"})


@app.route('/api/start_surveillance', methods=['POST'])
def api_start_surveillance():
    """Start the surveillance system."""
    return jsonify(start_surveillance())


@app.route('/api/stop_surveillance', methods=['POST'])
def api_stop_surveillance():
    """Stop the surveillance system."""
    return jsonify(stop_surveillance())


from flask import jsonify, request


def connect_to_surveillance():
    """Connect to surveillance system's Socket.IO to receive events."""
    try:
        import socketio as socketio_client

        def receive_surveillance_events():
            client = socketio_client.SimpleClient()
            try:
                client.connect(f'http://127.0.0.1:{SURVEILLANCE_PORT}')
                logger.info("Connected to surveillance system")
                while True:
                    event = client.receive()
                    if event:
                        event_name = event[0]
                        event_data = event[1] if len(event) > 1 else {}

                        if event_name == 'detection_alert':
                            handle_detection_alert(event_data)
                        elif event_name == 'alarm_triggered':
                            handle_alarm_triggered(event_data)
                        elif event_name == 'alarm_defused':
                            handle_alarm_defused(event_data)
            except Exception as e:
                logger.warning(f"Surveillance connection error: {e}")

        threading.Thread(target=receive_surveillance_events, daemon=True).start()
    except Exception as e:
        logger.warning(f"SocketIO client not available, using polling fallback: {e}")
        start_polling_surveillance()


def start_polling_surveillance():
    """Fallback: poll surveillance system for status changes."""
    import threading
    
    def poll_loop():
        last_alarm_state = None
        while True:
            try:
                status = get_surveillance_status()
                current_alarm = status.get("alarm_triggered")
                
                if current_alarm != last_alarm_state:
                    if current_alarm and not last_alarm_state:
                        handle_alarm_triggered({"source": "poll"})
                    elif not current_alarm and last_alarm_state:
                        handle_alarm_defused({"source": "poll"})
                    last_alarm_state = current_alarm
                
                motion = status.get("motion_detected") or status.get("motion_detected")
                if motion and not state.get("motion_detected"):
                    handle_detection_alert({"type": "motion", "source": "poll"})
                    
            except Exception as e:
                logger.debug(f"Poll error: {e}")
            
            time.sleep(2)
    
    threading.Thread(target=poll_loop, daemon=True).start()


def start_integration():
    """Start the unified security integration server."""
    logger.info("Starting Unified Security Integration...")
    
    try:
        connect_to_surveillance()
    except Exception as e:
        logger.warning(f"SocketIO connection failed, using polling: {e}")
        start_polling_surveillance()
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_integration()
