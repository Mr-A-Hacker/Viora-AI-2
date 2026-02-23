# Pocket AI

**Version 1** — *Project in active development; more features planned.*

A **Raspberry Pi 5**–focused, local-first AI assistant with voice, chat, and camera. The backend runs a small GGUF LLM (Qwen), Piper TTS, and optional Whisper/Vosk STT. The GUI is an Electron + React app that talks to the backend over HTTP and WebSockets. This README is written for **Raspberry Pi 5** and **Raspberry Pi OS** (64-bit).

---

## What’s in the repo

- **Backend (Python)**  
  - FastAPI app (`app.py`) with CORS, static files, and routers.  
  - **Chat** (`chat_ai.py`): conversation CRUD, WebSocket chat, voice pipeline (STT → LLM → TTS).  
  - **Camera** (`camera_stream.py`): Pi Camera 2 (libcamera/picamera2) stream, MJPEG feed, capture, gallery, detection hooks.  
  - **TTS** (`tts_piper.py`): Piper-based speech output.  
  - **STT** (`stt_whisper.py`, `stt_vosk.py`): optional Whisper and Vosk engines.

- **Frontend (Electron + React)**  
  - `chat-gui/`: Vite + React 19, Tailwind, Framer Motion, React Router.  
  - Features: home screen, chat UI with sidebar, camera view, settings, WebSocket context for chat and voice.

