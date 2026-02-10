#!/usr/bin/env python3
"""Test environment variable naming consistency across the codebase"""
import re
import os

def check_file_for_patterns(filepath, patterns, label):
    """Check a file for specific patterns"""
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    results.extend(matches)
    except Exception as e:
        print(f"⚠ Could not read {filepath}: {e}")
    return results

def main():
    print("Checking environment variable naming consistency...")
    print()
    
    # Define expected patterns (after fix)
    expected_patterns = [
        r'os\.getenv\([\'"]SMTP_HOST[\'"]\)',
        r'os\.getenv\([\'"]SMTP_PORT[\'"]\)',
        r'os\.getenv\([\'"]SMTP_USERNAME[\'"]\)',
        r'os\.getenv\([\'"]SMTP_PASSWORD[\'"]\)',
        r'os\.getenv\([\'"]EMAIL_RECIPIENT[\'"]\)',
    ]
    
    # Define old/incorrect patterns (should not exist after fix)
    old_patterns = [
        r'os\.getenv\([\'"]EMAIL_SMTP_HOST[\'"]\)',
        r'os\.getenv\([\'"]EMAIL_SMTP_PORT[\'"]\)',
        r'os\.getenv\([\'"]EMAIL_USERNAME[\'"]\)',
        r'os\.getenv\([\'"]EMAIL_PASSWORD[\'"]\)',
        r'os\.getenv\([\'"]GMAIL_ADDRESS[\'"]\)',
        r'os\.getenv\([\'"]GMAIL_APP_PASSWORD[\'"]\)',
        r'os\.getenv\([\'"]RECIPIENT_EMAIL[\'"]\)',
    ]
    
    files_to_check = [
        'src/notifiers/email_notifier.py',
        'scripts/budget_alert_runner.py',
        'scripts/rbi_alert_runner.py',
        'scripts/github_digest_runner.py',
        'main.py',
    ]
    
    all_good = True
    
    print("Checking for CONSISTENT env var naming (expected patterns):")
    for filepath in files_to_check:
        if os.path.exists(filepath):
            matches = check_file_for_patterns(filepath, expected_patterns, "expected")
            if matches:
                print(f"✓ {filepath}: Uses consistent naming")
            else:
                print(f"⚠ {filepath}: No expected patterns found")
        else:
            print(f"✗ {filepath}: File not found")
            all_good = False
    
    print()
    print("Checking for INCONSISTENT env var naming (old patterns - should be none):")
    found_old = False
    for filepath in files_to_check:
        if os.path.exists(filepath):
            matches = check_file_for_patterns(filepath, old_patterns, "old")
            if matches:
                print(f"✗ {filepath}: Still uses old naming: {matches}")
                found_old = True
                all_good = False
    
    if not found_old:
        print("✓ No old/inconsistent patterns found")
    
    print()
    print("Checking .env.example for consistency:")
    if os.path.exists('.env.example'):
        with open('.env.example', 'r') as f:
            content = f.read()
            checks = [
                ('SMTP_HOST', 'SMTP_HOST' in content),
                ('SMTP_PORT', 'SMTP_PORT' in content),
                ('SMTP_USERNAME', 'SMTP_USERNAME' in content),
                ('SMTP_PASSWORD', 'SMTP_PASSWORD' in content),
                ('EMAIL_RECIPIENT', 'EMAIL_RECIPIENT' in content),
            ]
            for name, found in checks:
                if found:
                    print(f"✓ .env.example defines {name}")
                else:
                    print(f"✗ .env.example missing {name}")
                    all_good = False
    else:
        print("✗ .env.example not found")
        all_good = False
    
    print()
    if all_good:
        print("=" * 50)
        print("✓ ENV VAR NAMING IS CONSISTENT")
        print("=" * 50)
        return 0
    else:
        print("=" * 50)
        print("✗ INCONSISTENCIES FOUND")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    exit(main())
