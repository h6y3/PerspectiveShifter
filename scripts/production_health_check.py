#!/usr/bin/env python3
"""
Production Health Check Script
PERMANENT SCRIPT - Should be committed to repo

This script performs comprehensive health checks on the production deployment,
capturing all the manual testing patterns used during development.

Usage:
    python scripts/production_health_check.py
    uv run python scripts/production_health_check.py
    
Returns exit code 0 if all checks pass, 1 if any fail.
"""

import requests
import json
import sys
import re
from datetime import datetime


class ProductionHealthChecker:
    def __init__(self, base_url="https://theperspectiveshift.vercel.app"):
        self.base_url = base_url.rstrip('/')
        self.test_quote_id = "51_0"  # Known working quote ID
        self.checks_passed = 0
        self.checks_failed = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PerspectiveShifter Health Check Bot'
        })
    
    def log_check(self, name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
        if details:
            print(f"       {details}")
        
        if passed:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
            
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
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                passed = response.status_code == 200
                self.log_check(name, passed, f"Status: {response.status_code}")
            except Exception as e:
                self.log_check(name, False, f"Error: {str(e)}")
    
    def check_share_tracking(self):
        """Test share tracking endpoints"""
        print("\n📊 SHARE TRACKING CHECKS")
        print("-" * 40)
        
        # Test valid platforms
        valid_platforms = ['x', 'linkedin', 'native', 'instagram']
        for platform in valid_platforms:
            try:
                response = self.session.post(
                    f"{self.base_url}/track-share/{self.test_quote_id}",
                    json={'platform': platform},
                    headers={'Content-Type': 'application/json'}
                )
                passed = response.status_code == 200 and response.json().get('status') == 'success'
                self.log_check(f"Track {platform}", passed, f"Response: {response.json()}")
            except Exception as e:
                self.log_check(f"Track {platform}", False, f"Error: {str(e)}")
        
        # Test invalid platform rejection
        try:
            response = self.session.post(
                f"{self.base_url}/track-share/{self.test_quote_id}",
                json={'platform': 'invalid'},
                headers={'Content-Type': 'application/json'}
            )
            passed = response.status_code == 400
            self.log_check("Invalid platform rejection", passed, f"Status: {response.status_code}")
        except Exception as e:
            self.log_check("Invalid platform rejection", False, f"Error: {str(e)}")
    
    def check_social_media_meta_tags(self):
        """Verify Open Graph and Twitter meta tags"""
        print("\n🔗 SOCIAL MEDIA META TAG CHECKS")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/share/{self.test_quote_id}")
            html = response.text
            
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
                    
        except Exception as e:
            self.log_check("Meta tag extraction", False, f"Error: {str(e)}")
    
    def check_image_consistency(self):
        """Verify image URL consistency (Instagram bug prevention)"""
        print("\n🖼️  IMAGE CONSISTENCY CHECKS")
        print("-" * 40)
        
        try:
            # Get share page to extract image URLs
            share_response = self.session.get(f"{self.base_url}/share/{self.test_quote_id}")
            share_html = share_response.text
            
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
                try:
                    response = self.session.head(url)
                    size = response.headers.get('content-length')
                    if size:
                        sizes.append(int(size))
                    passed = response.status_code == 200
                    self.log_check(f"{name} accessible", passed, f"Size: {size} bytes")
                except Exception as e:
                    self.log_check(f"{name} accessible", False, f"Error: {str(e)}")
            
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
        
        try:
            response = self.session.get(self.base_url)
            html = response.text
            
            js_checks = [
                ('UrlHelpers object', 'window.UrlHelpers'),
                ('getSocialMediaImageUrl', 'getSocialMediaImageUrl'),
                ('getTrackUrl', 'getTrackUrl'),
                ('SocialShareManager class', 'class SocialShareManager')
            ]
            
            for check_name, pattern in js_checks:
                found = pattern in html
                self.log_check(check_name, found, "Found in HTML" if found else "Not found")
                
        except Exception as e:
            self.log_check("JavaScript helper check", False, f"Error: {str(e)}")
    
    def check_database_functionality(self):
        """Test database operations through API"""
        print("\n🗄️  DATABASE FUNCTIONALITY CHECKS")
        print("-" * 40)
        
        try:
            # Check share stats (tests database read)
            stats_response = self.session.get(f"{self.base_url}/share-stats")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                total = stats.get('total', 0)
                platforms = stats.get('platforms', {})
                self.log_check("Share stats read", True, f"Total: {total}, Platforms: {len(platforms)}")
            else:
                self.log_check("Share stats read", False, f"Status: {stats_response.status_code}")
                
            # Test health endpoint (tests basic DB connection)
            health_response = self.session.get(f"{self.base_url}/health")
            if health_response.status_code == 200:
                health = health_response.json()
                db_status = health.get('database', 'unknown')
                self.log_check("Database connection", db_status == 'connected', f"Status: {db_status}")
            else:
                self.log_check("Database connection", False, f"Health check failed: {health_response.status_code}")
                
        except Exception as e:
            self.log_check("Database functionality", False, f"Error: {str(e)}")
    
    def run_all_checks(self):
        """Run comprehensive health check suite"""
        print("🏥 PRODUCTION HEALTH CHECK")
        print("=" * 50)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.utcnow().isoformat()}Z")
        
        # Run all check suites
        self.check_basic_endpoints()
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