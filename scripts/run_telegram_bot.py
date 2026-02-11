#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot Runner
Runs the Telegram bot in polling mode to listen for commands

Usage:
    python scripts/run_telegram_bot.py

Environment Variables Required:
    TELEGRAM_BOT_TOKEN - Your Telegram bot token
    GITHUB_TOKEN - GitHub personal access token
    GITHUB_REPO - Repository name (default: aijasminekaur11/khabri)
"""

import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file (only if file exists - not on Railway)
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"📁 Loaded environment from .env file")
else:
    print(f"☁️  Using Railway environment variables")

from src.notifiers.telegram_bot_handler import TelegramBotHandler


def setup_logging():
    """Configure logging for the bot"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(project_root / 'logs' / 'telegram_bot.log'),
            logging.StreamHandler()
        ]
    )


def check_environment():
    """
    Check if required environment variables are set

    Returns:
        bool: True if all required variables are set
    """
    required_vars = ['TELEGRAM_BOT_TOKEN', 'GH_TOKEN']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        return False

    return True


def main():
    """Main entry point"""
    print("=" * 60)
    print("🤖 TELEGRAM BOT - STARTING")
    print("=" * 60)
    print()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Get configuration
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    github_token = os.getenv('GH_TOKEN')
    github_repo = os.getenv('GITHUB_REPO', 'aijasminekaur11/khabri')

    # Check Claude API
    claude_api_key = os.getenv('ANTHROPIC_API_KEY')

    print(f"📋 Configuration:")
    print(f"   Repository: {github_repo}")
    print(f"   Bot Token: {bot_token[:10]}..." if bot_token else "   Bot Token: NOT SET")
    print(f"   GitHub Token: {'✅ SET' if github_token else '❌ NOT SET'}")
    print(f"   Claude API: {'✅ SET (AI-powered analysis enabled)' if claude_api_key else '⚠️  NOT SET (manual review only)'}")
    print()

    # Create and run bot
    logger.info("Initializing Telegram bot...")

    try:
        bot = TelegramBotHandler(
            bot_token=bot_token,
            github_token=github_token,
            github_repo=github_repo
        )

        print("✅ Bot initialized successfully")
        print()
        print("=" * 60)
        print("🚀 BOT IS NOW RUNNING")
        print("=" * 60)
        print()
        print("Available commands for users:")
        print("   /fix <description> - Create automated fix request")
        print("   /status - Check recent fixes")
        print("   /help - Show help message")
        print()
        print("Press Ctrl+C to stop the bot")
        print()

        # Run bot in polling mode
        bot.run_polling()

    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("🛑 BOT STOPPED BY USER")
        print("=" * 60)
        logger.info("Bot stopped by user")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error running bot: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
