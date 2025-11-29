import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func

from config import Config
from models import db, User, Deck, Card, CardProgress, Review, StudySession

from ai_generator import (
    GeminiFlashcardGenerator,
    SYLLABUS_MODULES,
    SYLLABUS_MODULE_SEQUENCE
)
from ai_generator_payal import (
    PayalFlashcardGenerator,
    PAYAL_SUBJECTS,
    PAYAL_SUBJECT_ORDER,
    PAYAL_CLASS_ORDER,
    PAYAL_CLASS_LABELS,
    PAYAL_CLASS_LABEL_TO_KEY
)
from dotenv import load_dotenv
load_dotenv()


def get_next_display_order(user_id, parent_id=None):
    """Return the next display_order value for the given user/parent."""
    query = db.session.query(func.max(Deck.display_order)).filter(Deck.user_id == user_id)
    if parent_id is None:
        query = query.filter(Deck.parent_id.is_(None))
    else:
        query = query.filter(Deck.parent_id == parent_id)
    max_value = query.scalar()
    return (max_value or 0) + 1


def _normalize_question(text: str) -> str:
    """Normalize question text for duplicate detection."""
    if not text:
        return ''
    return ' '.join(text.strip().lower().split())


def ensure_ai_deck_hierarchy(user):
    """Ensure AI modules/subjects have deck hierarchies with subdecks per topic."""
    if not user or not getattr(user, 'id', None):
        return 0

    user_decks = Deck.query.filter_by(user_id=user.id).all()
    deck_lookup = {(deck.parent_id, deck.name.strip().lower()): deck for deck in user_decks}

    created = 0

    def ensure_deck(name, parent=None):
        nonlocal created
        normalized_name = name.strip()
        key = (parent.id if parent else None, normalized_name.lower())

        existing = deck_lookup.get(key)
        if existing:
            return existing

        deck = Deck(
            user_id=user.id,
            name=normalized_name,
            parent_id=parent.id if parent else None,
            display_order=get_next_display_order(user.id, parent.id if parent else None)
        )
        db.session.add(deck)
        db.session.flush()
        deck_lookup[key] = deck
        created += 1
        return deck

    # Shubham modules and topics
    for module_name, module_info in SYLLABUS_MODULES.items():
        parent_deck = ensure_deck(module_name)
        for topic in module_info.get('topics', []) or []:
            ensure_deck(topic, parent_deck)

    # Payal subjects by class and topics
    for subject, class_map in PAYAL_SUBJECTS.items():
        for class_key, topics in class_map.items():
            class_label = class_key.replace('_', ' ').title()
            parent_name = f"{class_label} - {subject}"
            parent_deck = ensure_deck(parent_name)
            for topic in topics:
                ensure_deck(topic, parent_deck)

    if created:
        db.session.commit()

    return created


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

    def sort_decks(decks):
        def deck_order_key(d):
            order = d.display_order if d.display_order is not None else 10**6
            return (order, d.name.lower())

        return sorted(decks, key=deck_order_key)

    def build_node(deck):
        # Aggregate stats across subdecks
        stats = deck.get_stats(include_subdecks=True)
        # Due count is the not_studied count from stats (includes all subdecks)
        due_count = stats.get('not_studied', 0)

        node = {'deck': deck, 'stats': stats, 'due': due_count, 'children': []}
        for child in sort_decks(children_map.get(deck.id, [])):
            node['children'].append(build_node(child))
        return node

    deck_tree = [build_node(d) for d in sort_decks(roots)]

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
        today_correct = sum(1 for r in today_review_data if r.rating == 'correct')
        today_accuracy = round((today_correct / today_reviews * 100), 1)
    else:
        today_accuracy = 0
    
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
                         recent_sessions=recent_sessions)







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

    display_order = get_next_display_order(current_user.id, parent_id)
    deck = Deck(
        user_id=current_user.id,
        name=name,
        description=data.get('description'),
        parent_id=parent_id,
        display_order=display_order
    )
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


