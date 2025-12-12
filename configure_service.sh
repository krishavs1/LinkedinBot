#!/bin/bash
# Interactive script to configure the service with your email credentials

echo "LinkedIn Bot Service Configuration"
echo "=================================="
echo ""

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_FILE="$SCRIPT_DIR/com.linkedinbot.plist"

# Check if plist exists
if [ ! -f "$PLIST_FILE" ]; then
    echo "Error: plist file not found!"
    exit 1
fi

# Get email credentials
read -p "Enter your email address (sender): " EMAIL_SENDER
read -sp "Enter your email app password: " EMAIL_PASSWORD
echo ""
read -p "Enter recipient email address: " EMAIL_RECIPIENT
read -p "Enter LinkedIn URL (press Enter for default): " LINKEDIN_URL

# Use default URL if empty
if [ -z "$LINKEDIN_URL" ]; then
    LINKEDIN_URL="https://www.linkedin.com/jobs/search/?keywords=software%20engineer%20intern&f_TPR=r300&f_E=1"
fi

# Create a temporary plist with updated values
TEMP_PLIST=$(mktemp)

# Use sed to replace the values in the plist
sed -e "s|YOUR_EMAIL@gmail.com|$EMAIL_SENDER|g" \
    -e "s|YOUR_APP_PASSWORD|$EMAIL_PASSWORD|g" \
    -e "s|YOUR_RECIPIENT@gmail.com|$EMAIL_RECIPIENT|g" \
    -e "s|https://www.linkedin.com/jobs/search/?keywords=software%20engineer%20intern&f_TPR=r300&f_E=1|$LINKEDIN_URL|g" \
    "$PLIST_FILE" > "$TEMP_PLIST"

# Replace original with updated
mv "$TEMP_PLIST" "$PLIST_FILE"

echo ""
echo "✓ Configuration updated!"
echo ""
echo "Now run ./setup_service.sh to install and start the service."

