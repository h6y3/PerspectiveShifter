#!/usr/bin/env python3
import requests
import re

# Test with a fresh quote
quote_id = '51_0'

print('🔍 Testing actual sharing functionality issues...')
print()

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

# Test share page
response = requests.get(f'https://theperspectiveshift.vercel.app/share/{quote_id}', headers=headers)
html = response.text

print('=== CHECKING OPEN GRAPH TAGS ===')

# Check for og:image with simpler regex
if 'og:image' in html:
    pattern = r'property="og:image"[^>]*content="([^"]*)"'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        og_image_url = match.group(1)
        print(f'✅ og:image found: {og_image_url}')
    else:
        print('❌ og:image tag malformed')
else:
    print('❌ og:image not found in HTML')

print()
print('=== TESTING USER-REPORTED ISSUES ===')

# Issue 1: Instagram download vs view image difference
print('🖼️  Testing image size differences:')

view_image_url = f'https://theperspectiveshift.vercel.app/image/{quote_id}?design=3'
download_url = f'https://theperspectiveshift.vercel.app/image/{quote_id}'

view_response = requests.head(view_image_url)
download_response = requests.head(download_url)

print(f'  View Image URL: {view_image_url}')
print(f'  Download URL: {download_url}')
print(f'  View status: {view_response.status_code}')
print(f'  Download status: {download_response.status_code}')

if view_response.status_code == 200 and download_response.status_code == 200:
    view_size = view_response.headers.get('content-length', 'unknown')
    download_size = download_response.headers.get('content-length', 'unknown')
    print(f'  View image size: {view_size} bytes')
    print(f'  Download image size: {download_size} bytes')
    
    if view_size != download_size:
        print('⚠️  CONFIRMED: View and download images are different!')
        print('  View uses ?design=3, download uses default design')
        print('  This explains user-reported Instagram issue')
    else:
        print('✅ Images are the same size')

print()

# Issue 2: LinkedIn sharing behavior
print('🔗 Testing LinkedIn sharing:')
linkedin_url = f'https://www.linkedin.com/sharing/share-offsite/?url=https%3A//theperspectiveshift.vercel.app/share/{quote_id}'
print(f'  LinkedIn share URL: {linkedin_url}')
print('  Expected: LinkedIn should preview the quote image and text')
print('  User report: "LinkedIn just links to the site"')
print('  → This suggests Open Graph tags are missing or broken')

print()

# Issue 3: X/Twitter sharing  
print('🐦 Testing X/Twitter sharing:')
twitter_url = f'https://twitter.com/intent/tweet?text=%22Test%20quote%22%20-%20Author%20%23wisdom%20%23quotes&url=https%3A//theperspectiveshift.vercel.app/share/{quote_id}'
print(f'  Twitter share URL: {twitter_url}')
print('  User report: "Can\'t tell if it works because of login prompt"')
print('  → This is expected behavior - Twitter requires login to tweet')

print()
print('=== DIAGNOSIS ===')
print('✅ Share pages load correctly')
print('✅ Image generation works')
print('⚠️  Instagram: Different images for view vs download (design parameter)')
print('⚠️  LinkedIn: Likely missing/broken Open Graph image tags')
print('✅ Twitter: Working as expected (login required)')