# Flashcard Flask - User Guide

## Quick Start

### Setup

1. **Run the setup script** (macOS/Linux):
   ```bash
   ./setup.sh
   ```

   Or manually:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start the application**:
   ```bash
   python app.py
   ```

3. **Open your browser** to `http://localhost:5000`

## Features Guide

### 1. Importing Decks

- Click "Import" in the navigation
- Upload a JSON file following the format shown
- Sample decks are provided in `sample_decks/`:
  - `python_fundamentals.json` - Python programming concepts
  - `web_development.json` - HTML, CSS, JavaScript basics

### 2. Studying Cards

**Starting a Study Session:**
- From the home page, click "Study Now" on any deck with due cards
- Cards are presented one at a time

**Answering Questions:**
- For multiple choice: Click your answer
- The app shows if you're correct and displays the explanation
- For open-ended cards: Click "Show Answer" when ready

**Rating Your Recall:**
After seeing the answer, rate how well you knew it:
- **Again** - Didn't remember at all (card resets, review in 10 minutes)
- **Hard** - Difficult to recall (shorter review interval)
- **Good** - Recalled correctly (normal progression)
- **Easy** - Very easy to recall (longest interval)

### 3. Spaced Repetition Algorithm

The app uses the SM-2 algorithm (similar to Anki):

**Card States:**
- **New** - Never studied before
- **Learning** - Currently being learned
- **Review** - In the review cycle
- **Mastered** - Consistently remembered (21+ day intervals)

**How It Works:**
1. New cards start with short intervals (1 day)
2. Each successful review increases the interval
3. Failed reviews reset the card to learning mode
4. The ease factor adjusts based on your performance
5. Cards become "mastered" after consistent success

**Interval Examples:**
- Again: Review in 10 minutes
- Hard: ~1 day (reduced interval)
- Good: 1→6→15→37 days (normal progression)
- Easy: 4→10→26→67 days (accelerated)

### 4. Statistics

View your progress:
- Total decks and cards
- Daily review count
- Accuracy percentage
- 30-day review history chart
- Recent study sessions

### 5. Deck Management

- View individual deck statistics
- See breakdown of cards by state
- Check how many cards are due
- Delete decks you no longer need

## Creating Custom Decks

### JSON Format

```json
{
  "name": "Deck Name",
  "description": "Optional description",
  "cards": [
    {
      "question": "Your question here",
      "hint": "Optional hint",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "correct_answer": 1,
      "description": "Explanation after answering",
      "reference": "https://optional-link.com",
      "code": "optional code snippet"
    }
  ]
}
```

### Field Details

**Required:**
- `question` - The question text
- For multiple choice: `options` array and `correct_answer` index

**Optional:**
- `hint` - Helpful hint (hidden by default)
- `description` - Detailed explanation shown after answering
- `reference` - URL or reference link
- `code` - Code snippet with syntax highlighting

### Tips for Creating Cards

1. **Keep questions focused** - One concept per card
2. **Add context** - Use hints and descriptions liberally
3. **Include examples** - Code snippets help understanding
4. **Mix difficulty** - Some easy cards for confidence, some challenging
5. **Update regularly** - Remove outdated information

## Dark Mode

- Toggle between light and dark themes using the moon/sun icon
- Preference is saved in browser localStorage
- All code blocks optimized for dark mode

## Study Best Practices

1. **Study daily** - Even 10-15 minutes helps retention
2. **Be honest with ratings** - Accurate ratings improve scheduling
3. **Review explanations** - Don't skip the learning part
4. **Don't cram** - Trust the spaced repetition algorithm
5. **Focus on understanding** - Not just memorization

## Database

- Uses SQLite (file: `instance/flashcards.db`)
- All progress is automatically saved
- Backup the `instance/` folder to preserve your data
- Database is created automatically on first run

## Deployment

### Local Network
```bash
python app.py --host 0.0.0.0
```

### Production

For production deployment, consider:

1. **Heroku**:
   - Add `Procfile`: `web: gunicorn app:app`
   - Add `gunicorn` to requirements.txt
   - Set `SECRET_KEY` environment variable

2. **Railway/Render**:
   - Connect your GitHub repository
   - Set environment variables
   - Deploy automatically

3. **PythonAnywhere**:
   - Upload files via web interface
   - Configure WSGI
   - Set up virtual environment

## Troubleshooting

**Database not created:**
- Ensure `instance/` directory exists
- Check file permissions

**Import fails:**
- Verify JSON syntax (use a JSON validator)
- Check all required fields are present

**Cards not showing:**
- Check if cards are due (may need to wait for schedule)
- Verify deck has cards

**Dark mode not persisting:**
- Check browser localStorage is enabled
- Try clearing browser cache

## Advanced Usage

### Custom Configuration

Edit `config.py` to customize:
- Cards per session
- New cards per day
- Spaced repetition intervals
- Ease factor settings

### Backup Your Data

```bash
# Backup database
cp instance/flashcards.db backup_$(date +%Y%m%d).db

# Restore from backup
cp backup_20250101.db instance/flashcards.db
```

### Export Progress (Future Feature)

Currently, progress is stored in SQLite. You can access it directly:

```python
import sqlite3
conn = sqlite3.connect('instance/flashcards.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM card_progress")
# Process your data
```

## Contributing

Feel free to extend this app:
- Add more deck formats (CSV, Markdown)
- Implement deck sharing
- Add image support for cards
- Create mobile app version
- Add study streaks and achievements

## License

MIT License - Feel free to modify and distribute
