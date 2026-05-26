#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Activate venv
source "$PROJECT_DIR/.venv/bin/activate"

# Start frontend
cd "$PROJECT_DIR/chat-gui"
npm run dev &

# Wait for frontend to start
sleep 3

# Start backend and KEEP TERMINAL OPEN
cd "$PROJECT_DIR"
python app.py

# Prevent window from closing
echo ""
echo "=== BACKEND STOPPED ==="
echo "Press ENTER to close..."
read
