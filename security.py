import os
import subprocess
import threading
from fastapi import APIRouter, Response
from pydantic import BaseModel

router = APIRouter(prefix="/security", tags=["security"])

SECURITY_PASSWORD = os.environ.get("SECURITY_PASSWORD", "admin1")
_security_status = "disarmed"

class DefuseRequest(BaseModel):
    password: str

def play_alarm_sound():
    try:
        sound_file = "/home/admin/Mr-A-Hacker-pocket-Ai-version-2/static/sounds/alarm.mp3"
        if os.path.exists(sound_file):
            subprocess.Popen(["mpg123", sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["speaker-test", "-t", "sine", "-f", "440", "-l", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

@router.get("/status")
async def get_status():
    global _security_status
    return {"status": _security_status}

@router.post("/start_detection")
async def start_detection():
    global _security_status
    _security_status = "armed"
    return {"status": "detection_started", "message": "Motion detection activated"}

@router.post("/manual_alarm")
async def manual_alarm():
    global _security_status
    _security_status = "alarm"
    threading.Thread(target=play_alarm_sound, daemon=True).start()
    return {"status": "alarm_triggered", "message": "Manual alarm triggered"}

@router.post("/stop_alarm")
async def stop_alarm():
    global _security_status
    _security_status = "disarmed"
    return {"status": "alarm_stopped", "message": "Alarm stopped"}

@router.post("/defuse")
async def defuse(request: DefuseRequest):
    global _security_status
    if request.password == SECURITY_PASSWORD:
        _security_status = "disarmed"
        return {"status": "defused", "message": "Alarm defused successfully"}
    return Response(
        content='{"status":"error","message":"Incorrect password"}',
        status_code=401,
        media_type="application/json",
    )