def _build_payal_module_list():
    """Return ordered list like 'Class 11 - Physics'."""
    modules = []
    for class_key in PAYAL_CLASS_ORDER:
        class_label = PAYAL_CLASS_LABELS.get(class_key, class_key.replace('_', ' ').title())
        for subject in PAYAL_SUBJECT_ORDER:
            subject_topics = PAYAL_SUBJECTS.get(subject, {})
            if class_key not in subject_topics:
                continue
            modules.append(f"{class_label} - {subject}")
    return modules


@app.route('/api/ai/modules-payal', methods=['GET'])
@login_required
def get_ai_modules_payal():
    """Get ordered subjects for Payal's generator"""
    return jsonify({
        'success': True,
        'modules': _build_payal_module_list()
    })


@app.route('/api/ai/initialize-payal-decks', methods=['POST'])
@login_required
def initialize_payal_decks():
    """Create the 8 standard decks for Payal (Class 11 & 12 for Physics, Chemistry, Math, Biology)"""
    try:
        decks_created = []
        decks_existing = []
        
        deck_names = [
            "Class 11 - Physics",
            "Class 11 - Chemistry", 
            "Class 11 - Mathematics",
            "Class 11 - Biology",
            "Class 12 - Physics",
            "Class 12 - Chemistry",
            "Class 12 - Mathematics",
            "Class 12 - Biology"
        ]
        
        for deck_name in deck_names:
            # Check if deck already exists for this user
            existing = Deck.query.filter_by(
                user_id=current_user.id,
                name=deck_name
            ).first()
            
            if existing:
                decks_existing.append(deck_name)
            else:
                # Create new deck
                new_deck = Deck(
                    user_id=current_user.id,
                    name=deck_name,
                    description=f"Maharashtra Board {deck_name} - MHT-CET/JEE/NEET preparation"
                )
                db.session.add(new_deck)
                decks_created.append(deck_name)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'created': decks_created,
            'existing': decks_existing,
            'message': f'Created {len(decks_created)} new decks. {len(decks_existing)} already existed.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/modules-payal/<module_name>/topics', methods=['GET'])
