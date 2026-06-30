#!/bin/bash
# Quick launcher for Viora AI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting Viora AI..."

# Use venv python directly
PYTHON=".venv/bin/python"
if [ ! -f "$PYTHON" ]; then
    echo "ERROR: Virtual environment not found at $PYTHON"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Start backend
echo "Starting backend..."
$PYTHON app.py &
BACKEND_PID=$!

# Wait for backend (up to 30s)
echo "Waiting for backend..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
        echo "Backend ready."
        break
    fi
    sleep 1
done

# Check if backend is actually running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "ERROR: Backend failed to start. Check the logs."
    exit 1
fi

# Start GUI
cd chat-gui
npm run dev
GUI_EXIT=$?

# Cleanup
kill $BACKEND_PID 2>/dev/null
exit $GUI_EXIT