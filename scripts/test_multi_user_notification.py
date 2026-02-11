#!/usr/bin/env python3
"""
Test Multi-User Telegram Notifications
Sends a test message to all configured chat IDs
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv(project_root / '.env')

from src.notifiers.telegram_notifier import TelegramNotifier


def test_multi_user_notification():
    """Test sending notification to multiple users"""

    print("=" * 60)
    print("🧪 MULTI-USER NOTIFICATION TEST")
    print("=" * 60)
    print()

    # Get configuration
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_ids = os.getenv('TELEGRAM_CHAT_ID', '')

    print(f"📋 Configuration:")
    print(f"   Bot Token: {bot_token[:20]}..." if bot_token else "   Bot Token: NOT SET")
    print(f"   Chat IDs: {chat_ids}")
    print()

    # Initialize notifier
    notifier = TelegramNotifier()

    print(f"✅ Notifier initialized")
    print(f"   Will send to {len(notifier.chat_ids)} user(s):")
    for i, chat_id in enumerate(notifier.chat_ids, 1):
        print(f"      {i}. Chat ID: {chat_id}")
    print()

    # Create test digest
    test_digest = {
        'type': 'EVENT',
        'generated_at': datetime.now().isoformat(),
        'news_items': [
            {
                'title': '🧪 Multi-User Test Notification',
                'source': 'Test Script',
                'category': 'test',
                'impact_level': 'HIGH',
            },
            {
                'title': 'If you see this, notifications are working correctly!',
                'source': 'Telegram Multi-User Setup',
                'category': 'test',
                'impact_level': 'MEDIUM',
            }
        ]
    }

    print("📤 Sending test notification...")
    print()

    try:
        success = notifier.send(test_digest)

        if success:
            print("=" * 60)
            print("✅ SUCCESS!")
            print("=" * 60)
            print()
            print("✅ Test notification sent successfully to ALL users!")
            print()
            print("📱 Check both Telegram accounts:")
            for i, chat_id in enumerate(notifier.chat_ids, 1):
                print(f"   {i}. User with Chat ID {chat_id} should have received the message")
            print()
            print("If both users received the notification, setup is complete! 🎉")
        else:
            print("❌ FAILED!")
            print("Notification could not be sent.")
            print("Check the logs for details.")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    print()
    print("=" * 60)
    return True


if __name__ == "__main__":
    test_multi_user_notification()
