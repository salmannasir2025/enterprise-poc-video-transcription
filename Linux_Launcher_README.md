# Linux Launcher for Video Transcription GUI

## Files Created

1. **`start_transcription_gui.sh`** - Main launcher script
2. **`stop_transcription_gui.sh`** - Script to stop the background process
3. **`Video Transcription GUI.desktop`** - Desktop shortcut (GNOME)
4. **`Start Video Transcription GUI.desktop`** - Alternative desktop shortcut
5. **`launcher.py`** - Python launcher (most reliable)
6. **`run_gui`** - Simple bash launcher

## 🚀 How to Use (Try these in order)

### Method 1: Python Launcher (Recommended)
- Double-click on **`launcher.py`**
- Works on most Linux systems without trust issues
- Automatically opens browser when ready

### Method 2: Simple Launcher
- Double-click on **`run_gui`**
- Simple bash script that should work when double-clicked

### Method 3: Alternative Desktop Shortcut
- Double-click on **`Start Video Transcription GUI.desktop`**
- Try this if the first .desktop file doesn't work

### Method 4: Original Desktop Shortcut
- Double-click on **`Video Transcription GUI.desktop`**
- Choose "Run in Terminal" when prompted
- Terminal will open, start the server, and close automatically

### Method 5: Run from Terminal
```bash
./start_transcription_gui.sh
```

### Method 6: Desktop Shortcut to Desktop
- Copy any `.desktop` file to your Desktop
- Right-click → Properties → Permissions → Allow executing
- Double-click to run

## Features

✅ **Background Process**: Server continues running even after terminal closes  
✅ **Auto Browser**: Automatically opens browser when server is ready  
✅ **Process Management**: PID is saved for clean shutdown  
✅ **Multi-Browser Support**: Works with Firefox, Chrome, Chromium, etc.  
✅ **Dependency Check**: Verifies ffmpeg and Python packages are installed  

## Stopping the Server

### Method 1: Use Stop Script
```bash
./stop_transcription_gui.sh
```

### Method 2: Manual Stop
```bash
pkill -f "streamlit run app.py"
```

## Access the GUI

Once started, access the GUI at:
- **Local**: http://localhost:8501
- **Network**: http://192.168.1.100:8501
- **External**: http://5.193.110.229:8501

## 🔧 Troubleshooting

### Double-Click Not Working?
Try these solutions in order:
1. **Use `launcher.py`** - Most reliable method
2. **Use `run_gui`** - Simple bash script
3. **Right-click .desktop file → Open With** → Choose application
4. **Copy to Desktop** and set permissions:
   - Right-click → Properties → Permissions → Allow executing
5. **Trust the file**: Some Linux systems require you to "trust" .desktop files

### Port Already in Use
If port 8501 is already in use, the script will show an error. Run:
```bash
./stop_transcription_gui.sh
```

### Dependencies Missing
If dependencies are missing, install them:
```bash
sudo apt install ffmpeg
source venv/bin/activate
pip install -r requirements.txt
```

### Browser Doesn't Open
If browser doesn't open automatically, manually visit http://localhost:8501

### Desktop Files Not Executable
Make sure files are executable:
```bash
chmod +x launcher.py run_gui *.desktop
```

## File Permissions

All scripts are made executable:
- `start_transcription_gui.sh` ✅
- `stop_transcription_gui.sh` ✅  
- `Video Transcription GUI.desktop` ✅

## Process Details

- Server runs in background with PID tracking
- PID is saved in `.streamlit_pid` file
- Clean shutdown on Ctrl+C or script termination
- Automatic browser detection and opening
