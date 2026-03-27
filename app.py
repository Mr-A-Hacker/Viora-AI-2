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
from devai import router as devai_router
from games import router as games_router

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

@app.get("/health")
async def health():
    """Simple health check for monitoring and tests."""
    return {"status": "ok"}

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
