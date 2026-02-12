#!/usr/bin/env python3
"""
Quick test to verify Gemini API is working
"""
import os
import sys

try:
    import google.generativeai as genai
    print("✅ google-generativeai package installed")
except ImportError:
    print("❌ google-generativeai NOT installed")
    print("Run: pip install google-generativeai")
    sys.exit(1)

# Try to get API key
api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("❌ No API key found!")
    print("Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable")
    sys.exit(1)

print(f"✅ API key found (length: {len(api_key)})")

# Test API call
try:
    print("\n🔄 Testing Gemini API...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    # Simple test
    response = model.generate_content("Say 'Hello, I am working!' in JSON format with a 'message' key.")

    print("✅ API call successful!")
    print(f"\nResponse text:\n{response.text}")

except Exception as e:
    print(f"❌ API call failed: {e}")
    print(f"\nError type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All tests passed! Gemini API is working.")
