#!/bin/bash
# Stop the Video Transcription GUI background process

# Get the directory where this script is located
DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"

echo "🛑 Stopping Video Transcription GUI..."

# Try to stop using saved PID if available
if [ -f ".streamlit_pid" ]; then
    PID=$(cat .streamlit_pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Found running process (PID: $PID)"
        kill $PID
        echo "✅ Sent stop signal to process $PID"
        
        # Wait a bit for graceful shutdown
        sleep 2
        
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force stopping process..."
            kill -9 $PID
            echo "✅ Force stopped process $PID"
        fi
    else
        echo "Process $PID not found"
    fi
    rm -f .streamlit_pid
fi

# Also try to kill any streamlit processes
pkill -f "streamlit run app.py" 2>/dev/null

echo "✅ Video Transcription GUI stopped"
