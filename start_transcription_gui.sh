#!/bin/bash
# Linux launcher for Video Transcription GUI
# Double-click this file to start the transcription tool

# Get the directory where this script is located
DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Skip Streamlit telemetry/email prompts
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_HEADLESS=true

echo "🎬 Starting Video Transcription Tool..."
echo "📍 The app will be available at: http://localhost:8501"
echo "⏳ Starting server in background..."
echo ""

# Function to wait for server and open browser
open_browser_when_ready() {
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8501 > /dev/null 2>&1; then
            echo "✅ Server ready! Opening browser..."
            # Try different browsers based on what's available
            if command -v xdg-open &> /dev/null; then
                xdg-open "http://localhost:8501"
            elif command -v firefox &> /dev/null; then
                firefox "http://localhost:8501" &
            elif command -v google-chrome &> /dev/null; then
                google-chrome "http://localhost:8501" &
            elif command -v chromium &> /dev/null; then
                chromium "http://localhost:8501" &
            else
                echo "📍 Please open http://localhost:8501 in your browser manually"
            fi
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
        echo -n "."
    done
    echo ""
    echo "⚠️ Server may not have started properly. Check for errors."
    return 1
}

# Check if dependencies are available
echo "Checking dependencies..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ ffmpeg not found. Please install: sudo apt install ffmpeg"
fi

if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "⚠️ streamlit not found. Please install: source venv/bin/activate && pip install -r requirements.txt"
fi

if ! python3 -c "import yt_dlp" 2>/dev/null; then
    echo "⚠️ yt-dlp not found. Please install: source venv/bin/activate && pip install -r requirements.txt"
fi

echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping server..."
    # Find and kill the streamlit process
    pkill -f "streamlit run app.py" 2>/dev/null
    echo "✅ Server stopped"
    exit 0
}

# Set up signal handlers for clean shutdown
trap cleanup SIGINT SIGTERM

# Start browser checker in background
open_browser_when_ready &

# Start Streamlit in background and get its PID
echo "🚀 Launching Streamlit server..."
python3 -m streamlit run app.py --server.headless true --server.port 8501 &
STREAMLIT_PID=$!

# Save PID to file for later reference
echo $STREAMLIT_PID > .streamlit_pid

echo ""
echo "✅ GUI is running in background (PID: $STREAMLIT_PID)"
echo "📍 Access it at: http://localhost:8501"
echo ""
echo "💡 To stop the server later, run: ./stop_transcription_gui.sh"
echo "💡 Or close this terminal and the server will continue running"

# Wait a bit for the server to start
sleep 3

# Close the terminal automatically after server starts
echo "Terminal will close in 3 seconds..."
sleep 3

# Exit gracefully - the process continues in background
exit 0
