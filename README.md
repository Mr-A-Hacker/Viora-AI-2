# Viora AI 2

> A local-first AI assistant stack for Raspberry Pi/Linux with chat, voice, camera, tools, task scheduling, and an Electron UI.

Viora AI combines a FastAPI backend with a React/Electron desktop frontend. It is designed to run mostly on-device and can integrate with local models (Qwen + Function Gemma), offline speech tools (Vosk/Piper), camera streaming/detection, and utility modules (files, terminal, maps, weather, games, security, and banking simulator).

---

## Table of Contents

- [What this project includes](#what-this-project-includes)
- [Architecture](#architecture)
- [Repository layout](#repository-layout)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Configuration (`.env`)](#configuration-env)
- [Models](#models)
- [Run modes](#run-modes)
- [API overview](#api-overview)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security notes](#security-notes)
- [Roadmap ideas](#roadmap-ideas)

---

## What this project includes

### Core assistant
- Multi-conversation chat memory persisted in `conversations.json`.
- WebSocket chat streaming endpoint.
- Voice endpoint for STT → LLM → TTS flow.
- Optional semantic routing between "basic" and tool-oriented model behavior.

### Voice
- **Whisper** (faster-whisper) support.
- **Vosk** support for fully offline STT.
- **Piper TTS** output (`piper-tts`, `onnxruntime`).

### Camera & vision
- Live camera stream + capture gallery.
- Camera start/stop controls.
- Optional detection pipeline and detection websocket.

### Utility modules
- Weather (Open-Meteo).
- Maps geocoding/reverse geocoding + Organic Maps launcher.
- DevAI code assistant endpoints.
- File manager endpoints.
- Terminal execution endpoint (with basic blocklist).
- Security controls + alarm trigger routes.
- Game discovery/launch module.
- Banking demo module (local JSON-backed simulation).

---

## Architecture

- **Backend:** FastAPI (`app.py`) with modular routers.
- **Frontend:** Electron + React app under `chat-gui/`.
- **Transport:** REST + WebSocket.
- **Storage:** Flat JSON files in repo root by default (`conversations.json`, `task_jobs.json`, `banking_data.json`).
- **Model delivery:** Hugging Face Hub downloads for GGUF models.

---

## Repository layout

High-signal files/folders:

```text
app.py                    # Backend entrypoint, includes all routers
config.py                 # Environment-driven backend configuration
chat_ai.py                # Conversation manager + chat/voice websocket logic
camera_stream.py          # Camera pipeline, gallery, detection ws
devai.py                  # Dev assistant routes + indexing/search utilities
task_scheduler.py         # Scheduler initialization / job persistence
terminal.py               # Terminal command execution route
file_manager.py           # File browsing/manipulation routes
banking.py                # Local banking simulation CRUD API
weather.py                # Open-Meteo integration
maps.py                   # Nominatim + Organic Maps launcher
security.py               # Arm/disarm/manual alarm endpoints
chat-gui/                 # Electron + React desktop interface
requirements.txt          # Backend Python dependencies
.env.example              # Baseline environment variables
run.sh                    # Portable launcher (backend + GUI)
start_viora_ai.sh         # Alternate launcher script
```

---

## Requirements

### Hardware (recommended)
- Raspberry Pi 5 (Pi 4 minimum) or Linux PC.
- 8 GB RAM recommended.
- USB mic / speaker setup.
- USB or CSI camera (optional).

### System packages (Debian/Ubuntu baseline)

```bash
sudo apt-get update
sudo apt-get install -y \
  python3 python3-venv python3-pip \
  build-essential cmake git curl \
  portaudio19-dev libopenblas-dev liblapack-dev
```

### Language/tooling
- Python 3.10+
- Node.js 18+
- npm

---

## Quick start

### 1) Clone

```bash
git clone <your-fork-or-this-repo-url>
cd Viora-AI-2
```

### 2) Backend setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 3) Frontend setup

```bash
cd chat-gui
npm install
cd ..
```

### 4) Configure env

```bash
cp .env.example .env
```

Edit `.env` as needed.

### 5) Run

Portable launcher (recommended):

```bash
./run.sh
```

Manual split terminals:

```bash
# terminal A
source .venv/bin/activate
python app.py

# terminal B
cd chat-gui
npm run dev
```

Alternative launcher:

```bash
./start_viora_ai.sh
```

`start_viora_ai.sh` now verifies `.venv` exists and prints recovery steps if it is missing.

---

## Configuration (`.env`)

The backend reads from environment variables in `config.py`.

Common variables:

```env
PORT=8000
CONVERSATIONS_FILE=conversations.json
TOOLS_PATH=tools.json
JOBS_FILE=task_jobs.json
LOCAL_DIR=./models
CAPTURES_DIR=captures

CHAT_REPO_ID=Qwen/Qwen3-0.6B-GGUF
CHAT_FILENAME=Qwen3-0.6B-Q8_0.gguf

TOOL_REPO_ID=nlouis/functiongemma-pocket-q4_k_m
TOOL_FILENAME=functiongemma-pocket-q4_k_m.gguf

USE_WHISPER=true
USE_VOSK=false
VOSK_MODEL=./models/vosk/vosk-model-small-en-us-0.15

PIPER_MODEL=en_US-lessac-medium.onnx
```

Useful runtime flags:
- `SKIP_MODEL_LOAD=1` to skip model loading on startup (great for tests/dev bring-up).
- `LOG_LEVEL=DEBUG` for deeper logs.

---

## Models

### Chat model (GGUF)
Configured by:
- `CHAT_REPO_ID`
- `CHAT_FILENAME`

### Tool model (GGUF)
Configured by:
- `TOOL_REPO_ID`
- `TOOL_FILENAME`

### STT/TTS assets
- Whisper models download on demand via `faster-whisper`.
- Vosk model path is set by `VOSK_MODEL`.
- Piper ONNX model should be available to the runtime (commonly in `models/piper/`).

---

## Run modes

### Development mode
- Use `SKIP_MODEL_LOAD=1` if you’re only working UI/API plumbing.
- Start backend + frontend separately for easier debugging.

### Desktop mode
- `chat-gui` uses Electron/Vite (`npm run dev`, `npm run build`).

### Headless/backend mode
- Just run `python app.py` and call APIs from your own client.

---

## API overview

Base backend port defaults to `8000`.

### Health
- `GET /health`

Quick check:

```bash
curl -s http://127.0.0.1:8000/health
```

### Chat + tasks
- `GET /conversations`
- `POST /conversations`
- `GET /conversations/{conv_id}`
- `DELETE /conversations/{conv_id}`
- `GET /tasks`
- `POST /tasks`
- `DELETE /tasks/{job_id}`
- `WS /ws/chat/{conv_id}`
- `WS /ws/voice`

### Camera
- `GET /camera/list`
- `POST /camera/start`
- `POST /camera/stop`
- `GET /video_feed`
- `POST /camera/capture`
- `GET /gallery/images`
- `DELETE /gallery/images/{filename}`
- `WS /ws/detections`

### Dev AI
- `POST /devai/chat`
- `POST /devai/chat/stream`
- `GET /devai/status`
- `POST /devai/index`
- `GET /devai/search`
- `GET /devai/analyze`
- `POST /devai/reasoning`

### Utilities
- Weather: `GET /weather`
- Maps: `GET /maps/search`, `GET /maps/reverse`, `POST /maps/open`
- Security: `/security/*`
- Files: `/files/*`
- Terminal: `/terminal/*`
- Banking: `/banking/*`
- Games: `/games`, `/games/launch`

OpenAPI docs (while running):
- `http://127.0.0.1:8000/docs`

---

## Testing

Run test suite:

```bash
source .venv/bin/activate
pytest tests/
```

Targeted sanity checks:

```bash
python -m py_compile app.py banking.py
python -m pytest tests/test_api.py
```

---

## Troubleshooting

### Backend fails at startup
- Confirm venv activation.
- Confirm dependencies from `requirements.txt` are installed.
- Try `SKIP_MODEL_LOAD=1 python app.py` to isolate model-loading issues.

### GUI cannot connect to backend
- Ensure backend is reachable at `127.0.0.1:8000`.
- Check CORS/network/firewall in your environment.

### No audio input/output
- Verify mic/speaker devices with system tools (`arecord -l`, `aplay -l`).
- Install `portaudio19-dev` before installing PyAudio.

### Camera not detected
- Verify camera permissions/device index.
- Try forcing `CAMERA_INDEX` env var.

### Maps/weather failing
- Those endpoints require internet access to public APIs.

---

## Security notes

This project includes powerful endpoints (`/terminal`, `/files`, process launchers). For production or network-exposed usage:

- Restrict network exposure (bind localhost or reverse proxy with auth).
- Add authentication/authorization middleware.
- Add rate limits + audit logging.
- Harden the terminal/file manager routes before multi-user deployment.

---

## Roadmap ideas

- Add auth + role-based access control.
- Replace JSON flat files with SQLite/PostgreSQL.
- Add proper secrets management.
- Add CI (lint/tests) and release workflows.
- Add typed API client for frontend.

---

If you build something cool with Viora AI, consider documenting your hardware + model setup in a PR so others can reproduce it quickly.
