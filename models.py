from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User accounts"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    decks = db.relationship('Deck', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Deck(db.Model):
    """Represents a deck of flashcards"""
    __tablename__ = 'decks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cards = db.relationship('Card', backref='deck', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Deck {self.name}>'
    
    def get_stats(self):
        """Get statistics for this deck"""
        total_cards = len(self.cards)
        if total_cards == 0:
            return {
                'total': 0,
                'new': 0,
                'learning': 0,
                'review': 0,
                'mastered': 0
            }
        
        new = sum(1 for c in self.cards if c.progress and c.progress.state == 'new')
        learning = sum(1 for c in self.cards if c.progress and c.progress.state == 'learning')
        review = sum(1 for c in self.cards if c.progress and c.progress.state == 'review')
        mastered = sum(1 for c in self.cards if c.progress and c.progress.state == 'mastered')
        
        return {
            'total': total_cards,
            'new': new,
            'learning': learning,
            'review': review,
            'mastered': mastered
        }


class Card(db.Model):
    """Represents a single flashcard"""
    __tablename__ = 'cards'
    
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False)
    
    question = db.Column(db.Text, nullable=False)
    hint = db.Column(db.Text)
    options = db.Column(db.JSON)  # List of answer options
    correct_answer = db.Column(db.Integer)  # Index of correct answer
    description = db.Column(db.Text)  # Explanation after answering
    reference = db.Column(db.String(500))  # URL or reference
    code = db.Column(db.Text)  # Optional code snippet
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    progress = db.relationship('CardProgress', backref='card', uselist=False, 
                              cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='card', lazy=True,
                             cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Card {self.id}: {self.question[:50]}>'


class CardProgress(db.Model):
    """Tracks spaced repetition progress for a card"""
    __tablename__ = 'card_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=False, unique=True)
    
    # Spaced repetition data
    state = db.Column(db.String(20), default='new')  # new, learning, review, mastered
    due_date = db.Column(db.DateTime, default=datetime.utcnow)
    interval = db.Column(db.Integer, default=0)  # Days until next review
    ease_factor = db.Column(db.Float, default=2.5)  # Ease factor (SM-2 algorithm)
    repetitions = db.Column(db.Integer, default=0)  # Successful repetitions
    lapses = db.Column(db.Integer, default=0)  # Times card was forgotten
    
    last_reviewed = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CardProgress card_id={self.card_id} state={self.state}>'
    
    def is_due(self):
        """Check if card is due for review"""
        return self.due_date <= datetime.utcnow()


class Review(db.Model):
    """Records individual review sessions"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=False)
    
    rating = db.Column(db.String(10))  # again, hard, good, easy
    duration = db.Column(db.Integer)  # Time spent in seconds
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Review card_id={self.card_id} rating={self.rating}>'


class StudySession(db.Model):
    """Tracks study sessions"""
    __tablename__ = 'study_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'))
    
    cards_studied = db.Column(db.Integer, default=0)
    cards_correct = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<StudySession {self.id}>'
    
    @property
    def accuracy(self):
        """Calculate accuracy percentage"""
        if self.cards_studied == 0:
            return 0
        return round((self.cards_correct / self.cards_studied) * 100, 1)
