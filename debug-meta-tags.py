#!/usr/bin/env python3
import requests
import re

response = requests.get('https://theperspectiveshift.vercel.app/share/48_0')
html = response.text

print('=== CHECKING FOR IMAGE META TAGS ===')
print()

# Look for og:image
if 'og:image' in html:
    print('✅ og:image mentioned in HTML')
    pattern = r'property=["\']og:image["\'][^>]*content=["\']([^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        print(f'og:image content: "{match.group(1)}"')
        if match.group(1):
            print('✅ og:image has content')
        else:
            print('❌ og:image is empty')
    else:
        print('❌ og:image tag malformed or content not found')
else:
    print('❌ og:image NOT found in HTML')

print()

# Look for twitter:image  
if 'twitter:image' in html:
    print('✅ twitter:image mentioned in HTML')
    pattern = r'name=["\']twitter:image["\'][^>]*content=["\']([^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        print(f'twitter:image content: "{match.group(1)}"')
        if match.group(1):
            print('✅ twitter:image has content')
        else:
            print('❌ twitter:image is empty')
    else:
        print('❌ twitter:image tag malformed or content not found')
else:
    print('❌ twitter:image NOT found in HTML')

print()

# Look for the image URL variable
image_pattern = r'image_url["\']?\s*=\s*["\']([^"\']*)["\']'
image_match = re.search(image_pattern, html, re.IGNORECASE)
if image_match:
    print(f'Found image_url variable: "{image_match.group(1)}"')

# Show a snippet of the head section
head_start = html.find('<head>')
head_end = html.find('</head>')
if head_start != -1 and head_end != -1:
    head_section = html[head_start:head_end + 7]
    og_lines = [line.strip() for line in head_section.split('\n') if 'og:' in line]
    twitter_lines = [line.strip() for line in head_section.split('\n') if 'twitter:' in line]
    
    print('=== OPEN GRAPH TAGS ===')
    for line in og_lines:
        print(line)
    
    print('\n=== TWITTER TAGS ===')
    for line in twitter_lines:
        print(line)