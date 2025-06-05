import io
import textwrap
import os
from PIL import Image, ImageDraw, ImageFont
import logging
from flask import Response



def create_share_image_route(quote_text, attribution, perspective_text, design=3):
    """
    Generate image and return as Flask Response for Vercel
    Supports multiple designs via the 'design' parameter
    """
    try:
        # Generate the image
        image_bytes = create_share_image_buffer(quote_text, attribution, perspective_text, design=design)
        
        # Return as Flask Response with proper headers
        return Response(
            image_bytes,
            mimetype='image/png',
            headers={
                'Content-Type': 'image/png',
                'Cache-Control': 'public, max-age=31536000, immutable',
                'Content-Disposition': 'inline; filename="quote.png"'
            }
        )
    except Exception as e:
        logging.error(f"Error generating image: {str(e)}")
        # Return a 1x1 transparent PNG as fallback
        fallback_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\xdab\x00\x00\x00\x02\x00\x01\xe5\'\xde\xfc\x00\x00\x00\x00IEND\xaeB`\x82'
        return Response(fallback_png, mimetype='image/png')

def get_font_or_default(size=40, bold=False):
    """
    Get font with multiple fallback strategies
    CRITICAL: For Vercel, fonts must be included in the deployment
    """
    
    font_name = 'SpaceMono-Bold.ttf' if bold else 'SpaceMono-Regular.ttf'
    
    # Strategy 1: Use fonts from static directory (most reliable for Vercel)
    font_paths = [
        f'/var/task/static/fonts/{font_name}',  # Vercel deployment path
        f'static/fonts/{font_name}',            # Relative path
        os.path.join(os.getcwd(), 'static', 'fonts', font_name),  # CWD path
        os.path.join(os.path.dirname(__file__), 'static', 'fonts', font_name),  # Script dir
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'fonts', font_name),  # Parent dir
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                logging.info(f"Loading font from: {font_path}")
                return ImageFont.truetype(font_path, size)
            except Exception as e:
                logging.warning(f"Failed to load font from {font_path}: {e}")
                continue
    
    # Strategy 2: Use system fonts (these should work on Vercel)
    system_fonts = [
        '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/Monaco.ttf',     # macOS monospace
        '/System/Library/Fonts/Helvetica.ttc',  # macOS
        'C:\\Windows\\Fonts\\Consolas.ttf',     # Windows monospace
        'C:\\Windows\\Fonts\\Arial.ttf',        # Windows
    ]
    
    for font_path in system_fonts:
        if os.path.exists(font_path):
            try:
                logging.info(f"Loading system font from: {font_path}")
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    
    # Strategy 3: Use PIL's default font (always works but small)
    logging.warning(f"Using default font for size {size}")
    try:
        # Try to get a larger default font
        return ImageFont.load_default().font_variant(size=size)
    except:
        return ImageFont.load_default()

def get_text_size(draw, text, font):
    """
    Get text size with PIL version compatibility
    """
    try:
        # Modern PIL (Pillow 8.0.0+)
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        # Legacy PIL
        return draw.textsize(text, font=font)

