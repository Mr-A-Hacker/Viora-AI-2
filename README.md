<div align="center">

```
 ██╗   ██╗██╗ ██████╗ ██████╗  █████╗      █████╗ ██╗    ██████╗
 ██║   ██║██║██╔═══██╗██╔══██╗██╔══██╗    ██╔══██╗██║    ╚════██╗
 ██║   ██║██║██║   ██║██████╔╝███████║    ███████║██║     █████╔╝
 ╚██╗ ██╔╝██║██║   ██║██╔══██╗██╔══██║    ██╔══██║██║    ██╔═══╝
  ╚████╔╝ ██║╚██████╔╝██║  ██║██║  ██║    ██║  ██║██║    ███████╗
   ╚═══╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝  ╚═╝╚═╝    ╚══════╝
```

### *Your fully offline, voice-powered AI assistant — built for Raspberry Pi and Linux.*
### *No cloud. No subscriptions. No limits.*

</div>

---

## What is Viora AI?

Viora AI 2 is a privacy-first, fully offline AI assistant that runs entirely on your own hardware. No cloud services, no API keys, no data leaving your machine.

It combines:
- **Local LLM chat** (Qwen 0.6B GGUF) — real-time conversations, markdown, code blocks
- **Speech-to-text** via Whisper or Vosk — talk to it naturally
- **Text-to-speech** via Piper TTS — it talks back
- **Vision** — live camera feed with optional Hailo-8 NPU object detection
- **Task scheduling** — set reminders and recurring tasks
- **Weather, maps, file management, coding assistant, games, security surveillance**

You can use it either way:
- **CLI mode** (new): `viora` — runs the backend + web UI, open in browser
- **Electron mode**: Full-screen desktop app with touch support

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Mr-A-Hacker/Viora-AI-2.git
cd Viora-AI-2

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install system dependencies
sudo apt-get update && sudo apt-get install -y \
  portaudio19-dev cmake libopenblas-dev liblapack-dev ffmpeg espeak-ng

# 5. Install frontend dependencies
cd chat-gui && npm install && cd ..

# 6. Build the frontend (for CLI/browser mode)
cd chat-gui && npm run build && cd ..

# 7. Configure
cp .env.example .env
# Edit .env as needed

# 8. Install the viora CLI
sudo ln -sf "$(pwd)/viora" /usr/local/bin/viora

# 9. Launch
viora
```

Open **http://localhost:8000** in your browser.

---

## Installation (Detailed)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Mr-A-Hacker/Viora-AI-2.git
cd Viora-AI-2
```

### Step 2 — Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You'll need to activate the venv (`source .venv/bin/activate`) every time you work with Viora.

### Step 3 — Install Python Packages

```bash
pip install -r requirements.txt
```

This installs: FastAPI, Uvicorn, llama-cpp-python, faster-whisper, vosk, piper-tts, opencv, APScheduler, and all other dependencies.

If you run into issues on Raspberry Pi (arm64), you may need:
```bash
pip install --force-reinstall --no-cache-dir llama-cpp-python==0.3.16
```

### Step 4 — System Dependencies

```bash
sudo apt-get update && sudo apt-get install -y \
  portaudio19-dev cmake libopenblas-dev liblapack-dev ffmpeg espeak-ng
```

### Step 5 — Install Frontend

```bash
cd chat-gui
npm install
cd ..
```

### Step 6 — Build the Frontend

Required for CLI/browser mode. Skip if you only want Electron mode.

```bash
cd chat-gui
npm run build
cd ..
```

This creates the static web UI in `chat-gui/out/renderer/`.

### Step 7 — Download AI Models

**LLM — Qwen 0.6B GGUF (required for chat)**
```bash
mkdir -p models/qwen
huggingface-cli download Qwen/Qwen3-0.6B-GGUF \
  Qwen3-0.6B-Q8_0.gguf \
  --local-dir models/qwen/
```

**Tool LLM — Function Gemma (required for tool calling)**
```bash
huggingface-cli download nlouis/functiongemma-pocket-q4_k_m \
  functiongemma-pocket-q4_k_m.gguf \
  --local-dir models/
```

**Piper TTS Voice (required for speech output)**
```bash
mkdir -p models/piper
wget -O models/piper/en_US-lessac-medium.onnx \
  https://github.com/rhasspy/piper/releases/download/2024.11.14-2/en_US-lessac-medium.onnx
wget -O models/piper/en_US-lessac-medium.onnx.json \
  https://github.com/rhasspy/piper/releases/download/2024.11.14-2/en_US-lessac-medium.onnx.json
```

**Vosk STT (required for offline speech input)**
```bash
mkdir -p models/vosk && cd models/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
cd ../..
```

