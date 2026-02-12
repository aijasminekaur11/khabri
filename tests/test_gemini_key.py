"""Test script to verify Google Gemini API key is working."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_key():
    """Test if Gemini API key is valid and working."""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("[X] GOOGLE_API_KEY not found in .env file")
        return False, "missing"
    
    print(f"[OK] GOOGLE_API_KEY found: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        import google.generativeai as genai
    except ImportError:
        print("[X] google-generativeai package not installed")
        print("   Run: pip install google-generativeai")
        return False, "package_missing"
    
    print("[OK] google-generativeai package is installed")
    
    # Configure the API
    genai.configure(api_key=api_key)
    
    try:
        # List available models
        models = list(genai.list_models())
        gemini_models = [m.name for m in models if 'gemini' in m.name.lower()]
        
        if gemini_models:
            print(f"[OK] Successfully connected to Google AI API")
            print(f"     Available Gemini models: {len(gemini_models)}")
            for model in gemini_models[:5]:  # Show first 5
                print(f"       - {model}")
        else:
            print("[!] Connected but no Gemini models found")
        
        # Try a simple generation test
        print("\n[>] Testing text generation...")
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Say 'API key is working!' in 5 words or less.")
        
        if response and response.text:
            print(f"[SUCCESS] API KEY IS WORKING!")
            print(f"          Response: {response.text.strip()}")
            return True, "working"
        else:
            print("[!] No response text received")
            return False, "no_response"
            
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
            print(f"[INFO] Rate limit/quota exceeded - this means the KEY IS VALID!")
            print(f"       But you've hit the free tier limit. Retry in ~35 seconds.")
            return True, "quota_exceeded"
        elif "400" in error_str or "401" in error_str or "403" in error_str:
            print(f"[X] Authentication error - key may be invalid")
            print(f"    Error: {e}")
            return False, "invalid_key"
        else:
            print(f"[X] Error: {e}")
            return False, "error"

if __name__ == "__main__":
    print("=" * 55)
    print("Testing Google Gemini API Key")
    print("=" * 55)
    success, status = test_gemini_key()
    print("=" * 55)
    if success and status == "working":
        print("Result: SUCCESS - Gemini API key is WORKING perfectly!")
    elif success and status == "quota_exceeded":
        print("Result: KEY IS VALID (but quota exceeded - wait 35s)")
    elif status == "missing":
        print("Result: FAILED - API key not found in .env")
    elif status == "invalid_key":
        print("Result: FAILED - API key is invalid")
    else:
        print("Result: FAILED - Could not verify API key")
    print("=" * 55)
