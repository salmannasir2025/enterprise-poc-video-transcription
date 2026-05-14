#!/bin/bash
# Setup script to ensure desktop shortcut works after reboots

echo "🔧 Setting up persistent desktop shortcut..."

# Get the user's home directory
USER_HOME=$(eval echo ~$USER)
DESKTOP_DIR="$USER_HOME/Desktop"
SCRIPT_DIR="/home/salman/Documents/Video Materials"

# Create Desktop directory if it doesn't exist
mkdir -p "$DESKTOP_DIR"

# Copy the desktop file to Desktop
cp "$SCRIPT_DIR/Start Video Transcription GUI.desktop" "$DESKTOP_DIR/"

# Set proper permissions
chmod +x "$DESKTOP_DIR/Start Video Transcription GUI.desktop"

# Set owner to current user
chown $USER:$USER "$DESKTOP_DIR/Start Video Transcription GUI.desktop"

# Make sure the script files are executable
chmod +x "$SCRIPT_DIR/start_transcription_gui.sh"
chmod +x "$SCRIPT_DIR/stop_transcription_gui.sh"
chmod +x "$SCRIPT_DIR/run_gui"
chmod +x "$SCRIPT_DIR/launcher.py"

# Add to desktop applications directory for system-wide access
mkdir -p "$USER_HOME/.local/share/applications"
cp "$SCRIPT_DIR/Start Video Transcription GUI.desktop" "$USER_HOME/.local/share/applications/"

echo "✅ Desktop shortcut setup complete!"
echo "📍 Location: ~/Desktop/Start Video Transcription GUI.desktop"
echo "🔄 This shortcut will survive reboots"
echo ""
echo "💡 If the shortcut doesn't work after reboot:"
echo "   1. Right-click the shortcut"
echo "   2. Select 'Allow Launching' or 'Trust and Launch'"
echo "   3. Or run this script again: ./setup_desktop_shortcut.sh"
