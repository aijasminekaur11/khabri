#!/usr/bin/env python3
"""
Debug Environment Variables
Shows which environment variables are actually loaded
"""

import os
import sys

print("=" * 60)
print("ENVIRONMENT VARIABLE DEBUG")
print("=" * 60)
print()

# Check all relevant variables
variables_to_check = [
    'TELEGRAM_BOT_TOKEN',
    'TELEGRAM_CHAT_ID',
    'GH_TOKEN',
    'GITHUB_REPO',
    'ANTHROPIC_API_KEY'
]

print("Checking environment variables:")
print()

for var in variables_to_check:
    value = os.getenv(var)
    if value:
        # Show first 20 and last 10 chars for security
        if len(value) > 30:
            masked = f"{value[:20]}...{value[-10:]}"
        else:
            masked = f"{value[:10]}...{value[-4:]}" if len(value) > 15 else "***SET***"
        print(f"✅ {var}: {masked}")
    else:
        print(f"❌ {var}: NOT FOUND")

print()
print("=" * 60)
print()

# Try importing anthropic
try:
    from anthropic import Anthropic
    print("✅ anthropic library is installed")

    # Try to initialize
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        try:
            client = Anthropic(api_key=api_key)
            print("✅ Claude client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Claude client: {e}")
    else:
        print("❌ Cannot initialize - ANTHROPIC_API_KEY not found")

except ImportError as e:
    print(f"❌ anthropic library not installed: {e}")

print()
print("=" * 60)
