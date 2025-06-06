import os
import sys
import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.INFO)

# Add root directory to Python path for imports
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Environment validation - fail fast if critical env vars missing
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY or OPENAI_API_KEY == "default_key":
    logging.warning("OPENAI_API_KEY not configured - using fallback quotes only")

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app with correct paths for Vercel
app = Flask(__name__, 
           instance_relative_config=False,
           template_folder='../templates',
           static_folder='../static')
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    # Neon requires postgresql:// instead of postgres://
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///perspective_shift.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 1,        # Vercel functions are single-threaded
    "max_overflow": 0,     # No overflow for serverless
    "connect_args": {
        "sslmode": "require" if database_url else {},
        "connect_timeout": 10,
    } if database_url else {}
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Models and routes will be imported at the end of this file

def init_db():
    """Initialize database tables if they don't exist"""
    try:
        with app.app_context():
            # Check if tables exist by trying to query one
            db.session.execute(text("SELECT 1 FROM quote_cache LIMIT 1"))
            app.logger.info("Database tables already exist")
    except Exception:
        # Tables don't exist, create them
        try:
            with app.app_context():
                db.create_all()
                app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Failed to create database tables: {e}")

# Initialize database on first import
init_db()


# Import models and routes after app setup
import models  # noqa: F401
import routes  # noqa: F401

# Register template helpers for consistent URL generation
from utils import register_template_helpers
register_template_helpers(app)

# Export the app for Vercel
# Vercel will automatically detect this as the WSGI application
if __name__ == "__main__":
    app.run()
