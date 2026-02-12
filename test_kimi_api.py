#!/usr/bin/env python3
"""
Test Kimi API Key
"""
import os
import sys

try:
    from openai import OpenAI
    print("OK: openai package installed")
except ImportError:
    print("ERROR: openai NOT installed")
    print("Run: pip install openai")
    sys.exit(1)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("OK: Loaded .env file")
except ImportError:
    print("WARNING: python-dotenv not installed, using system env vars")

# Get API key
api_key = os.getenv('KIMI_API_KEY')

if not api_key:
    print("ERROR: KIMI_API_KEY not found in environment")
    sys.exit(1)

print(f"OK: API key found (starts with: {api_key[:10]}...)")

# Test API call with different endpoints
endpoints = [
    ("Moonshot CN", "https://api.moonshot.cn/v1"),
    ("Moonshot AI", "https://api.moonshot.ai/v1")
]

success = False
for name, base_url in endpoints:
    try:
        print(f"\nTesting {name} endpoint: {base_url}")

        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        response = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello! I am working!' in JSON format."}
            ],
            temperature=0.3,
            max_tokens=100
        )

        print(f"OK: API call successful with {name}!")
        print(f"\nResponse:\n{response.choices[0].message.content}")
        print(f"\nSUCCESS: Kimi API is working with endpoint: {base_url}")
        success = True
        break

    except Exception as e:
        print(f"FAILED with {name}: {e}")

if not success:
    print("\nERROR: All endpoints failed. Please check your API key.")
    sys.exit(1)
