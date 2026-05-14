#!/bin/bash
# Launch Streamlit GUI for Video Transcription Tool

cd "$(dirname "$0")"

echo "Starting Video Transcription GUI..."
echo "The app will open in your browser at http://localhost:8501"
echo ""

# Check if streamlit is installed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "Installing dependencies..."
    python3 -m pip install -r requirements.txt
fi

python3 -m streamlit run app.py
