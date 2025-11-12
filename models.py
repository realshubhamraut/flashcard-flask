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
    # Hierarchy: support parent deck (folder) and children (subdecks)
    parent_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=True)
    parent = db.relationship('Deck', remote_side=[id], backref=db.backref('children', cascade='all, delete-orphan'))

    # Relationships
    cards = db.relationship('Card', backref='deck', lazy=True, cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', backref='deck', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Deck {self.name}>'

    def _collect_descendant_ids(self):
        """Return list of this deck id and all descendant deck ids."""
        ids = [self.id]
        # Using children relationship which is lazy-loaded
        for child in getattr(self, 'children') or []:
            ids.extend(child._collect_descendant_ids())
        return ids

    def get_stats(self, include_subdecks=True):
        """Get statistics for this deck. If include_subdecks, aggregate cards from all descendants."""
        # Gather deck ids to include
        deck_ids = self._collect_descendant_ids() if include_subdecks else [self.id]

        # Use queries to avoid loading all objects into memory
        total_cards = Card.query.filter(Card.deck_id.in_(deck_ids)).count()
        if total_cards == 0:
            return {
                'total': 0,
                'new': 0,
                'learning': 0,
                'review': 0,
                'mastered': 0
            }

        # Count states by joining progress
        q = db.session.query(Card).outerjoin(CardProgress, Card.id == CardProgress.card_id).filter(Card.deck_id.in_(deck_ids))

        new = q.filter(CardProgress.state == 'new').count()
        learning = q.filter(CardProgress.state == 'learning').count()
        review = q.filter(CardProgress.state == 'review').count()
        mastered = q.filter(CardProgress.state == 'mastered').count()

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
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id', ondelete='CASCADE'))
    
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


class SpacedRepetitionSettings(db.Model):
    """User-specific spaced repetition settings"""
    __tablename__ = 'sr_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Multiplier for all intervals (1.0 = normal, 2.0 = double intervals, 0.5 = half intervals)
    interval_multiplier = db.Column(db.Float, default=1.0)
    
    # Base intervals in minutes/days
    again_minutes = db.Column(db.Integer, default=10)  # <10m by default
    hard_multiplier = db.Column(db.Float, default=1.2)  # Hard = Good * 1.2
    good_days = db.Column(db.Integer, default=1)  # 1 day default for new cards
    easy_multiplier = db.Column(db.Float, default=4.0)  # Easy = Good * 4
    
    # Ease factor settings
    starting_ease = db.Column(db.Float, default=2.5)
    easy_bonus = db.Column(db.Float, default=1.3)  # Multiplier for ease on "easy"
    hard_penalty = db.Column(db.Float, default=0.8)  # Multiplier for ease on "hard"
    
    # Graduating intervals
    graduating_interval = db.Column(db.Integer, default=1)  # Days
    easy_interval = db.Column(db.Integer, default=4)  # Days
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('sr_settings', uselist=False))
    
    def __repr__(self):
        return f'<SRSettings user_id={self.user_id} multiplier={self.interval_multiplier}>'
    
    @staticmethod
    def get_or_create(user_id):
        """Get settings for user or create default settings"""
        settings = SpacedRepetitionSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = SpacedRepetitionSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()
        return settings
