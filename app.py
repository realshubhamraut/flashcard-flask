import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func

from config import Config
from models import db, User, Deck, Card, CardProgress, Review, StudySession
from spaced_repetition import SpacedRepetition

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Ensure instance folder exists
os.makedirs('instance', exist_ok=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_request
def create_tables():
    """Create database tables before first request"""
    db.create_all()


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
        elif password != confirm_password:
            flash('Passwords do not match', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
        else:
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Home page showing all decks"""
    decks = Deck.query.filter_by(user_id=current_user.id).all()
    
    # Get statistics for each deck
    deck_stats = []
    for deck in decks:
        stats = deck.get_stats()
        due_count = Card.query.filter_by(deck_id=deck.id).join(
            CardProgress, Card.id == CardProgress.card_id, isouter=True
        ).filter(
            db.or_(
                CardProgress.due_date == None,
                CardProgress.due_date <= datetime.utcnow()
            )
        ).count()
        
        deck_stats.append({
            'deck': deck,
            'stats': stats,
            'due': due_count
        })
    
    return render_template('index.html', deck_stats=deck_stats)


@app.route('/deck/<int:deck_id>')
@login_required
def deck_detail(deck_id):
    """Deck detail page"""
    deck = Deck.query.filter_by(id=deck_id, user_id=current_user.id).first_or_404()
    stats = deck.get_stats()
    
    # Get due cards count
    due_count = Card.query.filter_by(deck_id=deck_id).join(
        CardProgress, Card.id == CardProgress.card_id, isouter=True
    ).filter(
        db.or_(
            CardProgress.due_date == None,
            CardProgress.due_date <= datetime.utcnow()
        )
    ).count()
    
    return render_template('deck_detail.html', deck=deck, stats=stats, due_count=due_count)


@app.route('/study/<int:deck_id>')
@login_required
def study(deck_id):
    """Study session page"""
    deck = Deck.query.filter_by(id=deck_id, user_id=current_user.id).first_or_404()
    
    # Get due cards
    cards = SpacedRepetition.get_due_cards(deck_id, limit=app.config['CARDS_PER_SESSION'])
    
    if not cards:
        flash('No cards due for review!', 'info')
        return redirect(url_for('deck_detail', deck_id=deck_id))
    
    # Initialize progress for cards without it
    for card in cards:
        if not card.progress:
            progress = SpacedRepetition.initialize_card_progress(card)
            db.session.add(progress)
    
    db.session.commit()
    
    # Create study session
    session = StudySession(deck_id=deck_id)
    db.session.add(session)
    db.session.commit()
    
    return render_template('study.html', deck=deck, cards=cards, session_id=session.id)


@app.route('/api/review', methods=['POST'])
@login_required
def review_card():
    """Record a card review"""
    data = request.json
    card_id = data.get('card_id')
    rating = data.get('rating')
    duration = data.get('duration', 0)
    session_id = data.get('session_id')
    
    if not card_id or not rating:
        return jsonify({'error': 'Missing card_id or rating'}), 400
    
    card = Card.query.get_or_404(card_id)
    
    # Get or create progress
    progress = card.progress
    if not progress:
        progress = SpacedRepetition.initialize_card_progress(card)
        db.session.add(progress)
        db.session.commit()
    
    # Update progress using spaced repetition algorithm
    progress = SpacedRepetition.schedule_card(progress, rating)
    
    # Record review
    review = SpacedRepetition.record_review(card_id, rating, duration)
    db.session.add(review)
    
    # Update study session
    if session_id:
        session = StudySession.query.get(session_id)
        if session:
            session.cards_studied += 1
            if rating in ['good', 'easy']:
                session.cards_correct += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'next_review': progress.due_date.isoformat(),
        'interval': progress.interval,
        'state': progress.state
    })


@app.route('/import', methods=['GET', 'POST'])
@login_required
def import_deck():
    """Import deck from JSON file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        format_type = request.form.get('format_type', 'shubham')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith('.json'):
            try:
                data = json.load(file)
                
                # Support two formats:
                # 1. Full format: {"name": "...", "cards": [...]}
                # 2. Simple format: [{"question": "...", ...}, ...]
                
                if isinstance(data, list):
                    # Simple format - array of cards
                    cards_data = data
                    deck_name = file.filename.replace('.json', '').replace('_', ' ').title()
                    deck_description = f'Imported from {file.filename}'
                elif isinstance(data, dict):
                    # Full format - with deck metadata
                    cards_data = data.get('cards', [])
                    deck_name = data.get('name', 'Imported Deck')
                    deck_description = data.get('description', '')
                else:
                    raise ValueError('Invalid JSON format. Expected array of cards or object with "cards" field.')
                
                # Create deck for current user
                deck = Deck(
                    user_id=current_user.id,
                    name=deck_name,
                    description=deck_description
                )
                db.session.add(deck)
                db.session.flush()
                
                # Create cards
                for card_data in cards_data:
                    # Get options and clean up any [cite_start] markers for Payal's format
                    options = card_data.get('options')
                    
                    # For Payal's format, clean up the description and hint from citation markers
                    description = card_data.get('description', '')
                    hint = card_data.get('hint', '')
                    
                    if format_type == 'payal':
                        # Remove [cite_start] markers and clean citations
                        if description:
                            description = description.replace('[cite_start]', '').strip()
                        if hint:
                            hint = hint.replace('[cite_start]', '').strip()
                    
                    correct_answer_value = card_data.get('correct_answer')
                    
                    # Handle correct_answer - support both index (int) and string value
                    correct_answer_index = None
                    if options and correct_answer_value is not None:
                        if isinstance(correct_answer_value, int):
                            # Already an index
                            correct_answer_index = correct_answer_value
                        elif isinstance(correct_answer_value, str):
                            # Convert string answer to index
                            try:
                                correct_answer_index = options.index(correct_answer_value)
                            except ValueError:
                                # If exact match not found, keep as None or use first match
                                correct_answer_index = None
                    
                    card = Card(
                        deck_id=deck.id,
                        question=card_data.get('question'),
                        hint=hint,
                        options=options,
                        correct_answer=correct_answer_index,
                        description=description,
                        reference=card_data.get('reference'),
                        code=card_data.get('code')
                    )
                    db.session.add(card)
                
                db.session.commit()
                flash(f'Successfully imported deck: {deck.name} with {len(cards_data)} cards', 'success')
                return redirect(url_for('deck_detail', deck_id=deck.id))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error importing deck: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Please upload a JSON file', 'error')
            return redirect(request.url)
    
    return render_template('import.html')


@app.route('/stats')
@login_required
def stats():
    """Statistics page"""
    # Overall statistics for current user
    total_decks = Deck.query.filter_by(user_id=current_user.id).count()
    total_cards = Card.query.join(Deck).filter(Deck.user_id == current_user.id).count()
    total_reviews = Review.query.count()
    
    # Today's statistics
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_reviews = Review.query.filter(Review.reviewed_at >= today_start).count()
    
    # Calculate accuracy for today
    today_review_data = Review.query.filter(Review.reviewed_at >= today_start).all()
    today_correct = sum(1 for r in today_review_data if r.rating in ['good', 'easy'])
    today_accuracy = round((today_correct / today_reviews * 100), 1) if today_reviews > 0 else 0
    
    # Get review history (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    review_history = db.session.query(
        func.date(Review.reviewed_at).label('date'),
        func.count(Review.id).label('count')
    ).filter(
        Review.reviewed_at >= thirty_days_ago
    ).group_by(
        func.date(Review.reviewed_at)
    ).all()
    
    # Format for chart - date is already a string from SQLite
    review_chart_data = [{'date': str(r.date), 'count': r.count} for r in review_history]
    
    # Get recent sessions
    recent_sessions = StudySession.query.order_by(
        StudySession.started_at.desc()
    ).limit(10).all()
    
    return render_template('stats.html',
                         total_decks=total_decks,
                         total_cards=total_cards,
                         total_reviews=total_reviews,
                         today_reviews=today_reviews,
                         today_accuracy=today_accuracy,
                         review_chart_data=review_chart_data,
                         recent_sessions=recent_sessions)


@app.route('/deck/<int:deck_id>/delete', methods=['POST'])
@login_required
def delete_deck(deck_id):
    """Delete a deck"""
    deck = Deck.query.filter_by(id=deck_id, user_id=current_user.id).first_or_404()
    deck_name = deck.name
    
    db.session.delete(deck)
    db.session.commit()
    
    flash(f'Deck "{deck_name}" deleted successfully', 'success')
    return redirect(url_for('index'))


@app.route('/api/session/<int:session_id>/end', methods=['POST'])
@login_required
def end_session(session_id):
    """End a study session"""
    session = StudySession.query.get_or_404(session_id)
    session.ended_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'cards_studied': session.cards_studied,
        'accuracy': session.accuracy
    })