### Step 8 — Configure

```bash
cp .env.example .env
nano .env
```

Key settings:
| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Backend API port |
| `SECURITY_PASSWORD` | (empty) | Set a password for security features |
| `OPENCODE_PATH` | `opencode` | Path to opencode binary (for Dev AI) |
| `SKIP_MODEL_LOAD` | (unset) | Set to `1` to skip LLM loading on startup |

### Step 9 — Install the viora CLI

```bash
sudo ln -sf "$(pwd)/viora" /usr/local/bin/viora
```

Now you can run `viora` from anywhere.

### Step 10 — Launch

```bash
source .venv/bin/activate
viora
```

Open **http://localhost:8000** or **http://<your-pi-ip>:8000** from any device on your network.

---

## How to Run

### CLI / Browser Mode (Recommended)

```bash
source .venv/bin/activate
viora
```

Opens the backend on port 8000. The built React UI is served directly by the backend — no Electron needed. Open a browser to `http://localhost:8000`.

The `viora` CLI:
- Auto-detects the project `.venv`
- Starts the FastAPI backend (serving API + frontend)
- Handles Ctrl+C cleanly
- Gracefully skips features with missing dependencies

### Electron Desktop App

```bash
cd chat-gui
npm run dev
```

Runs the Electron full-screen GUI alongside the backend.

### Build Electron App

```bash
cd chat-gui
npm run build
# App packaged in chat-gui/out/
```

### Manual Launch (No CLI)

```bash
# Terminal 1: Backend
source .venv/bin/activate
python app.py

# Terminal 2: Frontend dev server (optional, for development)
cd chat-gui && npm run dev
```

---

## What Each File Does

| File | Purpose |
|------|---------|
| `app.py` | FastAPI backend — serves API + frontend |
| `viora` | CLI launcher script |
| `chat_ai.py` | Core chat pipeline: STT -> LLM -> TTS |
| `stt_whisper.py` | Whisper speech recognition |
| `stt_vosk.py` | Vosk offline speech recognition |
| `tts_piper.py` | Piper text-to-speech |
| `semantic_router_ai.py` | Routes prompts to correct model |
| `tool_ai.py` | Function Gemma tool calling |
| `task_scheduler.py` | APScheduler task/job management |
| `weather.py` | Open-Meteo weather API |
| `maps.py` | Organic Maps launcher |
| `devai.py` | OpenCode Dev AI endpoint |
| `camera_stream.py` | MJPEG camera streaming |
| `security.py` | Security alarm FastAPI endpoints |
| `lan_surveillance.py` | LAN surveillance Flask server |
| `ai_security_camera.py` | AI-powered security camera |
| `file_manager.py` | File management API |
| `games.py` | Games module |
| `terminal.py` | Terminal command execution |
| `banking.py` | Banking/finance API |
| `config.py` | Centralized configuration |
| `agent.py` | Local developer agent (CLI) |
| `chat-gui/` | Electron + React frontend |

---

## Features

### Chat
Converse naturally via voice or text. Qwen 0.6B GGUF runs locally. Responses stream in real-time. Full markdown, code highlighting, multi-turn conversations.

### Voice Input
Two engines:
- **Whisper Tiny** — fast, needs internet only for first download
- **Vosk** — fully offline, lightweight

Switch between them in Settings.

### Voice Output
Piper TTS gives natural speech. Swap voices in `models/piper/`.

### Vision
USB webcam or Pi Camera Module. Live MJPEG stream, photo capture, Hailo-8 NPU object detection (optional).

### Task Scheduler
Set reminders with APScheduler. Persists across reboots.

### Weather
Open-Meteo, free, no API key. Temperature, humidity, wind, precipitation.

### Maps
Launches Organic Maps — offline navigation, no tracking.

### Dev AI
OpenCode-powered coding assistant built in. Write, debug, refactor code.

### Security
Motion detection, alarm, LAN surveillance dashboard. Accessible at `http://localhost:5001` when running.

---

## Configuration

Full `.env` reference:

```env
# Ports
PORT=8000
FRONTEND_PORT=5173

# Model Paths
LOCAL_DIR=./models
CHAT_REPO_ID=Qwen/Qwen3-0.6B-GGUF
CHAT_FILENAME=Qwen3-0.6B-Q8_0.gguf
TOOL_REPO_ID=nlouis/functiongemma-pocket-q4_k_m
TOOL_FILENAME=functiongemma-pocket-q4_k_m.gguf

# Speech-to-Text
USE_WHISPER=true
USE_VOSK=true
VOSK_MODEL=models/vosk/vosk-model-small-en-us-0.15

# Text-to-Speech
PIPER_MODEL=en_US-lessac-medium.onnx
PIPER_SPEED=1.0

# Camera
CAMERA_DEVICE=0
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720

# LLM Generation
MAX_TOKENS=2048
TEMPERATURE=0.7
TOP_P=0.9
CONTEXT_LENGTH=4096

# Feature Toggles
ENABLE_CAMERA=true
ENABLE_TTS=true
ENABLE_STT=true
ENABLE_LLM=true
ENABLE_HAILO=false

# Security
SECURITY_PASSWORD=

# Dev AI
OPENCODE_PATH=opencode

# Default Weather Location
LATITUDE=51.5074
LONGITUDE=-0.1278
```

