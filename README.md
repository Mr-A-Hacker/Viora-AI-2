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
![Issues](https://img.shields.io/github/issues/Mr-A-Hacker/Viora-AI-2?style=for-the-badge&color=ef4444)
![Last Commit](https://img.shields.io/github/last-commit/Mr-A-Hacker/Viora-AI-2?style=for-the-badge&color=22c55e)
![Languages](https://img.shields.io/github/languages/count/Mr-A-Hacker/Viora-AI-2?style=for-the-badge&color=06b6d4)

<br/>

> **"The smartest thing in the room doesn't need the internet to prove it."**
> — *Mr-A-Hacker*

<br/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=20&duration=2500&pause=800&color=A855F7&center=true&vCenter=true&multiline=true&width=750&height=110&lines=Viora+AI+2+%E2%80%94+Voice.+Vision.+Intelligence.;Runs+on+Raspberry+Pi.+Works+completely+offline.;Talk+to+it.+Show+it+things.+Get+things+done.)](https://github.com/Mr-A-Hacker/Viora-AI-2)

</div>

---

## 🧭 Navigation

<div align="center">

[🌟 Overview](#-overview) • [✨ Features](#-features) • [📋 Requirements](#-requirements) • [⚡ Quick Start](#-quick-start) • [🔧 Installation](#-installation) • [🏗 Architecture](#-architecture) • [🖥 Interface](#-the-viora-interface) • [🌐 API Reference](#-api-reference) • [⚙️ Configuration](#-configuration) • [📁 Project Structure](#-project-structure) • [🌐 Offline Capabilities](#-offline-capabilities) • [🧪 Testing](#-testing) • [🛠 Troubleshooting](#-troubleshooting) • [🎨 Customization](#-customization) • [🗺 Roadmap](#-roadmap) • [🙏 Credits](#-credits)

</div>

---

## 🌟 Overview

<table>
<tr>
<td width="55%">

**Viora AI 2** is a complete, self-contained AI assistant that runs **entirely on your device** — no cloud required, no API keys needed (beyond optional model downloads), no data ever leaving your machine.

Built by **Mr-A-Hacker** and optimized for **Raspberry Pi 4/5** and Linux, Viora is the AI assistant that privacy-conscious hackers, tinkerers, and makers have been waiting for.

Talk to it with your voice. Show it things with your camera. Ask it to remember tasks. Check the weather, open maps, write code — all from a beautiful, touch-friendly Electron interface that runs locally.

This isn't a demo. This is a real AI assistant you actually own.

</td>
<td width="45%" align="center">

```
╔══════════════════════════════╗
║    ◉  VIORA AI  v2.0         ║
║  ──────────────────────────  ║
║  💬 Chat      ✅  ONLINE     ║
║  🎤 Voice     ✅  ONLINE     ║
║  👁  Vision   ✅  ONLINE     ║
║  📝 Agent     ✅  RUNNING    ║
║  🌤 Weather   ✅  SYNCED     ║
║  🧠 Knowledge ✅  READY      ║
║  🤖 Dev AI    ✅  READY      ║
║  ──────────────────────────  ║
║  ▶  Listening...             ║
╚══════════════════════════════╝
```

</td>
</tr>
</table>

---

## ✨ Features

### 💬 Chat — *Talk to Viora*

Converse naturally with Viora AI using **voice or text**. Powered by **Qwen 0.6B GGUF** — a fast, local language model that runs entirely on-device. Responses are streamed in real-time and read aloud by **Piper TTS**. Fully supports markdown, code blocks, and multi-turn conversations with persistent history.

- Real-time streaming token output
- Full markdown + syntax-highlighted code blocks
- Multi-turn context with conversation history
- Conversations saved to `conversations.json` automatically
- Semantic routing sends your prompt to the right model automatically
- Knowledge injection — relevant web-fetched content is injected into the AI's context

---

### 🎤 Voice Input — *Speak Naturally*

Two speech-to-text engines, switchable in settings:

| Engine | Mode | Notes |
|--------|------|-------|
| **Whisper Tiny** | Fast, accurate | Requires internet for first model download only |
| **Vosk** | Fully offline | Lightweight, great for privacy |

- Tap the mic, speak, and Viora responds in her own voice
- Real-time partial transcription — see words as you speak them
- Configurable via `.env` — enable one or both simultaneously
- Error feedback when no microphone is detected

---

### 🗣 Voice Output — *She Has a Voice*

**Piper TTS** gives Viora a natural, low-latency voice. She sounds like a real assistant — not a robotic synthesizer.

- Multiple voice models available (swap in `/models/piper/`)
- Low latency — audio starts playing while text is still streaming
- Runs 100% offline, no internet required
- Outputs to any ALSA audio device

---

### 👁 Vision — *She Can See*

Connect any USB webcam or Raspberry Pi Camera Module and Viora gains vision:

- **Live video streaming** via MJPEG at 480x800 (optimized for portrait display)
- **Photo capture** saved to `/captures/`
- **Hailo AI Object Detection** — real-time object identification using the Hailo-8 NPU
- Supports Raspberry Pi Camera Module 3 and generic USB cameras
- Camera feed auto-rotates and resizes for the display

---

### 📷 Gallery — *Your Photos, Your Device*

All captured photos are saved locally and organized in a sleek gallery view:

- Tap any photo to view full-screen
- Delete photos directly from the gallery
- Send any photo to the chat for AI analysis
- Zero cloud storage — everything stays on-device

---

### ✅ Agent — *Your Personal Task Scheduler*

Tell Viora to remember things and she will — literally:

```
You   > "Remind me to water the plants every day at 9 AM"
Viora > "Got it! I'll remind you every day at 9:00 AM to water the plants."
```

- Backed by **APScheduler** for reliable job management
- Tasks persist across reboots via `task_jobs.json`
- Set one-time reminders or recurring schedules
- Runs silently in the background — no internet needed

---

### 🌦 Weather — *Stay Informed*

Real-time weather powered by **Open-Meteo** — completely free, no API key required:

- Current temperature, feels-like, humidity, wind speed, and precipitation
- WMO weather code mapping with emoji descriptions (☀️🌤️⛅☁️🌧️⛈️❄️)
- **IP geolocation auto-detect** — no configuration needed, finds your city automatically
- **City search** — type any city name to get its weather
- **Reverse geocode** — when using GPS coordinates, shows the actual city name
- Supports both Fahrenheit and Celsius
- Wind speed displayed in mph (Fahrenheit) or km/h (Celsius)
- Works in the Home screen modal or as a full-page component

---

### 🗺 Maps — *Navigate Offline*

Search any location using **Nominatim OpenStreetMap** and launch **Organic Maps** — a privacy-respecting offline map app:

- No Google. No tracking. No ads.
- Full offline navigation — maps stored on-device
- Reverse geocoding: coordinates → address
- Perfect for hiking, cycling, travel, or when data is unavailable

---

### 🤖 Dev AI — *Built-in Coding Assistant*

A fully integrated coding assistant powered by **OpenCode**:

- Ask Viora to write, debug, explain, or refactor code
- Supports Python, JavaScript, Bash, C, C++, and more
- Real-time streaming output with syntax highlighting
- Runs 100% offline — your code never leaves your machine

---

### 🧠 Knowledge — *Stays Current*

Viora can upgrade her knowledge by fetching the latest content from multiple sources:

| Source | Content | Count |
|--------|---------|-------|
| **Hacker News** | Top & new stories | ~200 |
| **Reddit** | Hot posts from 19 subreddits | ~280 |
| **YouTube** | Search results via DDGS | ~0-50 |
| **LinkedIn** | Recent posts via DDGS | ~0-10 |
| **Wikipedia** | Trending pages | fill to 1000 |

- **Upgrade button** in Settings — one tap fetches fresh content
- **Progress tracking** — shows "Upgrading... N/1000" in real-time
- **Automatic injection** — relevant knowledge is injected into chat context when you ask about a topic
- **Deduplication** — no duplicate articles across consecutive upgrades
- **Update check** — lightweight check compares latest HN story ID to know if new content is available
- **Persistent status** — leaving and returning to Settings shows the current state

---

### 🛡 Security — *Home Surveillance*

Turn your Pi into a security system:

- Motion detection with voice alerts
- LAN surveillance server
- Alarm and notification system
- Works with connected cameras

---

### 🖥 Terminal — *Built-in Shell*

Run system commands directly from the Viora UI:

- Full terminal emulator
- Real-time output streaming
- No SSH needed — access your Pi's shell from the app

---

### 📁 File Manager — *Browse & Manage Files*

Full file management without leaving the app:

- Browse directories
- Create, rename, and delete files
- Navigate the filesystem

---

### 🎮 Games — *Built-in Fun*

Play games directly in the Viora interface.

---

### 🏦 Banking — *Finance Dashboard*

View account balances and transactions.

---

### ⚙️ Settings — *Your AI, Your Rules*

Full control over every aspect of Viora:

- Toggle voice input/output on or off
- Switch between Whisper and Vosk STT
- Change the Piper voice model
- Enable/disable camera features
- Manage and clear conversation history
- **Upgrade Knowledge** button with progress tracking
- Update check indicator showing whether new content is available
- All configuration toggles from a clean UI

---

### 📱 Additional Features

| Feature | Description |
|---------|-------------|
| **GPIO Control** | Control Raspberry Pi GPIO pins from the UI |
| **Heartbeat Monitor** | System health monitoring |
| **Virtual Keyboard** | On-screen keyboard for touchscreens |
| **Avatar** | Animated Viora orb with voice-reactive glow |

---

## 📋 Requirements

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| 🖥 Device | Raspberry Pi 4 / any Linux PC | Raspberry Pi 5 |
| 🧠 RAM | 4 GB | 8 GB |
| 💾 Storage | 8 GB SD card or SSD | 32 GB+ SSD |
| 📷 Camera | USB webcam (optional) | Raspberry Pi Camera Module 3 |
| 🎤 Audio In | USB mic or 3.5mm jack | ReSpeaker USB Mic Array |
| 🔊 Audio Out | 3.5mm speaker | HDMI audio or USB speaker |
| ⚡ Optional | — | Hailo-8 NPU (real-time object detection) |

### Software

| Dependency | Version | How to Install |
|------------|---------|----------------|
| Python | 3.10+ | `sudo apt install python3 python3-venv` |
| Node.js | 18+ | `curl -fsSL https://deb.nodesource.com/setup_18.x \| sudo -E bash -` |
| Git | any | `sudo apt install git` |
| PortAudio | system | `sudo apt install portaudio19-dev` |
| CMake | any | `sudo apt install cmake` |
| OpenBLAS | system | `sudo apt install libopenblas-dev liblapack-dev` |

### Optional Dependencies

| Tool | Purpose |
|------|---------|
| Hugging Face account | Downloading LLM models (free) |
| OpenCode | Dev AI coding assistant |
| Hailo SDK | Hardware-accelerated object detection |
| Flatpak + Organic Maps | Offline maps navigation |

---

## ⚡ Quick Start

Get Viora running in under **5 minutes**:

```bash
# 1. Clone
git clone https://github.com/Mr-A-Hacker/Viora-AI-2.git
cd Viora-AI-2

# 2. Set up environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install system dependencies
sudo apt-get update && sudo apt-get install -y \
  portaudio19-dev cmake libopenblas-dev liblapack-dev ffmpeg espeak-ng

# 5. Install frontend
cd chat-gui && npm install && cd ..

# 6. Download AI models (see full installation below)
# The app will auto-download Whisper and warn about missing models

# 7. Configure
cp .env.example .env
nano .env   # Edit your settings

# 8. LAUNCH 🚀
./start_viora_ai.sh
```

Then open **http://localhost:5173** in your browser, or use the Electron desktop app.

---

## 🔧 Full Installation

### Step 1 — Clone & Setup

```bash
git clone https://github.com/Mr-A-Hacker/Viora-AI-2.git
cd Viora-AI-2

python3 -m venv .venv
source .venv/bin/activate
```

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt

sudo apt-get update
sudo apt-get install -y \
  portaudio19-dev cmake libopenblas-dev liblapack-dev ffmpeg espeak-ng
```

### Step 3 — Frontend

```bash
cd chat-gui
npm install
cd ..
```

### Step 4 — Download AI Models

**LLM — Qwen 0.6B GGUF (Chat Brain)**
```bash
mkdir -p models/qwen
huggingface-cli download Qwen/Qwen3-0.6B-GGUF \
  Qwen3-0.6B-Q8_0.gguf \
  --local-dir models/qwen/
```

**Tool LLM — Function Gemma (Tool Calling)**
```bash
huggingface-cli download nlouis/functiongemma-pocket-q4_k_m \
  functiongemma-pocket-q4_k_m.gguf \
  --local-dir models/
```

**Piper TTS Voice**
```bash
mkdir -p models/piper
wget https://github.com/rhasspy/piper/releases/download/2024.11.14-2/en_US-lessac-medium.onnx \
  -O models/piper/en_US-lessac-medium.onnx
wget https://github.com/rhasspy/piper/releases/download/2024.11.14-2/en_US-lessac-medium.onnx.json \
  -O models/piper/en_US-lessac-medium.onnx.json
```

**Vosk STT — Fully Offline Speech Recognition**
```bash
mkdir -p models/vosk && cd models/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
cd ../..
```

### Step 5 — Configure

```bash
cp .env.example .env
nano .env
```

### Step 6 — Install OpenCode (Dev AI)

```bash
curl -fsSL https://opencode.ai/install.sh | sh
```

### Step 7 — Launch 🚀

```bash
# One-command launch (recommended)
./start_viora_ai.sh

# Manual launch
# Terminal 1:
source .venv/bin/activate && python app.py

# Terminal 2:
cd chat-gui && npm run dev
```

**Build as a desktop Electron app:**
```bash
cd chat-gui
npm run build
# App is in chat-gui/out/
```

**Install desktop shortcut:**
```bash
cp viora-ai.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

---

## 🏗 Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    VIORA AI v2 — FULL SYSTEM                                 │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │              ELECTRON DESKTOP APP (React + Vite + Framer Motion)     │    │
│  │                                                                      │    │
│  │  Home │ Chat │ Vision │ Gallery │ Tasks │ Weather │ Maps │ Dev AI   │    │
│  │  Settings │ Terminal │ Files │ GPIO │ Heartbeat │ Banking │ Games   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                             │ WebSocket + REST                       │    │
│  └─────────────────────────────┬────────────────────────────────────────┘    │
│                                │                                              │
│                                ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │              FASTAPI BACKEND  (app.py — port 8000)                    │    │
│  │                                                                      │    │
│  │   /ws/chat    /ws/voice    /weather/*    /maps/*    /knowledge/*    │    │
│  │   /camera/*   /files/*     /security/*   /terminal   /tasks/*       │    │
│  │   /banking    /games       /devai        /gpio       /health        │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐      │    │
│  │  │              chat_ai.py  (Core Pipeline)                    │      │    │
│  │  │  Input → [STT: Whisper/Vosk] → [Semantic Router]           │      │    │
│  │  │       → [Qwen 0.6B / Function Gemma] → [Piper TTS]        │      │    │
│  │  │       → Stream to UI + conversations.json + knowledge      │      │    │
│  │  └────────────────────────────────────────────────────────────┘      │    │
│  │                                                                      │    │
│  │  weather.py   maps.py   knowledge.py   devai.py   task_scheduler.py │    │
│  │  Open-Meteo   Nominatim HN/Reddit/Wiki  OpenCode   APScheduler     │    │
│  │                                                                      │    │
│  │  camera_stream.py   file_manager.py   banking.py   games.py         │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │     AI MODELS  (100% local)                                          │    │
│  │  🧠 Qwen 0.6B Q8   🎤 Whisper Tiny   🔇 Vosk   🗣 Piper TTS        │    │
│  │  🔧 Function Gemma (tool calling)    👁 Hailo OD (optional)          │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Voice Pipeline

```
User speaks
    │
    ▼
┌──────────────────────┐
│   Mic captures audio │
└──────────┬───────────┘
           │
     ┌─────▼───────┐
     │ Whisper Tiny│  ←── Fast, accurate (internet for first download)
     │   OR  Vosk  │  ←── Fully offline, always private
     └─────┬───────┘
           │  transcript
           ▼
┌──────────────────────┐
│  Semantic Router     │  ←── Decides: Chat / Think / Tool use
│  semantic_router_ai  │
└──────────┬───────────┘
           │
    ┌──────┴──────────┐
    │                 │
    ▼                 ▼
┌────────────┐  ┌──────────────────┐
│ Qwen 0.6B  │  │  Function Gemma  │
│  (Chat)    │  │  (Tool calling)  │
└─────┬──────┘  └────────┬─────────┘
      │                  │ executes tool
      │              ┌───▼─────────────┐
      │              │ weather / maps  │
      │              │ tasks / devai   │
      │              │ knowledge search│
      │              └───┬─────────────┘
      └──────────┬───────┘
                 │  response (streaming)
                 ▼
    ┌────────────────────────┐
    │   Piper TTS Engine     │
    │   Text → Natural Voice │
    └────────────┬───────────┘
                 │
         🔊 Speaker plays
         💬 UI streams tokens in real-time
```

---

## 🖥 The Viora Interface

```
┌─────────────────────────────────────────────┐
│  🌡 CPU: 52°C  💾 RAM: 2.1/8GB  🕐 14:23   │
├─────────────────────────────────────────────┤
│                                             │
│           ╭─────────────╮                  │
│           │    ◉ VIORA  │  ← Animated      │
│           │    Avatar    │    glowing orb   │
│           ╰─────────────╯                  │
│                                             │
│  ╔══════════╗  ╔══════════╗  ╔══════════╗  │
│  ║ 💬 CHAT  ║  ║ 📷 VISION║  ║ 📝 AGENT ║  │
│  ║ purple   ║  ║  cyan    ║  ║  pink    ║  │
│  ╚══════════╝  ╚══════════╝  ╚══════════╝  │
│                                             │
│  ╔══════════╗  ╔══════════╗  ╔══════════╗  │
│  ║🖼 GALLERY║  ║ 🌦WEAHER║  ║ 🗺 MAPS  ║  │
│  ║  gray    ║  ║  cyan    ║  ║  green   ║  │
│  ╚══════════╝  ╚══════════╝  ╚══════════╝  │
│                                             │
│  ╔══════════╗  ╔══════════╗  ╔══════════╗  │
│  ║ 🎮 GAMES ║  ║🤖 DEV AI║  ║ 🛡SECURI║  │
│  ║  pink    ║  ║ orange   ║  ║  red     ║  │
│  ╚══════════╝  ╚══════════╝  ╚══════════╝  │
│                                             │
│  ╔══════════╗  ╔══════════╗  ╔══════════╗  │
│  ║ ⌨ TERM  ║  ║ 📁 FILES║  ║ 💰 BANK  ║  │
│  ║  gray    ║  ║  gray    ║  ║  blue    ║  │
│  ╚══════════╝  ╚══════════╝  ╚══════════╝  │
│                                             │
│     [⚙️ Settings]    [🧠 Upgrade Knowledge]│
└─────────────────────────────────────────────┘
```

### Frontend Routes

| Route | Page | Purpose |
|-------|------|---------|
| `/` | Home | Main menu with all feature buttons + modals |
| `/chat` | ChatInterface | Full chat with voice input + streaming responses |
| `/camera` | CameraView | Live camera with object detection overlay + capture |
| `/gallery` | Gallery | Browse, view, delete, and share captured photos |
| `/tasks` | TaskManager | View/manage scheduled tasks |
| `/tasks/add` | TaskAdd | Create or edit a scheduled task |
| `/maps` | Maps | Search locations + launch Organic Maps |
| `/terminal` | Terminal | Built-in shell emulator |
| `/files` | FileManager | Browse and manage filesystem |
| `/settings` | Settings | All configuration + Knowledge Upgrade button |
| `/devai` | DevAI | OpenCode coding assistant |
| `/gpio` | GPIOControl | Raspberry Pi GPIO pin control |
| `/heartbeat` | HeartbeatManager | System health monitoring |

---

## 🌐 API Reference

All endpoints are served from `http://localhost:8000`.

### Core

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check — returns `{"status": "ok"}` |
| WS | `/ws/chat/{conv_id}` | Chat WebSocket — streaming conversation |
| WS | `/ws/voice` | Voice WebSocket — mic input + speech |

### Weather

| Method | Endpoint | Parameters | Description |
|--------|----------|------------|-------------|
| GET | `/weather` | `lat`, `lon`, `city`, `unit` | Current weather via Open-Meteo. Supports IP geolocation (no params), city search (`?city=London`), or GPS coordinates (`?lat=...&lon=...`). Reverse geocodes lat/lon to city name. Default `unit=fahrenheit`. |

**Example responses:**

```json
// IP auto-detect (no params)
{"temperature":67.8,"feels_like":68.6,"humidity":66,"wind_speed":6.2,
 "precipitation":0.0,"description":"Clear sky","emoji":"☀️",
 "unit":"°F","timezone":"Europe/Berlin","location":"Berlin"}

// City search with Celsius
// GET /weather?city=Tokyo&unit=celsius
{"temperature":21.8,"feels_like":24.5,"humidity":83,"wind_speed":4.4,
 "precipitation":0.0,"description":"Mainly clear","emoji":"🌤️",
 "unit":"°C","timezone":"Asia/Tokyo","location":"Tokyo"}
```

### Maps

| Method | Endpoint | Parameters | Description |
|--------|----------|------------|-------------|
| GET | `/maps/search` | `q` (query) | Search places via Nominatim OpenStreetMap |
| GET | `/maps/reverse` | `lat`, `lon` | Reverse geocode coordinates → address |
| POST | `/maps/open` | — | Launch Organic Maps via Flatpak |

### Knowledge

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/knowledge/update` | Start knowledge upgrade in background |
| GET | `/knowledge` | Current knowledge status (entry count, running state) |
| GET | `/knowledge/check` | Lightweight check for new content (compares HN IDs) |

### Camera

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/video_feed` | MJPEG video stream |
| POST | `/camera/start` | Start camera session |
| POST | `/camera/stop` | Stop camera session |
| POST | `/camera/capture` | Capture and save a photo |
| POST | `/camera/detection/start` | Start object detection |
| POST | `/camera/detection/stop` | Stop object detection |
| WS | `/ws/detections` | Real-time detection results |

### Files

| Method | Endpoint | Parameters | Description |
|--------|----------|------------|-------------|
| GET | `/files/list` | `path` | List directory contents |
| POST | `/files/create` | `path`, `is_dir` | Create file or folder |
| POST | `/files/delete` | `path` | Delete file/folder |
| POST | `/files/rename` | `old_path`, `new_name` | Rename file/folder |

### Other

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks` | List scheduled tasks |
| GET | `/games` | List available games |
| GET | `/banking` | Banking dashboard |
| POST | `/start_surveillance` | Start LAN surveillance server |
| POST | `/security/motion_detected` | Motion detection webhook |
| POST | `/maps/open-dev` | Launch OpenCode |

---

## ⚙️ Configuration

Full `.env` reference:

```env
# ─── Ports ────────────────────────────────────────────────────────────────
PORT=8000
FRONTEND_PORT=5173

# ─── Model Paths ──────────────────────────────────────────────────────────
LOCAL_DIR=./models

CHAT_REPO_ID=Qwen/Qwen3-0.6B-GGUF
CHAT_FILENAME=Qwen3-0.6B-Q8_0.gguf

TOOL_REPO_ID=nlouis/functiongemma-pocket-q4_k_m
TOOL_FILENAME=functiongemma-pocket-q4_k_m.gguf

# ─── Speech-to-Text ───────────────────────────────────────────────────────
USE_WHISPER=true
USE_VOSK=true
VOSK_MODEL=models/vosk/vosk-model-small-en-us-0.15

# ─── Text-to-Speech ───────────────────────────────────────────────────────
PIPER_MODEL=en_US-lessac-medium.onnx
PIPER_SPEED=1.0

# ─── Camera ───────────────────────────────────────────────────────────────
CAMERA_INDEX=-1                  # -1 = auto-detect, or specify device number
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720

# ─── LLM Generation ───────────────────────────────────────────────────────
MAX_TOKENS=2048
TEMPERATURE=0.7
TOP_P=0.9
CONTEXT_LENGTH=4096

# ─── Features ─────────────────────────────────────────────────────────────
ENABLE_CAMERA=true
ENABLE_TTS=true
ENABLE_STT=true
ENABLE_LLM=true
ENABLE_HAILO=false               # Set true if Hailo-8 NPU connected
```

---

## 📁 Project Structure

```
Viora-AI-2/
├── 📄 README.md
├── 📄 requirements.txt             ← Python dependencies
├── 📄 .env.example                 ← Config template
├── 📄 .env                         ← Your local config (gitignored)
│
├── 🚀 app.py                       ← FastAPI backend (all endpoints + routers)
├── 🧠 chat_ai.py                   ← Core pipeline: STT → LLM → TTS
├── 🎤 stt_whisper.py               ← Whisper speech recognition
├── 🎤 stt_vosk.py                  ← Vosk offline STT
├── 🗣 tts_piper.py                 ← Piper text-to-speech
├── 🔀 semantic_router_ai.py        ← Prompt routing (chat/think/tool)
├── 🔧 tool_ai.py                   ← Function Gemma tool calling
├── 📅 task_scheduler.py            ← APScheduler task management
├── 🌦 weather.py                   ← Open-Meteo weather (IP geo + reverse geocode)
├── 🗺 maps.py                      ← Nominatim search + Organic Maps launcher
├── 🧠 knowledge.py                 ← HN + Reddit + Wikipedia knowledge fetcher
├── 🤖 devai.py                     ← OpenCode Dev AI endpoint
├── 📷 camera_stream.py             ← MJPEG camera + Hailo object detection
├── 🎮 games.py                     ← Games module
├── 📁 file_manager.py              ← Filesystem browsing API
├── 🏦 banking.py                   ← Banking dashboard
├── 🛡 security.py                  ← Security/disarm API
├── 🛡 security_flask.py            ← Flask security server (legacy)
├── 🛡 unified_security.py          ↑ Voice alerts for security events
├── 🛡 lan_surveillance.py         ↑ LAN surveillance server
├── 🛡 ai_security_camera.py        ↑ AI-powered camera detection
├── ⚡ speed_test.py                ← Performance benchmarks
├── ⚙️ config.py                    ← Centralized config from .env
├── 🤖 agent.py                     ← Agent logic
├── 💻 code_ai.py                   ← Code AI helper
├── 📝 test_mode.py                 ← Test mode controller
├── 📝 test_audio.py                ← Audio system test
├── 📝 test_gemma.py                ← LLM response quality test
├── 📝 test_viora_ai.py             ← Integration tests
│
├── 🛠 tools.json                   ← Tool definitions for function calling
├── 💬 conversations.json           ← Saved chat history
├── 📋 task_jobs.json               ← Scheduled task persistence
├── 🔊 asound.conf                  ← ALSA audio config for Pi
├── 🖥 viora-ai.desktop             ← Linux desktop shortcut
├── 🚀 start_viora_ai.sh            ← One-click launcher
│
├── 🖥 chat-gui/                    ← Electron + React + Vite frontend
│   ├── package.json
│   ├── electron.vite.config.js
│   ├── src/
│   │   ├── main/index.js           ← Electron main process
│   │   ├── preload/index.mjs       ← Electron preload
│   │   └── renderer/
│   │       ├── index.html
│   │       ├── App.jsx             ← Router + main app layout
│   │       ├── index.css           ← Purple Viora theme + Tailwind
│   │       ├── config.js           ← API/WS URL configuration
│   │       └── components/
│   │           ├── Home.jsx            ← Landing / main menu with modals
│   │           ├── ChatInterface.jsx   ← Full chat UI + mic button
│   │           ├── ChatHeader.jsx      ← Chat header with back button
│   │           ├── ChatInput.jsx       ← Chat text input
│   │           ├── ChatSidebar.jsx     ← Conversation history sidebar
│   │           ├── MessageList.jsx     ← Message list with markdown rendering
│   │           ├── MessageBubble.jsx   ← Individual message bubble
│   │           ├── CameraView.jsx      ← Live camera + OD overlay + capture
│   │           ├── Gallery.jsx         ← Photo gallery
│   │           ├── Settings.jsx        ← Configuration + Knowledge Upgrade
│   │           ├── Weather.jsx         ← Full weather page component
│   │           ├── Maps.jsx            ← Maps search + launch
│   │           ├── DevAI.jsx           ← OpenCode integration
│   │           ├── Terminal.jsx        ← Terminal emulator
│   │           ├── FileManager.jsx     ← File browser
│   │           ├── TaskManager.jsx     ← Task scheduler list
│   │           ├── TaskAdd.jsx         ← Create/edit tasks
│   │           ├── Avatar.jsx          ← Animated Viora avatar
│   │           ├── StatusBar.jsx       ← CPU/RAM/Temp bar
│   │           ├── VirtualKeyboard.jsx ← On-screen keyboard
│   │           ├── HeartbeatManager.jsx← System health
│   │           ├── GPIOControl.jsx     ← GPIO pin control
│   │           ├── ConnectionBar.jsx   ← Connection status bar
│   │           ├── ErrorBoundary.jsx   ← Error boundary wrapper
│   │           ├── ErrorMessage.jsx    ← Error display component
│   │           ├── LoadingSpinner.jsx  ← Loading indicator
│   │           ├── MiniChat.jsx        ← Compact chat view
│   │           └── CloseButton.jsx     ← Reusable close button
│   └── out/                         ← Built output (gitignored)
│       ├── main/
│       ├── preload/
│       └── renderer/
│
├── 📦 models/                      ← AI models (download separately)
│   ├── qwen/                       ← Qwen 0.6B GGUF
│   ├── piper/                      ← Piper TTS voice
│   └── vosk/                       ← Vosk offline STT
│
├── 📸 captures/                    ← Camera photos
├── 📊 hailo_od/                    ← Hailo object detection configs
└── 🧪 tests/                       ← Test suite
```

---

## 🌐 Offline Capabilities

<div align="center">

| Feature | Online | Offline | Notes |
|---------|--------|---------|-------|
| 💬 Chat with Viora | ✅ | ✅ | Fully local LLM |
| 🎤 Whisper STT | ✅ | ⚠️ | Internet for *first* download only |
| 🎤 Vosk STT | ✅ | ✅ | Always 100% offline |
| 🗣 Piper TTS | ✅ | ✅ | Always 100% offline |
| 📷 Camera + capture | ✅ | ✅ | No internet needed |
| 👁 Object detection | ✅ | ✅ | Runs on NPU locally |
| 📅 Scheduled tasks | ✅ | ✅ | Local APScheduler |
| 🖼 Photo gallery | ✅ | ✅ | Local storage |
| 📁 File manager | ✅ | ✅ | Local filesystem |
| ⌨ Terminal | ✅ | ✅ | Local shell |
| 🎮 Games | ✅ | ✅ | Local |
| 🏦 Banking | ✅ | ✅ | Local data |
| 🤖 Dev AI (OpenCode) | ✅ | ✅ | Local LLM |
| 🗺 Maps search | ✅ | ⚠️ | Requires Nominatim API for search; maps app works offline |
| 🌦 Weather | ✅ | ❌ | Requires Open-Meteo API |
| 🧠 Knowledge upgrade | ✅ | ❌ | Requires HN/Reddit/Wikipedia APIs |
| 🌐 Web search (YouTube/LinkedIn) | ✅ | ❌ | Requires DuckDuckGo search |

</div>

---

## 🧪 Testing

```bash
source .venv/bin/activate

pytest tests/ -v                  # Full test suite
python test_viora_ai.py           # Integration tests
python test_audio.py              # Audio system
python test_gemma.py              # LLM response quality
python speed_test.py              # Performance benchmarks
```

---

## 🛠 Troubleshooting

### Display / X11 Issues

```bash
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority
./start_viora_ai.sh
```

### GPU / Electron Crashes (Headless/VM)

```bash
# Add --disable-gpu if running in a headless environment
cd chat-gui
npx electron . --disable-gpu --no-sandbox
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
sudo usermod -a -G video $USER   # Then log out and back in
```

### Backend Port Already in Use

```bash
lsof -i :8000
pkill -f "python app.py"
python app.py
```

### No Audio Output

```bash
speaker-test -c 2 -t wav

# Raspberry Pi — HDMI
sudo raspi-config  # Advanced → Audio → HDMI

# Headphone jack
amixer cset numid=3 1
```

### Out of Memory on Pi 4 (4GB)

```bash
# Use a lighter quantization in config.py
CHAT_FILENAME=Qwen3-0.6B-Q4_K_M.gguf

# Reduce max tokens
MAX_TOKENS=512

# Free RAM
sudo systemctl stop bluetooth avahi-daemon
```

### Knowledge Upgrade Returns 0 Entries

```bash
# Test sources manually
curl -s https://hacker-news.firebaseio.com/v0/newstories.json | head -5
# If blocked (DNS hijacking), YouTube/LinkedIn/DDGS searches will return 0
# HN and Reddit should still work
```

---

## 🎨 Customization

### Change Viora's Voice

```bash
# Download a new Piper voice from github.com/rhasspy/piper
wget https://github.com/rhasspy/piper/releases/.../en_US-amy-medium.onnx \
  -O models/piper/en_US-amy-medium.onnx

# Update .env
PIPER_MODEL=en_US-amy-medium.onnx
```

### Use a Different LLM

```python
# In config.py
CHAT_REPO_ID = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
CHAT_FILENAME = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
```

### Change the UI Theme

```css
/* chat-gui/src/index.css */
:root {
  --ai-color: #7c3aed;    /* Primary purple — swap for any color */
  --bg: #faf8ff;          /* Background */
  --surface: #ffffff;     /* Cards */
  --border: #ede9f8;      /* Borders */
  --text: #1e1030;        /* Main text */
  --text-mid: #6b5b8e;    /* Secondary text */
  --glow: #a855f7;        /* Avatar glow */
}
```

### Add Custom Tools

```json
// tools.json
{
  "name": "get_system_stats",
  "description": "Get CPU, RAM, and temperature of the Raspberry Pi",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

Then implement the handler in `tool_ai.py`. The AI picks it up automatically on restart.

---

## 🗺 Roadmap

```
2025 Q1  ████████████  v2.0 Released ✅
2025 Q2  ████████░░░░  Multi-language STT + TTS 🚧
2025 Q3  ████░░░░░░░░  Vision-Language model integration 🔮
2025 Q3  ████░░░░░░░░  Home Assistant / MQTT integration 🔮
2025 Q4  ██░░░░░░░░░░  Mobile companion app 🔮
2026 Q1  ░░░░░░░░░░░░  Multi-agent orchestration 🤫
```

**Coming in future versions:**
- [ ] Multi-language support (Spanish, French, German, Arabic...)
- [ ] Vision-Language model (describe images with full detail)
- [ ] Home Assistant / MQTT smart home integration
- [ ] Mobile companion app
- [ ] Custom wake word ("Hey Viora")
- [ ] Fine-tuned Viora personality model
- [ ] Multi-agent task execution
- [ ] Music/media player
- [ ] Notes/memo pad
- [ ] Alarms and timers
- [ ] System monitor dashboard (CPU/RAM/disk/temp graphs)
- [ ] Translation tool
- [ ] QR code scanner

---

## 🤝 Contributing

All contributions are welcome!

```
🐛 Bug Reports    → Open an Issue with steps to reproduce
💡 Feature Ideas  → Open a Discussion
🔧 Code PRs       → Fork → Branch → PR with clear description
📖 Docs           → Fix typos, expand unclear sections
🌍 Translations   → Help localize the UI
```

```bash
git clone https://github.com/YOUR-USERNAME/Viora-AI-2.git
cd Viora-AI-2

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pytest black ruff

pytest tests/ -v
black . && ruff check .
```

---

## 📜 License

```
MIT License — Copyright (c) 2025 Mr-A-Hacker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is furnished
to do so, subject to the following conditions: The above copyright notice and
this permission notice shall be included in all copies or substantial portions.
```

---

## 🙏 Credits

Built with 💜 by **Mr-A-Hacker**. Engineered for offline AI, Raspberry Pi, and the hacker spirit.

| Project | Role |
|---------|------|
| **Qwen by Alibaba** | Core LLM |
| **Whisper by OpenAI** | Speech recognition |
| **Vosk by AlphaCEP** | Fully offline STT |
| **Piper by Rhasspy** | Text-to-speech |
| **Function Gemma by nlouis** | Tool-calling LLM |
| **Organic Maps** | Offline navigation |
| **OpenCode** | Dev AI assistant |
| **Open-Meteo** | Free weather API |
| **Nominatim (OpenStreetMap)** | Geocoding |
| **ip-api.com** | IP geolocation |
| **Hacker News API** | Knowledge source |
| **Reddit API** | Knowledge source |
| **Wikipedia API** | Knowledge source |
| **Hailo** | NPU object detection |
| **FastAPI** | Python web backend |
| **React + Vite + Electron** | Frontend framework |

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

**Made with 💜 by [Mr-A-Hacker](https://github.com/Mr-A-Hacker)**

*"Your AI. Your device. Your rules."*

---

[![GitHub](https://img.shields.io/badge/GitHub-Mr--A--Hacker-181717?style=for-the-badge&logo=github)](https://github.com/Mr-A-Hacker)
[![Star This Repo](https://img.shields.io/badge/⭐_Star_This_Repo-ffd700?style=for-the-badge)](https://github.com/Mr-A-Hacker/Viora-AI-2/stargazers)
[![Report Bug](https://img.shields.io/badge/🐛_Report_Bug-ef4444?style=for-the-badge)](https://github.com/Mr-A-Hacker/Viora-AI-2/issues)
[![Request Feature](https://img.shields.io/badge/💡_Request_Feature-a855f7?style=for-the-badge)](https://github.com/Mr-A-Hacker/Viora-AI-2/discussions)

<br/>

![Made with Love](https://img.shields.io/badge/Made%20with-💜%20%26%20Python-a855f7?style=for-the-badge)
![Raspberry Pi](https://img.shields.io/badge/Runs%20on-Raspberry%20Pi-e11d48?style=for-the-badge&logo=raspberrypi&logoColor=white)
![No Cloud](https://img.shields.io/badge/Zero-Cloud%20Required-22c55e?style=for-the-badge)
![Privacy First](https://img.shields.io/badge/Privacy-First-0ea5e9?style=for-the-badge)

⭐ **If Viora AI helped you, drop a star — it means the world!** ⭐

</div>
<img width="1408" height="768" alt="Gemini_Generated_Image_ddanssddanssddan (1)" src="https://github.com/user-attachments/assets/3978919f-1d81-482d-9b4f-3941468ce7f6" />
<img width="1408" height="768" alt="Gemini_Generated_Image_ddanssddanssddan (2)" src="https://github.com/user-attachments/assets/f04ff46c-a0a8-4414-853f-1a90be3c19d6" />
<img width="1408" height="768" alt="Gemini_Generated_Image_ddanssddanssddan" src="https://github.com/user-attachments/assets/3a0ed6ad-d9b2-44ea-9862-a2b6d87467cd" />
