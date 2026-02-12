"""Test script to verify multiple Google Gemini API keys."""
import os

# The 5 API keys provided by user
GEMINI_API_KEYS = [
    "AIzaSyD35zi84IEZGBqFl3SJX2BtqAL1uKTC9Q0",
    "AIzaSyA068uXXhLx3MQUh0eXOYNQalcJSNUUGt8",
    "AIzaSyCnGWXMFkEGmX2wEK1x7kBRV7SlDIOWo9w",
    "AIzaSyAj1RWvhoOBhix8mryl8YTZEWgvIjc3_Gw",
    "AIzaSyATiWCo1-eEHAU8fs5LNnSV5Z3ZTZ4Ge8w",
]

def test_single_key(api_key, key_index):
    """Test a single Gemini API key."""
    print(f"\n{'-' * 55}")
    print(f"Testing Key #{key_index + 1}: {api_key[:15]}...{api_key[-4:]}")
    print('-' * 55)
    
    try:
        import google.generativeai as genai
    except ImportError:
        print("  [X] google-generativeai package not installed")
        return False, "package_missing"
    
    # Configure the API with this key
    genai.configure(api_key=api_key)
    
    try:
        # List available models
        models = list(genai.list_models())
        gemini_models = [m.name for m in models if 'gemini' in m.name.lower()]
        
        if gemini_models:
            print(f"  [OK] Connected! Found {len(gemini_models)} Gemini models")
        else:
            print("  [!] Connected but no Gemini models found")
            return False, "no_models"
        
        # Try a simple generation test
        print("  [>] Testing text generation...")
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Say 'API key is working!' in 5 words or less.")
        
        if response and response.text:
            print(f"  [SUCCESS] Key is WORKING!")
            print(f"            Response: {response.text.strip()}")
            return True, "working"
        else:
            print("  [!] No response text received")
            return False, "no_response"
            
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
            print(f"  [INFO] Rate limit/quota exceeded - KEY IS VALID!")
            print(f"         Wait a bit before using this key again.")
            return True, "quota_exceeded"
        elif "400" in error_str or "401" in error_str or "403" in error_str:
            print(f"  [X] Authentication error - key is INVALID")
            return False, "invalid_key"
        else:
            print(f"  [X] Error: {error_str[:100]}")
            return False, "error"

def test_all_keys():
    """Test all Gemini API keys."""
    print(f"[INFO] Testing {len(GEMINI_API_KEYS)} API key(s)")
    
    results = []
    for i, key in enumerate(GEMINI_API_KEYS):
        success, status = test_single_key(key, i)
        results.append({
            "key": f"{key[:15]}...{key[-4:]}",
            "full_key": key,
            "success": success,
            "status": status
        })
    
    return results

if __name__ == "__main__":
    print("=" * 55)
    print("Testing Multiple Google Gemini API Keys")
    print("=" * 55)
    
    results = test_all_keys()
    
    print("\n" + "=" * 55)
    print("SUMMARY")
    print("=" * 55)
    
    working_keys = [r for r in results if r["success"]]
    failed_keys = [r for r in results if not r["success"]]
    
    print(f"\nTotal keys tested: {len(results)}")
    print(f"Working keys: {len(working_keys)}")
    print(f"Failed keys: {len(failed_keys)}")
    
    if working_keys:
        print("\n[WORKING KEYS]:")
        for r in working_keys:
            status_msg = "Fully working" if r["status"] == "working" else "Valid (quota exceeded)"
            print(f"  - {r['key']}: {status_msg}")
            print(f"    Full key: {r['full_key']}")
    
    if failed_keys:
        print("\n[FAILED KEYS]:")
        for r in failed_keys:
            print(f"  - {r['key']}: {r['status']}")
    
    print("=" * 55)
