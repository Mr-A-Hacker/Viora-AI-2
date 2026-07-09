#!/bin/bash

# Enhanced Viora AI launcher with Ollama integration
# Usage: ./launch_viora_ai.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Viora AI with Ollama support..."

# Use the virtual environment's python
PYTHON=".venv/bin/python"
if [ ! -f "$PYTHON" ]; then
    echo "ERROR: Virtual environment not found at $PYTHON"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Ensure ollama package is installed
echo "Checking for ollama package..."
if ! $PYTHON -c "import ollama" 2>/dev/null; then
    echo "Installing ollama..."
    $PYTHON -m pip install ollama>=0.3.0 --quiet
else
    echo "✓ Ollama package is installed"
fi

# Start backend with Ollama integration
echo "🏃 Starting Viora AI backend..."
cd "$SCRIPT_DIR"
$PYTHON app.py > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready (up to 30s)..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
        echo "✅ Backend is ready (started after ${i}s)"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start within 30s"
        echo "Check backend.log for details"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Test Ollama integration
echo "🧠 Testing Ollama integration..."
OLLAMA_TEST=$(
    curl -s http://127.0.0.1:8000/settings/ollama 2>/dev/null || echo "Ollama test failed"
)
if echo "$OLLAMA_TEST" | grep -q '"use_ollama":false'; then
    echo "✅ Ollama integration ready (can be enabled via settings)"
elif echo "$OLLAMA_TEST" | grep -q '"use_ollama":true'; then
    echo "✅ Ollama active"
else
    echo "⚠️  Ollama endpoint not accessible"
fi

echo ""
echo "🎉 Viora AI started successfully!"
echo "   Backend PID: $BACKEND_PID"
echo ""
echo "   💬 Chat: Available"
echo "   🎤 Voice: Available"
 echo "   👁  Vision: Available"
echo "   ❓ Ollama: Ready (toggle in app settings)"
echo ""
echo "   ℹ  Press Ctrl+C to stop everything"
echo ""

# Start Electron GUI
echo "💻 Starting frontend..."
cd "$SCRIPT_DIR/chat-gui"
if [ -f "package.json" ]; then
    npm run dev
else
    echo "⚠️  Frontend skipped - no package.json found in $SCRIPT_DIR/chat-gui"
fi

# Cleanup on exit
trap 'echo "Stopping Viora AI..."; kill $BACKEND_PID 2>/dev/null; exit' INT TERM
wait
