# 🚀 Viora AI 2 — Raspberry Pi 4/5 Edition

<p align="center">
  <strong>A local-first, on-device AI assistant stack built specifically for Raspberry Pi.</strong><br/>
  <em>Voice • Chat • Vision • Automation • Security • Tools • Electron UI</em>
</p>

<p align="center">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Raspberry%20Pi%204%2F5-cc0000?style=for-the-badge&logo=raspberrypi&logoColor=white" />
  <img alt="Backend" src="https://img.shields.io/badge/backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img alt="Frontend" src="https://img.shields.io/badge/frontend-Electron%20%2B%20React-20232a?style=for-the-badge&logo=electron&logoColor=9feaf9" />
  <img alt="Runtime" src="https://img.shields.io/badge/runtime-Python%20%2B%20Node-3776ab?style=for-the-badge&logo=python&logoColor=white" />
</p>

---

## ⚠️ Read This First (Hardware Target)

Viora AI 2 was made for **Raspberry Pi 4 and Raspberry Pi 5**.

- ✅ **Primary target:** Raspberry Pi 5
- ✅ **Supported minimum:** Raspberry Pi 4
- ✅ **Recommended OS:** Raspberry Pi OS (Debian-based)
- ⚠️ Other Linux hardware may work, but Pi 4/5 is the intended build and tuning baseline.

If you want the most predictable setup, use a Pi 5 with active cooling, solid power, and fast storage.

---

## 🌟 What Makes Viora AI Awesome

Viora AI is an ambitious all-in-one assistant platform designed to run locally and integrate multiple capabilities in one polished environment:

- 🧠 **Local chat assistant** with conversation memory.
- 🎙️ **Voice interactions** (STT + TTS pipelines).
- 📷 **Camera + vision tools** for stream/capture/security use-cases.
- 🛠️ **Practical utilities** (terminal, files, maps, weather, tasks).
- 🔐 **Security flows** including alarm and defuse controls.
- 💻 **Desktop experience** via Electron + React interface.

It’s ideal for makers, tinkerers, home-automation builders, and Pi enthusiasts who want a single AI hub.

---

## 🧱 High-Level Architecture

```text
┌───────────────────────────────────────────────────────────────┐
│                     Electron + React UI                      │
│   Home • Chat • Camera • Gallery • Tasks • DevAI • Settings │
└───────────────────────┬───────────────────────────────────────┘
                        │ REST + WebSocket
┌───────────────────────▼───────────────────────────────────────┐
│                        FastAPI Backend                        │
│   chat_ai • camera_stream • security • maps • weather • etc. │
└───────────────┬───────────────────────────────┬──────────────┘
                │                               │
        ┌───────▼────────┐              ┌───────▼────────┐
        │ Local Models   │              │ Local Data      │
        │ GGUF / STT/TTS │              │ JSON state/logs │
        └────────────────┘              └──────────────────┘
```

---

## 🎯 Core Feature Areas

### 1) Conversational AI
- Multi-conversation history storage.
- WebSocket streaming for responsive chat UX.
- Model routing paths for standard chat and tool-use behavior.

### 2) Voice Mode
- Whisper/Vosk support for speech-to-text.
- Piper-based text-to-speech output.
- Voice control states and live interaction loops.

### 3) Vision + Camera
- Camera start/stop controls.
- Live feed and capture functionality.
- Hooks for detection/security workflows.

### 4) Practical Assistant Tools
- File manager routes.
- Terminal execution endpoint.
- Weather and map/location helpers.
- Scheduled tasks and utility workflows.

### 5) Security Module
- Alarm trigger/stop operations.
- Defuse flow with password handling.
- Integrates with camera/security action surface.

---

## 🗂️ Project Layout (Important Files)

```text
app.py                    # Backend entrypoint and router registration
chat_ai.py                # Chat + conversation + voice websockets
camera_stream.py          # Camera lifecycle, feed, capture
security.py               # Alarm/security endpoints
task_scheduler.py         # Task scheduling and persistence
terminal.py               # Command execution endpoint
file_manager.py           # File browsing/manipulation endpoints
weather.py                # Weather integration
maps.py                   # Maps/geocoding integration
banking.py                # Local banking simulation
config.py                 # Environment/config management
requirements.txt          # Python dependency list
chat-gui/                 # Electron + React frontend
README.md                 # Full technical documentation
readme.md                 # Pi-focused quick overview (this file)
```

---

## 🔧 Recommended Raspberry Pi Setup

### Hardware
- Raspberry Pi 5 (preferred) or Raspberry Pi 4 (minimum)
- Official or high-quality USB-C power supply
- Active cooling (especially for Pi 5)
- SSD / high-endurance microSD
- Optional USB mic/speakers/camera

### OS & Base Packages
Use Raspberry Pi OS (Bookworm or compatible Debian derivative), then install baseline packages:

```bash
sudo apt-get update
sudo apt-get install -y \
  python3 python3-venv python3-pip \
  build-essential cmake git curl \
  portaudio19-dev libopenblas-dev liblapack-dev
```

---

## ⚡ Quick Start (Pi 4/5)

```bash
git clone <repo-url>
cd Viora-AI-2

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

cd chat-gui
npm install
cd ..

cp .env.example .env
./run.sh
```

If you prefer manual startup:

```bash
# terminal A
source .venv/bin/activate
python app.py

# terminal B
cd chat-gui
npm run dev
```

---

## 🎛️ Performance Notes for Raspberry Pi

To keep things smooth on Pi 4/5:

- Keep model sizes realistic for your RAM budget.
- Prefer quantized GGUF models for on-device inference.
- Use swap cautiously and monitor thermals.
- Close heavy desktop apps when running camera + voice + chat simultaneously.
- Use `SKIP_MODEL_LOAD=1` for rapid backend iteration/testing.

---

## ✅ Use Cases

- Home AI dashboard on a touchscreen Pi setup
- Local voice assistant kiosk
- Security monitor with AI-assisted controls
- Development workstation helper (terminal + file + DevAI)
- Offline-capable smart utility panel

---

## 🧪 Testing and Development

- Pytest discovery is configured via `pytest.ini`.
- Test fixtures are set to avoid heavy model loading during tests.
- In minimal environments, some API-heavy tests may be conditionally skipped.

Run tests with:

```bash
pytest -q
```

---

## 📚 Where to Read More

- Full technical documentation: [`README.md`](./README.md)
- Camera/security notes: [`AI_SECURITY_CAMERA.md`](./AI_SECURITY_CAMERA.md)
- Model details: [`MODEL_CARD.md`](./MODEL_CARD.md)

---

## ❤️ Final Note

If you're building on Raspberry Pi 4 or 5 and want a unified local AI control center,
**Viora AI 2 is built for exactly that mission.**

Have fun building.
