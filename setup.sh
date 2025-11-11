#!/bin/bash

# Flashcard Flask - Quick Start Script

echo "🧠 Flashcard Flask - Quick Start"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment found"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the app: python app.py"
echo "  3. Open http://localhost:5000 in your browser"
echo ""
echo "Sample decks are available in the sample_decks/ directory"
echo "You can import them through the web interface"
echo ""
