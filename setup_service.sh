#!/bin/bash
# Setup script for LinkedIn Bot as a macOS background service

echo "Setting up LinkedIn Bot as a background service..."
echo ""

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_FILE="$SCRIPT_DIR/com.linkedinbot.plist"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"

# Check if plist file exists
if [ ! -f "$PLIST_FILE" ]; then
    echo "Error: plist file not found at $PLIST_FILE"
    exit 1
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCHD_DIR"

# Copy plist to LaunchAgents
cp "$PLIST_FILE" "$LAUNCHD_DIR/"

echo "✓ Plist file copied to $LAUNCHD_DIR"
echo ""

# Check if service is already loaded
if launchctl list | grep -q "com.linkedinbot"; then
    echo "Service is already running. Unloading first..."
    launchctl unload "$LAUNCHD_DIR/com.linkedinbot.plist" 2>/dev/null
fi

# Load the service
echo "Loading service..."
launchctl load "$LAUNCHD_DIR/com.linkedinbot.plist"

if [ $? -eq 0 ]; then
    echo "✓ Service loaded successfully!"
    echo ""
    echo "The bot is now running in the background."
    echo "It will automatically start when you log in."
    echo ""
    echo "To check if it's running:"
    echo "  launchctl list | grep linkedinbot"
    echo ""
    echo "To view logs:"
    echo "  tail -f $SCRIPT_DIR/bot.log"
    echo ""
    echo "To stop the service:"
    echo "  launchctl unload $LAUNCHD_DIR/com.linkedinbot.plist"
    echo ""
    echo "To start it again:"
    echo "  launchctl load $LAUNCHD_DIR/com.linkedinbot.plist"
else
    echo "✗ Failed to load service. Check the error messages above."
    exit 1
fi