@app.template_filter('timeago')
def timeago_filter(dt):
    """Convert datetime to human-readable time ago"""
    if not dt:
        return 'Never'
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        return f'{diff.days // 365} year{"s" if diff.days // 365 > 1 else ""} ago'
    elif diff.days > 30:
        return f'{diff.days // 30} month{"s" if diff.days // 30 > 1 else ""} ago'
    elif diff.days > 0:
        return f'{diff.days} day{"s" if diff.days > 1 else ""} ago'
    elif diff.seconds > 3600:
        return f'{diff.seconds // 3600} hour{"s" if diff.seconds // 3600 > 1 else ""} ago'
    elif diff.seconds > 60:
        return f'{diff.seconds // 60} minute{"s" if diff.seconds // 60 > 1 else ""} ago'
    else:
        return 'Just now'


@app.template_filter('future_time')
def future_time_filter(dt):
    """Convert future datetime to human-readable format"""
    if not dt:
        return 'Not scheduled'
    
    now = datetime.utcnow()
    diff = dt - now
    
    if diff.total_seconds() < 0:
        return 'Now'
    
    if diff.days > 365:
        return f'in {diff.days // 365} year{"s" if diff.days // 365 > 1 else ""}'
    elif diff.days > 30:
        return f'in {diff.days // 30} month{"s" if diff.days // 30 > 1 else ""}'
    elif diff.days > 0:
        return f'in {diff.days} day{"s" if diff.days > 1 else ""}'
    elif diff.seconds > 3600:
        return f'in {diff.seconds // 3600} hour{"s" if diff.seconds // 3600 > 1 else ""}'
    elif diff.seconds > 60:
        return f'in {diff.seconds // 60} minute{"s" if diff.seconds // 60 > 1 else ""}'
    else:
        return 'in a moment'


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
