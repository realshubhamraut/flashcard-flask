"""
Initialize the database tables.
Run this once after deploying to Render to create the database schema.
"""
from app import app, db

with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")
