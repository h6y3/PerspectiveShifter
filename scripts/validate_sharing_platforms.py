#!/usr/bin/env python3
"""
Cross-platform sharing validation script
PERMANENT SCRIPT - Should be committed to repo

This script validates sharing URLs and Open Graph tags across platforms.
Can be run for any deployed instance to verify sharing works correctly.

Usage:
    python scripts/validate_sharing_platforms.py
    python scripts/validate_sharing_platforms.py --url https://your-app.vercel.app
    python scripts/validate_sharing_platforms.py --quote-id 1_0
"""

import requests
import argparse
import sys
import re
from urllib.parse import urljoin, quote
import json

DEFAULT_URL = "https://theperspectiveshift.vercel.app"

class PlatformValidator:
    def __init__(self, base_url=DEFAULT_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PerspectiveShifter-Validator/1.0 (Platform Testing)'
        })
    
    def find_quote_id(self):
        """Find a valid quote ID by generating a quote"""
        print("🔍 Finding a valid quote ID...")
        try:
            # Generate a quote
            data = {'user_input': 'testing sharing functionality'}
            response = self.session.post(f"{self.base_url}/shift", data=data)
            
            if response.status_code == 200:
                # Look for quote IDs in the response
                html = response.text
                matches = re.findall(r'data-quote-id="([^"]+)"', html)
                if matches:
                    quote_id = matches[0]
                    print(f"✅ Found quote ID: {quote_id}")
                    return quote_id
                else:
                    print("❌ No quote IDs found in response")
                    return None
            else:
                print(f"❌ Quote generation failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error finding quote ID: {e}")
            return None
    
    def validate_open_graph_tags(self, quote_id):
        """Validate Open Graph meta tags for a quote"""
        print(f"\n🏷️  Validating Open Graph tags for quote {quote_id}...")
        
        try:
            url = f"{self.base_url}/share/{quote_id}"
            response = self.session.get(url)
            
            if response.status_code != 200:
                print(f"❌ Share page returned {response.status_code}")
                return False
            
            html = response.text
            
            # Check required Open Graph tags
            checks = {
                'og:title': r'property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
                'og:description': r'property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']',
                'og:image': r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
                'og:url': r'property=["\']og:url["\'][^>]*content=["\']([^"\']+)["\']',
                'og:type': r'property=["\']og:type["\'][^>]*content=["\']([^"\']+)["\']',
                'twitter:card': r'name=["\']twitter:card["\'][^>]*content=["\']([^"\']+)["\']',
                'twitter:image': r'name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']',
            }
            
            results = {}
            for tag, pattern in checks.items():
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    content = match.group(1)
                    results[tag] = content
                    print(f"✅ {tag}: {content[:100]}{'...' if len(content) > 100 else ''}")
                else:
                    results[tag] = None
                    print(f"❌ {tag}: Missing")
            
            # Validate image URL is accessible
            if results['og:image']:
                try:
                    img_response = self.session.head(results['og:image'])
                    if img_response.status_code == 200:
                        content_type = img_response.headers.get('Content-Type', '')
                        if content_type.startswith('image/'):
                            print(f"✅ og:image is accessible ({content_type})")
                        else:
                            print(f"⚠️  og:image has wrong content type: {content_type}")
                    else:
                        print(f"❌ og:image not accessible: {img_response.status_code}")
                except Exception as e:
                    print(f"❌ Error checking og:image: {e}")
            
            return all(results[tag] for tag in ['og:title', 'og:description', 'og:image', 'og:url'])
            
        except Exception as e:
            print(f"❌ Error validating Open Graph tags: {e}")
            return False
    
    def test_platform_sharing_urls(self, quote_id):
        """Test that sharing URLs work for each platform"""
        print(f"\n🔗 Testing platform sharing URLs for quote {quote_id}...")
        
        share_url = f"{self.base_url}/share/{quote_id}"
        quote_text = "Test quote for sharing validation"
        attribution = "Test Author"
        
        # X/Twitter sharing URL
        twitter_text = f'"{quote_text}" - {attribution} #wisdom #quotes'
        twitter_url = f"https://twitter.com/intent/tweet?text={quote(twitter_text)}&url={quote(share_url)}"
        print(f"🐦 Twitter URL: {twitter_url}")
        
        # LinkedIn sharing URL  
        linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={quote(share_url)}"
        print(f"💼 LinkedIn URL: {linkedin_url}")
        
        # Test if URLs are properly formatted
        try:
            # These should not make actual requests, just validate URL structure
            from urllib.parse import urlparse, parse_qs
            
            # Validate Twitter URL
            parsed_twitter = urlparse(twitter_url)
            if parsed_twitter.netloc == 'twitter.com' and 'text' in twitter_url and 'url' in twitter_url:
                print("✅ Twitter sharing URL is properly formatted")
            else:
                print("❌ Twitter sharing URL has issues")
            
            # Validate LinkedIn URL
            parsed_linkedin = urlparse(linkedin_url)
            if parsed_linkedin.netloc == 'www.linkedin.com' and 'url' in linkedin_url:
                print("✅ LinkedIn sharing URL is properly formatted")
            else:
                print("❌ LinkedIn sharing URL has issues")
                
        except Exception as e:
            print(f"❌ Error validating sharing URLs: {e}")
    
    def test_image_generation(self, quote_id):
        """Test image generation for sharing"""
        print(f"\n🖼️  Testing image generation for quote {quote_id}...")
        
        try:
            # Test different design variations
            designs = [1, 2, 3]
            for design in designs:
                url = f"{self.base_url}/image/{quote_id}?design={design}"
                response = self.session.head(url)
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    content_length = response.headers.get('Content-Length', 'unknown')
                    
                    if content_type == 'image/png':
                        print(f"✅ Design {design}: PNG generated ({content_length} bytes)")
                    else:
                        print(f"❌ Design {design}: Wrong content type: {content_type}")
                else:
                    print(f"❌ Design {design}: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"❌ Error testing image generation: {e}")
    
    def test_share_tracking(self, quote_id):
        """Test share tracking API"""
        print(f"\n📊 Testing share tracking for quote {quote_id}...")
        
        platforms = ['x', 'linkedin', 'native', 'instagram']
        
        for platform in platforms:
            try:
                url = f"{self.base_url}/track-share/{quote_id}"
                data = {'platform': platform}
                response = self.session.post(url, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'success':
                        print(f"✅ {platform}: Tracking successful")
                    else:
                        print(f"❌ {platform}: Unexpected response: {result}")
                else:
                    print(f"❌ {platform}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {platform}: Error - {e}")
    
    def generate_platform_test_urls(self, quote_id):
        """Generate URLs for manual platform testing"""
        print(f"\n🧪 Manual Platform Testing URLs:")
        print("=" * 60)
        
        share_url = f"{self.base_url}/share/{quote_id}"
        
        print(f"Share Page: {share_url}")
        print(f"Image URL: {self.base_url}/image/{quote_id}")
        print()
        
        print("Platform Validators:")
        print(f"📘 Facebook Debugger: https://developers.facebook.com/tools/debug/?q={quote(share_url)}")
        print(f"🐦 Twitter Card Validator: https://cards-dev.twitter.com/validator")
        print(f"💼 LinkedIn Post Inspector: https://www.linkedin.com/post-inspector/inspect/{quote(share_url)}")
        print()
        
        print("Direct Sharing URLs:")
        twitter_text = quote(f'"Test wisdom quote" - Test Author #wisdom #quotes')
        print(f"🐦 Twitter: https://twitter.com/intent/tweet?text={twitter_text}&url={quote(share_url)}")
        print(f"💼 LinkedIn: https://www.linkedin.com/sharing/share-offsite/?url={quote(share_url)}")
        
    def run_validation(self, quote_id=None):
        """Run all validation tests"""
        print(f"🧪 Platform Sharing Validation for {self.base_url}")
        print("=" * 60)
        
        # Find or use provided quote ID
        if not quote_id:
            quote_id = self.find_quote_id()
            
        if not quote_id:
            print("❌ Cannot proceed without a valid quote ID")
            return False
        
        # Run all validation tests
        og_valid = self.validate_open_graph_tags(quote_id)
        self.test_platform_sharing_urls(quote_id)
        self.test_image_generation(quote_id)
        self.test_share_tracking(quote_id)
        self.generate_platform_test_urls(quote_id)
        
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        if og_valid:
            print("✅ Open Graph tags are properly configured")
        else:
            print("❌ Open Graph tags need attention")
        
        print("📋 Next Steps:")
        print("1. Test the generated URLs manually in platform validators")
        print("2. Share a test quote on each platform")
        print("3. Verify images display correctly in social media previews")
        print("4. Check analytics tracking in your admin dashboard")
        
        return og_valid

def main():
    parser = argparse.ArgumentParser(description='Validate sharing functionality across platforms')
    parser.add_argument('--url', default=DEFAULT_URL, 
                       help=f'Base URL to test (default: {DEFAULT_URL})')
    parser.add_argument('--quote-id', 
                       help='Specific quote ID to test (will generate one if not provided)')
    
    args = parser.parse_args()
    
    validator = PlatformValidator(args.url)
    success = validator.run_validation(args.quote_id)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()