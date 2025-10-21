#!/bin/bash
# Watchdog script to keep the RSS Telegram bot running
# This script checks if the bot is running and starts it if not
#
# Usage: ./keep_alive.sh
# To run automatically, add to crontab:
# */5 * * * * /path/to/keep_alive.sh >> /path/to/cron.log 2>&1

# Configuration - Adjust these variables to match your setup
BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOT_SCRIPT="rss_telegram_bot.py"
PYTHON_BIN="${PYTHON_BIN:-python3}"  # Use system python3 if not specified
LOG_FILE="$BOT_DIR/bot.log"
PID_FILE="$BOT_DIR/bot.pid"

# If you're using a virtual environment, uncomment and set this:
# PYTHON_BIN="$BOT_DIR/venv/bin/python3"

# Check if the bot is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        # Bot is running, check if it's actually our bot
        if ps -p "$PID" -o cmd= | grep -q "$BOT_SCRIPT"; then
            # Bot is running fine, exit
            exit 0
        fi
    fi
    # PID file exists but process is not running, clean up
    rm -f "$PID_FILE"
fi

# Start the bot
cd "$BOT_DIR"
nohup "$PYTHON_BIN" "$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

echo "$(date): Bot started with PID $(cat $PID_FILE)" >> "$LOG_FILE"