def create_share_image_buffer(quote_text, attribution, perspective_text, design=3):
    """
    Generate a clean, modern quote image optimized for social sharing
    Supports multiple designs via the 'design' parameter
    """
    # Design 3: Enhanced Split Layout (Default)
    if design == 3:
        width = 1080
        height = 1080
        bg_color = (255, 255, 255)  # White
        black = (0, 0, 0)
        orange = (255, 87, 34)  # #FF5722
        light_gray = (248, 248, 248)  # Very light gray
        bar_height = 240
        padding = 60
        
        # Create image
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Fonts - larger and more impactful
        quote_font = get_font_or_default(52)
        author_font = get_font_or_default(32)
        brand_font = get_font_or_default(24)
        
        # Add subtle background texture to top area
        draw.rectangle([0, 0, width, height - bar_height], fill=light_gray)
        
        # Draw main black bar at bottom
        draw.rectangle([0, height - bar_height, width, height], fill=black)
        
        # Add orange accent stripe at the top of black bar
        accent_height = 6
        draw.rectangle([0, height - bar_height, width, height - bar_height + accent_height], fill=orange)
        
        # Intelligent quote text wrapping for optimal readability
        lines = []
        for line in quote_text.split('\n'):
            lines.extend(textwrap.wrap(line, width=30))  # Optimal line length for readability
        
        # Perfect line spacing for visual harmony
        line_height = get_text_size(draw, 'A', quote_font)[1] + 20
        quote_block_height = len(lines) * line_height
        quote_y = ((height - bar_height) - quote_block_height) // 2 + 50  # Perfectly centered
        
        # Draw large opening quote mark - perfectly positioned
        quote_mark_font = get_font_or_default(140)
        quote_mark_y = quote_y - 50
        quote_mark_x = padding - 10
        draw.text((quote_mark_x, quote_mark_y), '"', font=quote_mark_font, fill=orange)
        
        # Draw quote lines (centered, with better spacing)
        for line in lines:
            w, h = get_text_size(draw, line, quote_font)
            x = (width - w) // 2
            draw.text((x, quote_y), line, font=quote_font, fill=black)
            quote_y += line_height
        
        # Author section - perfectly balanced layout
        author_text = f"{attribution}"
        author_y = height - bar_height + 45
        draw.text((padding, author_y), author_text, font=author_font, fill=orange)
        
        # Website URL - elegant positioning
        website_font = get_font_or_default(18)
        website_text = "theperspectiveshift.com"
        website_y = author_y + 50
        draw.text((padding, website_y), website_text, font=website_font, fill=orange)
        
        # Brand section - right aligned with perfect spacing
        brand_text = "THE PERSPECTIVE SHIFT"
        brand_w, _ = get_text_size(draw, brand_text, brand_font)
        brand_x = width - padding - brand_w
        brand_y = author_y + 15
        draw.text((brand_x, brand_y), brand_text, font=brand_font, fill=(255, 255, 255))
        
        # Elegant vertical separator - perfectly positioned
        separator_x = brand_x - 35
        separator_top = author_y + 8
        separator_bottom = author_y + 45
        draw.rectangle([separator_x, separator_top, separator_x + 3, separator_bottom], fill=orange)
        

        
        # Output
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        return buffer.getvalue()
    
    # Legacy design (design=1 or anything else)
    width = 1200
    height = 630
    
    # Colors
    bg_color = (255, 255, 255)      # White background
    text_color = (0, 0, 0)          # Black text
    accent_color = (100, 100, 100)  # Gray for attribution
    
    # Create image
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Load fonts with fallbacks
    quote_font = get_font_or_default(48)
    attribution_font = get_font_or_default(32)
    brand_font = get_font_or_default(24)
    
    # Add padding
    padding = 60
    
    # Draw brand name at top
    brand_text = "The Perspective Shift"
    brand_width, _ = get_text_size(draw, brand_text, brand_font)
    brand_x = (width - brand_width) // 2
    draw.text((brand_x, padding), brand_text, fill=accent_color, font=brand_font)
    
    # Calculate vertical center for quote
    quote_start_y = height // 3
    
    # Wrap and draw quote text
    wrapped_quote = textwrap.fill(f'"{quote_text}"', width=40)
    lines = wrapped_quote.split('\n')
    
    current_y = quote_start_y
    for line in lines:
        line_width, _ = get_text_size(draw, line, quote_font)
        line_x = (width - line_width) // 2
        draw.text((line_x, current_y), line, fill=text_color, font=quote_font)
        current_y += 60
    
    # Draw attribution
    attribution_text = f"— {attribution}"
    current_y += 30
    attr_width, _ = get_text_size(draw, attribution_text, attribution_font)
    attr_x = (width - attr_width) // 2
    draw.text((attr_x, current_y), attribution_text, fill=accent_color, font=attribution_font)
    
    # Add footer
    footer_y = height - padding - 30
    footer_text = "theperspectiveshift.com"
    footer_width, _ = get_text_size(draw, footer_text, brand_font)
    footer_x = (width - footer_width) // 2
    draw.text((footer_x, footer_y), footer_text, fill=accent_color, font=brand_font)
    
    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    
    return buffer.getvalue()

# Legacy compatibility functions (keep for any existing imports)
def create_share_image(quote_text, attribution, perspective_text):
    """Legacy function - redirects to buffer version"""
    return create_share_image_buffer(quote_text, attribution, perspective_text)
