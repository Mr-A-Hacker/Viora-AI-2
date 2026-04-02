#!/bin/bash
# demo_launcher.sh - Launch camera feed with timestamp overlays and sound alerts

echo "🛡️ Viora AI - LAN Surveillance Demo Launcher"
echo "=============================================="

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check dependencies
echo "🔍 Checking dependencies..."
python3 -c "import cv2, flask, flask_socketio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
fi

# Create necessary directories
echo "📁 Setting up directories..."
mkdir -p static/sounds
mkdir -p logs

# Check for camera
echo "📷 Checking camera..."
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'No camera')"

# Start the surveillance server
echo "🚀 Starting surveillance server on http://localhost:5001"
echo ""
echo "📍 Access the dashboard at:"
echo "   http://localhost:5001"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

python3 lan_surveillance.py
