#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Activate venv
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
  source "$PROJECT_DIR/.venv/bin/activate"
else
  echo "❌ Missing virtualenv at $PROJECT_DIR/.venv"
  echo "Create it first: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

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
