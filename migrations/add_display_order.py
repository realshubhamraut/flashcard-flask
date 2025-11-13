"""
Migration script to add display_order column to decks table
Run this script after deploying the updated models.py
"""
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Deck
from sqlalchemy import text

def run_migration():
    """Add display_order column to decks table"""
    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('decks')]
            
            if 'display_order' in columns:
                print("✓ Column 'display_order' already exists in decks table")
                return
            
            print("Adding display_order column to decks table...")
            
            # For PostgreSQL
            if 'postgresql' in str(db.engine.url):
                db.session.execute(text("""
                    ALTER TABLE decks 
                    ADD COLUMN display_order INTEGER DEFAULT 0
                """))
                db.session.commit()
                print("✓ Column added successfully (PostgreSQL)")
            
            # For SQLite
            else:
                db.session.execute(text("""
                    ALTER TABLE decks 
                    ADD COLUMN display_order INTEGER DEFAULT 0
                """))
                db.session.commit()
                print("✓ Column added successfully (SQLite)")
            
            print("\n✓ Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Migration failed: {str(e)}")
            return False
        
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRATION: Add display_order column to decks table")
    print("=" * 60)
    print()
    
    confirm = input("Run migration? (yes/no): ")
    if confirm.lower() == 'yes':
        success = run_migration()
        if not success:
            sys.exit(1)
    else:
        print("Migration cancelled")