@login_required
def get_ai_topics_payal(module_name):
    """Get topics for a specific class-subject combination in Payal's generator"""
    # Parse module_name like "Class 11 - Physics"
    try:
        parts = module_name.split(' - ')
        if len(parts) != 2:
            return jsonify({'success': False, 'error': 'Invalid module format'}), 400
        
        class_part = parts[0].strip()  # "Class 11" or "Class 12"
        subject = parts[1].strip()      # "Physics", "Chemistry", etc.
        
        # Determine which class
        class_key = PAYAL_CLASS_LABEL_TO_KEY.get(class_part)
        if not class_key:
            return jsonify({'success': False, 'error': 'Invalid class'}), 400
        
        # Get topics for this subject and class
        if subject not in PAYAL_SUBJECTS:
            return jsonify({'success': False, 'error': 'Invalid subject'}), 400
        
        topics = PAYAL_SUBJECTS[subject].get(class_key, [])
        
        return jsonify({
            'success': True,
            'topics': topics
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/ai/modules/<module_name>/topics', methods=['GET'])
@login_required
def get_ai_topics(module_name):
    """Get topics for a specific module in Shubham's generator"""
    if module_name not in SYLLABUS_MODULES:
        return jsonify({'success': False, 'error': 'Invalid module'}), 400
    
    topics = SYLLABUS_MODULES[module_name].get('topics', [])
    
    return jsonify({
        'success': True,
        'topics': topics
    })


@app.route('/api/ai/generate-cards', methods=['POST'])
@login_required
def generate_ai_cards():
    """Generate flashcards using Gemini API"""
    try:
        data = request.get_json()
        
        # Validate required fields
        deck_id = data.get('deck_id')
        module_name = data.get('module')
        count = data.get('count', 50)
        difficulty = data.get('difficulty', 'medium')
        topic_single = data.get('topic')
        topics_raw = data.get('topics')
        selected_topics = []

        if isinstance(topic_single, str) and topic_single.strip():
            selected_topics = [topic_single.strip()]
        elif isinstance(topics_raw, list):
            selected_topics = [t.strip() for t in topics_raw if isinstance(t, str) and t.strip()]
        elif isinstance(topics_raw, str) and topics_raw.strip():
            selected_topics = [topics_raw.strip()]
        
        if not deck_id or not module_name:
            return jsonify({
                'error': 'deck_id and module are required'
            }), 400
        
        # Verify user owns the deck
        deck = Deck.query.get_or_404(deck_id)
        if deck.user_id != current_user.id:
            return jsonify({
                'error': 'Unauthorized access to deck'
            }), 403
        
        # Initialize Gemini generator
        generator = GeminiFlashcardGenerator()
        
        # Log request details for debugging
        topics_for_log = selected_topics if selected_topics else 'All Topics'
        app.logger.info(f"Generating cards: module={module_name}, topics={topics_for_log}, count={count}, difficulty={difficulty}")

        topics_for_generation = selected_topics if selected_topics else None

        existing_questions = {
            _normalize_question(q[0])
            for q in db.session.query(Card.question).filter(Card.deck_id == deck_id)
        }
        duplicates_skipped = 0
        invalid_skipped = 0
        invalid_skipped = 0
        
        # Handle mixed difficulty
        if difficulty == 'mixed':
            # Generate cards with different difficulties (20% easy, 50% medium, 30% hard)
            total = count
            easy_count = max(1, int(total * 0.2))
            medium_count = max(1, int(total * 0.5))
            hard_count = total - easy_count - medium_count
            
            all_flashcards = []
            
            # Generate easy cards
            if easy_count > 0:
                app.logger.info(f"Generating {easy_count} easy cards")
                result = generator.generate_flashcards(module_name, topics_for_generation, easy_count, 'easy')
                if result.get('success'):
                    for card in result['cards']:
                        card['difficulty'] = 'easy'
                    all_flashcards.extend(result['cards'])
                else:
                    app.logger.error(f"Easy cards generation failed: {result.get('error')}")
            
            # Generate medium cards
            if medium_count > 0:
                app.logger.info(f"Generating {medium_count} medium cards")
                result = generator.generate_flashcards(module_name, topics_for_generation, medium_count, 'medium')
                if result.get('success'):
                    for card in result['cards']:
                        card['difficulty'] = 'medium'
                    all_flashcards.extend(result['cards'])
                else:
                    app.logger.error(f"Medium cards generation failed: {result.get('error')}")
            
            # Generate hard cards
            if hard_count > 0:
                app.logger.info(f"Generating {hard_count} hard cards")
                result = generator.generate_flashcards(module_name, topics_for_generation, hard_count, 'hard')
                if result.get('success'):
                    for card in result['cards']:
                        card['difficulty'] = 'hard'
                    all_flashcards.extend(result['cards'])
                else:
                    app.logger.error(f"Hard cards generation failed: {result.get('error')}")
            
            flashcards = all_flashcards
        else:
            # Generate flashcards with single difficulty
            result = generator.generate_flashcards(module_name, topics_for_generation, count, difficulty)
            
            if not result.get('success'):
                app.logger.error(f"Generation failed: {result.get('error')}")
                return jsonify({
                    'error': result.get('error', 'Failed to generate flashcards')
                }), 500
            
            flashcards = result.get('cards', [])
        
        # Insert generated cards into the deck
        cards_added = 0
        for flashcard_data in flashcards:
            # Validate card format - new format uses arrays directly
            options = flashcard_data.get('options')
            if not isinstance(options, list) or len(options) != 4:
                invalid_skipped += 1
                continue
            
            correct_answer = flashcard_data.get('correct_answer')
            if not isinstance(correct_answer, int) or correct_answer not in [0, 1, 2, 3]:
                invalid_skipped += 1
                continue
            
            question_text = flashcard_data.get('question', '')
            normalized_question = _normalize_question(question_text)
            if not normalized_question:
                invalid_skipped += 1
                continue
            if normalized_question in existing_questions:
                duplicates_skipped += 1
                continue
            existing_questions.add(normalized_question)
            
            card = Card(
                deck_id=deck_id,
                question=question_text,
                hint=flashcard_data.get('hint', ''),
                options=options,
                correct_answer=correct_answer,
                description=flashcard_data.get('description', ''),
                reference=flashcard_data.get('reference', ''),
                code=flashcard_data.get('code', ''),
                difficulty=flashcard_data.get('difficulty', difficulty if difficulty != 'mixed' else 'medium')
            )
            db.session.add(card)
            cards_added += 1
        
        db.session.commit()
        
        # Format topics for response
        topics_str = ', '.join(selected_topics) if selected_topics else 'All Topics'
        
        return jsonify({
            'success': True,
            'cards_generated': cards_added,
            'deck_id': deck_id,
            'deck_name': deck.name,
            'module': module_name,
            'topics': topics_str,
            'duplicates_skipped': duplicates_skipped,
            'invalid_skipped': invalid_skipped
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


@app.route('/api/ai/generate-cards-payal', methods=['POST'])
@login_required
def generate_ai_cards_payal():
    """Generate flashcards for Payal using Maharashtra Board context"""
    try:
        data = request.get_json()
        
        # Validate required fields
        deck_id = data.get('deck_id')
        module = data.get('module')  # e.g., "Class 11 - Physics"
        count = data.get('count', 10)
        difficulty = data.get('difficulty', 'medium')
        exam_focus = data.get('exam_focus', 'MHT-CET')  # MHT-CET, JEE, NEET
        topic_single = data.get('topic')
        topics_raw = data.get('topics', [])

        selected_topics = []
        if isinstance(topic_single, str) and topic_single.strip():
            selected_topics = [topic_single.strip()]
        elif isinstance(topics_raw, list):
            selected_topics = [t.strip() for t in topics_raw if isinstance(t, str) and t.strip()]
        elif isinstance(topics_raw, str) and topics_raw.strip():
            selected_topics = [topics_raw.strip()]
        
        if not deck_id or not module or not selected_topics:
            return jsonify({
                'error': 'deck_id, module, and topic are required'
            }), 400
        
        # Parse module name to extract subject
        # Format: "Class 11 - Physics" -> subject = "Physics"
        try:
            parts = module.split(' - ')
            if len(parts) != 2:
                raise ValueError("Invalid module format")
            subject = parts[1]  # e.g., "Physics"
        except:
            return jsonify({
                'error': 'Invalid module format. Expected "Class X - Subject"'
            }), 400
        
        # Verify user owns the deck
        deck = Deck.query.get_or_404(deck_id)
        if deck.user_id != current_user.id:
            return jsonify({
                'error': 'Unauthorized access to deck'
            }), 403
        
        # Initialize Payal's generator
        generator = PayalFlashcardGenerator()
        
        # Generate flashcards for all selected topics
        all_flashcards = []
        topics_count = len(selected_topics)
        base = count // topics_count if topics_count else 0
        remainder = count % topics_count if topics_count else 0
        
        for idx, topic in enumerate(selected_topics):
            topic_cards = base + (1 if idx < remainder else 0)
            if topics_count > count and idx >= count:
                topic_cards = 0
            if topic_cards <= 0:
                continue
            app.logger.info(f"Generating Payal's cards: subject={subject}, topic={topic}, count={topic_cards}, difficulty={difficulty}, exam={exam_focus}")
            
            # Generate flashcards for this topic
            flashcards = generator.generate_cards(
                topic=topic,
                subject=subject,
                num_cards=topic_cards,
                difficulty=difficulty,
                exam_focus=exam_focus
            )
            
            if flashcards:
                all_flashcards.extend(flashcards)
        
        if not all_flashcards:
            return jsonify({
                'error': 'Failed to generate flashcards. Please try again.'
            }), 500
        
        # Insert generated cards into the deck
        cards_added = 0
        duplicates_skipped = 0
        invalid_skipped = 0
        existing_questions = {
            _normalize_question(q[0])
            for q in db.session.query(Card.question).filter(Card.deck_id == deck_id)
        }
        for flashcard_data in all_flashcards:
            options = flashcard_data.get('options')
            correct_answer = flashcard_data.get('correct_answer')
            if not isinstance(options, list) or len(options) != 4 or not isinstance(correct_answer, int) or correct_answer not in [0, 1, 2, 3]:
                invalid_skipped += 1
                continue
            question_text = flashcard_data.get('question', '')
            normalized_question = _normalize_question(question_text)
            if not normalized_question:
                invalid_skipped += 1
                continue
            if normalized_question in existing_questions:
                duplicates_skipped += 1
                continue
            existing_questions.add(normalized_question)
            # Create card with Payal's format (no code field)
            card = Card(
                deck_id=deck_id,
                question=question_text,
                options=options,
                correct_answer=correct_answer,
                hint=flashcard_data.get('hint', ''),
                description=flashcard_data.get('explanation', ''),
                reference=flashcard_data.get('reference', ''),
                code='',  # Payal's cards have NO code
                difficulty=flashcard_data.get('difficulty', difficulty)
            )
            db.session.add(card)
            cards_added += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'cards_added': cards_added,
            'message': f'Successfully generated {cards_added} cards for {exam_focus} preparation',
            'duplicates_skipped': duplicates_skipped,
            'invalid_skipped': invalid_skipped,
            'topics': ', '.join(selected_topics),
            'duplicates_skipped': duplicates_skipped,
            'invalid_skipped': invalid_skipped
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error generating Payal's cards: {str(e)}")
        return jsonify({
            'error': f'Error generating cards: {str(e)}'
        }), 500


@app.route('/api/create-user-decks', methods=['POST'])
@login_required
def create_user_decks():
    """Create complete deck hierarchy for specific users (payal/shubham)"""
    try:
        username = current_user.username.lower()
        
        # Check if user is authorized
        if username not in ['payal', 'shubham']:
            return jsonify({
                'success': False,
                'error': 'This feature is only available for specific users'
            }), 403
        
        created_count = 0
        existing_count = 0

        def upsert_deck(name, parent_id=None, description=None, order_index=0, legacy_names=None):
            deck = Deck.query.filter_by(
                user_id=current_user.id,
                name=name,
                parent_id=parent_id
            ).first()

            if not deck and legacy_names:
                for legacy_name in legacy_names:
                    legacy_deck = Deck.query.filter_by(
                        user_id=current_user.id,
                        name=legacy_name,
                        parent_id=parent_id
                    ).first()
                    if legacy_deck:
                        legacy_deck.name = name
                        deck = legacy_deck
                        break

            created_local = False
            if not deck:
                deck = Deck(
                    name=name,
                    user_id=current_user.id,
                    parent_id=parent_id,
                    description=description,
                    display_order=order_index
                )
                db.session.add(deck)
                db.session.flush()
                created_local = True
            else:
                if deck.display_order != order_index:
                    deck.display_order = order_index
                if description and not deck.description:
                    deck.description = description

            return deck, created_local

        if username == 'payal':
            parent_order = 1
            for class_key in PAYAL_CLASS_ORDER:
                class_label = PAYAL_CLASS_LABELS.get(class_key, class_key.replace('_', ' ').title())
                for subject in PAYAL_SUBJECT_ORDER:
                    classes = PAYAL_SUBJECTS.get(subject, {})
                    topics = classes.get(class_key)
                    if not topics:
                        continue

                    parent_name = f"{class_label} - {subject}"
                    parent_desc = f"{subject} syllabus for {class_label}"
                    legacy_name = f"{subject} - {class_label}"
                    parent_deck, was_created = upsert_deck(
                        parent_name,
                        None,
                        parent_desc,
                        parent_order,
                        legacy_names=[legacy_name]
                    )
                    if was_created:
                        created_count += 1
                    else:
                        existing_count += 1

                    topic_order = 1
                    for topic in topics:
                        _, topic_created = upsert_deck(
                            topic,
                            parent_deck.id,
                            f"Topic: {topic}",
                            topic_order
                        )
                        if topic_created:
                            created_count += 1
                        else:
                            existing_count += 1
                        topic_order += 1

                    parent_order += 1

        elif username == 'shubham':
            parent_order = 1
            for module_name in SYLLABUS_MODULE_SEQUENCE:
                module_info = SYLLABUS_MODULES[module_name]
                parent_desc = module_info.get('description', f'{module_name} topics')
                parent_deck, was_created = upsert_deck(
                    module_name,
                    None,
                    parent_desc,
                    parent_order
                )
                if was_created:
                    created_count += 1
                else:
                    existing_count += 1

                topic_order = 1
                for topic in module_info.get('topics', []):
                    _, topic_created = upsert_deck(
                        topic,
                        parent_deck.id,
                        f"Topic: {topic}",
                        topic_order
                    )
                    if topic_created:
                        created_count += 1
                    else:
                        existing_count += 1
                    topic_order += 1

                parent_order += 1
        
        db.session.commit()
        
        if created_count == 0 and existing_count > 0:
            return jsonify({
                'success': True,
                'message': 'Decks and subdecks already present',
                'created': 0,
                'existing': existing_count
            })
        
        return jsonify({
            'success': True,
            'message': f'Successfully created {created_count} new decks/subdecks',
            'created': created_count,
            'existing': existing_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai/generate-cards-shubham', methods=['POST'])
@login_required
def generate_ai_cards_shubham():
    """Generate flashcards for Shubham (original format with code field)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        deck_id = data.get('deck_id')
        module_name = data.get('module')
        topics_raw = data.get('topics')
        topic_single = data.get('topic')
        count = data.get('count', 50)
        difficulty = data.get('difficulty', 'medium')
        selected_topics = []
        if isinstance(topic_single, str) and topic_single.strip():
            selected_topics = [topic_single.strip()]
        elif isinstance(topics_raw, list):
            selected_topics = [t.strip() for t in topics_raw if isinstance(t, str) and t.strip()]
        elif isinstance(topics_raw, str) and topics_raw.strip():
            selected_topics = [topics_raw.strip()]
        
        if not deck_id or not module_name:
            return jsonify({
                'error': 'deck_id and module are required'
            }), 400
        
        # Verify user owns the deck
        deck = Deck.query.get_or_404(deck_id)
        if deck.user_id != current_user.id:
            return jsonify({
                'error': 'Unauthorized access to deck'
            }), 403
        
        # Initialize Gemini generator (Shubham's format)
        generator = GeminiFlashcardGenerator()
        
        topics_for_generation = selected_topics[0] if len(selected_topics) == 1 else (selected_topics if selected_topics else None)
        topics_for_log = selected_topics if selected_topics else 'All Topics'
        app.logger.info(f"Generating Shubham's cards: module={module_name}, topics={topics_for_log}, count={count}, difficulty={difficulty}")
        
        # Generate flashcards with code field support
        result = generator.generate_flashcards(module_name, topics_for_generation, count, difficulty)
        
        if not result.get('success'):
            app.logger.error(f"Generation failed: {result.get('error')}")
            return jsonify({
                'error': result.get('error', 'Failed to generate flashcards')
            }), 500
        
        flashcards = result.get('cards', [])
        
        # Insert generated cards into the deck
        cards_added = 0
        duplicates_skipped = 0
        invalid_skipped = 0
        existing_questions = {
            _normalize_question(q[0])
            for q in db.session.query(Card.question).filter(Card.deck_id == deck_id)
        }
        for flashcard_data in flashcards:
            options = flashcard_data.get('options')
            correct_answer = flashcard_data.get('correct_answer')
            if not isinstance(options, list) or len(options) != 4 or not isinstance(correct_answer, int):
                invalid_skipped += 1
                continue
            question_text = flashcard_data.get('question', '')
            normalized_question = _normalize_question(question_text)
            if not normalized_question:
                invalid_skipped += 1
                continue
            if normalized_question in existing_questions:
                duplicates_skipped += 1
                continue
            existing_questions.add(normalized_question)
            # Create card with Shubham's format (includes code field)
            card = Card(
                deck_id=deck_id,
                question=question_text,
                options=options,
                correct_answer=correct_answer,
                hint=flashcard_data.get('hint', ''),
                description=flashcard_data.get('explanation', ''),
                code=flashcard_data.get('code', ''),  # Code field for programming questions
                reference=flashcard_data.get('reference', ''),
                difficulty=flashcard_data.get('difficulty', difficulty)
            )
            db.session.add(card)
            cards_added += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'cards_added': cards_added,
            'message': f'Successfully generated {cards_added} cards',
            'duplicates_skipped': duplicates_skipped,
            'invalid_skipped': invalid_skipped,
            'topics': ', '.join(selected_topics) if selected_topics else 'All Topics'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error generating Shubham's cards: {str(e)}")
        return jsonify({
            'error': f'Error generating cards: {str(e)}'
        }), 500


@app.route('/api/ai/generate-payal/<int:deck_id>', methods=['POST'])
@login_required
def generate_ai_cards_payal_deck(deck_id):
    """Generate flashcards for Payal with deck integration"""
    try:
        data = request.get_json()
        
        # Get parameters from request
        subject = data.get('module')  # Subject name (Physics, Chemistry, etc.)
        topic = data.get('topic')  # Optional specific topic
        num_cards = data.get('num_cards', 10)
        difficulty = data.get('difficulty', 'medium')
        
        if not subject:
            return jsonify({
                'success': False,
                'error': 'Subject (module) is required'
            }), 400
        
        # Verify user owns the deck
        deck = Deck.query.get_or_404(deck_id)
        if deck.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to deck'
            }), 403
        
        # Initialize Payal's generator
        generator = PayalFlashcardGenerator()
        
        app.logger.info(f"Generating Payal's cards: subject={subject}, topic={topic}, num_cards={num_cards}, difficulty={difficulty}")
        
        # Generate flashcards (NO code field)
        cards = generator.generate_cards(
            topic=topic if topic else f"General {subject}",
            subject=subject,
            num_cards=num_cards,
            difficulty=difficulty,
            exam_focus="MHT-CET"
        )
        
        # Insert generated cards into the deck
        cards_added = 0
        for card_data in cards:
            card = Card(
                deck_id=deck_id,
                question=card_data.get('question', ''),
                options=card_data.get('options', []),
                correct_answer=card_data.get('correct_answer', 0),
                hint=card_data.get('hint', ''),
                description=card_data.get('explanation', ''),
                code='',  # NO CODE FIELD for Payal
                reference=card_data.get('reference', ''),
                difficulty=card_data.get('difficulty', difficulty)
            )
            db.session.add(card)
            cards_added += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'cards_generated': cards_added,
            'message': f'Successfully generated {cards_added} cards for Payal'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error generating Payal's cards: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error generating cards: {str(e)}'
        }), 500


@app.route('/api/ai/generate-shubham/<int:deck_id>', methods=['POST'])
@login_required
def generate_ai_cards_shubham_deck(deck_id):
    """Generate flashcards for Shubham with deck integration"""
    try:
        data = request.get_json()
        
        # Get parameters from request
        module_name = data.get('module')
        topics = data.get('topic')  # Can be None for all topics
        num_cards = data.get('num_cards', 10)
        difficulty = data.get('difficulty', 'medium')
        
        if not module_name:
            return jsonify({
                'success': False,
                'error': 'Module is required'
            }), 400
        
        # Verify user owns the deck
        deck = Deck.query.get_or_404(deck_id)
        if deck.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to deck'
            }), 403
        
        # Initialize Shubham's generator
        generator = GeminiFlashcardGenerator()
        
        app.logger.info(f"Generating Shubham's cards: module={module_name}, topics={topics}, num_cards={num_cards}, difficulty={difficulty}")
        
        # Generate flashcards with code field
        result = generator.generate_flashcards(
            module_name=module_name,
            topics=[topics] if topics else None,
            count=num_cards,
            difficulty=difficulty
        )
        
        if not result.get('success'):
            app.logger.error(f"Generation failed: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to generate flashcards')
            }), 500
        
        flashcards = result.get('cards', [])
        
        # Insert generated cards into the deck
        cards_added = 0
        for card_data in flashcards:
            card = Card(
                deck_id=deck_id,
                question=card_data.get('question', ''),
                options=card_data.get('options', []),
                correct_answer=card_data.get('correct_answer', 0),
                hint=card_data.get('hint', ''),
                description=card_data.get('explanation', card_data.get('description', '')),
                code=card_data.get('code', ''),  # Code field for programming
                reference=card_data.get('reference', ''),
                difficulty=card_data.get('difficulty', difficulty)
            )
            db.session.add(card)
            cards_added += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'cards_generated': cards_added,
            'message': f'Successfully generated {cards_added} cards for Shubham'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error generating Shubham's cards: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error generating cards: {str(e)}'
        }), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
