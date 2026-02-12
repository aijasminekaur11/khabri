"""Test a single Gemini API key."""
import google.generativeai as genai

API_KEY = "AIzaSyD5VLy5UNu16fXF6HipBg1OapGt13ijy9k"

print("=" * 55)
print("Testing Single Gemini API Key")
print("=" * 55)
print(f"Key: {API_KEY[:15]}...{API_KEY[-4:]}")
print("-" * 55)

genai.configure(api_key=API_KEY)

try:
    # Test connection
    models = list(genai.list_models())
    gemini_models = [m.name for m in models if 'gemini' in m.name.lower()]
    print(f"[OK] Connected! Found {len(gemini_models)} Gemini models")
    
    # Test generation
    print("[>] Testing text generation...")
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Say 'API key is working!' in 5 words or less.")
    
    if response and response.text:
        print(f"[SUCCESS] Key is WORKING!")
        print(f"          Response: {response.text.strip()}")
        print("=" * 55)
        print("Result: FULLY WORKING!")
    else:
        print("[!] No response text")
        
except Exception as e:
    error_str = str(e)
    if "429" in error_str or "quota" in error_str.lower():
        print(f"[INFO] Rate limit hit - KEY IS VALID but quota exceeded!")
        print("=" * 55)
        print("Result: VALID (quota exceeded)")
    elif "400" in error_str or "401" in error_str or "403" in error_str:
        print(f"[X] INVALID KEY")
        print(f"    Error: {error_str[:80]}")
        print("=" * 55)
        print("Result: INVALID")
    else:
        print(f"[X] Error: {error_str[:80]}")
        print("=" * 55)
        print("Result: ERROR")

print("=" * 55)
