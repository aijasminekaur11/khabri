#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Configuration Check for Telegram Auto-Fix System
Verifies that all required components are properly configured
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check(condition, success_msg, fail_msg):
    """Print check result"""
    if condition:
        print(f"{GREEN}✅ {success_msg}{RESET}")
        return True
    else:
        print(f"{RED}❌ {fail_msg}{RESET}")
        return False

def info(msg):
    """Print info message"""
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def warn(msg):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def main():
    print("=" * 70)
    print(f"{BLUE}🔍 TELEGRAM AUTO-FIX SYSTEM - CONFIGURATION CHECK{RESET}")
    print("=" * 70)
    print()

    # Load .env file
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'

    if env_file.exists():
        load_dotenv(env_file)
        info(f"Loaded .env from: {env_file}")
    else:
        warn(".env file not found (using system environment variables)")

    print()

    # Track overall status
    all_checks_passed = True

    # ========================================
    # 1. Check Local Environment Variables
    # ========================================
    print(f"{BLUE}📋 LOCAL ENVIRONMENT VARIABLES{RESET}")
    print("-" * 70)

    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    gh_token = os.getenv('GH_TOKEN')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    all_checks_passed &= check(
        telegram_bot_token,
        f"TELEGRAM_BOT_TOKEN set ({telegram_bot_token[:15]}...)",
        "TELEGRAM_BOT_TOKEN not set"
    )

    all_checks_passed &= check(
        telegram_chat_id,
        f"TELEGRAM_CHAT_ID set ({telegram_chat_id})",
        "TELEGRAM_CHAT_ID not set"
    )

    all_checks_passed &= check(
        gh_token,
        f"GH_TOKEN set ({gh_token[:10]}...)",
        "GH_TOKEN not set"
    )

    if anthropic_key:
        all_checks_passed &= check(
            anthropic_key.startswith('sk-ant-'),
            f"ANTHROPIC_API_KEY valid ({anthropic_key[:20]}...)",
            "ANTHROPIC_API_KEY invalid format"
        )
    else:
        check(False, "", "ANTHROPIC_API_KEY not set (auto-fix will fail)")
        all_checks_passed = False

    print()

    # ========================================
    # 2. Check File Structure
    # ========================================
    print(f"{BLUE}📁 FILE STRUCTURE{RESET}")
    print("-" * 70)

    required_files = [
        'src/notifiers/telegram_bot_handler.py',
        'scripts/run_telegram_bot.py',
        'scripts/auto_fix_with_claude.py',
        '.github/workflows/auto-fix-issues.yml'
    ]

    for file_path in required_files:
        full_path = project_root / file_path
        check(
            full_path.exists(),
            f"{file_path}",
            f"{file_path} MISSING"
        )

    print()

    # ========================================
    # 3. Test Telegram Bot Connection
    # ========================================
    print(f"{BLUE}🤖 TELEGRAM BOT CONNECTION{RESET}")
    print("-" * 70)

    if telegram_bot_token:
        try:
            import requests
            response = requests.get(
                f"https://api.telegram.org/bot{telegram_bot_token}/getMe",
                timeout=5
            )

            if response.status_code == 200:
                bot_info = response.json()
                bot_username = bot_info.get('result', {}).get('username', 'Unknown')
                check(True, f"Bot connected: @{bot_username}", "")
            else:
                check(False, "", f"Bot connection failed: {response.status_code}")
                all_checks_passed = False

        except Exception as e:
            check(False, "", f"Bot connection error: {e}")
            all_checks_passed = False
    else:
        check(False, "", "Cannot test bot connection - token not set")
        all_checks_passed = False

    print()

    # ========================================
    # 4. Test GitHub Connection
    # ========================================
    print(f"{BLUE}🔗 GITHUB CONNECTION{RESET}")
    print("-" * 70)

    if gh_token:
        try:
            import requests
            github_repo = os.getenv('GITHUB_REPO', 'aijasminekaur11/khabri')

            response = requests.get(
                f"https://api.github.com/repos/{github_repo}",
                headers={'Authorization': f'token {gh_token}'},
                timeout=5
            )

            if response.status_code == 200:
                check(True, f"GitHub access verified: {github_repo}", "")
            else:
                check(False, "", f"GitHub access failed: {response.status_code}")
                all_checks_passed = False

        except Exception as e:
            check(False, "", f"GitHub connection error: {e}")
            all_checks_passed = False
    else:
        check(False, "", "Cannot test GitHub connection - token not set")
        all_checks_passed = False

    print()

    # ========================================
    # 5. Test Claude API (Optional)
    # ========================================
    print(f"{BLUE}🤖 CLAUDE API CONNECTION{RESET}")
    print("-" * 70)

    if anthropic_key:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_key)

            # Simple test message
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Say hello"}
                ]
            )

            check(True, "Claude API working", "")

        except Exception as e:
            check(False, "", f"Claude API error: {e}")
            warn("Auto-fix will not work without Claude API")
            all_checks_passed = False
    else:
        warn("Claude API not configured - auto-fix will fail")
        info("Add ANTHROPIC_API_KEY to .env and GitHub Secrets")

    print()

    # ========================================
    # 6. Summary and Next Steps
    # ========================================
    print("=" * 70)
    if all_checks_passed:
        print(f"{GREEN}✅ ALL CHECKS PASSED - SYSTEM READY!{RESET}")
        print()
        print(f"{BLUE}🚀 NEXT STEPS:{RESET}")
        print()
        print("1. Start the Telegram bot:")
        print("   python scripts/run_telegram_bot.py")
        print()
        print("2. Test with Telegram command:")
        print("   /fix Add a simple test function")
        print()
        print("3. Check GitHub Actions:")
        print("   https://github.com/aijasminekaur11/khabri/actions")
        print()
    else:
        print(f"{RED}❌ CONFIGURATION INCOMPLETE{RESET}")
        print()
        print(f"{BLUE}📋 ACTION REQUIRED:{RESET}")
        print()

        if not telegram_bot_token:
            print("• Add TELEGRAM_BOT_TOKEN to .env file")
        if not telegram_chat_id:
            print("• Add TELEGRAM_CHAT_ID to .env file")
        if not gh_token:
            print("• Add GH_TOKEN to .env file")
        if not anthropic_key:
            print("• Add ANTHROPIC_API_KEY to .env file")
            print("• Add ANTHROPIC_API_KEY to GitHub Secrets:")
            print("  https://github.com/aijasminekaur11/khabri/settings/secrets/actions")

        print()
        print("See: TELEGRAM_AUTO_FIX_STATUS.md for detailed setup guide")
        print()

    print("=" * 70)

    sys.exit(0 if all_checks_passed else 1)


if __name__ == "__main__":
    main()
