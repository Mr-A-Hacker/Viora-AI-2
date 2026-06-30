#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Activate venv
source "$PROJECT_DIR/.venv/bin/activate"

# Start backend in background
echo "Starting backend..."
cd "$PROJECT_DIR"
python app.py &
BACKEND_PID=$!

# Wait for backend to be ready (up to 30s)
echo "Waiting for backend..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
        echo "Backend ready."
        break
    fi
    sleep 1
done

# Start frontend
cd "$PROJECT_DIR/chat-gui"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== Viora AI is running ==="
echo "Press Ctrl+C to stop everything."

# Wait for either process to exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
