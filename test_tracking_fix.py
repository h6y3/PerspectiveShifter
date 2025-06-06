#!/usr/bin/env python3
"""Test that share tracking works correctly with valid platforms"""

import requests

base_url = 'https://theperspectiveshift.vercel.app'
quote_id = '51_0'

print('📊 SHARE TRACKING TEST')
print('=' * 30)

# Test each platform
platforms = ['x', 'linkedin', 'native', 'instagram']

for platform in platforms:
    print(f'\n🔹 Testing {platform} tracking...')
    
    response = requests.post(
        f'{base_url}/track-share/{quote_id}',
        json={'platform': platform},
        headers={'Content-Type': 'application/json'}
    )
    
    print(f'   Status: {response.status_code}')
    print(f'   Response: {response.json()}')
    
    if response.status_code == 200 and response.json().get('status') == 'success':
        print(f'   ✅ {platform} tracking works')
    else:
        print(f'   ❌ {platform} tracking failed')

# Test invalid platform
print(f'\n🔹 Testing invalid platform...')
response = requests.post(
    f'{base_url}/track-share/{quote_id}',
    json={'platform': 'invalid'},
    headers={'Content-Type': 'application/json'}
)

print(f'   Status: {response.status_code}')
print(f'   Response: {response.json()}')

if response.status_code == 400:
    print('   ✅ Invalid platform correctly rejected')
else:
    print('   ❌ Invalid platform should return 400')

print('\n📈 Getting share stats...')
stats_response = requests.get(f'{base_url}/share-stats')
print(f'   Status: {stats_response.status_code}')
print(f'   Stats: {stats_response.json()}')