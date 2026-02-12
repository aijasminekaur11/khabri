"""Test Kimi API key from .env file."""
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("KIMI_API_KEY")

if not API_KEY:
    print("[X] ERROR: KIMI_API_KEY not found in .env file")
    exit(1)

print("=" * 55)
print("Testing Kimi API Key")
print("=" * 55)
print(f"Key: {API_KEY[:15]}...{API_KEY[-4:]}")
print("-" * 55)

# Initialize Kimi client (OpenAI-compatible)
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.moonshot.cn/v1"
)

try:
    # Test connection by listing models
    print("[>] Testing connection to Kimi API...")
    models = client.models.list()
    model_names = [m.id for m in models.data]
    print(f"[OK] Connected! Found {len(model_names)} models")
    
    # Test generation
    print("[>] Testing text generation...")
    response = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "user", "content": "Say 'API key is working!' in 5 words or less."}
        ],
        max_tokens=20
    )
    
    if response and response.choices and response.choices[0].message.content:
        print(f"[SUCCESS] Key is WORKING!")
        print(f"          Response: {response.choices[0].message.content.strip()}")
        print("=" * 55)
        print("Result: FULLY WORKING!")
    else:
        print("[!] No response text")
        print("=" * 55)
        print("Result: FAILED")
        
except Exception as e:
    error_str = str(e)
    if "429" in error_str or "rate limit" in error_str.lower():
        print(f"[INFO] Rate limit hit - KEY IS VALID but quota exceeded!")
        print(f"       Error: {error_str[:100]}")
        print("=" * 55)
        print("Result: VALID (quota exceeded)")
    elif "401" in error_str or "403" in error_str or "invalid" in error_str.lower():
        print(f"[X] INVALID KEY")
        print(f"    Error: {error_str[:100]}")
        print("=" * 55)
        print("Result: INVALID")
    else:
        print(f"[X] Error: {error_str[:100]}")
        print("=" * 55)
        print("Result: ERROR")

print("=" * 55)
