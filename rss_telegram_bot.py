#!/usr/bin/env python3
"""
Telegram RSS Feed Monitor Bot
Monitors RSS feeds and sends notifications for new posts
"""

import logging
import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Set
import feedparser
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set. Please create a .env file or set the BOT_TOKEN variable.")

DATA_FILE = os.getenv("DATA_FILE", "rss_bot_data.json")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))  # Check every 5 minutes (in seconds)

class RSSBot:
    def __init__(self):
        self.data = self.load_data()

    def load_data(self) -> Dict:
        """Load bot data from JSON file"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading data: {e}")

        # Default data structure
        return {
            "feeds": ["https://status.aws.amazon.com/rss/multipleservices-us-east-1.rss"],
            "seen_posts": {},
            "chat_ids": []
        }

    def save_data(self):
        """Save bot data to JSON file"""
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def get_feed_posts(self, feed_url: str) -> List[Dict]:
        """Fetch and parse RSS feed"""
        try:
            feed = feedparser.parse(feed_url)
            posts = []

            for entry in feed.entries:
                post = {
                    'title': entry.get('title', 'No title'),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', entry.get('description', '')),
                    'id': entry.get('id', entry.get('link', ''))
                }
                posts.append(post)

            return posts
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {e}")
            return []

# Initialize bot
rss_bot = RSSBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued"""
    chat_id = update.effective_chat.id

    # Add chat_id to list if not already present
    if chat_id not in rss_bot.data['chat_ids']:
        rss_bot.data['chat_ids'].append(chat_id)
        rss_bot.save_data()

    message = (
        "Welcome to RSS Feed Monitor Bot!\n\n"
        "Available commands:\n"
        "/feeds - List all monitored RSS feeds\n"
        "/addfeed <url> - Add a new RSS feed\n"
        "/removefeed <url> - Remove an RSS feed\n"
        "/check - Manually check feeds for updates\n"
        "/list - Show last 10 posts from all feeds\n\n"
        f"Currently monitoring {len(rss_bot.data['feeds'])} feed(s)"
    )

    await update.message.reply_text(message)

async def list_feeds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all monitored RSS feeds"""
    if not rss_bot.data['feeds']:
        await update.message.reply_text("No RSS feeds are being monitored.")
        return

    message = "Monitored RSS Feeds:\n\n"
    for i, feed in enumerate(rss_bot.data['feeds'], 1):
        message += f"{i}. {feed}\n"

    await update.message.reply_text(message)

async def add_feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new RSS feed"""
    if not context.args:
        await update.message.reply_text("Please provide a feed URL.\nUsage: /addfeed <url>")
        return

    feed_url = context.args[0]

    # Check if feed already exists
    if feed_url in rss_bot.data['feeds']:
        await update.message.reply_text("This feed is already being monitored.")
        return

    # Try to fetch the feed to validate it
    await update.message.reply_text("Validating RSS feed...")
    posts = rss_bot.get_feed_posts(feed_url)

    if not posts:
        await update.message.reply_text("Could not fetch the RSS feed. Please check the URL and try again.")
        return

    # Add feed
    rss_bot.data['feeds'].append(feed_url)
    rss_bot.data['seen_posts'][feed_url] = []

    # Mark existing posts as seen to avoid spam
    for post in posts:
        if post['id'] not in rss_bot.data['seen_posts'][feed_url]:
            rss_bot.data['seen_posts'][feed_url].append(post['id'])

    rss_bot.save_data()

    await update.message.reply_text(
        f"Successfully added feed!\n"
        f"Found {len(posts)} existing posts.\n"
        f"You'll be notified of new posts from now on."
    )