- **Data**  
  - Conversations: `conversations.json`.  
  - Captures: `captures/`.  
  - Models: `models/` (LLM, Piper, and optionally Vosk — see [Models](#models-what-downloads-where) below).

---

## Prerequisites (Raspberry Pi 5)

| Requirement | Notes |
|-------------|--------|
| **Raspberry Pi 5** | 4 GB or 8 GB RAM; 8 GB recommended for running the LLM plus camera/GUI comfortably. |
| **Raspberry Pi OS (64-bit)** | Bookworm or later. Use the **desktop** image if you want to run the Electron GUI on the Pi; **lite** is fine if you only run the backend and use the GUI from another machine. |
| **Storage** | SD card or (better) SSD. Plan for **at least 4–5 GB free** for models (Qwen GGUF ~500 MB, Piper, Whisper cache, Vosk). |
| **Python 3.10+** | Raspberry Pi OS Bookworm ships with Python 3.11; that’s fine. |
| **Node.js 18+** (and npm) | For building and running the Electron GUI. Install on the Pi (see below). |
| **Microphone** | USB microphone or the Pi’s 3.5 mm jack input (if configured). Needed for voice (STT). |
| **Speaker / USB audio** | For TTS. The code defaults to a USB audio device; see [TTS playback](#other-setup-notes-pi-5-gotchas) below. |
| **Camera (optional)** | Official Raspberry Pi Camera Module (or compatible libcamera camera) for the camera stream. |

---

## Installing Node.js on Raspberry Pi OS

The Electron GUI needs Node.js and npm. On **Raspberry Pi OS (Debian-based)** use one of these.

**Option A — NodeSource (recommended, Node 20 LTS):**

```bash
sudo apt update
sudo apt install -y curl

curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

node -v   # e.g. v20.x.x
npm -v    # e.g. 10.x.x
```

**Option B — Raspberry Pi OS packages (may be older):**

```bash
sudo apt update
sudo apt install -y nodejs npm
node -v
npm -v
```

If you use a different OS on your Pi 5 (e.g. Ubuntu), the same NodeSource steps usually work.

---

## Backend setup (Raspberry Pi 5, step by step)

Do this on your **Pi 5** from the **project root** (the folder that contains `app.py` and `requirements.txt`).

### 1. System packages (Raspberry Pi OS)

Install dependencies for audio (PyAudio), Python dev headers, and the Pi camera stack:

```bash
sudo apt update
sudo apt install -y portaudio19-dev python3-dev python3-pip python3-venv
sudo apt install -y python3-picamera2   # Pi 5 camera (libcamera)
```

- **Camera:** If you use a camera module, enable it:  
  `sudo raspi-config` → **Interface Options** → **Camera** → **Enable** → reboot if needed. Connect the camera to the Pi 5’s camera port (small ribbon connector).

### 2. Python virtual environment

```bash
python3 --version   # Should be 3.10+ (e.g. 3.11 on Bookworm)
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt should show `(.venv)`.

**Using the system’s picamera2 from the venv:**  
If you want to use the `picamera2` you installed with apt (recommended on Pi 5), create the venv with system site-packages:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
```

Then you can leave the `picamera2` line in `requirements.txt` commented out. If you prefer to install `picamera2` inside the venv instead, uncomment that line and run `pip install -r requirements.txt` (may take a while to build on Pi).

### 3. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If PyAudio fails to build, ensure you ran step 1 (`portaudio19-dev`).

### 4. Models: what downloads where

The app uses several models. Most are downloaded automatically; **only Vosk must be downloaded and placed by you.**

| Model | Used for | How you get it |
|-------|----------|-----------------|
| **Qwen3-0.6B (GGUF)** | Chat LLM | **Auto:** first run downloads from Hugging Face into `./models/`. ~400–500 MB. Fits in 4 GB RAM on Pi 5. |
| **Piper (en_US-lessac-medium)** | Text-to-speech | **Auto:** first TTS use downloads into the project’s `models/` folder. |
| **Whisper “tiny”** | Optional STT (push-to-talk) | **Auto:** `faster-whisper` downloads on first use (ARM-friendly). |
| **Vosk (small EN-US)** | Optional STT (live listening) | **Manual** — see below. |

#### Vosk model (manual download)

The code in `stt_vosk.py` expects the Vosk model at a specific path. By default:

`/home/pocket-ai/Documents/pocket-ai/models/vosk/vosk-model-small-en-us-0.15`

On your Pi 5, do this (adjust paths if your project or username differ):

1. **Download a Vosk model** (small model is a good fit for Pi 5):
   - [vosk-model-small-en-us-0.15](https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip) (~40 MB)
   - Or pick another from [Vosk models](https://alphacephei.com/vosk/models).

2. **Unzip and place it** in your project:
   ```bash
   mkdir -p models/vosk
   cd models/vosk
   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
   unzip vosk-model-small-en-us-0.15.zip
   # You should have:  .../models/vosk/vosk-model-small-en-us-0.15/  with am/, conf/, graph/, etc.
   ```

3. **Set the path in code:**  
   Edit `stt_vosk.py` and set `MODEL_PATH` at the top to the **full path** to that folder on your Pi, e.g.:
   ```python
   MODEL_PATH = "/home/pi/pocket-ai/models/vosk/vosk-model-small-en-us-0.15"
   ```
   Replace `/home/pi/pocket-ai` with your actual project path. If the path is wrong, the backend will print an error on startup.

### 5. Run the backend

```bash
python app.py
```

The server listens on `http://0.0.0.0:8000`. The **first run** can take several minutes while the Qwen model (and optionally Piper/Whisper) download. On Pi 5 this is normal.

---

## Frontend (chat GUI) setup on Pi 5

Open a **second terminal** (or a second SSH session). Start the **backend first** (see above), then:

```bash
cd chat-gui
npm install
npm run dev
```

- **Packaged app:**  
  `npm run build`  
  then run the built app from the output folder (see `chat-gui/package.json`).

- **Start backend from the GUI folder (optional):**  
  From `chat-gui`, `npm run backend` runs `python ../app.py`.

The GUI expects the backend at **port 8000** on the same machine. To use the GUI from another computer, point it at your Pi 5’s IP and port 8000 (you may need to adjust the frontend’s API/WebSocket base URL).

---

## Order of operations (Pi 5 checklist)

1. **Raspberry Pi OS** up to date; **Node.js** and **system packages** installed (NodeSource, `portaudio19-dev`, `python3-picamera2`, etc.).  
2. **Camera (if used):** Enable in `raspi-config`, connect module, reboot.  
3. **Backend:**  
   - Clone/open project, create venv (optionally `--system-site-packages` for picamera2).  
   - `pip install -r requirements.txt`.  
   - Download and place the **Vosk** model; set `MODEL_PATH` in `stt_vosk.py`.  
   - Run `python app.py` and wait for first-time model downloads.  
4. **Frontend:**  
   - `cd chat-gui`, `npm install`, `npm run dev`.  
5. Use the app; for voice, ensure a microphone is connected and (for Vosk) `MODEL_PATH` is correct.

---

## Other setup notes (Pi 5 gotchas)

- **Port 8000:** Nothing else should use it. If needed, change the port in `app.py` and the frontend’s backend URL.
- **First run is slow:** Qwen (~500 MB), Piper, and Whisper download on first use. Use a stable connection and enough free space (several GB).
- **Microphone on Pi:** Prefer a USB microphone. Ensure your user is in the `audio` group:  
  `groups` (check for `audio`); if missing:  
  `sudo usermod -aG audio $USER`  
  then log out and back in.
- **TTS playback:** `tts_piper.py` uses `aplay -D plughw:3,0`. On the Pi, the “card 3” device is often a **USB sound card**. If you use the Pi’s 3.5 mm jack or a different USB device, list devices with:
  ```bash
  aplay -l
  ```
  Then change the `-D plughw:X,Y` in `tts_piper.py` to match your card (e.g. `plughw:0,0` for the built-in jack, or the correct `hw:x,y` for your USB device).
- **Camera:** If the camera stream fails, check: camera enabled in `raspi-config`, cable seated, and `libcamera-hello` or `python3 -c "from picamera2 import Picamera2; print('ok')"` working.
- **Running headless:** You can run only the backend on the Pi and use the GUI from a laptop/desktop by pointing it at `http://<pi-ip>:8000` (and updating the frontend config if needed).
- **CORS:** The backend allows all origins (`*`); for production you’d restrict this.

---

## Main endpoints (backend)

| Area | Examples |
|------|----------|
| Chat | `GET/POST /conversations`, `GET /conversations/{id}`, `WS /ws/chat/{conv_id}` |
| Voice | `WS /ws/voice` (commands: start_vosk, stop_vosk, toggle_voice, abort) |
| Camera | `POST /camera/start`, `POST /camera/stop`, `GET /video_feed`, `POST /camera/capture` |
| Gallery | `GET /gallery/images`, `DELETE /gallery/images/{filename}` |
| System | `GET /system/stats` |
| Shutdown | `POST /shutdown` |

---

## Project status

This is **v1** of the README, written for **Raspberry Pi 5** and Raspberry Pi OS. The project is **not finished**; features and structure may change. This file will be updated as the project evolves.
