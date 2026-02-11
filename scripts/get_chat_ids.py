#!/usr/bin/env python3
"""
Get Chat IDs from Bot Updates
Shows all users who have interacted with the bot
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

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


def get_all_chat_ids():
    """Get all chat IDs from recent bot interactions"""

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env")
        return

    print("=" * 60)
    print("📋 TELEGRAM BOT - CHAT IDs")
    print("=" * 60)
    print()
    print(f"🤖 Bot: @Khabri420_bot")
    print(f"🔑 Token: {bot_token[:20]}...")
    print()
    print("Fetching recent updates...")
    print()

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getUpdates",
            timeout=10
        )

        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return

        data = response.json()

        if not data.get('ok'):
            print("❌ Failed to get updates")
            return

        updates = data.get('result', [])

        if not updates:
            print("⚠️  No recent messages found.")
            print()
            print("Make sure users have sent at least one message to the bot.")
            return

        # Collect unique chat IDs
        chat_info = {}

        for update in updates:
            if 'message' in update:
                message = update['message']
                chat = message.get('chat', {})
                chat_id = chat.get('id')

                if chat_id and chat_id not in chat_info:
                    chat_info[chat_id] = {
                        'first_name': chat.get('first_name', 'Unknown'),
                        'last_name': chat.get('last_name', ''),
                        'username': chat.get('username', ''),
                        'type': chat.get('type', 'private')
                    }

        print("=" * 60)
        print(f"✅ Found {len(chat_info)} unique user(s):")
        print("=" * 60)
        print()

        chat_ids_list = []

        for i, (chat_id, info) in enumerate(chat_info.items(), 1):
            full_name = f"{info['first_name']} {info['last_name']}".strip()
            username = f"@{info['username']}" if info['username'] else "No username"

            print(f"👤 User {i}:")
            print(f"   Name: {full_name}")
            print(f"   Username: {username}")
            print(f"   Chat ID: {chat_id}")
            print(f"   Type: {info['type']}")
            print()

            chat_ids_list.append(str(chat_id))

        # Show .env format
        print("=" * 60)
        print("📝 COPY THIS TO YOUR .env FILE:")
        print("=" * 60)
        print()
        print(f"TELEGRAM_CHAT_ID={','.join(chat_ids_list)}")
        print(f"TELEGRAM_AUTHORIZED_IDS={','.join(chat_ids_list)}")
        print()
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    get_all_chat_ids()
