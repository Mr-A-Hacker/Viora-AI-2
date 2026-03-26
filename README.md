# 🧠 Pocket‑AI Version 2  
A fully offline, Raspberry‑Pi‑optimized personal AI assistant featuring a FastAPI backend, Electron GUI, Whisper STT, Vosk STT, Piper TTS, Qwen LLM, Function‑Gemma tool LLM, camera support, and a complete one‑click desktop launcher.

This project is engineered for **speed**, **local privacy**, and **full offline capability**.  
It is designed to run on lightweight hardware while still providing a modern AI experience.

---

# 📚 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Model Downloads](#model-downloads)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Debugging & Fixes](#debugging--fixes)
- [Desktop Launcher](#desktop-launcher)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Credits](#credits)
- [License](#license)

---

# 🧩 Overview
Pocket‑AI Version 2 is a **local AI assistant** designed for Raspberry Pi and Linux systems.  
It includes:

- A **FastAPI backend** that loads all AI models locally  
- An **Electron GUI** for a modern desktop experience  
- **Speech‑to‑text** via Whisper or Vosk  
- **Text‑to‑speech** via Piper  
- **Local LLM** (Qwen 0.6B GGUF)  
- **Tool LLM** (Function‑Gemma)  
- **Camera support**  
- **One‑click desktop launcher**  
- **Full offline operation**  

This version includes major stability improvements, fixed model paths, improved environment handling, and a fully working launcher.

---

# 🚀 Features

### 🧠 Local LLM
- Qwen 0.6B GGUF  
- Runs fully offline  
- Fast inference on Raspberry Pi 5  

### 🎤 Speech‑to‑Text
- Whisper Tiny (fast, accurate)
- Vosk (optional, fully offline, lightweight)

### 🔊 Text‑to‑Speech
- Piper TTS  
- High‑quality, low‑latency voice output  

### 🖥 Electron GUI
- Modern interface  
- Live chat  
- Camera integration  
- Real‑time transcription  

### 📷 Camera Support
- Capture images  
- Process frames  
- Future vision‑model integration  

### 🛠 Tool LLM
- Function‑Gemma  
- Enables structured tool calling  

### 🖱 One‑Click Desktop Launcher
- Starts backend + GUI  
- Auto‑sets DISPLAY  
- Kills old processes  
- Works on Raspberry Pi OS  

---

# 🖥 System Requirements

### Minimum:
- Raspberry Pi 4 or any Linux machine  
- 4GB RAM  
- Python 3.10+  
- Node.js 18+  
- 4GB free storage  

### Recommended:
- Raspberry Pi 5  
- 8GB RAM  
- SSD storage  

---

# 📦 Installation

## 1. Clone the repository

```bash
git clone https://github.com/Mr-A-Hacker/Mr-A-Hacker-pocket-Ai-version-2
cd Mr-A-Hacker-pocket-Ai-version-2
```

---

## 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Install frontend dependencies

```bash
cd chat-gui
npm install
cd ..
```

---

## 5. Create and edit `.env`

```bash
cp .env.example .env
nano .env
```

Use this configuration:

```env
# Speech-to-Text
USE_WHISPER=true
USE_VOSK=true
VOSK_MODEL=models/vosk/vosk-model-small-en-us-0.15

# Text-to-Speech (Piper)
PIPER_MODEL=en_US-lessac-medium.onnx

# Camera
CAMERA_DEVICE=0

# LLM Settings
MAX_TOKENS=2048
TEMPERATURE=0.7

# Feature Toggles
ENABLE_CAMERA=true
ENABLE_TTS=true
ENABLE_STT=true
ENABLE_LLM=true
```

---

# 📥 Model Downloads

## Whisper (auto‑downloaded)
Whisper Tiny is downloaded automatically on first run.

---

## Piper TTS model

Place inside:

```
models/piper/
```

Example:

```
models/piper/en_US-lessac-medium.onnx
```

---

## Vosk Model

```bash
mkdir -p models/vosk
cd models/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

Folder structure:

```
models/vosk/vosk-model-small-en-us-0.15/
    am/
    conf/
    graph/
    README
```

---

# 🧠 Backend Architecture

### Components:
- `app.py` — FastAPI server  
- `chat_ai.py` — LLM + STT/TTS manager  
- `stt_whisper.py` — Whisper engine  
- `stt_vosk.py` — Vosk engine  
- `tts_piper.py` — Piper TTS  
- `tools.json` — Tool definitions  
- `task_jobs.json` — Background jobs  

### Workflow:
1. GUI sends request → backend  
2. Backend processes text or audio  
3. STT converts speech → text  
4. LLM generates response  
5. TTS converts text → audio  
6. GUI displays output  

---

# 🖼 Frontend Architecture

### Built with:
- Electron  
- Vite  
- Vue/React (depending on version)  
- WebSocket connection to backend  

### Features:
- Live chat  
- Microphone input  
- Camera preview  
- Settings panel  
- Model status indicators  

---

# 🛠 Debugging & Fixes

This section documents all fixes applied during setup.

---

## ✅ Fix 1 — Vosk hard‑coded path

Original broken code:

```python
MODEL_PATH = "/home/pocket-ai/Documents/pocket-ai/models/vosk/vosk-model-small-en-us-0.15"
```

This ignored `.env`.

### ✔ Fixed version:

```python
import os
MODEL_PATH = os.getenv("VOSK_MODEL")
```

---

## ✅ Fix 2 — Electron “Missing X server or $DISPLAY”

Error:

```
Missing X server or $DISPLAY
The platform failed to initialize.
```

### ✔ Fix added to launcher:

```bash
export DISPLAY=:0
export XAUTHORITY=/home/admin/.Xauthority
```

---

## ✅ Fix 3 — Desktop launcher not executing

Solution:

```bash
chmod +x ~/Desktop/PocketAI.desktop
gio set ~/Desktop/PocketAI.desktop metadata::trusted true
```

---

## ✅ Fix 4 — Backend crashing on startup

Cause: Vosk model path incorrect  
Fix: Correct `.env` + updated `stt_vosk.py`

---

# 🖱 Desktop Launcher

## `start-pocket-ai.sh`

```bash
#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=/home/admin/.Xauthority

pkill -f "python app.py"
pkill -f electron
pkill -f "npm run dev"

sleep 2

cd /home/admin/Mr-A-Hacker-pocket-Ai-version-2
source .venv/bin/activate
python app.py &

sleep 3

cd /home/admin/Mr-A-Hacker-pocket-Ai-version-2/chat-gui
npm run dev
```

Make executable:

```bash
chmod +x start-pocket-ai.sh
```

---

## Desktop Icon

`/home/admin/Desktop/PocketAI.desktop`

```ini
[Desktop Entry]
Type=Application
Name=Pocket AI
Comment=Start Pocket AI
Exec=/home/admin/Mr-A-Hacker-pocket-Ai-version-2/start-pocket-ai.sh
Path=/home/admin/Mr-A-Hacker-pocket-Ai-version-2
Icon=utilities-terminal
Terminal=true
Categories=Utility;
```

Enable:

```bash
chmod +x ~/Desktop/PocketAI.desktop
gio set ~/Desktop/PocketAI.desktop metadata::trusted true
```

---

# 📁 Project Structure

```
Mr-A-Hacker-pocket-Ai-version-2/
│
├── app.py
├── chat_ai.py
├── stt_vosk.py
├── stt_whisper.py
├── tts_piper.py
├── tools.json
├── task_jobs.json
├── start-pocket-ai.sh
├── .env
│
├── models/
│   ├── vosk/
│   ├── piper/
│   └── qwen/
│
├── chat-gui/
│   ├── src/
│   ├── package.json
│   └── electron config
│
└── README.md
```

---

# 🛣 Roadmap

### ✔ Version 2 (current)
- Full offline support  
- Desktop launcher  
- Whisper + Vosk  
- Piper TTS  
- Qwen LLM  
- Electron GUI  

### 🔜 Version 3 (planned)
- Vision model integration  
- Local embeddings  
- File search  
- Offline RAG  
- Multi‑modal chat  
- Custom voice cloning  
- Plugin system  

---

# ❤️ Credits

Created by **Mr‑A‑Hacker**  
Engineered for Raspberry Pi and offline AI experimentation.

---

# 📄 License

MIT License  
See `LICENSE` file for details.

