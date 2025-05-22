#!/bin/bash

echo "Starting Discord Bot Setup..."

# Display custom message
echo
echo "==========================================="
echo "THIS BOT MADE BY IVX"
echo "BUY ME COFFEE"
echo "https://guns.lol/ivx.1x"
echo "==========================================="
echo

# Wait for 10 seconds
echo "Starting bot in 10 seconds..."
sleep 10

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed! Please install Python 3.8 or higher."
    exit 1
fi

# Check if virtual environment exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment!"
        exit 1
    fi
fi

# Activate virtual environment
source .venv/bin/activate

# Install/upgrade pip
python -m pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install requirements!"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
LOG_CHANNEL_ID=your_log_channel_id_here

# Bot Settings
COMMAND_PREFIX=!
AUTO_RESTORE=true
ADMIN_ROLE_ID=your_admin_role_id_here

# Logging
LOG_LEVEL=INFO
EOL
    echo "Please edit the .env file with your bot token and other settings!"
    read -p "Press Enter to continue..."
fi

# Create necessary directories
mkdir -p database logs

# Start the bot
echo "Starting the bot..."
python main.py 