"""Auto migration script - runs without prompts"""
import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = 'instance/flashcards.db'

def migrate():
    print("=" * 60)
    print("Database Migration: Spaced Repetition → Simple Tracking")
    print("=" * 60)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return
    
    # Backup
    backup_path = f'instance/flashcards_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Add difficulty column to cards
        print("\n📝 Adding difficulty column to cards table...")
        cursor.execute("ALTER TABLE cards ADD COLUMN difficulty VARCHAR(20)")
        print("✅ Added difficulty column")
        
        # Add new columns to card_progress
        print("\n📝 Adding tracking columns to card_progress table...")
        cursor.execute("ALTER TABLE card_progress ADD COLUMN correct_count INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE card_progress ADD COLUMN incorrect_count INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE card_progress ADD COLUMN trippy_count INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE card_progress ADD COLUMN last_result VARCHAR(20)")
        print("✅ Added tracking columns")
        
        # Migrate existing data
        print("\n📝 Migrating existing progress data...")
        cursor.execute("""
            UPDATE card_progress 
            SET correct_count = CASE 
                WHEN state = 'mastered' THEN 5
                WHEN state = 'review' THEN 3
                WHEN state = 'learning' THEN 1
                ELSE 0
            END,
            incorrect_count = CASE 
                WHEN lapses > 0 THEN lapses
                ELSE 0
            END,
            last_result = CASE 
                WHEN state = 'mastered' OR state = 'review' THEN 'correct'
                WHEN state = 'learning' THEN 'incorrect'
                ELSE NULL
            END
        """)
        migrated = cursor.rowcount
        print(f"✅ Migrated {migrated} card progress records")
        
        conn.commit()
        
        # Create new table without old columns (SQLite doesn't support DROP COLUMN easily)
        print("\n📝 Recreating card_progress table without spaced repetition columns...")
        
        # Get current data
        cursor.execute("""
            SELECT id, user_id, card_id, correct_count, incorrect_count, 
                   trippy_count, last_result, last_reviewed
            FROM card_progress
        """)
        data = cursor.fetchall()
        
        # Drop old table
        cursor.execute("DROP TABLE card_progress")
        
        # Create new table
        cursor.execute("""
            CREATE TABLE card_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                correct_count INTEGER DEFAULT 0,
                incorrect_count INTEGER DEFAULT 0,
                trippy_count INTEGER DEFAULT 0,
                last_result VARCHAR(20),
                last_reviewed DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (card_id) REFERENCES cards(id),
                UNIQUE (user_id, card_id)
            )
        """)
        
        # Insert data back
        cursor.executemany("""
            INSERT INTO card_progress 
            (id, user_id, card_id, correct_count, incorrect_count, trippy_count, last_result, last_reviewed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        
        conn.commit()
        print(f"✅ Recreated table with {len(data)} records")
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Replace templates: mv templates/study_new.html templates/study.html")
        print("2. Replace JavaScript: mv static/js/study_new.js static/js/study.js")
        print("3. Restart the Flask app")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print(f"Database restored from backup: {backup_path}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
