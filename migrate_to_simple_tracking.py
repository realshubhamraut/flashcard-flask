#!/usr/bin/env python3
"""
Migration script to update database from spaced repetition to simple tracking.
Run this ONCE after updating models.py
"""

from app import app, db
from sqlalchemy import text

def migrate_database():
    """Migrate database schema to new tracking system"""
    with app.app_context():
        try:
            print("Starting database migration...")
            
            # Add new columns to cards table
            print("\n1. Adding 'difficulty' column to cards table...")
            try:
                db.session.execute(text("""
                    ALTER TABLE cards 
                    ADD COLUMN difficulty VARCHAR(20);
                """))
                db.session.commit()
                print("   ✅ Added difficulty column")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("   ℹ️  Column already exists, skipping")
                    db.session.rollback()
                else:
                    raise
            
            # Update card_progress table
            print("\n2. Updating card_progress table...")
            
            # Add new columns
            new_columns = [
                ("correct_count", "INTEGER DEFAULT 0"),
                ("incorrect_count", "INTEGER DEFAULT 0"),
                ("trippy_count", "INTEGER DEFAULT 0"),
                ("last_result", "VARCHAR(20)")
            ]
            
            for col_name, col_type in new_columns:
                try:
                    db.session.execute(text(f"""
                        ALTER TABLE card_progress 
                        ADD COLUMN {col_name} {col_type};
                    """))
                    db.session.commit()
                    print(f"   ✅ Added {col_name} column")
                except Exception as e:
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"   ℹ️  {col_name} already exists, skipping")
                        db.session.rollback()
                    else:
                        raise
            
            # Migrate existing data: convert states to last_result
            print("\n3. Migrating existing progress data...")
            try:
                db.session.execute(text("""
                    UPDATE card_progress
                    SET last_result = CASE
                        WHEN state = 'mastered' THEN 'correct'
                        WHEN state = 'review' THEN 'correct'
                        WHEN state = 'learning' THEN 'incorrect'
                        ELSE NULL
                    END,
                    correct_count = CASE
                        WHEN state IN ('mastered', 'review') THEN repetitions
                        ELSE 0
                    END,
                    incorrect_count = lapses
                    WHERE last_result IS NULL;
                """))
                db.session.commit()
                print("   ✅ Migrated progress data")
            except Exception as e:
                print(f"   ⚠️  Migration warning: {e}")
                db.session.rollback()
            
            # Drop old spaced repetition columns (optional - comment out if you want to keep them)
            print("\n4. Dropping old spaced repetition columns...")
            old_columns = ['state', 'due_date', 'interval', 'ease_factor', 'repetitions', 'lapses']
            
            for col_name in old_columns:
                try:
                    db.session.execute(text(f"""
                        ALTER TABLE card_progress 
                        DROP COLUMN {col_name};
                    """))
                    db.session.commit()
                    print(f"   ✅ Dropped {col_name} column")
                except Exception as e:
                    if "does not exist" in str(e).lower() or "no such column" in str(e).lower():
                        print(f"   ℹ️  {col_name} already dropped, skipping")
                        db.session.rollback()
                    else:
                        print(f"   ⚠️  Could not drop {col_name}: {e}")
                        db.session.rollback()
            
            print("\n✅ Migration completed successfully!")
            print("\nNext steps:")
            print("1. Review the changes")
            print("2. Re-import your decks to set difficulty tags")
            print("3. Start studying with the new system!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Migration failed: {e}")
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Spaced Repetition → Simple Tracking")
    print("=" * 60)
    
    confirm = input("\n⚠️  This will modify your database schema. Continue? (yes/no): ")
    
    if confirm.lower() == 'yes':
        migrate_database()
    else:
        print("Migration cancelled.")
