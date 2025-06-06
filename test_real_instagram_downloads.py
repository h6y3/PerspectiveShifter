#!/usr/bin/env python3
"""Test what Instagram downloads would actually get from main page vs share page"""

import requests
import re

base_url = 'https://theperspectiveshift.vercel.app'
quote_id = '51_0'

print('📱 REAL INSTAGRAM DOWNLOAD TEST')
print('=' * 40)

# Test 1: What does main page Instagram download?
print('\n1️⃣  Main page Instagram download...')
# Based on main.js line 615: imageUrl: `/image/${quoteId}?design=3`
main_page_url = f'{base_url}/image/{quote_id}?design=3'
print(f'   Main page downloads from: {main_page_url}')

response = requests.head(main_page_url)
main_size = response.headers.get('content-length', 'unknown')
print(f'   Size: {main_size} bytes | Status: {response.status_code}')

# Test 2: What does share page Instagram download?
print('\n2️⃣  Share page Instagram download...')
# Get the actual image_url from share page
share_response = requests.get(f'{base_url}/share/{quote_id}')
share_html = share_response.text

# Extract the JavaScript imageUrl value
js_match = re.search(r'imageUrl: "([^"]*)"', share_html)
if js_match:
    share_page_url = js_match.group(1)
    # Convert relative to absolute URL
    if share_page_url.startswith('/'):
        share_page_url = base_url + share_page_url
    
    print(f'   Share page downloads from: {share_page_url}')
    
    response = requests.head(share_page_url)
    share_size = response.headers.get('content-length', 'unknown')
    print(f'   Size: {share_size} bytes | Status: {response.status_code}')
else:
    print('   ❌ Could not extract imageUrl from share page')
    share_size = 'unknown'

# Test 3: Comparison
print('\n3️⃣  Instagram Download Consistency...')
if main_size == share_size and main_size != 'unknown':
    print(f'   ✅ CONSISTENT: Both download {main_size} byte images')
    print('   Instagram users will get identical images from main page and share page')
else:
    print(f'   ❌ INCONSISTENT: Main={main_size}, Share={share_size}')
    print('   Instagram users will get different images depending on where they download')

# Test 4: View vs Download consistency (within share page)
print('\n4️⃣  Share page view vs download consistency...')
view_match = re.search(r'<img src="([^"]*)" alt="Quote by', share_html)
if view_match:
    view_url = view_match.group(1)
    if view_url.startswith('/'):
        view_url = base_url + view_url
    
    view_response = requests.head(view_url)
    view_size = view_response.headers.get('content-length', 'unknown')
    
    print(f'   Share page view image: {view_size} bytes')
    print(f'   Share page download: {share_size} bytes')
    
    if view_size == share_size:
        print('   ✅ CONSISTENT: View and download match on share page')
    else:
        print('   ❌ INCONSISTENT: View and download differ on share page')
else:
    print('   ❌ Could not extract view image URL')