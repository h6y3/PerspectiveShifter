#!/usr/bin/env python3
"""
Production Health Check Script
PERMANENT SCRIPT - Should be committed to repo

This script performs comprehensive health checks on the production deployment,
capturing all the manual testing patterns used during development.

Usage:
    python3 scripts/tests/production_health_check.py
    python3 scripts/tests/production_health_check.py --url https://your-preview-url.vercel.app
    
Returns exit code 0 if all checks pass, 1 if any fail.
Uses only built-in Python libraries for maximum compatibility.
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import sys
import re
import time
from datetime import datetime


class ProductionHealthChecker:
    def __init__(self, base_url="https://theperspectiveshift.vercel.app"):
        self.base_url = base_url.rstrip('/')
        self.test_quote_id = "51_0"  # Known working quote ID
        self.checks_passed = 0
        self.checks_failed = 0
        self.user_agent = 'PerspectiveShifter Health Check Bot'
    
    def log_check(self, name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
        if details:
            print(f"       {details}")
        
        if passed:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
    
    def make_request(self, url, method='GET', data=None, headers=None):
        """Make HTTP request using urllib."""
        if headers is None:
            headers = {}
        headers['User-Agent'] = self.user_agent
        
        try:
            if data and isinstance(data, dict):
                data = json.dumps(data).encode('utf-8')
                headers['Content-Type'] = 'application/json'
            
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')
                return {
                    'status_code': response.status,
                    'content': content,
                    'headers': dict(response.headers),
                    'success': True
                }
        except urllib.error.HTTPError as e:
            return {
                'status_code': e.code,
                'content': e.read().decode('utf-8') if hasattr(e, 'read') else '',
                'success': False,
                'error': f'HTTP {e.code}: {e.reason}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def check_basic_endpoints(self):
        """Test all basic endpoints return 200"""
        print("\n🔍 BASIC ENDPOINT CHECKS")
        print("-" * 40)
        
        endpoints = [
            ("/", "Homepage"),
            (f"/share/{self.test_quote_id}", "Share page"),
            (f"/image/{self.test_quote_id}?design=3", "Image generation"),
            ("/health", "Health endpoint"),
            ("/privacy", "Privacy page"),
            ("/share-stats", "Share statistics API")
        ]
        
        for endpoint, name in endpoints:
            response = self.make_request(f"{self.base_url}{endpoint}")
            if response['success']:
                passed = response['status_code'] == 200
                self.log_check(name, passed, f"Status: {response['status_code']}")
            else:
                self.log_check(name, False, f"Error: {response.get('error', 'Unknown error')}")
    
    def check_api_v1_endpoints(self):
        """Test API v1 endpoints and functionality"""
        print("\n🔧 API v1 ENDPOINT CHECKS")
        print("-" * 40)
        
        # Test GET endpoints
        api_endpoints = [
            ("/api/v1/health", "API v1 Health"),
            ("/api/v1/stats", "API v1 Statistics"),
        ]
        
        for endpoint, name in api_endpoints:
            response = self.make_request(f"{self.base_url}{endpoint}")
            if response['success']:
                passed = response['status_code'] == 200
                try:
                    json_data = json.loads(response['content'])
                    details = f"Status: {response['status_code']}, Keys: {list(json_data.keys())}"
                except:
                    details = f"Status: {response['status_code']}"
                self.log_check(name, passed, details)
            else:
                self.log_check(name, False, f"Error: {response.get('error', 'Unknown error')}")
        
        # Test POST /api/v1/quotes
        print("\n📝 Testing API v1 Quote Generation...")
        quote_data = {
            "input": "test deployment verification",
            "style": "practical"
        }
        response = self.make_request(f"{self.base_url}/api/v1/quotes", 'POST', quote_data)
        if response['success']:
            passed = response['status_code'] == 200
            try:
                json_data = json.loads(response['content'])
                quote_id = json_data.get('quote_id')
                quote = json_data.get('quote', '')[:50] + '...' if json_data.get('quote') else 'None'
                details = f"Status: {response['status_code']}, Quote ID: {quote_id}, Quote: {quote}"
            except:
                details = f"Status: {response['status_code']}"
            self.log_check("API v1 Quote Generation", passed, details)
            
            # If quote generation succeeded, test image generation
            if passed and quote_id:
                img_response = self.make_request(f"{self.base_url}/api/v1/images/{quote_id}")
                img_passed = img_response['success'] and img_response['status_code'] == 200
                self.log_check("API v1 Image Generation", img_passed, 
                             f"Status: {img_response.get('status_code', 'Error')}")
        else:
            self.log_check("API v1 Quote Generation", False, f"Error: {response.get('error', 'Unknown error')}")
    
    def check_share_tracking(self):
        """Test share tracking endpoints"""
        print("\n📊 SHARE TRACKING CHECKS")
        print("-" * 40)
        
        # Test valid platforms
        valid_platforms = ['x', 'linkedin', 'native', 'instagram']
        for platform in valid_platforms:
            response = self.make_request(
                f"{self.base_url}/track-share/{self.test_quote_id}",
                'POST',
                {'platform': platform}
            )
            if response['success']:
                passed = response['status_code'] == 200
                try:
                    json_data = json.loads(response['content'])
                    details = f"Response: {json_data}"
                    passed = passed and json_data.get('status') == 'success'
                except:
                    details = f"Status: {response['status_code']}"
                self.log_check(f"Track {platform}", passed, details)
            else:
                self.log_check(f"Track {platform}", False, f"Error: {response.get('error', 'Unknown error')}")
        
        # Test invalid platform rejection
        response = self.make_request(
            f"{self.base_url}/track-share/{self.test_quote_id}",
            'POST',
            {'platform': 'invalid'}
        )
        if response['success'] or 'status_code' in response:
            passed = response.get('status_code') == 400
            self.log_check("Invalid platform rejection", passed, f"Status: {response.get('status_code')}")
        else:
            self.log_check("Invalid platform rejection", False, f"Error: {response.get('error', 'Unknown error')}")
    
    def check_social_media_meta_tags(self):
        """Verify Open Graph and Twitter meta tags"""
        print("\n🔗 SOCIAL MEDIA META TAG CHECKS")
        print("-" * 40)
        
        response = self.make_request(f"{self.base_url}/share/{self.test_quote_id}")
        if response['success']:
            html = response['content']
            
            # Check for required meta tags
            meta_checks = [
                ('og:image', r'property="og:image"[^>]*content="([^"]*)"'),
                ('og:title', r'property="og:title"[^>]*content="([^"]*)"'),
                ('og:description', r'property="og:description"[^>]*content="([^"]*)"'),
                ('twitter:image', r'name="twitter:image"[^>]*content="([^"]*)"'),
                ('twitter:card', r'name="twitter:card"[^>]*content="([^"]*)"')
            ]
            
            for tag_name, pattern in meta_checks:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    content = match.group(1)
                    passed = bool(content.strip())
                    self.log_check(f"{tag_name} tag", passed, f"Content: {content[:50]}...")
                else:
                    self.log_check(f"{tag_name} tag", False, "Tag not found")
        else:
            self.log_check("Meta tag extraction", False, f"Error: {response.get('error', 'Unknown error')}")
    
    def check_image_consistency(self):
        """Verify image URL consistency (Instagram bug prevention)"""
        print("\n🖼️  IMAGE CONSISTENCY CHECKS")
        print("-" * 40)
        
        try:
            # Get share page to extract image URLs
            share_response = self.make_request(f"{self.base_url}/share/{self.test_quote_id}")
            if not share_response['success']:
                self.log_check("Image consistency check", False, f"Error: {share_response.get('error', 'Unknown error')}")
                return
            share_html = share_response['content']
            
            # Extract different image URLs
            og_image_match = re.search(r'property="og:image"[^>]*content="([^"]*)"', share_html)
            display_image_match = re.search(r'<img src="([^"]*)" alt="Quote by', share_html)
            js_image_match = re.search(r'imageUrl: "([^"]*)"', share_html)
            
            urls_to_test = []
            if og_image_match:
                urls_to_test.append(('og:image', og_image_match.group(1)))
            if display_image_match:
                urls_to_test.append(('display image', display_image_match.group(1)))
            if js_image_match:
                js_url = js_image_match.group(1)
                if js_url.startswith('/'):
                    js_url = self.base_url + js_url
                urls_to_test.append(('JS imageUrl', js_url))
            
            # Test all URLs and check consistency
            sizes = []
            for name, url in urls_to_test:
                # Use HEAD request equivalent by making a GET request and checking response
                response = self.make_request(url)
                if response['success']:
                    size = response['headers'].get('content-length')
                    if size:
                        sizes.append(int(size))
                    passed = response['status_code'] == 200
                    self.log_check(f"{name} accessible", passed, f"Size: {size} bytes")
                else:
                    self.log_check(f"{name} accessible", False, f"Error: {response.get('error', 'Unknown error')}")
            
            # Check consistency
            if len(set(sizes)) <= 1:
                self.log_check("Image size consistency", True, f"All images: {sizes[0] if sizes else 'unknown'} bytes")
            else:
                self.log_check("Image size consistency", False, f"Inconsistent sizes: {set(sizes)}")
                
        except Exception as e:
            self.log_check("Image consistency check", False, f"Error: {str(e)}")
    
    def check_javascript_helpers(self):
        """Verify JavaScript URL helpers are loaded"""
        print("\n🟨 JAVASCRIPT HELPER CHECKS")
        print("-" * 40)
        
        response = self.make_request(self.base_url)
        if response['success']:
            html = response['content']
            
            js_checks = [
                ('UrlHelpers object', 'window.UrlHelpers'),
                ('getSocialMediaImageUrl', 'getSocialMediaImageUrl'),
                ('getTrackUrl', 'getTrackUrl'),
                ('SocialShareManager class', 'class SocialShareManager')
            ]
            
            for check_name, pattern in js_checks:
                found = pattern in html
                self.log_check(check_name, found, "Found in HTML" if found else "Not found")
        else:
            self.log_check("JavaScript helper check", False, f"Error: {response.get('error', 'Unknown error')}")
    
    def check_database_functionality(self):
        """Test database operations through API"""
        print("\n🗄️  DATABASE FUNCTIONALITY CHECKS")
        print("-" * 40)
        
        # Check share stats (tests database read)
        stats_response = self.make_request(f"{self.base_url}/share-stats")
        if stats_response['success'] and stats_response['status_code'] == 200:
            try:
                stats = json.loads(stats_response['content'])
                total = stats.get('total', 0)
                platforms = stats.get('platforms', {})
                self.log_check("Share stats read", True, f"Total: {total}, Platforms: {len(platforms)}")
            except:
                self.log_check("Share stats read", False, "Invalid JSON response")
        else:
            self.log_check("Share stats read", False, f"Status: {stats_response.get('status_code', 'Error')}")
            
        # Test health endpoint (tests basic DB connection)
        health_response = self.make_request(f"{self.base_url}/health")
        if health_response['success'] and health_response['status_code'] == 200:
            try:
                health = json.loads(health_response['content'])
                db_status = health.get('database', 'unknown')
                self.log_check("Database connection", db_status == 'connected', f"Status: {db_status}")
            except:
                self.log_check("Database connection", False, "Invalid JSON response")
        else:
            self.log_check("Database connection", False, f"Health check failed: {health_response.get('status_code', 'Error')}")
    
    def run_all_checks(self):
        """Run comprehensive health check suite"""
        print("🏥 PRODUCTION HEALTH CHECK")
        print("=" * 50)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.utcnow().isoformat()}Z")
        
        # Run all check suites
        self.check_basic_endpoints()
        self.check_api_v1_endpoints()
        self.check_share_tracking()
        self.check_social_media_meta_tags()
        self.check_image_consistency()
        self.check_javascript_helpers()
        self.check_database_functionality()
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 HEALTH CHECK SUMMARY")
        print("=" * 50)
        
        total_checks = self.checks_passed + self.checks_failed
        pass_rate = (self.checks_passed / total_checks * 100) if total_checks > 0 else 0
        
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")
        
        if self.checks_failed == 0:
            print("\n🎉 ALL CHECKS PASSED - Production is healthy!")
            return 0
        else:
            print(f"\n⚠️  {self.checks_failed} CHECKS FAILED - Investigate issues above")
            return 1


def main():
    """Run production health check and exit with appropriate code"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Production health check for PerspectiveShifter')
    parser.add_argument('--url', default='https://theperspectiveshift.vercel.app',
                       help='Base URL to check (default: production)')
    parser.add_argument('--quote-id', default='51_0',
                       help='Test quote ID to use (default: 51_0)')
    
    args = parser.parse_args()
    
    checker = ProductionHealthChecker(args.url)
    checker.test_quote_id = args.quote_id
    
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()