import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func

from config import Config
from models import db, User, Deck, Card, CardProgress, Review, StudySession, SpacedRepetitionSettings
from spaced_repetition import SpacedRepetition
from ai_generator import GeminiFlashcardGenerator, SYLLABUS_MODULES

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

    # Lightweight migration: ensure parent_id column exists on decks table for hierarchical decks
    # This avoids requiring Alembic for simple schema additions in development.
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    cols = [c['name'] for c in inspector.get_columns('decks')]
    if 'parent_id' not in cols:
        try:
            # Add parent_id column referencing decks.id
            db.session.execute(text('ALTER TABLE decks ADD COLUMN parent_id INTEGER REFERENCES decks(id)'))
            db.session.commit()
            app.logger.info('Added parent_id column to decks table')
        except Exception as e:
            app.logger.warning(f'Could not add parent_id column automatically: {e}')


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

    # Build parent->children mapping for hierarchical display
    deck_map = {d.id: d for d in decks}
    children_map = {d.id: [] for d in decks}
    roots = []
    for d in decks:
        if d.parent_id and d.parent_id in deck_map:
            children_map[d.parent_id].append(d)
        else:
            roots.append(d)

    def build_node(deck):
        # Aggregate stats across subdecks
        stats = deck.get_stats(include_subdecks=True)
        # Count not-studied cards across the deck and its descendants
        descendant_ids = deck._collect_descendant_ids()
        not_studied_count = Card.query.filter(Card.deck_id.in_(descendant_ids)).outerjoin(
            CardProgress, Card.id == CardProgress.card_id
        ).filter(CardProgress.id == None).count()

        node = {'deck': deck, 'stats': stats, 'due': not_studied_count, 'children': []}
        for child in sorted(children_map.get(deck.id, []), key=lambda x: (x.display_order, x.name.lower())):
            node['children'].append(build_node(child))
        return node

    deck_tree = [build_node(d) for d in sorted(roots, key=lambda x: (x.display_order, x.name.lower()))]

    return render_template('index.html', deck_stats=deck_tree)


@app.route('/deck/<int:deck_id>')
@login_required
def deck_detail(deck_id):
    """Deck detail page"""
    deck = Deck.query.filter_by(id=deck_id, user_id=current_user.id).first_or_404()
    stats = deck.get_stats()
    
    # Get not-studied cards count
    not_studied_count = Card.query.filter_by(deck_id=deck_id).outerjoin(
        CardProgress, Card.id == CardProgress.card_id
    ).filter(CardProgress.id == None).count()
    
    return render_template('deck_detail.html', deck=deck, stats=stats, due_count=not_studied_count)


@app.route('/study/<int:deck_id>')
@login_required
def study(deck_id):
    """Study session page - show mode selection or start studying"""
    deck = Deck.query.filter_by(id=deck_id, user_id=current_user.id).first_or_404()
    
    # Get study mode from query parameter
    mode = request.args.get('mode', 'select')
    
    if mode == 'select':
        # Show mode selection page
        # Count cards for each mode
        all_cards = Card.query.filter_by(deck_id=deck_id).count()
        
        trippy_cards = db.session.query(Card).join(
            CardProgress, Card.id == CardProgress.card_id
        ).filter(
            Card.deck_id == deck_id,
            CardProgress.last_result == 'trippy'
        ).count()
        
        missed_cards = db.session.query(Card).join(
            CardProgress, Card.id == CardProgress.card_id
        ).filter(
            Card.deck_id == deck_id,
            CardProgress.last_result == 'incorrect'
        ).count()
        
        return render_template('study_mode_select.html', 
                             deck=deck, 
                             all_cards=all_cards,
                             trippy_cards=trippy_cards,
                             missed_cards=missed_cards)
    
    # Get cards based on mode
    query = Card.query.filter_by(deck_id=deck_id)
    
    if mode == 'trippy':
        # Only cards marked as trippy
        query = query.join(CardProgress, Card.id == CardProgress.card_id).filter(
            CardProgress.last_result == 'trippy'
        )
    elif mode == 'missed':
        # Only cards marked as incorrect
        query = query.join(CardProgress, Card.id == CardProgress.card_id).filter(
            CardProgress.last_result == 'incorrect'
        )
    # else mode == 'all' - get all cards
    
    # Shuffle and limit
    from sqlalchemy import func
    cards = query.order_by(func.random()).limit(app.config['CARDS_PER_SESSION']).all()
    
    if not cards:
        flash(f'No cards available for {mode} mode!', 'info')
        return redirect(url_for('deck_detail', deck_id=deck_id))
    
    # Initialize progress for cards without it
    for card in cards:
        if not card.progress:
            progress = CardProgress(card_id=card.id)
            db.session.add(progress)
    
    db.session.commit()
    
    # Get or create study session
    session = StudySession.query.filter_by(
        deck_id=deck_id, 
        ended_at=None
    ).first()
    
    if not session:
        session = StudySession(deck_id=deck_id)
        db.session.add(session)
        db.session.commit()
    
    return render_template('study.html', deck=deck, cards=cards, session_id=session.id, mode=mode)


