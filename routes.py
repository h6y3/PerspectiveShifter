import json
import random
import time
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, send_file, Response
from api.index import app, db
from models import QuoteCache, DailyStats, ShareStats
from openai_service import get_wisdom_quotes
from utils import get_social_media_image_url, get_share_url
import logging
import os
import hashlib

# Prompts that rotate
PROMPTS = [
    "How are you feeling right now?",
    "What's on your mind?", 
    "Describe this moment",
    "What's on your mind?",
    "What's on your mind?"
]

def update_daily_stats():
    """Update daily analytics anonymously"""
    today = datetime.utcnow().date()
    stats = DailyStats.query.filter_by(date=today).first()
    
    if not stats:
        stats = DailyStats(date=today, total_shifts=1)
        db.session.add(stats)
    else:
        stats.total_shifts += 1
    
    db.session.commit()

@app.route('/')
def index():
    """Main page - completely stateless and anonymous"""
    # Get a random prompt
    current_prompt = random.choice(PROMPTS)
    
    # Get today's shift count for display
    today = datetime.utcnow().date()
    stats = DailyStats.query.filter_by(date=today).first()
    daily_shifts = stats.total_shifts if stats else 0
    
    # Get sharing stats for display
    try:
        total_shares = ShareStats.get_total_shares()
        platform_breakdown = ShareStats.get_platform_breakdown()
        platform_stats = dict(platform_breakdown)
    except:
        total_shares = 0
        platform_stats = {}
    
    return render_template('index.html', 
                         prompt=current_prompt,
                         daily_shifts=daily_shifts,
                         total_shares=total_shares,
                         platform_stats=platform_stats,
                         show_results=False)

@app.route('/shift', methods=['POST'])
def shift_perspective():
    """Process user input and get wisdom quotes - completely stateless"""
    start_time = time.time()
    user_input = request.form.get('user_input', '').strip()
    if not user_input:
        flash('Please enter how you\'re feeling or what\'s on your mind.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Generate a hash for the user input
        input_hash = hashlib.sha256(user_input.encode()).hexdigest()
        
        # Check if quotes for this input already exist
        existing_cache = QuoteCache.query.filter_by(input_hash=input_hash).first()
        
        if existing_cache:
            # Use existing quotes
            quotes_data = json.loads(existing_cache.response_data)
            # Add the cache ID to each quote for sharing
            for i, quote in enumerate(quotes_data):
                quote['id'] = f"{existing_cache.id}_{i}"
        else:
            # Get fresh quotes from OpenAI
            logging.info(f"Processing user input: '{user_input}'")
            quotes_data = get_wisdom_quotes(user_input)
            logging.info(f"Received {len(quotes_data)} quotes from OpenAI service")
            
            # Store all quotes as a single JSON array in one database row
            quote_cache = QuoteCache(
                input_hash=input_hash,
                user_input=user_input,
                response_data=json.dumps(quotes_data)
            )
            db.session.add(quote_cache)
            db.session.commit()
            
            # Add IDs to quotes for sharing (cache_id + quote_index)
            for i, quote in enumerate(quotes_data):
                quote['id'] = f"{quote_cache.id}_{i}"
        
        # Update anonymous daily stats
        update_daily_stats()
        
        # Get updated daily count
        today = datetime.utcnow().date()
        stats = DailyStats.query.filter_by(date=today).first()
        daily_shifts = stats.total_shifts if stats else 0
        
        # Get sharing stats for display
        try:
            total_shares = ShareStats.get_total_shares()
            platform_breakdown = ShareStats.get_platform_breakdown()
            platform_stats = dict(platform_breakdown)
        except:
            total_shares = 0
            platform_stats = {}
        
        total_duration = time.time() - start_time
        logging.info(f"Total /shift route duration: {total_duration:.2f}s")
        
        return render_template('index.html',
                             prompt=random.choice(PROMPTS),
                             user_input=user_input,
                             quotes=quotes_data,
                             daily_shifts=daily_shifts,
                             total_shares=total_shares,
                             platform_stats=platform_stats,
                             show_results=True)
    except Exception as e:
        total_duration = time.time() - start_time
        logging.error(f"Error processing shift after {total_duration:.2f}s: {str(e)}")
        flash('An error occurred while processing your request.', 'error')
        return redirect(url_for('index'))

@app.route('/new_perspective')
def new_perspective():
    """Start fresh with a new perspective"""
    return redirect(url_for('index'))

@app.route('/privacy')
def privacy():
    """Privacy and data storage information"""
    today = datetime.utcnow().date()
    stats = DailyStats.query.filter_by(date=today).first()
    daily_shifts = stats.total_shifts if stats else 0
    
    return render_template('privacy.html', 
                         daily_shifts=daily_shifts)

@app.route('/share/<quote_id>')
def share_quote(quote_id):
    """Shareable page with Open Graph meta tags for social media"""
    try:
        # Parse the quote_id format: cache_id_quote_index
        if '_' not in quote_id:
            flash('Invalid quote ID format', 'error')
            return redirect(url_for('index'))
        
        cache_id, quote_index = quote_id.split('_', 1)
        quote_index = int(quote_index)
        
        # Get quote cache from database
        quote_cache = QuoteCache.query.get(cache_id)
        if not quote_cache:
            flash('Quote not found', 'error')
            return redirect(url_for('index'))
        
        # Parse the stored quotes data (JSON array)
        quotes_data = json.loads(quote_cache.response_data)
        
        # Get the specific quote by index
        if quote_index >= len(quotes_data):
            flash('Quote index out of range', 'error')
            return redirect(url_for('index'))
        
        quote_data = quotes_data[quote_index]
        
        # Create sharing data using centralized helpers
        share_url = request.url
        image_url = get_social_media_image_url(quote_id)
        
        return render_template('share.html', 
                             quote=quote_data,
                             quote_id=quote_id,
                             share_url=share_url,
                             image_url=image_url,
                             quote_cache=quote_cache)
                             
    except Exception as e:
        logging.error(f"Error in share_quote: {str(e)}")
        flash('Quote not found', 'error')
        return redirect(url_for('index'))

@app.route('/image/<quote_id>')
def quote_image(quote_id):
    """Generate and return quote image"""
    try:
        # Parse the quote_id format: cache_id_quote_index
        if '_' not in quote_id:
            flash('Invalid quote ID format', 'error')
            return redirect(url_for('index'))
        cache_id, quote_index = quote_id.split('_', 1)
        quote_index = int(quote_index)
        # Get quote cache from database
        quote_cache = QuoteCache.query.get(cache_id)
        if not quote_cache:
            flash('Quote not found', 'error')
            return redirect(url_for('index'))
        # Parse the stored quotes data (JSON array)
        quotes_data = json.loads(quote_cache.response_data)
        # Get the specific quote by index
        if quote_index >= len(quotes_data):
            flash('Quote index out of range', 'error')
            return redirect(url_for('index'))
        quote_data = quotes_data[quote_index]
        # Get design parameter from query string
        design = 1
        try:
            design = int(request.args.get('design', 1))
        except Exception:
            design = 1
        # Generate and return image directly using Python
        from image_generator import create_share_image_route
        return create_share_image_route(
            quote_text=quote_data['quote'],
            attribution=quote_data['attribution'],
            perspective_text=quote_data['perspective'],
            design=design
        )
    except Exception as e:
        logging.error(f"Error in quote_image: {str(e)}")
        # Fallback to text if anything fails
        return redirect(url_for('share_text', quote_id=quote_id))

@app.route('/share_text/<quote_id>')
def share_text(quote_id):
    """Text-only fallback for when image generation fails"""
    try:
        # Parse the quote_id format: cache_id_quote_index
        if '_' not in quote_id:
            flash('Invalid quote ID format', 'error')
            return redirect(url_for('index'))
        
        cache_id, quote_index = quote_id.split('_', 1)
        quote_index = int(quote_index)
        
        # Get quote cache from database
        quote_cache = QuoteCache.query.get(cache_id)
        if not quote_cache:
            flash('Quote not found', 'error')
            return redirect(url_for('index'))
        
        # Parse the stored quotes data (JSON array)
        quotes_data = json.loads(quote_cache.response_data)
        
        # Get the specific quote by index
        if quote_index >= len(quotes_data):
            flash('Quote index out of range', 'error')
            return redirect(url_for('index'))
        
        quote_data = quotes_data[quote_index]
        
        # Return formatted text
        formatted_text = f'''"{quote_data['quote']}"
— {quote_data['attribution']}

{quote_data['perspective']}

{quote_data.get('context', '')}

Shared from The Perspective Shift
theperspectiveshift.vercel.app
'''
        
        return Response(
            formatted_text,
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename=perspective_shift_{quote_id}.txt'
            }
        )
    except Exception as e:
        logging.error(f"Error in text share: {str(e)}")
        flash('Error sharing quote', 'error')
        return redirect(url_for('index'))






