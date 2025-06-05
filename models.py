from api.index import db
from datetime import datetime
import hashlib

class QuoteCache(db.Model):
    __tablename__ = 'quote_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    input_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_input = db.Column(db.Text, nullable=False)  # Store original input
    response_data = db.Column(db.Text, nullable=False)  # JSON string of quotes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def get_hash(user_input):
        """Create a hash of the user input for caching"""
        return hashlib.sha256(user_input.strip().lower().encode()).hexdigest()

class DailyStats(db.Model):
    __tablename__ = 'daily_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow().date, unique=True)
    total_shifts = db.Column(db.Integer, default=0)