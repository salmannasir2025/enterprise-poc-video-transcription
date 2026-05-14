#!/usr/bin/env python3
"""
Python launcher for Video Transcription GUI
This can be double-clicked and will work on most Linux systems
"""

import os
import sys
import subprocess
import time
import signal
import webbrowser
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🎬 Starting Video Transcription GUI...")
    print("📍 The app will be available at: http://localhost:8501")
    print("⏳ Starting server...")
    
    # Activate virtual environment if it exists
    venv_python = script_dir / "venv" / "bin" / "python"
    python_cmd = str(venv_python) if venv_python.exists() else "python3"
    
    # Set environment variables
    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    
    # Start Streamlit server
    try:
        process = subprocess.Popen(
            [python_cmd, "-m", "streamlit", "run", "app.py", "--server.headless", "true"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✅ Server starting with PID: {process.pid}")
        
        # Wait for server to be ready
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                import requests
                response = requests.get("http://localhost:8501", timeout=1)
                if response.status_code == 200:
                    print("✅ Server ready! Opening browser...")
                    webbrowser.open("http://localhost:8501")
                    print("🌐 Browser opened. You can close this window.")
                    break
            except:
                pass
            time.sleep(1)
            print(".", end="", flush=True)
        
        print()
        print("📍 GUI is running at: http://localhost:8501")
        print("💡 To stop the server, run: ./stop_transcription_gui.sh")
        print("🔧 This window will close in 5 seconds...")
        
        # Wait a bit then exit (process continues in background)
        time.sleep(5)
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
