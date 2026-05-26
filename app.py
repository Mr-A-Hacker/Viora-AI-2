import logging
import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import PORT, CAPTURES_DIR, setup_logging
from camera_stream import router as camera_router
from chat_ai import router as chat_router, ai as ai_state
from weather import router as weather_router
from maps import router as maps_router
from devai import router as devai_router
from games import router as games_router
from security import router as security_router
from terminal import router as terminal_router
from file_manager import router as file_manager_router
from banking import router as banking_router
try:
    from unified_security import trigger_voice_alert, send_alarm_to_surveillance
except ImportError:
    trigger_voice_alert = None
    send_alarm_to_surveillance = None

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Viora AI Unified Backend")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for gallery
os.makedirs(CAPTURES_DIR, exist_ok=True)
app.mount("/captures", StaticFiles(directory=CAPTURES_DIR), name="captures")

# Include the routers
app.include_router(camera_router)
app.include_router(chat_router)
app.include_router(weather_router)
app.include_router(maps_router)
app.include_router(devai_router)
app.include_router(games_router)
app.include_router(security_router)
app.include_router(terminal_router)
app.include_router(file_manager_router)
app.include_router(banking_router)

@app.get("/health")
async def health():
    """Simple health check for monitoring and tests."""
    return {"status": "ok"}

@app.post("/security/motion_detected")
async def security_motion_detected(request: dict):
    """Endpoint to receive motion detection from security camera."""
    if trigger_voice_alert:
        import threading
        threading.Thread(target=trigger_voice_alert, daemon=True).start()
    return {"status": "notified"}

@app.post("/security/trigger_alarm")
async def security_trigger_alarm():
    """Endpoint to trigger the alarm."""
    if send_alarm_to_surveillance:
        success = send_alarm_to_surveillance()
        return {"status": "success" if success else "error"}
    return {"status": "error", "message": "unified_security not available"}

@app.post("/security/stop_alarm")
async def security_stop_alarm():
    """Endpoint to stop the alarm."""
    try:
        from unified_security import stop_alarm_on_surveillance
        success = stop_alarm_on_surveillance()
        return {"status": "success" if success else "error"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.on_event("startup")
async def startup_event():
    logger.info("Unified Backend starting up...")
    if not os.environ.get("SKIP_MODEL_LOAD"):
        ai_state.load_model()
        # Dev AI model loads on first request (lazy)
    try:
        from task_scheduler import init_scheduler
        init_scheduler(ai_state.conv_manager)
    except Exception as e:
        logger.warning("Task scheduler not started: %s", e)
    logger.info("Unified Backend ready.")

@app.post("/shutdown")
async def shutdown():
    import threading
    import time
    def delayed_exit():
        time.sleep(1)
        os._exit(0)
    threading.Thread(target=delayed_exit, daemon=True).start()
    return {"status": "shutting down..."}

@app.post("/start_surveillance")
async def start_surveillance():
    import subprocess
    import threading
    
    def run_surveillance():
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            python = sys.executable
            subprocess.Popen(
                [python, os.path.join(base, "lan_surveillance.py")],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=base
            )
        except Exception as e:
            print(f"Failed to start surveillance: {e}")
    
    threading.Thread(target=run_surveillance, daemon=True).start()
    return {"status": "starting", "message": "Surveillance server starting on port 5001"}

# Serve built React frontend (if available) so no Electron GUI is needed
frontend_build = os.path.join(os.path.dirname(__file__), "chat-gui", "out", "renderer")
if os.path.isdir(frontend_build):
    app.mount("/", StaticFiles(directory=frontend_build, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
