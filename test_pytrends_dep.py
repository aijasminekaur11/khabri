#!/usr/bin/env python3
"""Test pytrends dependency availability"""
import sys

def test_pytrends_import():
    """Verify pytrends can be imported"""
    try:
        from pytrends.request import TrendReq
        print("✓ pytrends import successful")
        print(f"  TrendReq class available: {TrendReq}")
        return True
    except ImportError as e:
        print(f"✗ pytrends import failed: {e}")
        print("  Note: This is expected if pytrends is not installed yet.")
        print("  Run: pip install pytrends>=4.9.0")
        return False

def test_keyword_engine_import():
    """Verify KeywordEngine can be imported (with or without pytrends)"""
    try:
        from src.notifiers.keyword_engine import KeywordEngine
        print("✓ KeywordEngine import successful")
        
        # Test instantiation
        engine = KeywordEngine()
        print(f"  pytrends_available: {engine.pytrends_available}")
        return True
    except Exception as e:
        print(f"✗ KeywordEngine import failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing pytrends dependency...")
    print()
    
    pytrends_ok = test_pytrends_import()
    print()
    
    engine_ok = test_keyword_engine_import()
    print()
    
    if engine_ok:
        print("=" * 50)
        print("✓ KEYWORD ENGINE WORKS")
        if not pytrends_ok:
            print("  (with fallback extraction - pytrends not installed)")
        print("=" * 50)
        sys.exit(0)
    else:
        print("=" * 50)
        print("✗ KEYWORD ENGINE FAILED")
        print("=" * 50)
        sys.exit(1)
