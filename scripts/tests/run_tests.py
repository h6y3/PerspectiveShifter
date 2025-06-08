#!/usr/bin/env python3
"""
Test Suite Runner for PerspectiveShifter

Runs all tests in the correct order with proper reporting.
"""

import os
import sys
import subprocess
import glob
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_test_file(test_file):
    """Run a single test file and return success status"""
    print(f"\n🧪 Running {test_file}")
    print("-" * 50)
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ {test_file} - PASSED")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {test_file} - FAILED")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_file} - TIMEOUT (30s)")
        return False
    except Exception as e:
        print(f"💥 {test_file} - ERROR: {e}")
        return False

def run_test_category(category_name, test_dir):
    """Run all tests in a category"""
    print(f"\n🎯 Running {category_name.upper()} Tests")
    print("=" * 60)
    
    test_files = glob.glob(os.path.join(test_dir, "test_*.py"))
    if not test_files:
        print(f"No test files found in {test_dir}")
        return 0, 0
    
    passed = 0
    total = len(test_files)
    
    for test_file in test_files:
        if run_test_file(test_file):
            passed += 1
    
    print(f"\n📊 {category_name} Results: {passed}/{total} passed")
    return passed, total

def main():
    """Run all test categories"""
    print("🏥 PerspectiveShifter Test Suite")
    print("=" * 60)
    
    test_base = Path(__file__).parent
    categories = [
        ("Unit", test_base / "unit"),
        ("Integration", test_base / "integration"), 
        ("Deployment", test_base / "deployment"),
        ("Performance", test_base / "performance")
    ]
    
    total_passed = 0
    total_tests = 0
    
    for category_name, category_dir in categories:
        if category_dir.exists():
            passed, count = run_test_category(category_name, category_dir)
            total_passed += passed
            total_tests += count
        else:
            print(f"\n⚠️  {category_name} test directory not found: {category_dir}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 TEST SUITE SUMMARY")
    print("=" * 60)
    
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_tests - total_passed}")
    print(f"📊 Pass Rate: {pass_rate:.1f}%")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)