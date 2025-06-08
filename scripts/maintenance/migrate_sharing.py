#!/usr/bin/env python3
"""
Database migration script for ShareStats model
PERMANENT SCRIPT - Should be committed to repo

This script creates the ShareStats table in the existing database.
Can be run safely multiple times (idempotent).

Usage:
    python scripts/migrate_sharing.py
    uv run python scripts/migrate_sharing.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.index import app, db
from models import ShareStats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_sharing_tables():
    """Create ShareStats table if it doesn't exist"""
    with app.app_context():
        try:
            # Check if ShareStats table exists
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'share_stats' not in existing_tables:
                logger.info("Creating ShareStats table...")
                db.create_all()
                logger.info("✅ ShareStats table created successfully")
            else:
                logger.info("ShareStats table already exists")
                
            # Verify the table structure
            if 'share_stats' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('share_stats')]
                expected_columns = ['id', 'quote_id', 'platform', 'shared_at']
                
                if all(col in columns for col in expected_columns):
                    logger.info("✅ ShareStats table structure verified")
                else:
                    logger.warning(f"⚠️  Table structure mismatch. Expected: {expected_columns}, Found: {columns}")
            
            # Test the model methods
            try:
                total_shares = ShareStats.get_total_shares()
                platform_breakdown = ShareStats.get_platform_breakdown()
                logger.info(f"✅ Model methods working. Total shares: {total_shares}")
            except Exception as e:
                logger.error(f"❌ Model method error: {e}")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    logger.info("Starting ShareStats migration...")
    migrate_sharing_tables()
    logger.info("Migration completed!")