---

## Running on Raspberry Pi

### Enable Camera
```bash
sudo raspi-config  # Interface Options -> Camera -> Enable
sudo reboot
```

### Optimize Memory
```bash
# In /boot/firmware/config.txt (Pi 4/5):
gpu_mem=128
```

### Use Lite Quantization
Set in `.env`:
```env
CHAT_FILENAME=Qwen3-0.6B-Q4_K_M.gguf
MAX_TOKENS=512
```

### Free Resources
```bash
sudo systemctl stop bluetooth avahi-daemon
```

---

## Offline Capabilities

| Feature | Works Offline? | Notes |
|---------|---------------|-------|
| Chat | Yes | Fully local LLM |
| Vosk STT | Yes | Always offline |
| Whisper STT | Partial | First download needs internet |
| Piper TTS | Yes | Always offline |
| Camera | Yes | No internet needed |
| Object detection | Yes | Runs on NPU |
| Tasks | Yes | Local scheduler |
| Photos | Yes | Local storage |
| Maps | Yes | Offline maps |
| Weather | No | Requires Open-Meteo API |
| Dev AI | Yes | Local LLM |

---

## Troubleshooting

### "No module named 'uvicorn'"
```bash
source .venv/bin/activate
pip install uvicorn fastapi
```

### Server crashes at startup
The `viora` CLI skips features with missing dependencies. If it still crashes, run with verbose output:
```bash
source .venv/bin/activate
python app.py
```

### Camera not found
```bash
ls /dev/video*
sudo usermod -a -G video $USER
# Log out and back in
```

### Port 8000 already in use
```bash
lsof -i :8000
pkill -f "python app.py"
```

### Frontend shows blank page
```bash
cd chat-gui && npm run build && cd ..
# Then restart viora
```

### No audio
```bash
speaker-test -c 2 -t wav
# Raspberry Pi HDMI:
sudo raspi-config  # Advanced -> Audio -> HDMI
```

---

## Testing

```bash
source .venv/bin/activate
pytest tests/ -v
python test_viora_ai.py
python test_audio.py
python test_gemma.py
python speed_test.py
```

---

## Project Structure

```
Viora-AI-2/
├── app.py                 # FastAPI backend
├── viora                  # CLI launcher
├── chat_ai.py             # Core chat pipeline
├── stt_whisper.py         # Whisper STT
├── stt_vosk.py            # Vosk STT
├── tts_piper.py           # Piper TTS
├── semantic_router_ai.py  # Prompt routing
├── tool_ai.py             # Function Gemma tool calling
├── task_scheduler.py      # APScheduler tasks
├── weather.py             # Weather API
├── maps.py                # Maps launcher
├── devai.py               # Dev AI endpoint
├── camera_stream.py       # Camera stream
├── games.py               # Games module
├── security.py            # Security alarm API
├── lan_surveillance.py    # LAN surveillance
├── ai_security_camera.py  # AI security camera
├── file_manager.py        # File management
├── terminal.py            # Terminal API
├── banking.py             # Banking API
├── config.py              # Centralized config
├── agent.py               # CLI agent
├── tools.json             # Tool definitions
├── .env.example           # Config template
├── requirements.txt       # Python deps
├── start_viora_ai.sh      # Legacy launcher
│
├── chat-gui/              # React + Electron frontend
│   ├── src/main/          # Electron main process
│   ├── src/preload/       # IPC bridge
│   ├── src/renderer/      # React app
│   └── out/               # Built frontend
│
├── models/                # AI models (download separately)
├── captures/              # Camera photos
├── recordings/            # Surveillance recordings
├── hailo_od/              # Hailo object detection
├── tests/                 # Test suite
└── templates/             # Flask HTML templates
```

---

## License

MIT License — Copyright (c) 2025 Mr-A-Hacker

---

## Credits

Built by **Mr-A-Hacker**. Powered by Qwen, Whisper, Vosk, Piper TTS, Function Gemma, Organic Maps, OpenCode, Open-Meteo, Hailo, FastAPI, React, and Electron.
