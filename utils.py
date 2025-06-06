"""
Utility functions for PerspectiveShifter application
"""

from flask import url_for


def get_quote_image_url(quote_id, design=3, external=False):
    """
    Generate a consistent quote image URL with proper design parameter.
    
    Args:
        quote_id (str): The quote ID in format "cache_id_quote_index"
        design (int): Design template number (default: 3 for social media)
        external (bool): Whether to generate absolute URL (default: False)
    
    Returns:
        str: Properly formatted image URL
    """
    return url_for('quote_image', quote_id=quote_id, design=design, _external=external)


def get_share_url(quote_id, external=False):
    """
    Generate a consistent share page URL.
    
    Args:
        quote_id (str): The quote ID in format "cache_id_quote_index" 
        external (bool): Whether to generate absolute URL (default: False)
    
    Returns:
        str: Properly formatted share URL
    """
    return url_for('share_quote', quote_id=quote_id, _external=external)


def get_social_media_image_url(quote_id):
    """
    Get the standardized image URL for social media sharing.
    Always uses design=3 and external=True for Open Graph compatibility.
    
    Args:
        quote_id (str): The quote ID in format "cache_id_quote_index"
    
    Returns:
        str: Absolute image URL optimized for social media
    """
    return get_quote_image_url(quote_id, design=3, external=True)


# Template context processor to make functions available in templates
def register_template_helpers(app):
    """
    Register utility functions as template context processors.
    Call this during app initialization.
    """
    @app.context_processor
    def inject_url_helpers():
        return {
            'get_quote_image_url': get_quote_image_url,
            'get_share_url': get_share_url,
            'get_social_media_image_url': get_social_media_image_url
        }


# JavaScript URL patterns for frontend consistency
JS_URL_PATTERNS = {
    'image_url': '/image/{quote_id}?design={design}',
    'share_url': '/share/{quote_id}',
    'track_url': '/track-share/{quote_id}'
}


def get_js_url_pattern(pattern_name):
    """
    Get JavaScript URL pattern for consistent frontend URL construction.
    
    Args:
        pattern_name (str): One of 'image_url', 'share_url', 'track_url'
    
    Returns:
        str: JavaScript template string pattern
    """
    return JS_URL_PATTERNS.get(pattern_name, '')