@app.route('/track-share/<quote_id>', methods=['POST'])
def track_share(quote_id):
    """Track sharing attempts anonymously"""
    try:
        # Parse the quote_id format: cache_id_quote_index
        if '_' not in quote_id:
            return {'status': 'error', 'message': 'Invalid quote ID format'}, 400
        
        cache_id, quote_index = quote_id.split('_', 1)
        platform = request.json.get('platform') if request.json else None
        
        if platform in ['x', 'linkedin', 'native', 'instagram']:
            share = ShareStats(quote_id=int(cache_id), platform=platform)
            db.session.add(share)
            db.session.commit()
            return {'status': 'success'}
        else:
            return {'status': 'error', 'message': 'Invalid platform'}, 400
    except Exception as e:
        logging.error(f"Error tracking share: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/share-stats')
def get_share_stats():
    """Get sharing statistics for display"""
    try:
        total_shares = ShareStats.get_total_shares()
        platform_breakdown = ShareStats.get_platform_breakdown()
        
        return {
            'total': total_shares,
            'platforms': dict(platform_breakdown)
        }
    except Exception as e:
        logging.error(f"Error getting share stats: {str(e)}")
        return {'total': 0, 'platforms': {}}

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring deployment status"""
    try:
        from sqlalchemy import text
        db.session.execute(text("SELECT 1"))
        from api.index import OPENAI_API_KEY
        return {
            "status": "healthy", 
            "database": "connected",
            "openai": "configured" if OPENAI_API_KEY else "fallback_mode",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('index.html', 
                         error="Page not found",
                         prompt=random.choice(PROMPTS)), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"500 error: {str(error)}")
    return render_template('index.html',
                         error="Something went wrong. Please try again.",
                         prompt=random.choice(PROMPTS)), 500