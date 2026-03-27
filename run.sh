#!/bin/bash
# Quick launcher for Viora AI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Viora AI..."

# Activate venv if exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Start backend
python app.py &
BACKEND_PID=$!

# Wait for backend
echo "Waiting for backend..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Start GUI
cd chat-gui
npm run dev
GUI_EXIT=$?

# Cleanup
kill $BACKEND_PID 2>/dev/null
exit $GUI_EXIT