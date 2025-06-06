#!/usr/bin/env python3
"""
Production database migration script
PERMANENT SCRIPT - Should be committed to repo

This script runs migrations against the production database using
the same DATABASE_URL environment variable as the production app.

Usage:
    # Set environment variables first
    export DATABASE_URL="postgresql://..."
    python scripts/migrate_production.py
    
    # Or use Vercel's environment
    vercel env pull .env.local
    source .env.local  # Load environment variables
    python scripts/migrate_production.py

Safety Features:
- Requires explicit confirmation for production migrations
- Validates database connection before making changes
- Logs all operations for audit trail
"""

import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_info():
    """Get database connection info"""
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        logger.info("To migrate production database:")
        logger.info("1. Run: vercel env pull .env.local")
        logger.info("2. Run: source .env.local")
        logger.info("3. Run: python scripts/migrate_production.py")
        return None
    
    if database_url.startswith("sqlite"):
        logger.warning("⚠️  Using SQLite database (likely local development)")
        return "local"
    elif "postgres" in database_url:
        logger.info("🐘 Using PostgreSQL database (likely production)")
        return "production"
    else:
        logger.warning(f"⚠️  Unknown database type: {database_url[:50]}...")
        return "unknown"

def confirm_production_migration():
    """Get user confirmation for production migration"""
    print("\n" + "="*60)
    print("🚨 PRODUCTION DATABASE MIGRATION")
    print("="*60)
    print("This will modify the production database schema.")
    print("Make sure you have:")
    print("✅ Backed up the database")
    print("✅ Tested the migration locally")
    print("✅ Coordinated with team members")
    print("="*60)
    
    response = input("Proceed with production migration? (type 'yes' to continue): ")
    return response.lower() == "yes"

def run_production_migration():
    """Run migration against production database"""
    # Import here to ensure environment is set up first
    from api.index import app, db
    from models import ShareStats
    
    with app.app_context():
        try:
            # Check current database state
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            logger.info(f"Found {len(existing_tables)} existing tables")
            
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
                return True
            except Exception as e:
                logger.error(f"❌ Model method error: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False

def main():
    logger.info("🔍 Checking database configuration...")
    
    db_type = get_database_info()
    if not db_type:
        sys.exit(1)
    
    if db_type == "production":
        if not confirm_production_migration():
            logger.info("Migration cancelled by user")
            sys.exit(0)
    
    logger.info("Starting database migration...")
    
    success = run_production_migration()
    
    if success:
        logger.info("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()