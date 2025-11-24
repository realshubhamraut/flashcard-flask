# AI Flashcard Generation - Setup Guide

## What's Been Implemented

### 1. Files Created:
- `/ai_generator.py` - Gemini AI integration with syllabus modules
- `/static/js/ai_generator.js` - Frontend JavaScript for AI generation
- `/api_route_initialize_decks.py` - Route code to add to app.py

### 2. What You Need to Do:

#### Step 1: Add the Initialize Decks Route to app.py

Open `app.py` and add this route after the other AI routes (around line 1180):

```python
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
            
            # Create child decks for major subtopics (first 7 topics)
            topics = module_info['topics'][:7]
            
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
```

#### Step 2: Fix the JavaScript in deck_detail.html

Find the `<script>` section at the bottom of `templates/deck_detail.html` and **replace** the loadModules and onModuleChange functions with:

```javascript
function loadModules() {
    fetch('/api/ai/modules')
        .then(response => response.json())
        .then(data => {
            const moduleSelect = document.getElementById('ai-module-select');
            moduleSelect.innerHTML = '<option value="">Select a module...</option>';
            
            if (data.success && data.modules) {
                data.modules.forEach(module => {
                    const option = document.createElement('option');
                    option.value = module.name;
                    option.textContent = module.name;
                    option.dataset.topics = JSON.stringify(module.topics);
                    moduleSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading modules:', error);
            alert('Failed to load modules. Please try again.');
        });
}

function onModuleChange() {
    const moduleSelect = document.getElementById('ai-module-select');
    const topicSelect = document.getElementById('ai-topic-select');
    const selectedOption = moduleSelect.options[moduleSelect.selectedIndex];
    
    topicSelect.innerHTML = '<option value="">All topics (general overview)</option>';
    
    if (selectedOption && selectedOption.dataset.topics) {
        const topics = JSON.parse(selectedOption.dataset.topics);
        topics.forEach(topic => {
            const option = document.createElement('option');
            option.value = topic;
            option.textContent = topic;
            topicSelect.appendChild(option);
        });
    }
}
```

#### Step 3: Add Initialize Button to index.html

In `templates/index.html`, find the "Create New Deck" button and add this button next to it:

```html
<button onclick="initializeModuleDecks()" class="btn btn-secondary" id="init-decks-btn" style="margin-left: 1rem;">
    🚀 Initialize Module Decks
</button>
```

Then at the bottom of index.html before `{% endblock %}`, add:

```html
<script src="{{ url_for('static', filename='js/ai_generator.js') }}"></script>
```

#### Step 4: Test the App

1. Restart Flask:
```bash
python app.py
```

2. Open http://127.0.0.1:5000

3. Click "🚀 Initialize Module Decks" button - this will create:
   - 8 parent module decks
   - ~50 child subtopic decks

4. Open any deck and click "🤖 Generate AI Cards"
   - You should now see module names (not [object Object])
   - Select a module and topic
   - Click Generate

## Summary

This creates a complete hierarchical deck structure:

**Parent Decks (8):**
1. Linux Programming and Cloud Computing
2. Python and R Programming
3. Java Programming
4. Advanced Analytics using Statistics
5. Data Collection and DBMS
6. Big Data Technologies
7. Data Visualization
8. Practical Machine Learning

**Child Decks (~7 per parent = ~56 total):**
Each parent has subtopic decks from the syllabus topics.

**AI Generation:**
- Works with any deck
- Generates 1-100 cards per request
- Uses Gemini 1.5 Flash
- Creates MCQ cards with code examples
- Quality explanations

## Troubleshooting

If you see "[object Object]":
- Check that you updated the loadModules() function
- Clear browser cache (Cmd+Shift+R)

If module initialization fails:
- Check that the route was added to app.py
- Verify imports at top of app.py include: `from ai_generator import SYLLABUS_MODULES`
