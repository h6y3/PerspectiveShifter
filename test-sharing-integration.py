#!/usr/bin/env python3
"""
Quick integration test for sharing functionality
TEMPORARY SCRIPT - Delete after testing

This bypasses the circular import issue by testing against
a deployed instance or manually started server.
"""

import requests
import sys
import json

# Test configuration
BASE_URL = "https://theperspectiveshift.vercel.app"  # Change to your deployed URL
LOCAL_URL = "http://localhost:5000"

def test_deployed_sharing():
    """Test sharing functionality on deployed instance"""
    print("🧪 Testing deployed sharing functionality...")
    print(f"Testing URL: {BASE_URL}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test quote generation (to get a real quote ID)
    print("\n📝 Testing quote generation...")
    try:
        data = {'user_input': 'feeling anxious about testing'}
        response = requests.post(f"{BASE_URL}/shift", data=data)
        if response.status_code == 200:
            print("✅ Quote generation successful")
            # Extract quote ID from HTML
            import re
            html = response.text
            match = re.search(r'data-quote-id="([^"]+)"', html)
            if match:
                quote_id = match.group(1)
                print(f"✅ Found quote ID: {quote_id}")
            else:
                print("❌ Could not extract quote ID")
                return False
        else:
            print(f"❌ Quote generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Quote generation failed: {e}")
        return False
    
    # Test share page
    print(f"\n🔗 Testing share page: /share/{quote_id}")
    try:
        response = requests.get(f"{BASE_URL}/share/{quote_id}")
        if response.status_code == 200:
            html = response.text
            og_title = 'property="og:title"' in html
            og_image = 'property="og:image"' in html
            twitter_card = 'name="twitter:card"' in html
            
            if og_title and og_image and twitter_card:
                print("✅ Share page with Open Graph tags working")
            else:
                print(f"⚠️  Share page missing tags - Title: {og_title}, Image: {og_image}, Twitter: {twitter_card}")
        else:
            print(f"❌ Share page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Share page failed: {e}")
    
    # Test image generation
    print(f"\n🖼️  Testing image generation: /image/{quote_id}")
    try:
        response = requests.get(f"{BASE_URL}/image/{quote_id}")
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if content_type == 'image/png':
                print(f"✅ Image generation working ({len(response.content)} bytes)")
            else:
                print(f"❌ Image generation returned wrong content type: {content_type}")
        else:
            print(f"❌ Image generation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
    
    # Test share tracking
    print(f"\n📊 Testing share tracking: /track-share/{quote_id}")
    platforms = ['x', 'linkedin', 'native', 'instagram']
    for platform in platforms:
        try:
            data = {'platform': platform}
            response = requests.post(f"{BASE_URL}/track-share/{quote_id}", json=data)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    print(f"✅ Share tracking working for {platform}")
                else:
                    print(f"❌ Share tracking failed for {platform}: {result}")
            else:
                print(f"❌ Share tracking failed for {platform}: {response.status_code}")
        except Exception as e:
            print(f"❌ Share tracking failed for {platform}: {e}")
    
    # Test share stats
    print(f"\n📈 Testing share stats: /share-stats")
    try:
        response = requests.get(f"{BASE_URL}/share-stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Share stats working: {data}")
        else:
            print(f"❌ Share stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Share stats failed: {e}")
    
    print("\n🎉 Integration test completed!")
    return True

def test_open_graph_validation():
    """Test Open Graph tags with external validators"""
    print("\n🔍 Open Graph Validation URLs:")
    print("Test these URLs manually:")
    print(f"Facebook Debugger: https://developers.facebook.com/tools/debug/?q={BASE_URL}/share/")
    print(f"Twitter Card Validator: https://cards-dev.twitter.com/validator")
    print(f"LinkedIn Inspector: https://www.linkedin.com/post-inspector/")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Allow specifying different URL
        BASE_URL = sys.argv[1].rstrip('/')
    
    test_deployed_sharing()
    test_open_graph_validation()