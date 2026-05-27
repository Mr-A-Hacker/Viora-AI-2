import logging
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import PORT, CAPTURES_DIR, setup_logging
from camera_stream import router as camera_router
from chat_ai import router as chat_router, ai as ai_state
from weather import router as weather_router
from maps import router as maps_router
from games import router as games_router
from security import router as security_router
from terminal import router as terminal_router
from file_manager import router as file_manager_router
from banking import router as banking_router
from unified_security import trigger_voice_alert, send_alarm_to_surveillance
from knowledge import update_knowledge_async, get_knowledge, check_updates

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
    import threading
    threading.Thread(target=trigger_voice_alert, daemon=True).start()
    return {"status": "notified"}

@app.post("/security/trigger_alarm")
async def security_trigger_alarm():
    """Endpoint to trigger the alarm."""
    success = send_alarm_to_surveillance()
    return {"status": "success" if success else "error"}

@app.post("/security/stop_alarm")
async def security_stop_alarm():
    """Endpoint to stop the alarm."""
    from unified_security import stop_alarm_on_surveillance
    success = stop_alarm_on_surveillance()
    return {"status": "success" if success else "error"}

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

@app.post("/knowledge/update")
async def knowledge_update():
    result = {"status": "started", "message": "Knowledge update started in background"}
    update_knowledge_async()
    return result


@app.get("/knowledge")
async def knowledge_status():
    return get_knowledge()


@app.get("/knowledge/check")
async def knowledge_check():
    return check_updates()


@app.post("/start_surveillance")
async def start_surveillance():
    import subprocess
    import threading
    from pathlib import Path
    
    project_dir = Path(__file__).resolve().parent
    lan_surv = project_dir / "lan_surveillance.py"
    venv_python = project_dir / ".venv" / "bin" / "python"
    
    def run_surveillance():
        try:
            python_path = str(venv_python) if venv_python.exists() else "python3"
            subprocess.Popen(
                [python_path, str(lan_surv)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(project_dir)
            )
        except Exception as e:
            logger.error("Failed to start surveillance: %s", e)
    
    threading.Thread(target=run_surveillance, daemon=True).start()
    return {"status": "starting", "message": "Surveillance server starting on port 5001"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
