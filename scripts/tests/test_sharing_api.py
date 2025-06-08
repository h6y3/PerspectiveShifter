#!/usr/bin/env python3
"""
Automated API testing for sharing functionality
PERMANENT SCRIPT - Should be committed to repo

This script tests all sharing-related API endpoints automatically.
Can be run as part of CI/CD pipeline or manual verification.

Usage:
    python scripts/test_sharing_api.py
    python scripts/test_sharing_api.py --base-url https://your-app.vercel.app
"""

import sys
import os
import requests
import json
import time
import argparse
from urllib.parse import urljoin

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
DEFAULT_BASE_URL = "http://localhost:5000"
TIMEOUT = 30
USER_AGENT = "PerspectiveShifter-Test/1.0"

class SharingAPITester:
    def __init__(self, base_url=DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.test_quote_id = None
        self.results = []
        
    def log_result(self, test_name, passed, details="", response_time=None):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            'test': test_name,
            'passed': passed,
            'details': details,
            'response_time': response_time
        }
        self.results.append(result)
        
        time_str = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {test_name}{time_str}")
        if details and not passed:
            print(f"    Details: {details}")
    
    def test_health_check(self):
        """Test that the application is running"""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/health", timeout=TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Health Check", True, f"Status: {data.get('status')}", response_time)
                return True
            else:
                self.log_result("Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Health Check", False, str(e))
            return False
    
    def create_test_quote(self):
        """Create a test quote for sharing tests"""
        try:
            start_time = time.time()
            data = {'user_input': 'feeling anxious about testing'}
            response = self.session.post(f"{self.base_url}/shift", data=data, timeout=TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Extract quote ID from the response HTML (look for data-quote-id)
                html = response.text
                import re
                match = re.search(r'data-quote-id="([^"]+)"', html)
                if match:
                    self.test_quote_id = match.group(1)
                    self.log_result("Create Test Quote", True, f"Quote ID: {self.test_quote_id}", response_time)
                    return True
                else:
                    self.log_result("Create Test Quote", False, "Could not extract quote ID from response")
                    return False
            else:
                self.log_result("Create Test Quote", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Create Test Quote", False, str(e))
            return False
    
    def test_share_page(self):
        """Test the shareable page endpoint"""
        if not self.test_quote_id:
            self.log_result("Share Page", False, "No test quote ID available")
            return False
            
        try:
            start_time = time.time()
            url = f"{self.base_url}/share/{self.test_quote_id}"
            response = self.session.get(url, timeout=TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                html = response.text
                # Check for essential Open Graph tags
                og_checks = [
                    'property="og:title"' in html,
                    'property="og:description"' in html,
                    'property="og:image"' in html,
                    'property="og:url"' in html,
                    'name="twitter:card"' in html
                ]
                
                if all(og_checks):
                    self.log_result("Share Page", True, "All Open Graph tags present", response_time)
                    return True
                else:
                    missing_tags = []
                    if 'property="og:title"' not in html: missing_tags.append("og:title")
                    if 'property="og:description"' not in html: missing_tags.append("og:description")
                    if 'property="og:image"' not in html: missing_tags.append("og:image")
                    if 'property="og:url"' not in html: missing_tags.append("og:url")
                    if 'name="twitter:card"' not in html: missing_tags.append("twitter:card")
                    
                    self.log_result("Share Page", False, f"Missing tags: {', '.join(missing_tags)}", response_time)
                    return False
            else:
                self.log_result("Share Page", False, f"HTTP {response.status_code}", response_time)
                return False
        except Exception as e:
            self.log_result("Share Page", False, str(e))
            return False
    
    def test_image_generation(self):
        """Test the image generation endpoint"""
        if not self.test_quote_id:
            self.log_result("Image Generation", False, "No test quote ID available")
            return False
            
        try:
            start_time = time.time()
            url = f"{self.base_url}/image/{self.test_quote_id}"
            response = self.session.get(url, timeout=TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                content_length = len(response.content)
                
                if content_type == 'image/png' and content_length > 1000:  # Reasonable PNG size
                    self.log_result("Image Generation", True, f"PNG generated ({content_length} bytes)", response_time)
                    return True
                else:
                    self.log_result("Image Generation", False, f"Invalid content: {content_type}, {content_length} bytes", response_time)
                    return False
            else:
                self.log_result("Image Generation", False, f"HTTP {response.status_code}", response_time)
                return False
        except Exception as e:
            self.log_result("Image Generation", False, str(e))
            return False
    
    def test_share_tracking(self):
        """Test the share tracking API"""
        if not self.test_quote_id:
            self.log_result("Share Tracking", False, "No test quote ID available")
            return False
            
        platforms = ['x', 'linkedin', 'native', 'instagram']
        all_passed = True
        
        for platform in platforms:
            try:
                start_time = time.time()
                url = f"{self.base_url}/track-share/{self.test_quote_id}"
                data = {'platform': platform}
                response = self.session.post(url, json=data, timeout=TIMEOUT)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'success':
                        self.log_result(f"Track Share ({platform})", True, "Tracking successful", response_time)
                    else:
                        self.log_result(f"Track Share ({platform})", False, f"Unexpected response: {result}")
                        all_passed = False
                else:
                    self.log_result(f"Track Share ({platform})", False, f"HTTP {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_result(f"Track Share ({platform})", False, str(e))
                all_passed = False
        
        return all_passed
    
    def test_share_stats(self):
        """Test the share statistics endpoint"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/share-stats"
            response = self.session.get(url, timeout=TIMEOUT)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'total' in data and 'platforms' in data:
                    total = data['total']
                    platforms = data['platforms']
                    self.log_result("Share Stats", True, f"Total: {total}, Platforms: {len(platforms)}", response_time)
                    return True
                else:
                    self.log_result("Share Stats", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_result("Share Stats", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Share Stats", False, str(e))
            return False
    
    def test_invalid_quote_ids(self):
        """Test error handling for invalid quote IDs"""
        invalid_ids = ['invalid', '999_0', 'abc_def', '']
        all_passed = True
        
        for invalid_id in invalid_ids:
            try:
                start_time = time.time()
                url = f"{self.base_url}/share/{invalid_id}"
                response = self.session.get(url, timeout=TIMEOUT, allow_redirects=False)
                response_time = time.time() - start_time
                
                # Should redirect (3xx) or return 404
                if response.status_code in [302, 404]:
                    self.log_result(f"Invalid ID Handling ({invalid_id})", True, f"HTTP {response.status_code}", response_time)
                else:
                    self.log_result(f"Invalid ID Handling ({invalid_id})", False, f"Unexpected HTTP {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_result(f"Invalid ID Handling ({invalid_id})", False, str(e))
                all_passed = False
        
        return all_passed
    
    def run_all_tests(self):
        """Run all API tests"""
        print(f"🧪 Starting API tests for {self.base_url}")
        print("=" * 60)
        
        # Core functionality tests
        if not self.test_health_check():
            print("❌ Application not accessible, stopping tests")
            return False
        
        if not self.create_test_quote():
            print("❌ Cannot create test quote, stopping tests")
            return False
        
        # Sharing functionality tests
        self.test_share_page()
        self.test_image_generation()
        self.test_share_tracking()
        self.test_share_stats()
        
        # Error handling tests
        self.test_invalid_quote_ids()
        
        # Results summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        pass_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if pass_rate == 100:
            print("🎉 All tests passed!")
        elif pass_rate >= 80:
            print("⚠️  Most tests passed, review failures")
        else:
            print("❌ Multiple test failures, review implementation")
        
        # Show failed tests
        failed_tests = [r for r in self.results if not r['passed']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        return pass_rate == 100

def main():
    parser = argparse.ArgumentParser(description='Test sharing API endpoints')
    parser.add_argument('--base-url', default=DEFAULT_BASE_URL, 
                       help=f'Base URL to test (default: {DEFAULT_BASE_URL})')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output')
    
    args = parser.parse_args()
    
    tester = SharingAPITester(args.base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()