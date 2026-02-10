#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Claude API Integration
Verifies that the Anthropic API key works correctly
"""

import os
import sys
from dotenv import load_dotenv

# Fix Unicode output on Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Load environment variables from project root
from pathlib import Path
from dotenv import dotenv_values

project_root = Path(__file__).parent
env_file = project_root / '.env'

# Load .env explicitly
if env_file.exists():
    env_vars = dotenv_values(env_file)
    for key, value in env_vars.items():
        if value and not os.getenv(key):  # Only set if not already in environment
            os.environ[key] = value

def test_claude_api():
    """Test if Claude API is configured and working"""

    print("=" * 60)
    print("🤖 CLAUDE API VALIDATION TEST")
    print("=" * 60)
    print()

    # Check if API key exists
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found in environment")
        print("   Make sure .env file has ANTHROPIC_API_KEY set")
        return False

    print(f"✅ API Key found: {api_key[:20]}...{api_key[-10:]}")
    print()

    # Test 1: Import anthropic library
    print("TEST 1: Checking anthropic library...")
    try:
        from anthropic import Anthropic
        print("✅ Anthropic library imported successfully")
    except ImportError as e:
        print("❌ Failed to import anthropic library")
        print(f"   Error: {e}")
        print("   Run: pip install anthropic>=0.18.0")
        return False

    print()

    # Test 2: Initialize client
    print("TEST 2: Initializing Claude client...")
    try:
        client = Anthropic(api_key=api_key)
        print("✅ Claude client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False

    print()

    # Test 3: Make a simple API call
    print("TEST 3: Making test API call...")
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'Hello! API is working!' in exactly those words."}
            ]
        )

        response_text = message.content[0].text
        tokens_used = message.usage.input_tokens + message.usage.output_tokens

        print(f"✅ API call successful!")
        print(f"   Response: {response_text}")
        print(f"   Tokens used: {tokens_used}")
        print(f"   Model: claude-sonnet-4")

    except Exception as e:
        print(f"❌ API call failed: {e}")
        print()
        print("Common issues:")
        print("  - Invalid API key")
        print("  - No credits remaining")
        print("  - Network connection issue")
        return False

    print()
    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("Your Claude API is configured correctly!")
    print("The Telegram bot should now provide AI-powered analysis.")
    print()

    return True


if __name__ == "__main__":
    success = test_claude_api()

    if not success:
        print()
        print("=" * 60)
        print("❌ TESTS FAILED")
        print("=" * 60)
        print()
        print("Please fix the issues above and try again.")
        print()
        exit(1)
    else:
        print("🎉 Ready for AI-powered auto-fix!")
        print()
        print("Try sending this on Telegram:")
        print("   /fix Add pagination to news list")
        print()
        print("You should get:")
        print("   ✅ Issue created")
        print("   🤖 Claude analysis posted")
        print("   📊 Token usage shown")
        print()
        exit(0)
