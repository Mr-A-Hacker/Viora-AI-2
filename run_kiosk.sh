#!/bin/bash

# Configuration
URL="http://localhost:5173"
WIDTH=480
HEIGHT=800
PROJECT_DIR="/home/pocket-ai/Documents/pocket-ai"
FRONTEND_DIR="$PROJECT_DIR/chat-gui"

# --- Process Management ---
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function to kill background processes
cleanup() {
    echo ""
    echo "Cleaning up..."
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null && echo "Stopped Backend ($BACKEND_PID)"
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && echo "Stopped Frontend ($FRONTEND_PID)"
    exit 0
}

# Trap exit signals (Ctrl+C, termination, and script finish)
trap cleanup EXIT INT TERM

# 1. Check/Start Python Backend
if pgrep -f "python3 app.py" > /dev/null; then
    echo "Backend (app.py) is already running."
    # If already running, we won't stop it on exit unless we track it.
    # We could capture its PID here if we wanted to be aggressive.
else
    echo "Starting Backend (app.py)..."
    cd "$PROJECT_DIR"
    # Run in background, redirect output to log
    python3 app.py > backend.log 2>&1 &
    BACKEND_PID=$!
    sleep 2 # Give it a moment to start
fi

# 2. Check/Start React Frontend
if pgrep -f "vite" > /dev/null; then
    echo "Frontend (Vite) is already running."
else
    echo "Starting Frontend (Vite)..."
    cd "$FRONTEND_DIR"
    # Run in background, redirect output to log
    npm run dev -- --host > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "Waiting for frontend to be ready..."
    # Simple wait loop until port 5173 is active (optional, or just sleep)
    sleep 5
fi

# 3. Launch Browser in Kiosk/App Mode
echo "Launching application in $WIDTH x $HEIGHT mode..."

# Try to find chromium or chrome
if [ -x "$(command -v chromium)" ]; then
    BROWSER="chromium"
elif [ -x "$(command -v chromium-browser)" ]; then
    BROWSER="chromium-browser"
elif [ -x "$(command -v google-chrome)" ]; then
    BROWSER="google-chrome"
else
    # Fallback to absolute path common on Pi
    if [ -f "/usr/bin/chromium" ]; then
        BROWSER="/usr/bin/chromium"
    else
        echo "Error: Chromium or Chrome not found."
        exit 1
    fi
fi

# Launch (Wait for browser to close)
"$BROWSER" --app="$URL" --window-size=$WIDTH,$HEIGHT --window-position=0,0 --user-data-dir="/tmp/kiosk_browser_data"

# Script will now hit 'cleanup' via EXIT trap when browser process finishes