@app.route('/api/review', methods=['POST'])
@login_required
def review_card():
    """Record a card review"""
    data = request.json
    card_id = data.get('card_id')
    result = data.get('result')  # 'correct', 'incorrect', or 'trippy'
    duration = data.get('duration', 0)
    session_id = data.get('session_id')
    
    if not card_id or not result:
        return jsonify({'error': 'Missing card_id or result'}), 400
    
    if result not in ['correct', 'incorrect', 'trippy']:
        return jsonify({'error': 'Invalid result value'}), 400
    
    card = Card.query.get_or_404(card_id)
    
    # Get or create progress
    progress = card.progress
    if not progress:
        progress = CardProgress(card_id=card.id)
        db.session.add(progress)
    
    # Update progress counts
    if result == 'correct':
        progress.correct_count += 1
    elif result == 'incorrect':
        progress.incorrect_count += 1
    elif result == 'trippy':
        progress.trippy_count += 1
    
    # IMPORTANT: Update last_result - this clears 'incorrect' or 'trippy' status
    # when the card is answered correctly in a later session
    progress.last_result = result
    progress.last_reviewed = datetime.utcnow()
    
    # Record review
    review = Review(
        card_id=card_id,
        rating=result,
        duration=duration,
        reviewed_at=datetime.utcnow()
    )
    db.session.add(review)
    
    # Update study session
    if session_id:
        session = StudySession.query.get(session_id)
        if session:
            session.cards_studied += 1
            if result == 'correct':
                session.cards_correct += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'result': result,
        'correct_count': progress.correct_count,
        'incorrect_count': progress.incorrect_count,
        'trippy_count': progress.trippy_count
    })


