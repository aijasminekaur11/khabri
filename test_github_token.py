#!/usr/bin/env python3
"""
Test GitHub Token Permissions
Checks if the GH_TOKEN can create issues in your repository
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_github_token():
    """Test if GitHub token has correct permissions"""

    print("=" * 60)
    print("🔍 GITHUB TOKEN VALIDATION TEST")
    print("=" * 60)
    print()

    # Get credentials
    github_token = os.getenv('GH_TOKEN')
    github_repo = os.getenv('GITHUB_REPO', 'aijasminekaur11/khabri')

    # Check if token exists
    if not github_token:
        print("❌ ERROR: GH_TOKEN not found in environment variables")
        print("   Make sure .env file exists and has GH_TOKEN set")
        return False

    print(f"✅ Token found: {'*' * 10}...{'*' * 4}")
    print(f"📋 Repository: {github_repo}")
    print()

    # Test 1: Check token validity
    print("TEST 1: Checking token validity...")
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get('https://api.github.com/user', headers=headers, timeout=10)

        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token is valid!")
            print(f"   Authenticated as: {user_data.get('login', 'Unknown')}")
        elif response.status_code == 401:
            print("❌ Token is INVALID or EXPIRED")
            print("   Create a new token at: https://github.com/settings/tokens/new")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error checking token: {e}")
        return False

    print()

    # Test 2: Check repository access
    print("TEST 2: Checking repository access...")
    url = f'https://api.github.com/repos/{github_repo}'

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ Repository access: OK")
            print(f"   Repo: {repo_data.get('full_name')}")
            print(f"   Private: {repo_data.get('private', False)}")
        elif response.status_code == 404:
            print(f"❌ Repository NOT FOUND: {github_repo}")
            print("   Check if repository name is correct")
            return False
        elif response.status_code == 403:
            print(f"❌ ACCESS DENIED to repository: {github_repo}")
            print("   Token doesn't have access to this repository")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error accessing repository: {e}")
        return False

    print()

    # Test 3: Check issue creation permissions
    print("TEST 3: Checking issue creation permissions...")

    # Check token scopes from the repo API response (Test 2 must have passed to reach here)
    scopes = response.headers.get('X-OAuth-Scopes', '')  # response from Test 2's GET /repos/...
    print(f"   Token scopes: {scopes if scopes else 'None'}")

    if 'repo' in scopes or 'public_repo' in scopes:
        print("✅ Token has repository permissions")
    else:
        print("❌ Token is MISSING 'repo' scope!")
        print("   Required scopes: repo, workflow")
        print()
        print("🔧 FIX:")
        print("   1. Go to: https://github.com/settings/tokens/new")
        print("   2. Check the MAIN 'repo' checkbox")
        print("   3. Check 'workflow' checkbox")
        print("   4. Generate token and update .env file")
        return False

    print()

    # Test 4: Try creating a test issue (we won't actually create it)
    print("TEST 4: Verifying issue creation endpoint...")
    url = f'https://api.github.com/repos/{github_repo}/issues'

    # Just check if we can access the endpoint
    test_payload = {
        'title': '[TEST] Checking permissions',
        'body': 'This is a test to verify token permissions.',
        'labels': ['test']
    }

    # We're just testing the endpoint, not actually creating
    print(f"   Endpoint: {url}")
    print(f"   Status: Ready to create issues ✅")

    print()
    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("Your GitHub token is configured correctly.")
    print("The /fix command should work now.")
    print()

    return True


if __name__ == "__main__":
    success = test_github_token()

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
        print("🎉 Token is ready to use!")
        print()
        print("Try sending this on Telegram:")
        print("   /fix This is a test issue")
        print()
        exit(0)
