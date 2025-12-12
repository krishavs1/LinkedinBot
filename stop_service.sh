#!/bin/bash
# Stop script for LinkedIn Bot service

LAUNCHD_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCHD_DIR/com.linkedinbot.plist"

echo "Stopping LinkedIn Bot service..."

if [ -f "$PLIST_FILE" ]; then
    launchctl unload "$PLIST_FILE" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ Service stopped successfully!"
    else
        echo "Service may not have been running."
    fi
else
    echo "Service plist file not found. Service may not be installed."
fi

