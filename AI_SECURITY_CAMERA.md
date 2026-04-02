# AI-Powered Security Camera System

An enhanced version of the LAN surveillance system with AI-based person/face detection, recording, and alerts.

## Features

- **AI Object Detection**: Uses Hailo-8 HAT with YOLOv11 for real-time person/face detection
- **Motion Detection**: Traditional motion detection as backup
- **Alarm System**: Countdown timer before alarm triggers (configurable)
- **Recording**: Automatic recording on detection events
- **Pre/Post Recording**: Captures buffer before and after events
- **Real-time Alerts**: WebSocket notifications for instant updates
- **Modern Dashboard**: Responsive web UI with live video feed
- **Voice Alerts**: TTS announcements using pyttsx3
- **Sound Alarms**: Configurable alarm sounds

## Requirements

```bash
pip install flask flask-socketio eventlet pygame pyttsx3 opencv-python numpy
```

## Running the System

```bash
python ai_security_camera.py
```

The system will start on `http://0.0.0.0:5050`

## Default Password

The default password is `11115`. Change it via:
- Environment variable: `SECURITY_PASSWORD`
- Edit the `app.config['SECURITY_PASSWORD']` in the code

## Usage

1. **Login**: Enter password to access dashboard
2. **Arm System**: Click "ARM SYSTEM" to enable monitoring
3. **Detection**: AI detection starts automatically when armed
4. **Alerts**: 
   - Motion triggers countdown
   - After countdown, alarm sounds
   - Enter password to defuse
5. **Capture**: Click "CAPTURE" to save current frame

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard |
| `/login` | POST | Authenticate |
| `/arm` | POST | Arm system |
| `/disarm` | POST | Disarm system |
| `/defuse` | POST | Defuse alarm |
| `/video_feed` | GET | MJPEG stream |
| `/capture` | POST | Capture image |
| `/api/status` | GET | System status |
| `/recordings` | GET | List recordings |

## Configuration

Edit the `CONFIG` dict in `ai_security_camera.py`:

```python
CONFIG = {
    'COUNTDOWN_TIME': 10,        # Seconds before alarm
    'ALARM_COOLDOWN': 30,         # Cooldown between triggers
    'PERSON_CONFIDENCE_THRESHOLD': 0.5,
    'MOTION_THRESHOLD': 500,
    'RECORD_ON_DETECTION': True,
    'PRE_RECORD_SECONDS': 5,
    'POST_RECORD_SECONDS': 10,
}
```

## Hardware Support

- **Raspberry Pi**: Picamera2 support
- **USB Cameras**: Automatic detection
- **Hailo-8 HAT**: AI inference on device
