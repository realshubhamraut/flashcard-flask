import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///flashcards.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application config
    CARDS_PER_SESSION = 100
    NEW_CARDS_PER_DAY = 10
    
    # Spaced repetition defaults (similar to Anki)
    SR_GRADUATING_INTERVAL = 1  # days
    SR_EASY_INTERVAL = 4  # days
    SR_STARTING_EASE = 2.5
    SR_MINIMUM_EASE = 1.3
    SR_EASY_BONUS = 1.3
    SR_HARD_INTERVAL = 1.2
