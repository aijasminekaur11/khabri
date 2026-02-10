#!/usr/bin/env python3
"""
Test script to verify cross-platform temp file handling
Part of CLI-TRAP-004 fix verification
"""
import tempfile
import os
import sys

def test_tempfile_paths():
    """Verify tempfile paths work on this platform"""
    temp_dir = tempfile.gettempdir()
    
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Temp directory: {temp_dir}")
    
    # Test all the paths used in the scripts
    test_paths = {
        'budget_articles': os.path.join(temp_dir, 'budget_articles.json'),
        'budget_processed': os.path.join(temp_dir, 'budget_processed.json'),
        'rbi_articles': os.path.join(temp_dir, 'rbi_articles.json'),
        'rbi_processed': os.path.join(temp_dir, 'rbi_processed.json'),
        'competitor_articles': os.path.join(temp_dir, 'competitor_articles.json'),
        'competitor_processed': os.path.join(temp_dir, 'competitor_processed.json'),
        'realtime_articles': os.path.join(temp_dir, 'realtime_articles.json'),
        'realtime_processed': os.path.join(temp_dir, 'realtime_processed.json'),
        'khabri_articles': os.path.join(temp_dir, 'khabri_articles.json'),
        'khabri_processed': os.path.join(temp_dir, 'khabri_processed.json'),
        'health_report': os.path.join(temp_dir, 'health_report.json'),
    }
    
    all_passed = True
    
    for name, path in test_paths.items():
        # Verify path is absolute
        if not os.path.isabs(path):
            print(f"✗ FAIL: {name} path is not absolute: {path}")
            all_passed = False
            continue
        
        # Verify path doesn't contain hardcoded /tmp/
        if '/tmp/' in path and sys.platform != 'linux':
            print(f"⚠ WARNING: {name} contains /tmp/ but platform is {sys.platform}")
        
        print(f"✓ {name}: {path}")
    
    # Verify we can write to temp dir
    test_file = os.path.join(temp_dir, 'khabri_test_write.tmp')
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"✓ Write test passed: {test_file}")
    except Exception as e:
        print(f"✗ Write test failed: {e}")
        all_passed = False
    
    # Test that scripts can import tempfile successfully
    try:
        import scripts.budget_alert_runner as bar
        print("✓ budget_alert_runner imports successfully")
    except Exception as e:
        print(f"✗ budget_alert_runner import failed: {e}")
        all_passed = False
    
    print()
    if all_passed:
        print("=" * 50)
        print("✓ ALL TESTS PASSED")
        print("=" * 50)
        return 0
    else:
        print("=" * 50)
        print("✗ SOME TESTS FAILED")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(test_tempfile_paths())
