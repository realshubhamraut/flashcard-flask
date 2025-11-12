#!/usr/bin/env python3
"""
Migration script to fix foreign key constraints.
This adds CASCADE DELETE to the study_sessions.deck_id foreign key.

Run this ONCE on the production database to fix the constraint.
"""

import os
from app import app, db

def fix_foreign_keys():
    """Fix foreign key constraints in the database"""
    with app.app_context():
        try:
            # For PostgreSQL, we need to drop and recreate the constraint
            # This is safe because we're adding CASCADE, not removing it
            
            print("Fixing foreign key constraints...")
            
            # Drop the old constraint
            db.session.execute("""
                ALTER TABLE study_sessions 
                DROP CONSTRAINT IF EXISTS study_sessions_deck_id_fkey;
            """)
            
            # Add the new constraint with CASCADE
            db.session.execute("""
                ALTER TABLE study_sessions 
                ADD CONSTRAINT study_sessions_deck_id_fkey 
                FOREIGN KEY (deck_id) 
                REFERENCES decks(id) 
                ON DELETE CASCADE;
            """)
            
            db.session.commit()
            print("✅ Foreign key constraints fixed successfully!")
            print("   - study_sessions.deck_id now has ON DELETE CASCADE")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing constraints: {e}")
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("Foreign Key Migration Script")
    print("=" * 60)
    
    # Confirm before running
    confirm = input("\n⚠️  This will modify the database schema. Continue? (yes/no): ")
    
    if confirm.lower() == 'yes':
        fix_foreign_keys()
    else:
        print("Migration cancelled.")
