#!/bin/bash
# Start script for LinkedIn Bot service

LAUNCHD_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCHD_DIR/com.linkedinbot.plist"

echo "Starting LinkedIn Bot service..."

if [ -f "$PLIST_FILE" ]; then
    launchctl load "$PLIST_FILE" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ Service started successfully!"
    else
        echo "Service may already be running. Try stopping it first."
    fi
else
    echo "Service plist file not found. Run setup_service.sh first."
fi

