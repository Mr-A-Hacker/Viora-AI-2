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

<br/>

![Version](https://img.shields.io/badge/Version-2.0-a855f7?style=for-the-badge&logo=github&logoColor=white)
![Status](https://img.shields.io/badge/Status-LIVE-22c55e?style=for-the-badge&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20%7C%20Linux-e11d48?style=for-the-badge&logo=raspberrypi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3b82f6?style=for-the-badge&logo=python&logoColor=white)
![Offline](https://img.shields.io/badge/100%25-Offline%20Ready-0ea5e9?style=for-the-badge&logo=tor-browser&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-f59e0b?style=for-the-badge)

<br/>

![Built By](https://img.shields.io/badge/Built%20by-Mr--A--Hacker-a855f7?style=for-the-badge&logo=hackaday&logoColor=white)
![Stars](https://img.shields.io/github/stars/Mr-A-Hacker/Viora-AI-2?style=for-the-badge&color=ffd700)
![Forks](https://img.shields.io/github/forks/Mr-A-Hacker/Viora-AI-2?style=for-the-badge&color=a855f7)
![Last Commit](https://img.shields.io/github/last-commit/Mr-A-Hacker/Viora-AI-2?style=for-the-badge&color=22c55e)

<br/>

> **"The smartest thing in the room doesn't need the internet to prove it."**
> — *Mr-A-Hacker*

<br/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=20&duration=2500&pause=800&color=A855F7&center=true&vCenter=true&multiline=true&width=750&height=110&lines=Viora+AI+2+%E2%80%94+Voice.+Vision.+Intelligence.;Runs+on+Raspberry+Pi.+Works+completely+offline.;Talk+to+it.+Show+it+things.+Get+things+done.)](https://github.com/Mr-A-Hacker/Viora-AI-2)

</div>

Viora AI combines a FastAPI backend with a React/Electron desktop frontend. It is designed to run mostly on-device and can integrate with local models (Qwen + Function Gemma), offline speech tools (Vosk/Piper), camera streaming/detection, and utility modules (files, terminal, maps, weather, games, security, and banking simulator).

## Navigation

[Overview](#overview) • [Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [Configuration](#configuration) • [Offline Capabilities](#offline-capabilities) • [Troubleshooting](#troubleshooting) • [Customization](#customization) • [Testing](#testing) • [Roadmap](#roadmap) • [Contributing](#contributing) • [Credits](#credits)

---

## Overview

**Viora AI 2** is a complete, self-contained AI assistant that runs entirely on your device — no cloud, no API keys, no data leaving your machine.

Built for **Raspberry Pi 4/5** and Linux, Viora combines local LLM inference, speech recognition, text-to-speech, computer vision, task scheduling, and more into a single touch-friendly interface.

```
╔══════════════════════════════╗
║    ◉  VIORA AI  v2.0         ║
║  ──────────────────────────  ║
║  Chat      Voice    Vision   ║
║  Agent     Weather  Dev AI   ║
║  ──────────────────────────  ║
║  ▶  Listening...             ║
╚══════════════════════════════╝
```

---

## Features

### Chat
Converse naturally using voice or text. Powered by **Qwen 0.6B GGUF** — a fast, local LLM. Responses stream in real-time and are read aloud via **Piper TTS**. Supports markdown, code blocks, and multi-turn conversations with persistent history. Semantic routing automatically selects the right model (chat vs. tool calling).

### Voice Input
Two speech-to-text engines, switchable in settings:

| Engine | Notes |
|--------|-------|
| **Whisper Tiny** | Fast, accurate; internet needed for initial model download |
| **Vosk** | Fully offline, lightweight, great for privacy |

Tap the mic and Viora responds in her own voice. Real-time partial transcription shows words as you speak.

### Voice Output
**Piper TTS** delivers natural, low-latency speech. Multiple voice models available — swap them in `models/piper/`. Runs 100% offline.

### Vision
Connect any USB webcam or Raspberry Pi Camera Module for live MJPEG streaming, photo capture, and **Hailo-8 NPU** object detection. Captured images can be sent to chat for AI analysis.

### Task Scheduler
Backed by **APScheduler**. Set one-time or recurring reminders. Tasks persist across reboots via `task_jobs.json`.
```
You   > "Remind me to water the plants every day at 9 AM"
Viora > "Got it! I'll remind you every day at 9:00 AM to water the plants."
```

### Weather
Real-time weather via **Open-Meteo** (free, no API key). Temperature, conditions, humidity, wind speed, and precipitation. Graceful offline fallback.

### Maps
Launches **Organic Maps** — privacy-respecting offline navigation. No tracking, no ads. One-tap launch from the Viora home screen.

### Dev AI
Built-in coding assistant powered by **OpenCode**. Ask Viora to write, debug, explain, or refactor code. Supports Python, JavaScript, Bash, C, C++, and more. Runs 100% offline.

### Gallery
All captured photos saved locally in a gallery view. View full-screen, delete, or send to chat for AI analysis. Zero cloud storage.

### Settings
Toggle voice I/O, switch STT engines, change TTS voice, enable/disable camera, manage conversation history, and configure feature toggles from a clean UI.

---

## Requirements

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Device | Raspberry Pi 4 / any Linux PC | Raspberry Pi 5 |
| RAM | 4 GB | 8 GB |
| Storage | 8 GB SD/SSD | 32 GB+ SSD |
| Camera | USB webcam (optional) | Raspberry Pi Camera Module 3 |
| Audio In | USB mic or 3.5mm jack | ReSpeaker USB Mic Array |
| Audio Out | 3.5mm speaker | HDMI audio or USB speaker |
| Optional | — | Hailo-8 NPU |

### Software

| Dependency | Version | Install |
|------------|---------|---------|
| Python | 3.10+ | `sudo apt install python3 python3-venv` |
| Node.js | 18+ | `curl -fsSL https://deb.nodesource.com/setup_18.x \| sudo -E bash -` |
| PortAudio | system | `sudo apt install portaudio19-dev` |
| CMake | any | `sudo apt install cmake` |
| OpenBLAS | system | `sudo apt install libopenblas-dev liblapack-dev` |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Mr-A-Hacker/Viora-AI-2.git
cd Viora-AI-2

# 2. Set up Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Install system dependencies
sudo apt-get update && sudo apt-get install -y \
  portaudio19-dev cmake libopenblas-dev liblapack-dev ffmpeg espeak-ng

# 4. Install frontend
cd chat-gui && npm install && cd ..

# 5. Configure
cp .env.example .env
# Edit .env to match your setup

# 6. Download AI models
mkdir -p models/qwen
huggingface-cli download Qwen/Qwen3-0.6B-GGUF \
  Qwen3-0.6B-Q8_0.gguf --local-dir models/qwen/

mkdir -p models/piper
wget -O models/piper/en_US-lessac-medium.onnx \
  https://github.com/rhasspy/piper/releases/download/2024.11.14-2/en_US-lessac-medium.onnx
wget -O models/piper/en_US-lessac-medium.onnx.json \
  https://github.com/rhasspy/piper/releases/download/2024.11.14-2/en_US-lessac-medium.onnx.json

# 7. Install OpenCode (for Dev AI feature)
curl -fsSL https://opencode.ai/install.sh | sh

# 8. Launch
./start_viora_ai.sh
```

Open **http://localhost:5173** in your browser.

### Manual Launch
```bash
# Terminal 1:
source .venv/bin/activate && python app.py

# Terminal 2:
cd chat-gui && npm run dev
```

### Build as Desktop App
```bash
cd chat-gui && npm run build
# App output: chat-gui/out/
```

### Install Desktop Shortcut
```bash
cp viora-ai.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

---

## Architecture

```
                    ELECTRON / BROWSER FRONTEND (React + Vite)
                    ┌─────────────────────────────────────────┐
                    │  Chat    Vision    Agent    Gallery     │
                    │             Dev AI                      │
                    └─────────────────┬───────────────────────┘
                                      │ WebSocket + REST
                                      ▼
                    FASTAPI BACKEND (app.py)
                    ┌─────────────────────────────────────────┐
                    │  /ws/chat  /ws/voice  /camera  /weather │
                    │                                         │
                    │  ┌─── chat_ai.py (Core Pipeline) ────┐  │
                    │  │  Input → STT → Semantic Router     │  │
                    │  │  → Qwen 0.6B / Function Gemma      │  │
                    │  │  → Piper TTS → Stream to UI        │  │
                    │  └────────────────────────────────────┘  │
                    │                                         │
                    │  weather.py  maps.py  devai.py          │
                    │  task_scheduler.py  tool_ai.py           │
                    └─────────────────────────────────────────┘
                                        │
                    AI MODELS (100% local)
                    ┌─────────────────────────────────────────┐
                    │  Qwen 0.6B   Whisper Tiny   Vosk        │
                    │  Piper TTS   Function Gemma             │
                    │  Hailo OD (optional)                     │
                    └─────────────────────────────────────────┘
```

### Voice Pipeline
```
User speaks → Mic captures audio → Whisper/Vosk STT → Semantic Router
    ├─ Qwen 0.6B (chat)
    └─ Function Gemma (tool calling) → weather/maps/tasks/devai
         └─ Both → Piper TTS → Speaker + UI stream
```

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

# Features
ENABLE_CAMERA=true
ENABLE_TTS=true
ENABLE_STT=true
ENABLE_LLM=true
ENABLE_HAILO=false

# Security
SECURITY_PASSWORD=your_secure_password

# Dev AI
OPENCODE_PATH=opencode

# Weather Default Location
LATITUDE=51.5074
LONGITUDE=-0.1278
```

---

## Project Structure

```
Viora-AI-2/
├── app.py                       # FastAPI backend
├── chat_ai.py                   # Core pipeline: STT → LLM → TTS
├── stt_whisper.py               # Whisper speech recognition
├── stt_vosk.py                  # Vosk offline STT
├── tts_piper.py                 # Piper text-to-speech
├── semantic_router_ai.py        # Prompt routing (chat/think/tool)
├── tool_ai.py                   # Function Gemma tool calling
├── task_scheduler.py            # APScheduler task management
├── weather.py                   # Open-Meteo weather
├── maps.py                      # Organic Maps launcher
├── devai.py                     # OpenCode Dev AI endpoint
├── camera_stream.py             # MJPEG camera + Hailo OD
├── games.py                     # Games module
├── security.py                  # Security alarm API
├── lan_surveillance.py          # LAN surveillance system
├── ai_security_camera.py        # AI-powered security camera
├── unified_security.py          # Bridges surveillance with Viora
├── file_manager.py              # File management API
├── banking.py                   # Banking/finance API
├── terminal.py                  # Terminal command execution
├── config.py                    # Centralized configuration
├── agent.py                     # Local developer agent (CLI)
├── code_ai.py                   # Standalone code AI (CLI)
├── tools.json                   # Tool definitions
├── .env.example                 # Configuration template
├── requirements.txt             # Python dependencies
├── start_viora_ai.sh            # Launcher script
│
├── chat-gui/                    # Electron + React frontend
│   └── src/
│       ├── main/index.js        # Electron main process
│       ├── preload/index.mjs    # IPC bridge
│       └── renderer/src/
│           ├── App.jsx          # Router + main app
│           ├── config.js        # API/WS URL config
│           ├── apiClient.js     # HTTP client
│           ├── contexts/        # React contexts (WS, keyboard, dark mode)
│           └── components/      # UI components
│
├── hailo_od/                    # Hailo object detection
├── tests/                       # Test suite
├── models/                      # AI models (download separately)
├── captures/                    # Camera photos
├── recordings/                  # Surveillance recordings
├── static/sounds/               # Alarm sounds
└── templates/                   # Flask HTML templates
```

```env
PORT=8000
CONVERSATIONS_FILE=conversations.json
TOOLS_PATH=tools.json
JOBS_FILE=task_jobs.json
LOCAL_DIR=./models
CAPTURES_DIR=captures

## Offline Capabilities

| Feature | Online | Offline | Notes |
|---------|--------|---------|-------|
| Chat | Yes | Yes | Fully local LLM |
| Whisper STT | Yes | Partial | Internet for first download only |
| Vosk STT | Yes | Yes | Always offline |
| Piper TTS | Yes | Yes | Always offline |
| Camera + capture | Yes | Yes | No internet needed |
| Object detection | Yes | Yes | Runs on NPU |
| Scheduled tasks | Yes | Yes | Local APScheduler |
| Photo gallery | Yes | Yes | Local storage |
| Organic Maps | Yes | Yes | Offline maps |
| Weather | Yes | No | Requires Open-Meteo API |
| Dev AI | Yes | Yes | Local LLM |

---

## Troubleshooting

### Display Issues
```bash
export DISPLAY=:0
export XAUTHORITY=~/.Xauthority
./start_viora_ai.sh
```

### Vosk Model Not Found
```bash
ls models/vosk/
# Should show: vosk-model-small-en-us-0.15/
VOSK_MODEL=models/vosk/vosk-model-small-en-us-0.15
```

### Camera Not Working
```bash
ls /dev/video*
ffmpeg -i /dev/video0 -frames:v 1 test.jpg
sudo usermod -a -G video $USER   # Log out and back in
```

### Port Already in Use
```bash
lsof -i :8000
pkill -f "python app.py"
python app.py
```

### No Audio
```bash
speaker-test -c 2 -t wav

# Raspberry Pi — HDMI
sudo raspi-config  # Advanced → Audio → HDMI

# Headphone jack
amixer cset numid=3 1
```

### OpenCode Not Found
```bash
opencode --version
curl -fsSL https://opencode.ai/install.sh | sh

# Set path in .env if not in PATH
echo 'OPENCODE_PATH=/path/to/opencode' >> .env
```

### Out of Memory on Pi 4 (4GB)
```bash
# Use lighter quantization
CHAT_FILENAME=Qwen3-0.6B-Q4_K_M.gguf
MAX_TOKENS=512

# Free RAM
sudo systemctl stop bluetooth avahi-daemon
```

---

## Customization

### Change Voice
```bash
wget -O models/piper/en_US-amy-medium.onnx \
  https://github.com/rhasspy/piper/releases/download/2024.11.14-2/en_US-amy-medium.onnx
# Update .env: PIPER_MODEL=en_US-amy-medium.onnx
```

### Use a Different LLM
```python
# In config.py
CHAT_REPO_ID = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
CHAT_FILENAME = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
```

### Change the Theme
```css
/* chat-gui/src/renderer/src/index.css */
:root {
  --ai-color: #7c3aed;    /* Primary purple */
  --bg: #faf8ff;          /* Background */
  --surface: #ffffff;     /* Cards */
  --border: #ede9f8;      /* Borders */
  --text: #1e1030;        /* Main text */
  --glow: #a855f7;        /* Avatar glow */
}
```

### Add Custom Tools
```json
// tools.json — AI picks up new tools automatically on restart
{
  "name": "get_system_stats",
  "description": "Get CPU, RAM, and temperature",
  "parameters": { "type": "object", "properties": {}, "required": [] }
}
```

---

## Testing

```bash
source .venv/bin/activate
pytest tests/ -v                  # Full test suite
python test_viora_ai.py           # Integration tests
python test_audio.py              # Audio system
python test_gemma.py              # LLM response quality
python speed_test.py              # Performance benchmarks
```

---

## Roadmap

```
2025 Q1  ████████████  v2.0 Released
2025 Q2  ████████░░░░  Multi-language STT + TTS
2025 Q3  ████░░░░░░░░  Vision-Language model
2025 Q3  ████░░░░░░░░  Home Assistant / MQTT integration
2025 Q4  ██░░░░░░░░░░  Mobile companion app
2026 Q1  ░░░░░░░░░░░░  Multi-agent orchestration
```

**Planned:**
- [ ] Multi-language support
- [ ] Vision-Language model for full image description
- [ ] Home Assistant / MQTT smart home integration
- [ ] Mobile companion app
- [ ] Custom wake word ("Hey Viora")
- [ ] Fine-tuned Viora personality model
- [ ] Multi-agent task execution

### GUI cannot connect to backend
- Ensure backend is reachable at `127.0.0.1:8000`.
- Check CORS/network/firewall in your environment.

## Contributing

```
Bug Reports    → Open an Issue with steps to reproduce
Feature Ideas  → Start a Discussion
Code PRs       → Fork → Branch → PR with clear description
Docs           → Fix typos, expand unclear sections
```

```bash
git clone https://github.com/YOUR-USERNAME/Viora-AI-2.git
cd Viora-AI-2
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest black ruff
pytest tests/ -v
black . && ruff check .
```

---

## License

MIT License — Copyright (c) 2025 Mr-A-Hacker

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions.

---

## Credits

Built with by **Mr-A-Hacker**. Engineered for offline AI, Raspberry Pi, and the hacker spirit.

| Project | Role |
|---------|------|
| Qwen by Alibaba | Core LLM |
| Whisper by OpenAI | Speech recognition |
| Vosk by AlphaCEP | Fully offline STT |
| Piper by Rhasspy | Text-to-speech |
| Function Gemma by nlouis | Tool-calling LLM |
| Organic Maps | Offline navigation |
| OpenCode | Dev AI assistant |
| Open-Meteo | Free weather API |
| Hailo | NPU object detection |
| FastAPI | Python web backend |
| React + Vite | Frontend framework |

---

<div align="center">

```
 ██╗   ██╗██╗ ██████╗ ██████╗  █████╗      █████╗ ██╗    ██████╗ 
 ██║   ██║██║██╔═══██╗██╔══██╗██╔══██╗    ██╔══██╗██║    ╚════██╗
 ██║   ██║██║██║   ██║██████╔╝███████║    ███████║██║     █████╔╝
 ╚██╗ ██╔╝██║██║   ██║██╔══██╗██╔══██║    ██╔══██║██║    ██╔═══╝ 
  ╚████╔╝ ██║╚██████╔╝██║  ██║██║  ██║    ██║  ██║██║    ███████╗
   ╚═══╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝  ╚═╝╚═╝    ╚══════╝
```

**Made with by [Mr-A-Hacker](https://github.com/Mr-A-Hacker)**

*"Your AI. Your device. Your rules."*

[![GitHub](https://img.shields.io/badge/GitHub-Mr--A--Hacker-181717?style=for-the-badge&logo=github)](https://github.com/Mr-A-Hacker)
[![Star This Repo](https://img.shields.io/badge/Star_This_Repo-ffd700?style=for-the-badge)](https://github.com/Mr-A-Hacker/Viora-AI-2/stargazers)
[![Report Bug](https://img.shields.io/badge/Report_Bug-ef4444?style=for-the-badge)](https://github.com/Mr-A-Hacker/Viora-AI-2/issues)

![Raspberry Pi](https://img.shields.io/badge/Runs%20on-Raspberry%20Pi-e11d48?style=for-the-badge&logo=raspberrypi&logoColor=white)
![No Cloud](https://img.shields.io/badge/Zero-Cloud%20Required-22c55e?style=for-the-badge)
![Privacy First](https://img.shields.io/badge/Privacy-First-0ea5e9?style=for-the-badge)

</div>
