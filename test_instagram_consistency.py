#!/usr/bin/env python3
"""Test Instagram image consistency across main page and share page"""

import requests

base_url = 'https://theperspectiveshift.vercel.app'
quote_id = '51_0'

print('🖼️  INSTAGRAM IMAGE CONSISTENCY TEST')
print('=' * 50)

# URLs to test
test_urls = {
    'Default image': f'{base_url}/image/{quote_id}',
    'Design=3 image': f'{base_url}/image/{quote_id}?design=3',
    'Share page og:image': None,  # We'll extract this
    'Share page display image': None  # We'll extract this
}

# Get share page to extract actual image URLs
print('\n1️⃣  Extracting image URLs from share page...')
share_response = requests.get(f'{base_url}/share/{quote_id}')
share_html = share_response.text

# Extract og:image URL
import re
og_image_match = re.search(r'property="og:image"[^>]*content="([^"]*)"', share_html)
if og_image_match:
    test_urls['Share page og:image'] = og_image_match.group(1)
    print(f'   og:image: {og_image_match.group(1)}')

# Extract display image URL  
display_image_match = re.search(r'<img src="([^"]*)" alt="Quote by', share_html)
if display_image_match:
    test_urls['Share page display image'] = display_image_match.group(1)
    print(f'   Display image: {display_image_match.group(1)}')

# Test all image URLs
print('\n2️⃣  Testing image sizes...')
for name, url in test_urls.items():
    if url:
        try:
            response = requests.head(url)
            size = response.headers.get('content-length', 'unknown')
            status = response.status_code
            print(f'   {name:25} | {status} | {size:>8} bytes | {url}')
        except Exception as e:
            print(f'   {name:25} | ERROR | {str(e)}')
    else:
        print(f'   {name:25} | MISSING |')

print('\n3️⃣  Analysis...')
print('   Expected: All Instagram-related images should use design=3')
print('   Expected: og:image, display image, and downloads should match')

# Check if there are different sizes
sizes = []
for name, url in test_urls.items():
    if url and 'design=3' in url:
        try:
            response = requests.head(url)
            size = response.headers.get('content-length')
            if size:
                sizes.append(int(size))
        except:
            pass

if len(set(sizes)) == 1:
    print('   ✅ All design=3 images have consistent size')
else:
    print(f'   ⚠️  Size inconsistency detected: {set(sizes)}')

print('\n4️⃣  Instagram Download Test...')
print('   Main page Instagram should download from: /image/{quote_id}?design=3')
print('   Share page Instagram should download from: image_url (with design=3)')
print('   Both should result in same file size for consistency')