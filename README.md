# RSS Telegram Bot

A Telegram bot that monitors RSS feeds and sends notifications when new posts are published.

## Features

- Monitor multiple RSS feeds simultaneously
- Automatic checking every 5 minutes (configurable)
- Manual check on demand
- List latest posts from feeds
- Add/remove feeds dynamically
- Persistent storage of seen posts
- Environment-based configuration for security

## Prerequisites

- Python 3.8 or higher
- A Telegram bot token from [@BotFather](https://t.me/botfather)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd rss_telegrambot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your bot token
nano .env  # or use your preferred editor
```

4. Get your Telegram Bot Token:
   - Open Telegram and search for [@BotFather](https://t.me/botfather)
   - Send `/newbot` and follow the instructions
   - Copy the token and paste it in your `.env` file

## Configuration

The bot is configured using environment variables in the `.env` file:

- `BOT_TOKEN` (required): Your Telegram bot token from BotFather
- `DATA_FILE` (optional): Path to store bot data (default: `rss_bot_data.json`)
- `CHECK_INTERVAL` (optional): How often to check feeds in seconds (default: `300`)

Example `.env` file:
```bash
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
CHECK_INTERVAL=300
```

## Usage

1. Start the bot:
```bash
python3 rss_telegram_bot.py
```

2. Open Telegram and start a chat with your bot (search for the username you created with BotFather)

3. Send `/start` to initialize the bot

## Available Commands

- `/start` - Initialize bot and see instructions
- `/feeds` - List all monitored RSS feeds
- `/addfeed <url>` - Add a new RSS feed to monitor
- `/removefeed <url>` - Remove an RSS feed from monitoring
- `/check` - Manually check all feeds for new posts
- `/list` - Show the last 10 posts from all feeds

## Example Usage

```
/start
# Welcome message appears

/feeds
# Shows currently monitored feeds (AWS Status by default)

/addfeed https://example.com/feed.rss
# Adds a new feed to monitor

/check
# Manually checks for new posts

/list
# Shows last 10 posts from all feeds
```

## How It Works

1. The bot automatically checks all monitored RSS feeds every 5 minutes
2. When a new post is detected, it sends a notification to all users who have started the bot
3. Each post ID is stored to prevent duplicate notifications
4. Data is persisted in `rss_bot_data.json`

## Running as a Service

To keep the bot running continuously, you can choose one of these methods:

### Option 1: Using the keep_alive.sh script (recommended for simple deployments)

The included `keep_alive.sh` script automatically restarts the bot if it crashes.

1. Make the script executable:
```bash
chmod +x keep_alive.sh
```

2. Add to crontab to check every 5 minutes:
```bash
crontab -e
# Add this line:
*/5 * * * * /path/to/rss_telegrambot/keep_alive.sh >> /path/to/rss_telegrambot/cron.log 2>&1
```

The script automatically detects its directory and uses the system Python by default. If you're using a virtual environment, edit the script and uncomment the PYTHON_BIN line.

### Option 2: Using screen (simple)
```bash
screen -S rss_bot
python3 rss_telegram_bot.py
# Press Ctrl+A, then D to detach
```

### Option 3: Using systemd (recommended for production)

Create a service file `/etc/systemd/system/rss-bot.service`:

```ini
[Unit]
Description=RSS Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/rss_telegrambot
ExecStart=/usr/bin/python3 /path/to/rss_telegrambot/rss_telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `/path/to/rss_telegrambot` with the actual path to your bot directory and `your_username` with your system username.

Then enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rss-bot
sudo systemctl start rss-bot
sudo systemctl status rss-bot
```

### Option 4: Using nohup
```bash
nohup python3 rss_telegram_bot.py > bot.log 2>&1 &
```

## Data Storage

The bot stores data in `rss_bot_data.json`:
- List of monitored feeds
- IDs of seen posts (to prevent duplicates)
- Chat IDs of users who have started the bot

## Troubleshooting

**Bot not responding:**
- Make sure the bot is running
- Check that you've used the `/start` command
- Verify the bot token is correct

**Not receiving notifications:**
- Make sure you've started the bot with `/start`
- Check that the RSS feed URL is valid
- Look at the logs for any errors

**Duplicate notifications:**
- If you delete `rss_bot_data.json`, the bot will forget which posts it has seen
- This is normal after first adding a new feed

## Security

- Never commit your `.env` file or share your bot token
- The `.gitignore` file is configured to prevent accidentally committing sensitive files
- Your bot token has full control over your bot, keep it secret
- `rss_bot_data.json` contains user chat IDs and should not be shared publicly

## Default Feed

The bot comes with AWS Status RSS feed pre-configured as an example. You can remove it and add your own feeds using the `/removefeed` and `/addfeed` commands.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See the [LICENSE](LICENSE) file for details.

This means you can use, modify, and distribute this software, but if you run a modified version on a server, you must make the source code available to users.
