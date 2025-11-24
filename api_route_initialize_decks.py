# Add this route to app.py after the other AI routes

@app.route('/api/ai/initialize-decks', methods=['POST'])
@login_required
def initialize_module_decks():
    """Initialize parent module decks with child subtopic decks"""
    try:
        from ai_generator import SYLLABUS_MODULES
        
        parent_decks_created = 0
        child_decks_created = 0
        
        for module_name, module_info in SYLLABUS_MODULES.items():
            # Create or get parent deck
            parent_deck = Deck.query.filter_by(
                user_id=current_user.id,
                name=module_name,
                parent_id=None
            ).first()
            
            if not parent_deck:
                parent_deck = Deck(
                    user_id=current_user.id,
                    name=module_name,
                    description=f"Module covering {module_info['hours']} hours of curriculum"
                )
                db.session.add(parent_deck)
                db.session.flush()
                parent_decks_created += 1
            
            # Create child decks for major subtopics (first 5-7 topics)
            topics = module_info['topics'][:7]  # Limit to first 7 major topics
            
            for topic in topics:
                # Check if child deck already exists
                child_deck = Deck.query.filter_by(
                    user_id=current_user.id,
                    name=topic,
                    parent_id=parent_deck.id
                ).first()
                
                if not child_deck:
                    child_deck = Deck(
                        user_id=current_user.id,
                        name=topic,
                        description=f"Subtopic of {module_name}",
                        parent_id=parent_deck.id
                    )
                    db.session.add(child_deck)
                    child_decks_created += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'decks_created': parent_decks_created + child_decks_created,
            'parent_decks': parent_decks_created,
            'child_decks': child_decks_created
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Failed to initialize decks: {str(e)}'
        }), 500
