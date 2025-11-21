# Development Guide

## Project Structure

```
flashcard-flask/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── models.py                   # Database models (SQLAlchemy)
├── spaced_repetition.py        # SM-2 algorithm implementation
├── requirements.txt            # Python dependencies
├── setup.sh                    # Quick setup script
├── README.md                   # Project overview
├── USER_GUIDE.md              # Comprehensive user guide
├── .gitignore                 # Git ignore rules
│
├── instance/                   # Database directory (auto-created)
│   ├── .gitkeep
│   └── flashcards.db          # SQLite database
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html              # Base template with navigation
│   ├── index.html             # Home page (deck list)
│   ├── deck_detail.html       # Individual deck view
│   ├── study.html             # Study session interface
│   ├── stats.html             # Statistics dashboard
│   └── import.html            # Deck import page
│
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css          # Main stylesheet with dark mode
│   └── js/
│       ├── main.js            # Global JS (theme, utilities)
│       ├── study.js           # Study session functionality
│       └── stats.js           # Statistics charts
│
└── sample_decks/              # Example quiz data
    ├── python_fundamentals.json
    └── web_development.json
```

## Technology Stack

### Backend
- **Flask 3.0** - Web framework
- **SQLAlchemy 3.1** - ORM for database operations
- **SQLite** - Database (can be swapped for PostgreSQL)
- **Python 3.8+** - Programming language

### Frontend
- **Jinja2** - Template engine
- **Vanilla JavaScript** - No frameworks, minimal dependencies
- **CSS3** - Custom styling with CSS variables for theming
- **HTML5** - Semantic markup

### Key Features
- SM-2 spaced repetition algorithm
- Dark mode with localStorage persistence
- Responsive design (mobile-friendly)
- RESTful API endpoints
- Code syntax highlighting
- Session tracking

## Database Schema

### Tables

**decks**
- `id` (Primary Key)
- `name` (String)
- `description` (Text)
- `created_at` (DateTime)

**cards**
- `id` (Primary Key)
- `deck_id` (Foreign Key → decks.id)
- `question` (Text, required)
- `hint` (Text, optional)
- `options` (JSON array, optional)
- `correct_answer` (Integer, optional)
- `description` (Text, optional)
- `reference` (String, optional)
- `code` (Text, optional)
- `created_at` (DateTime)

**card_progress**
- `id` (Primary Key)
- `card_id` (Foreign Key → cards.id, unique)
- `correct_count` (Integer, times answered correctly)
- `incorrect_count` (Integer, times answered incorrectly)
- `trippy_count` (Integer, times marked as trippy/tricky)
- `last_result` (String: correct/incorrect/trippy)
- `last_reviewed` (DateTime)
- `updated_at` (DateTime)

**reviews**
- `id` (Primary Key)
- `card_id` (Foreign Key → cards.id)
- `rating` (String: again/hard/good/easy)
- `duration` (Integer, seconds)
- `reviewed_at` (DateTime)

**study_sessions**
- `id` (Primary Key)
- `deck_id` (Foreign Key → decks.id)
- `cards_studied` (Integer)
- `cards_correct` (Integer)
- `started_at` (DateTime)
- `ended_at` (DateTime)

## API Endpoints

### Web Routes (HTML)

```
GET  /                          # Home page with deck list
GET  /deck/<deck_id>            # Deck detail page
GET  /study/<deck_id>           # Study session
GET  /import                    # Import form
POST /import                    # Process import
GET  /stats                     # Statistics page
POST /deck/<deck_id>/delete     # Delete deck
```

### API Routes (JSON)

```
POST /api/review                # Record card review
POST /api/session/<id>/end      # End study session
```

## Study System

### Simple Tracking Implementation

The system uses a simple tracking approach instead of complex spaced repetition:

1. **Progress Tracking**: Cards track three counts:
   - Correct answers
   - Incorrect answers
   - Trippy marks (cards you find confusing)

2. **Study Modes**:
   - **Study Entirely**: All cards in deck, shuffled
   - **Study Only Trippy**: Cards marked as tricky
   - **Study Missed**: Cards answered incorrectly

3. **Result Tracking**:
   - Last result determines if card appears in trippy/missed lists
   - Answering correctly clears incorrect/trippy status
   - Can manually mark cards as "mastered" to clear status

4. **Session Flow**:
   - Choose study mode
   - Answer questions (correct/incorrect)
   - Mark confusing questions as trippy (hover on right side)
   - Review only problematic cards later

### Customization

Edit `config.py` to adjust:
```python
CARDS_PER_SESSION = 100  # Number of cards per study session
```

## Extending the Application

### Adding New Features

**1. Image Support for Cards**

Add to models.py:
```python
class Card(db.Model):
    # ... existing fields ...
    image_url = db.Column(db.String(500))
```

Update JSON format and templates accordingly.

**2. Audio Pronunciation**

Similar approach with `audio_url` field.

**3. Deck Sharing**

Add export endpoint:
```python
@app.route('/deck/<int:deck_id>/export')
def export_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    # Convert to JSON and return
```

**4. User Authentication**

Install Flask-Login:
```bash
pip install flask-login
```

Add User model and authentication routes.

**5. Study Streaks**

Track consecutive study days:
```python
class UserStats(db.Model):
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_study_date = db.Column(db.Date)
```

### Database Migrations

For production, use Flask-Migrate:

```bash
pip install flask-migrate
```

In app.py:
```python
from flask_migrate import Migrate
migrate = Migrate(app, db)
```

Commands:
```bash
flask db init
flask db migrate -m "description"
flask db upgrade
```

### Testing

Create `tests/` directory:

```python
# tests/test_spaced_repetition.py
import unittest
from spaced_repetition import SpacedRepetition
from models import CardProgress

class TestSpacedRepetition(unittest.TestCase):
    def test_again_rating(self):
        progress = CardProgress(
            interval=10,
            ease_factor=2.5,
            repetitions=5
        )
        new_progress = SpacedRepetition.schedule_card(progress, 'again')
        self.assertEqual(new_progress.interval, 0)
        self.assertEqual(new_progress.repetitions, 0)
```

Run tests:
```bash
python -m pytest tests/
```

### Code Quality

**Linting:**
```bash
pip install flake8
flake8 *.py
```

**Formatting:**
```bash
pip install black
black *.py
```

## Performance Optimization

### Database Indexing

Add indexes for frequently queried fields:
```python
class CardProgress(db.Model):
    # ...
    __table_args__ = (
        db.Index('idx_due_date', 'due_date'),
        db.Index('idx_card_state', 'state'),
    )
```

### Caching

Install Flask-Caching:
```bash
pip install flask-caching
```

Usage:
```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=300)
@app.route('/stats')
def stats():
    # ... expensive computations ...
```

### Production Settings

Update `config.py` for production:
```python
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Use PostgreSQL in production
```

## Deployment Checklist

- [ ] Set `SECRET_KEY` environment variable
- [ ] Use production database (PostgreSQL)
- [ ] Enable HTTPS
- [ ] Set `DEBUG = False`
- [ ] Configure error logging
- [ ] Set up database backups
- [ ] Add rate limiting
- [ ] Configure CORS if needed
- [ ] Minify CSS/JS
- [ ] Add monitoring (Sentry, etc.)

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## License

MIT License - see LICENSE file for details