async def remove_feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove an RSS feed"""
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text("Please provide a feed URL.\nUsage: /removefeed <url>")
        return

    feed_url = context.args[0]

    if feed_url not in rss_bot.data['feeds']:
        await update.message.reply_text("This feed is not being monitored.")
        return

    rss_bot.data['feeds'].remove(feed_url)
    if feed_url in rss_bot.data['seen_posts']:
        del rss_bot.data['seen_posts'][feed_url]

    rss_bot.save_data()
    await update.message.reply_text(f"Removed feed: {feed_url}")

async def check_feeds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually check all feeds for new posts"""
    await update.message.reply_text("Checking feeds for updates...")

    new_posts_found = 0

    for feed_url in rss_bot.data['feeds']:
        posts = rss_bot.get_feed_posts(feed_url)

        # Initialize seen_posts for this feed if not exists
        if feed_url not in rss_bot.data['seen_posts']:
            rss_bot.data['seen_posts'][feed_url] = []

        for post in posts:
            if post['id'] not in rss_bot.data['seen_posts'][feed_url]:
                # New post found
                rss_bot.data['seen_posts'][feed_url].append(post['id'])
                new_posts_found += 1

                # Format and send notification
                message = (
                    f"🔔 New Post Alert!\n\n"
                    f"📰 {post['title']}\n\n"
                    f"🔗 {post['link']}\n\n"
                )

                if post['published']:
                    message += f"📅 {post['published']}\n\n"

                if post['summary']:
                    # Truncate summary if too long
                    summary = post['summary'][:500]
                    if len(post['summary']) > 500:
                        summary += "..."
                    message += f"{summary}"

                await update.message.reply_text(message)

    rss_bot.save_data()

    if new_posts_found == 0:
        await update.message.reply_text("No new posts found.")
    else:
        await update.message.reply_text(f"Found {new_posts_found} new post(s)!")

async def list_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List the last 10 posts from all feeds"""
    if not rss_bot.data['feeds']:
        await update.message.reply_text("No RSS feeds are being monitored.")
        return

    await update.message.reply_text("Fetching latest posts...")

    all_posts = []

    for feed_url in rss_bot.data['feeds']:
        posts = rss_bot.get_feed_posts(feed_url)
        for post in posts[:10]:  # Get up to 10 posts per feed
            post['feed_url'] = feed_url
            all_posts.append(post)

    if not all_posts:
        await update.message.reply_text("No posts found in any feed.")
        return

    # Show last 10 posts
    all_posts = all_posts[:10]

    message = "📋 Last 10 Posts:\n\n"

    for i, post in enumerate(all_posts, 1):
        message += f"{i}. {post['title']}\n"
        message += f"   🔗 {post['link']}\n"
        if post['published']:
            message += f"   📅 {post['published']}\n"
        message += "\n"

    # Telegram has a message length limit, so split if needed
    if len(message) > 4000:
        for i in range(0, len(message), 4000):
            await update.message.reply_text(message[i:i+4000])
    else:
        await update.message.reply_text(message)

async def check_feeds_periodic(context: ContextTypes.DEFAULT_TYPE):
    """Periodically check all feeds for new posts"""
    logger.info("Running periodic feed check...")

    for feed_url in rss_bot.data['feeds']:
        posts = rss_bot.get_feed_posts(feed_url)

        # Initialize seen_posts for this feed if not exists
        if feed_url not in rss_bot.data['seen_posts']:
            rss_bot.data['seen_posts'][feed_url] = []

        for post in posts:
            if post['id'] not in rss_bot.data['seen_posts'][feed_url]:
                # New post found
                rss_bot.data['seen_posts'][feed_url].append(post['id'])

                # Format notification message
                message = (
                    f"🔔 New Post Alert!\n\n"
                    f"📰 {post['title']}\n\n"
                    f"🔗 {post['link']}\n\n"
                )

                if post['published']:
                    message += f"📅 {post['published']}\n\n"

                if post['summary']:
                    # Truncate summary if too long
                    summary = post['summary'][:500]
                    if len(post['summary']) > 500:
                        summary += "..."
                    message += f"{summary}"

                # Send to all registered chat IDs
                for chat_id in rss_bot.data['chat_ids']:
                    try:
                        await context.bot.send_message(chat_id=chat_id, text=message)
                    except Exception as e:
                        logger.error(f"Error sending message to {chat_id}: {e}")

    rss_bot.save_data()

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("feeds", list_feeds))
    application.add_handler(CommandHandler("addfeed", add_feed))
    application.add_handler(CommandHandler("removefeed", remove_feed))
    application.add_handler(CommandHandler("check", check_feeds))
    application.add_handler(CommandHandler("list", list_posts))

    # Add periodic job to check feeds
    job_queue = application.job_queue
    job_queue.run_repeating(check_feeds_periodic, interval=CHECK_INTERVAL, first=10)

    # Start the bot
    logger.info("Starting RSS Feed Monitor Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
