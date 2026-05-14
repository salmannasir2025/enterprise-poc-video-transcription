#!/bin/bash
# Double-click to run Video Transcription GUI
# This file launches the Streamlit interface in your browser

# Add Homebrew to PATH (for ffmpeg and other tools)
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

# Skip Streamlit telemetry/email prompts
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_HEADLESS=true

# Get the directory where this .command file is located
DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"

echo "Checking dependencies..."
if ! command -v ffmpeg &> /dev/null || ! python3 -c "import streamlit" 2>/dev/null || ! python3 -c "import yt_dlp" 2>/dev/null; then
    echo "Some dependencies missing. Please ensure ffmpeg, streamlit, and yt-dlp are installed."
    echo "Run: brew install ffmpeg && pip install -r requirements.txt"
    echo ""
fi

echo ""
echo "🎬 Starting Video Transcription Tool..."
echo "📍 The app will be available at: http://localhost:8501"
echo "⏳ Waiting for server to start..."
echo ""

# Function to wait for server and open browser
open_browser_when_ready() {
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8501 > /dev/null 2>&1; then
            echo "✅ Server ready! Opening browser..."
            open "http://localhost:8501"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
        echo -n "."
    done
    echo ""
    echo "⚠️ Server may not have started properly. Check the terminal above for errors."
    return 1
}

# Start browser checker in background
open_browser_when_ready &

# Run the Streamlit app (headless mode skips email prompt)
echo "🚀 Launching Streamlit server..."
python3 -m streamlit run app.py --server.headless true

# Keep terminal window open
echo ""
echo "----------------------------------------"
echo "Server stopped. Press Enter to close..."
echo "----------------------------------------"
read