@app.route('/api/card/<int:card_id>/clear_status', methods=['POST'])
@login_required
def clear_card_status(card_id):
    """Clear incorrect/trippy status - mark as mastered"""
    card = Card.query.get_or_404(card_id)
    
    # Verify ownership through deck
    if card.deck.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        progress = card.progress
        if progress:
            # Clear the last_result to remove from missed/trippy lists
            progress.last_result = 'correct'
            progress.last_reviewed = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Card status cleared'})
        else:
            return jsonify({'success': False, 'message': 'No progress found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/card/<int:card_id>/delete', methods=['DELETE'])
@login_required
def delete_card(card_id):
    """Delete a card"""
    card = Card.query.get_or_404(card_id)
    
    # Verify ownership through deck
    if card.deck.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        db.session.delete(card)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/card/<int:card_id>/progress', methods=['GET', 'PUT'])
@login_required
def card_progress(card_id):
    """Get or update card progress"""
    card = Card.query.get_or_404(card_id)
    
    # Verify ownership through deck
    if card.deck.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        # Get current progress
        progress = card.progress
        if not progress:
            progress = SpacedRepetition.initialize_card_progress(card)
            db.session.add(progress)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'progress': {
                'state': progress.state,
                'due_date': progress.due_date.isoformat() if progress.due_date else None,
                'interval': progress.interval,
                'ease_factor': progress.ease_factor,
                'repetitions': progress.repetitions,
                'lapses': progress.lapses
            }
        })
    
    elif request.method == 'PUT':
        # Update progress manually
        data = request.json
        progress = card.progress
        if not progress:
            progress = SpacedRepetition.initialize_card_progress(card)
            db.session.add(progress)
        
        # Update fields
        if 'state' in data:
            progress.state = data['state']
        if 'interval' in data:
            progress.interval = data['interval']
        if 'ease_factor' in data:
            progress.ease_factor = max(1.3, min(5.0, data['ease_factor']))
        if 'repetitions' in data:
            progress.repetitions = data['repetitions']
        if 'due_date' in data:
            # Parse datetime string
            from dateutil import parser
            progress.due_date = parser.parse(data['due_date'])
        
        progress.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            return jsonify({
                'success': True,
                'progress': {
                    'state': progress.state,
                    'due_date': progress.due_date.isoformat(),
                    'interval': progress.interval,
                    'ease_factor': progress.ease_factor,
                    'repetitions': progress.repetitions
                }
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500



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
        parent_deck_id = request.form.get('parent_deck')
        existing_deck_id = request.form.get('existing_deck')
        
        # Convert empty strings to None
        if parent_deck_id:
            parent_deck_id = int(parent_deck_id)
        else:
            parent_deck_id = None
            
        if existing_deck_id:
            existing_deck_id = int(existing_deck_id)
        else:
            existing_deck_id = None
        
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
                
                # Use existing deck or create new one
                if existing_deck_id:
                    deck = Deck.query.filter_by(id=existing_deck_id, user_id=current_user.id).first_or_404()
                    flash(f'Importing cards into existing deck: {deck.name}', 'info')
                else:
                    # Create deck for current user with optional parent
                    deck = Deck(
                        user_id=current_user.id,
                        name=deck_name,
                        description=deck_description,
                        parent_id=parent_deck_id
                    )
                    db.session.add(deck)
                    db.session.flush()
                
                # Create cards
                for card_data in cards_data:
                    # Handle different formats
                    if format_type == 'sanfoundry':
                        # Sanfoundry format: options as object {a, b, c, d}, answer as letter
                        options_dict = card_data.get('options', {})
                        
                        # Support both 'answer' and 'correct_answer' field names
                        answer_letter = (card_data.get('correct_answer') or card_data.get('answer', '')).lower().strip()
                        
                        # Support both 'question' and 'question_text' field names
                        question_text = (card_data.get('question_text') or card_data.get('question', '')).strip()
                        
                        explanation = card_data.get('explanation', '').strip()
                        
                        # Get difficulty if provided
                        difficulty = card_data.get('difficulty', '').lower().strip()
                        if difficulty not in ['easy', 'medium', 'hard']:
                            difficulty = None
                        
                        # Skip section headers (no answer and no explanation)
                        if not answer_letter and not explanation:
                            continue
                        
                        # Skip empty questions
                        if not question_text:
                            continue
                        
                        # Build options array and letter-to-index mapping
                        # Handle inconsistent option sets (missing b, only a/b, etc.)
                        options = []
                        letter_to_index = {}
                        
                        # Check all possible letters in order (support up to 'f' for some formats)
                        for letter in ['a', 'b', 'c', 'd', 'e', 'f']:
                            opt_text = options_dict.get(letter, '').strip()
                            if opt_text:
                                letter_to_index[letter] = len(options)
                                options.append(opt_text)
                        
                        # Determine correct answer index
                        if not options:
                            # No options - treat as open-ended question
                            options = None
                            correct_answer_index = None
                        elif answer_letter in letter_to_index:
                            # Valid answer letter
                            correct_answer_index = letter_to_index[answer_letter]
                        else:
                            # Answer letter not in options (data inconsistency)
                            # Skip this card or default to first option
                            print(f"Warning: Skipping card - answer '{answer_letter}' not found in options for question: {question_text[:50]}...")
                            continue  # Skip invalid cards
                        
                        # Map sanfoundry fields to our schema
                        question = question_text
                        hint = None  # Sanfoundry doesn't have hints
                        description = explanation
                        reference = card_data.get('source_url', '')
                        
                        # Handle code_blocks array - join multiple code blocks with newlines
                        code_blocks = card_data.get('code_blocks', [])
                        if code_blocks and isinstance(code_blocks, list):
                            code = '\n\n'.join(str(block) for block in code_blocks if block)
                        else:
                            code = None
                        
                    else:
                        # Get options and clean up any [cite_start] markers for Payal's format
                        raw_options = card_data.get('options')

                        # For Payal's format, clean up the description and hint from citation markers
                        description = card_data.get('description', '')
                        hint = card_data.get('hint', '')
                        # Support both 'question' and 'question_text'
                        question = (card_data.get('question') or card_data.get('question_text') or '').strip()
                        reference = card_data.get('reference') or card_data.get('source_url') or ''

                        # Normalize difficulty field if present
                        difficulty = (card_data.get('difficulty') or '').lower().strip()
                        if format_type == 'payal':
                            # Remove [cite_start] markers and clean citations
                            if description:
                                description = description.replace('[cite_start]', '').strip()
                            if hint:
                                hint = hint.replace('[cite_start]', '').strip()
                            difficulty = (card_data.get('difficulty') or '').lower()

                        if difficulty not in ['easy', 'medium', 'hard']:
                            difficulty = None

                        # Normalize options: support dict (letter keys) or list
                        options = None
                        if isinstance(raw_options, dict):
                            options = []
                            letter_to_index = {}
                            for letter in ['a', 'b', 'c', 'd', 'e', 'f']:
                                opt_text = (raw_options.get(letter) or '').strip()
                                if opt_text:
                                    letter_to_index[letter] = len(options)
                                    options.append(opt_text)
                        elif isinstance(raw_options, list):
                            options = [o for o in raw_options if o is not None]

                        # Extract code from multiple possible fields
                        code = None
                        for key in ['code', 'code_blocks', 'code_block', 'example_code', 'examples', 'sample_code', 'codeExample', 'codeExamples']:
                            if key in card_data and card_data.get(key):
                                val = card_data.get(key)
                                if isinstance(val, list):
                                    code = '\n\n'.join(str(x) for x in val if x)
                                else:
                                    code = str(val)
                                break

                        # Fallback: sometimes 'explanation' contains code blocks marked with backticks — leave as description

                        correct_answer_value = card_data.get('correct_answer') or card_data.get('answer')

                        # Handle correct_answer - support both index (int) and string value (letter or exact option)
                        correct_answer_index = None
                        if options and correct_answer_value is not None:
                            if isinstance(correct_answer_value, int):
                                correct_answer_index = correct_answer_value
                            elif isinstance(correct_answer_value, str):
                                ans = correct_answer_value.strip().lower()
                                # If single-letter, map via ordered letters
                                if len(ans) == 1 and ans in 'abcdef' and isinstance(raw_options, dict):
                                    mapping = {l: i for i, l in enumerate([l for l in ['a','b','c','d','e','f'] if (raw_options.get(l) or '').strip()])}
                                    correct_answer_index = mapping.get(ans)
                                else:
                                    # Try matching option text
                                    try:
                                        correct_answer_index = options.index(correct_answer_value)
                                    except ValueError:
                                        # try case-insensitive match
                                        found = None
                                        for i, opt in enumerate(options):
                                            if isinstance(opt, str) and opt.strip().lower() == ans:
                                                found = i
                                                break
                                        correct_answer_index = found
                    
                    card = Card(
                        deck_id=deck.id,
                        question=question,
                        hint=hint,
                        options=options,
                        correct_answer=correct_answer_index,
                        description=description,
                        reference=reference,
                        code=code,
                        difficulty=difficulty
                    )
                    db.session.add(card)
                
                db.session.commit()
                
                # Count actual imported cards
                imported_count = Card.query.filter_by(deck_id=deck.id).count()
                skipped_count = len(cards_data) - imported_count
                
                if skipped_count > 0:
                    flash(f'Successfully imported deck: {deck.name} with {imported_count} cards ({skipped_count} skipped due to invalid data)', 'success')
                else:
                    flash(f'Successfully imported deck: {deck.name} with {imported_count} cards', 'success')
                
                return redirect(url_for('deck_detail', deck_id=deck.id))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error importing deck: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Please upload a JSON file', 'error')
            return redirect(request.url)
    
    # GET request - show form with deck list for parent selection
    def get_deck_full_path(deck):
        """Get full hierarchical path for a deck (e.g., 'Parent / Child / Grandchild')"""
        path_parts = [deck.name]
        current = deck
        while current.parent_id:
            current = Deck.query.get(current.parent_id)
            if current:
                path_parts.insert(0, current.name)
        return ' / '.join(path_parts)
    
    user_decks = Deck.query.filter_by(user_id=current_user.id).order_by(Deck.name).all()
    decks_with_paths = []
    for deck in user_decks:
        decks_with_paths.append({
            'id': deck.id,
            'full_path': get_deck_full_path(deck)
        })
    
    return render_template('import.html', decks=decks_with_paths)


@app.route('/stats')
@login_required
def stats():
    """Statistics page"""
    # Overall statistics for current user
    total_decks = Deck.query.filter_by(user_id=current_user.id).count()
    total_cards = Card.query.join(Deck).filter(Deck.user_id == current_user.id).count()
    
    # Get reviews only for cards belonging to current user's decks
    total_reviews = Review.query.join(Card).join(Deck).filter(
        Deck.user_id == current_user.id
    ).count()
    
    # Today's statistics
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_reviews = Review.query.join(Card).join(Deck).filter(
        Deck.user_id == current_user.id,
        Review.reviewed_at >= today_start
    ).count()
    
    # Calculate accuracy for today - FIXED
    today_review_data = Review.query.join(Card).join(Deck).filter(
        Deck.user_id == current_user.id,
        Review.reviewed_at >= today_start
    ).all()
    
    if today_reviews > 0:
        today_correct = sum(1 for r in today_review_data if r.rating in ['good', 'easy'])
        today_accuracy = round((today_correct / today_reviews * 100), 1)
    else:
        today_accuracy = 0
    
    # Get review history (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    review_history = db.session.query(
        func.date(Review.reviewed_at).label('date'),
        func.count(Review.id).label('count')
    ).join(Card).join(Deck).filter(
        Deck.user_id == current_user.id,
        Review.reviewed_at >= thirty_days_ago
    ).group_by(
        func.date(Review.reviewed_at)
    ).all()
    
    # Format for chart - date is already a string from SQLite
    review_chart_data = [{'date': str(r.date), 'count': r.count} for r in review_history]
    
    # Get recent sessions for current user only
    recent_sessions = StudySession.query.join(Deck).filter(
        Deck.user_id == current_user.id
    ).order_by(
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


@app.route('/api/stats/review-history')
@login_required
def api_review_history():
    """Get review history for specified time range"""
    days = request.args.get('days', 7, type=int)
    
    # Limit to reasonable ranges
    if days not in [7, 14, 30, 60, 180]:
        days = 7
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get review history
    review_history = db.session.query(
        func.date(Review.reviewed_at).label('date'),
        func.count(Review.id).label('count')
    ).join(Card).join(Deck).filter(
        Deck.user_id == current_user.id,
        Review.reviewed_at >= start_date
    ).group_by(
        func.date(Review.reviewed_at)
    ).all()
    
    # Format for chart
    review_data = [{'date': str(r.date), 'count': r.count} for r in review_history]
    
    # Get accuracy data
    accuracy_history = db.session.query(
        func.date(Review.reviewed_at).label('date'),
        func.count(Review.id).label('total'),
        func.sum(
            db.case(
                (Review.result == 'correct', 1),
                else_=0
            )
        ).label('correct')
    ).join(Card).join(Deck).filter(
        Deck.user_id == current_user.id,
        Review.reviewed_at >= start_date
    ).group_by(
        func.date(Review.reviewed_at)
    ).all()
    
    accuracy_data = [
        {
            'date': str(a.date),
            'accuracy': round((a.correct / a.total * 100), 1) if a.total > 0 else 0
        } 
        for a in accuracy_history
    ]
    
    return jsonify({
        'reviews': review_data,
        'accuracy': accuracy_data
    })


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Spaced repetition settings page"""
    user_settings = SpacedRepetitionSettings.get_or_create(current_user.id)
    
    if request.method == 'POST':
        try:
            # Update settings from form
            user_settings.interval_multiplier = float(request.form.get('interval_multiplier', 1.0))
            user_settings.again_minutes = int(request.form.get('again_minutes', 10))
            user_settings.hard_multiplier = float(request.form.get('hard_multiplier', 1.2))
            user_settings.good_days = int(request.form.get('good_days', 1))
            user_settings.easy_multiplier = float(request.form.get('easy_multiplier', 4.0))
            user_settings.starting_ease = float(request.form.get('starting_ease', 2.5))
            user_settings.easy_bonus = float(request.form.get('easy_bonus', 1.3))
            user_settings.hard_penalty = float(request.form.get('hard_penalty', 0.8))
            user_settings.graduating_interval = int(request.form.get('graduating_interval', 1))
            user_settings.easy_interval = int(request.form.get('easy_interval', 4))
            
            db.session.commit()
            flash('Settings saved successfully!', 'success')
            return redirect(url_for('settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving settings: {str(e)}', 'error')
    
    return render_template('settings.html', settings=user_settings)


@app.route('/api/retention-data')
@login_required
def retention_data():
    """Get retention data with historical reviews and predictions"""
    # Get all cards for the current user
    cards = Card.query.join(Deck).filter(Deck.user_id == current_user.id).all()
    
    if not cards:
        return jsonify({'historical': [], 'predictions': []})
    
    # Get review history for the past 90 days
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    
    # Calculate retention for each day
    retention_data = []
    today = datetime.utcnow().date()
    
    for day_offset in range(90):
        target_date = today - timedelta(days=90 - day_offset)
        next_date = target_date + timedelta(days=1)
        
        # Count cards that were supposed to be reviewed on this day
        cards_due = CardProgress.query.join(Card).join(Deck).filter(
            Deck.user_id == current_user.id,
            func.date(CardProgress.due_date) == target_date
        ).count()
        
        if cards_due > 0:
            # Count how many were actually reviewed
            cards_reviewed = Review.query.join(Card).join(Deck).filter(
                Deck.user_id == current_user.id,
                func.date(Review.reviewed_at) == target_date
            ).count()
            
            retention_rate = (cards_reviewed / cards_due) * 100
        else:
            retention_rate = None
        
        retention_data.append({
            'date': str(target_date),
            'retention': retention_rate,
            'cards_due': cards_due,
            'cards_reviewed': cards_reviewed if cards_due > 0 else 0
        })
    
    # Calculate predictions for next 30 days
    predictions = []
    
    # Calculate average retention rate from historical data
    valid_retention_rates = [d['retention'] for d in retention_data if d['retention'] is not None]
    if valid_retention_rates:
        avg_retention = sum(valid_retention_rates) / len(valid_retention_rates)
    else:
        avg_retention = 85  # Default assumption
    
    # Use exponential decay model for predictions
    # retention(t) = base_retention * e^(-decay_rate * t)
    decay_rate = 0.01  # Configurable decay rate
    
    for day_offset in range(1, 31):
        future_date = today + timedelta(days=day_offset)
        
        # Count cards that will be due on this date
        cards_due_future = CardProgress.query.join(Card).join(Deck).filter(
            Deck.user_id == current_user.id,
            func.date(CardProgress.due_date) == future_date
        ).count()
        
        # Predict retention using exponential decay
        import math
        predicted_retention = avg_retention * math.exp(-decay_rate * day_offset)
        
        predictions.append({
            'date': str(future_date),
            'predicted_retention': round(predicted_retention, 1),
            'cards_due': cards_due_future
        })
    
    return jsonify({
        'historical': retention_data,
        'predictions': predictions,
        'avg_retention': round(avg_retention, 1) if valid_retention_rates else None
    })


@app.route('/deck/<int:deck_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_deck(deck_id):
    """Delete a deck"""
    # If GET request, show confirmation page
    if request.method == 'GET':
        deck = Deck.query.filter_by(id=deck_id, user_id=current_user.id).first_or_404()
        return render_template('confirm_delete.html', deck=deck)
    
    # POST request - actually delete
    deck = Deck.query.filter_by(id=deck_id, user_id=current_user.id).first_or_404()
    deck_name = deck.name
    
    try:
        # Delete deck - cascade will handle subdecks, cards, and study sessions
        db.session.delete(deck)
        db.session.commit()
        
        flash(f'Deck "{deck_name}" deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting deck: {str(e)}', 'error')
        
    return redirect(url_for('index'))


@app.route('/api/deck/<int:deck_id>/rename', methods=['PUT'])
@login_required
def rename_deck(deck_id):
    """Rename a deck"""
    deck = Deck.query.filter_by(id=deck_id, user_id=current_user.id).first_or_404()
    
    data = request.json
    new_name = data.get('name', '').strip()
    
    if not new_name:
        return jsonify({'error': 'Deck name cannot be empty'}), 400
    
    if len(new_name) > 200:
        return jsonify({'error': 'Deck name too long (max 200 characters)'}), 400
    
    try:
        deck.name = new_name
        db.session.commit()
        return jsonify({'success': True, 'name': new_name})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/deck', methods=['POST'])
@login_required
def create_deck_api():
    """Create a new deck (optionally as a subdeck)."""
    data = request.json or {}
    name = (data.get('name') or '').strip()
    parent_id = data.get('parent_id')

    if not name:
        return jsonify({'error': 'Deck name is required'}), 400

    # Validate parent belongs to user (if provided)
    if parent_id:
        parent = Deck.query.filter_by(id=parent_id, user_id=current_user.id).first()
        if not parent:
            return jsonify({'error': 'Invalid parent deck'}), 400

    deck = Deck(user_id=current_user.id, name=name, description=data.get('description'), parent_id=parent_id)
    try:
        db.session.add(deck)
        db.session.commit()
        return jsonify({'success': True, 'deck_id': deck.id, 'name': deck.name})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/deck/<int:deck_id>/move', methods=['PUT'])
@login_required
def move_deck(deck_id):
    """Change a deck's parent (move into a folder or make top-level)."""
    deck = Deck.query.filter_by(id=deck_id, user_id=current_user.id).first_or_404()
    data = request.json or {}
    new_parent = data.get('parent_id')

    if new_parent == deck.id:
        return jsonify({'error': 'Cannot set deck as its own parent'}), 400

    if new_parent:
        parent = Deck.query.filter_by(id=new_parent, user_id=current_user.id).first()
        if not parent:
            return jsonify({'error': 'Invalid parent deck'}), 400
        # Prevent cycles: ensure parent is not a descendant of deck
        descendant_ids = deck._collect_descendant_ids()
        if new_parent in descendant_ids:
            return jsonify({'error': 'Cannot move deck into its own descendant'}), 400

    deck.parent_id = new_parent
    try:
        db.session.commit()
        return jsonify({'success': True, 'deck_id': deck.id, 'parent_id': deck.parent_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/deck/<int:deck_id>/reorder', methods=['PUT'])
@login_required
def reorder_deck(deck_id):
    """Change a deck's display order relative to a target deck."""
    deck = Deck.query.filter_by(id=deck_id, user_id=current_user.id).first_or_404()
    data = request.json or {}
    target_id = data.get('target_id')
    position = data.get('position', 'after')  # 'before' or 'after'
    
    if not target_id:
        return jsonify({'error': 'target_id required'}), 400
    
    target = Deck.query.filter_by(id=target_id, user_id=current_user.id).first_or_404()
    
    # Must be at same level (same parent)
    if deck.parent_id != target.parent_id:
        return jsonify({'error': 'Can only reorder decks at the same level'}), 400
    
    # Get all decks at this level
    siblings = Deck.query.filter_by(
        user_id=current_user.id,
        parent_id=deck.parent_id
    ).order_by(Deck.display_order, Deck.name).all()
    
    # Remove the dragged deck from list
    siblings = [d for d in siblings if d.id != deck.id]
    
    # Find target position
    target_idx = next((i for i, d in enumerate(siblings) if d.id == target_id), None)
    if target_idx is None:
        return jsonify({'error': 'Target deck not found'}), 400
    
    # Insert deck at new position
    if position == 'before':
        siblings.insert(target_idx, deck)
    else:  # after
        siblings.insert(target_idx + 1, deck)
    
    # Update display_order for all siblings
    for i, sibling in enumerate(siblings):
        sibling.display_order = i
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


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


@app.route('/api/ai/modules', methods=['GET'])
@login_required
def get_ai_modules():
    """Get available modules and topics from AI generator"""
    modules = []
    for module_name, module_info in SYLLABUS_MODULES.items():
        modules.append({
            'name': module_name,
            'hours': module_info['hours'],
            'topics': module_info['topics']
        })
    
    return jsonify({
        'success': True,
        'modules': modules
    })


@app.route('/api/ai/generate-cards', methods=['POST'])
@login_required
def generate_ai_cards():
    """Generate flashcards using Gemini API"""
    try:
        data = request.get_json()
        
        # Validate required fields
        deck_id = data.get('deck_id')
        module_name = data.get('module_name')
        topic = data.get('topic')  # Optional
        count = data.get('count', 50)
        difficulty = data.get('difficulty', 'medium')
        
        if not deck_id or not module_name:
            return jsonify({
                'error': 'deck_id and module_name are required'
            }), 400
        
        # Verify user owns the deck
        deck = Deck.query.get_or_404(deck_id)
        if deck.user_id != current_user.id:
            return jsonify({
                'error': 'Unauthorized access to deck'
            }), 403
        
        # Initialize Gemini generator
        generator = GeminiFlashcardGenerator()
        
        # Generate flashcards
        flashcards = generator.generate_flashcards(
            module_name=module_name,
            topic=topic,
            count=count,
            difficulty=difficulty
        )
        
        # Insert generated cards into the deck
        cards_added = 0
        for flashcard_data in flashcards:
            # Convert correct_answer letter (a-d) to index (0-3)
            correct_letter = flashcard_data.get('correct_answer', 'a').lower()
            correct_index = ord(correct_letter) - ord('a')
            
            # Convert options dict to array
            options_dict = flashcard_data.get('options', {})
            options_array = [
                options_dict.get('a', ''),
                options_dict.get('b', ''),
                options_dict.get('c', ''),
                options_dict.get('d', '')
            ] if options_dict else None
            
            # Join code_blocks array into single string
            code_blocks = flashcard_data.get('code_blocks', [])
            code_string = '\n\n'.join(code_blocks) if code_blocks else None
            
            card = Card(
                deck_id=deck_id,
                question=flashcard_data.get('question_text', ''),
                hint=flashcard_data.get('hint'),
                options=options_array,
                correct_answer=correct_index,
                description=flashcard_data.get('explanation', ''),
                reference=flashcard_data.get('reference'),
                code=code_string,
                difficulty=flashcard_data.get('difficulty', 'medium')
            )
            db.session.add(card)
            cards_added += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'cards_generated': cards_added,
            'deck_id': deck_id,
            'module': module_name,
            'topic': topic
        })
        
    except ValueError as e:
        return jsonify({
            'error': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Failed to generate cards: {str(e)}'
        }), 500


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
