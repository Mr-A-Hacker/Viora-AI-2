import logging
import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import PORT, CAPTURES_DIR, setup_logging

def _safe_import(mod_name, attr):
    try:
        mod = __import__(mod_name, fromlist=[attr])
        return getattr(mod, attr)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("Failed to import %s from %s: %s", attr, mod_name, e)
        return None

camera_router = _safe_import("camera_stream", "router")
chat_router = _safe_import("chat_ai", "router")
ai_state = _safe_import("chat_ai", "ai")
weather_router = _safe_import("weather", "router")
maps_router = _safe_import("maps", "router")
devai_router = _safe_import("devai", "router")
games_router = _safe_import("games", "router")
security_router = _safe_import("security", "router")
terminal_router = _safe_import("terminal", "router")
file_manager_router = _safe_import("file_manager", "router")
banking_router = _safe_import("banking", "router")

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

# Include the routers (skip any that failed to import)
_routers = [
    ("camera_stream", camera_router),
    ("chat", chat_router),
    ("weather", weather_router),
    ("maps", maps_router),
    ("devai", devai_router),
    ("games", games_router),
    ("security", security_router),
    ("terminal", terminal_router),
    ("file_manager", file_manager_router),
    ("banking", banking_router),
]
for name, router in _routers:
    if router is not None:
        app.include_router(router)
    else:
        logger.warning("Skipping /%s — dependencies not available", name)

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
    if not os.environ.get("SKIP_MODEL_LOAD") and ai_state is not None:
        try:
            ai_state.load_model()
        except Exception as e:
            logger.warning("Model not loaded: %s", e)
    try:
        if ai_state is not None:
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
