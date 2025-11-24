# MemFlash - AI-Powered Flashcard App

A full-stack flashcard web application built with Python and Flask. Features AI-powered card generation using Google Gemini API.

## Features

- 🤖 **AI Card Generation** - Generate flashcards using Google Gemini API
- 👤 **User Authentication** - Login/logout with isolated user data
- 📚 **Deck Management** - Import quiz decks from JSON files or generate with AI
- 💡 **Rich Question Format** - Support for hints, explanations, references, and code snippets
- 🎨 **Syntax Highlighting** - Code snippets with proper highlighting
- 🌙 **Dark Mode** - Toggle between light and dark themes
- 📊 **Statistics** - Track daily reviews and accuracy
- 💾 **Progress Tracking** - SQLite database stores all user progress
- 📱 **Responsive Design** - Works on desktop and mobile
- 🎯 **Clean UI** - Modern design with Inter, Source Serif 4, and JetBrains Mono fonts

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python app.py
   ```
2. Open your browser to `http://localhost:5000`
3. Register a new user account
4. Login with your credentials
5. Import a deck from JSON or use the sample deck
6. Start studying!

Each user has their own isolated decks and progress tracking.

## AI-Powered Flashcard Generation

This app includes AI-powered flashcard generation using Google Gemini API.

### Setup Gemini API Key

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set the environment variable:

**Local Development:**
```bash
export GEMINI_API_KEY='your-api-key-here'
```

**On Render (Production):**
1. Go to your Render dashboard
2. Select your web service
3. Go to "Environment" tab
4. Add environment variable:
   - Key: `GEMINI_API_KEY`
   - Value: Your Gemini API key
5. Save changes (app will redeploy automatically)

### Using AI Generation

1. Open any deck
2. Click "🤖 Generate AI Cards" button
3. Select a module from the syllabus (e.g., "Big Data Technologies")
4. Optionally select a specific topic
5. Choose number of cards (up to 100)
6. Select difficulty level
7. Click "Generate" and wait for AI to create the cards

The AI will generate high-quality flashcards with:
- Multiple choice questions
- Code examples (where applicable)
- Detailed explanations
- Appropriate difficulty level

## JSON Deck Format

### Simple Format (Array of Cards):
```json
[
  {
    "question": "What is the output of the following code?",
    "code": "print(len(list(range(1, 6, 2))))",
    "hint": "Check how range works with step.",
    "options": ["1", "2", "3", "Error"],
    "correct_answer": "3",
    "description": "range(1, 6, 2) yields 1, 3, 5; len is 3.",
    "reference": "https://docs.python.org/3/library/stdtypes.html"
  }
]
```

### Full Format (With Deck Metadata):
```json
{
  "name": "Deck Name",
  "description": "Deck description",
  "cards": [
    {
      "question": "What is Python?",
      "hint": "It's a programming language",
      "options": ["A snake", "A programming language", "A framework", "A database"],
      "correct_answer": 1,
      "description": "Python is a high-level programming language...",
      "reference": "https://python.org",
      "code": "print('Hello, World!')"
    }
  ]
}
```

**Note**: `correct_answer` can be either:
- An integer index (0, 1, 2, 3) 
- The exact string of the correct option

## Rating System

- **Again** - Completely forgot, reset the card
- **Hard** - Difficult to recall, reduce interval
- **Good** - Recalled correctly, normal interval
- **Easy** - Very easy to recall, increase interval significantly

## Deployment

For free deployment options suitable for <10 users, see [DEPLOYMENT.md](DEPLOYMENT.md).

Recommended platforms:
- **Render.com** (recommended) - Free tier, auto-sleep after 15min
- **PythonAnywhere** - Always on, free tier available
- **Fly.io** - Fast, generous free tier
- **Railway.app** - $5/month credit

See the deployment guide for detailed setup instructions.

## License

MIT License
