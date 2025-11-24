# Dual AI Generator System - User Guide

## Overview

The flashcard app now has **TWO separate AI generators** for different study needs:

### 🎓 Payal's Generator (Maharashtra Board + Competitive Exams)
- **Purpose**: Academic MCQs for Maharashtra State Board students
- **Target Exams**: MHT-CET, JEE Main, NEET
- **Subjects**: Physics, Chemistry, Mathematics, Biology
- **Format**: Question, Hint, Difficulty, Options, Explanation, Reference
- **Special Feature**: NO code field - pure academic content

### 💻 Shubham's Generator (Programming & Technology)
- **Purpose**: Technical MCQs for programming and computer science
- **Subjects**: Linux, Python, R, Java, DBMS, Big Data, ML/DL, GenAI, etc.
- **Format**: Question, Code (optional), Options, Hint, Explanation, Reference, Difficulty
- **Special Feature**: Includes code field for programming examples

---

## How to Use

### Step 1: Open Your Deck
Navigate to any deck detail page where you can see your flashcards.

### Step 2: Choose Your Generator
You'll see **TWO blue buttons**:

1. **🎓 Generate AI Cards for Payal** (Blue)
   - Click this for academic subjects (Physics, Chemistry, Math, Biology)
   - Best for MHT-CET/JEE/NEET preparation
   
2. **💻 Generate AI Cards for Shubham** (Green)
   - Click this for programming and tech subjects
   - Best for coding practice and tech interviews

### Step 3: Select Subject/Module
- **For Payal**: Choose from Physics, Chemistry, Mathematics, or Biology
- **For Shubham**: Choose from Linux, Python, Java, DBMS, etc.

### Step 4: Choose Topic (Optional)
- **For Payal**: Select specific chapter (e.g., "Rotational Dynamics", "Chemical Bonding")
- **For Shubham**: Select specific topic (e.g., "Functions", "OOP Concepts")
- Leave blank to generate from all topics

### Step 5: Set Parameters
- **Number of Cards**: 1-100 (default: 10)
- **Difficulty**: Easy, Medium, or Hard

### Step 6: Generate!
Click "Generate" and wait. The AI will create customized MCQs based on your selection.

---

## Payal's Generator Details

### Subjects & Topics

#### Physics
**Class 11 Topics:**
- Units and Measurements, Mathematical Methods
- Motion in a Plane, Laws of Motion
- Gravitation, Mechanical Properties of Solids
- Thermal Properties, Sound, Optics
- Electrostatics, Current Electricity
- Magnetism, EM Waves, Semiconductors

**Class 12 Topics:**
- Rotational Dynamics, Fluid Mechanics
- Kinetic Theory & Radiation, Thermodynamics
- Oscillations, Wave Optics
- Electrostatics, Current Electricity
- Magnetic Fields, EM Induction
- AC Circuits, Dual Nature, Atomic Structure
- Semiconductor Devices

#### Chemistry
**Class 11 Topics:**
- Basic Concepts, Analytical Chemistry
- Atomic Structure, Chemical Bonding
- Redox Reactions, Periodic Table
- States of Matter, Chemical Equilibrium
- Organic Fundamentals, Hydrocarbons

**Class 12 Topics:**
- Solid State, Solutions, Ionic Equilibria
- Thermodynamics, Electrochemistry
- Chemical Kinetics, Transition Elements
- Coordination Compounds, Halogen Derivatives
- Alcohols/Phenols/Ethers, Aldehydes/Ketones
- Amines, Biomolecules, Polymers

#### Mathematics
**Class 11 Topics:**
- Trigonometry I & II, Matrices & Determinants
- Straight Line, Circle, Conic Sections
- Probability, Complex Numbers
- Sequences & Series, Permutations & Combinations
- Sets, Relations, Functions
- Limits, Differentiation

**Class 12 Topics:**
- Mathematical Logic, Matrices
- Trigonometric Functions, Vectors
- 3D Geometry, Line & Plane
- Linear Programming, Differentiation
- Applications of Derivatives
- Integration (Indefinite & Definite)
- Differential Equations, Probability Distributions

#### Biology
**Class 11 Topics:**
- Living World, Systematics
- Kingdom Plantae & Animalia
- Cell Structure, Biomolecules, Cell Division
- Plant & Animal Tissues
- Morphology, Cockroach Study
- Photosynthesis, Respiration
- Human Nutrition, Excretion

**Class 12 Topics:**
- Reproduction (Plants & Animals)
- Inheritance & Variation
- Molecular Basis of Inheritance, Evolution
- Plant Water Relations, Plant Growth
- Respiration & Circulation
- Control & Coordination
- Health & Diseases, Food Production
- Biotechnology, Ecosystems, Biodiversity

### Card Format (Payal)
```json
{
  "question": "What is the SI unit of force?",
  "options": [
    "Newton (N)",
    "Joule (J)",
    "Watt (W)",
    "Pascal (Pa)"
  ],
  "correct_answer": 0,
  "difficulty": "easy",
  "hint": "Think about $F = ma$ and the unit of mass times acceleration",
  "explanation": "Force = mass × acceleration. SI unit of mass is kg, acceleration is m/s². Therefore, force unit is kg⋅m/s² = Newton (N). $$F = ma = (kg)(m/s^2) = N$$",
  "reference": "Maharashtra Board Class 11 Physics Ch.3: Laws of Motion, NCERT Physics Part-I Section 5.3"
}
```

**Note**: NO `code` field in Payal's cards!

---

## Shubham's Generator Details

### Modules & Topics

Available modules include:
- **Linux**: Commands, Shell Scripting, System Administration
- **Python**: Basics, OOP, Data Structures, Libraries
- **R Programming**: Data Analysis, Statistics, Visualization
- **Java**: Core Java, OOP, Collections, Advanced Concepts
- **DBMS**: SQL, Normalization, Transactions, Indexing
- **Big Data**: Hadoop, Spark, Data Processing
- **Machine Learning**: Algorithms, Neural Networks, Deep Learning
- **GenAI**: LLMs, Transformers, Prompt Engineering

### Card Format (Shubham)
```json
{
  "question": "What does the following Python code output?",
  "code": "nums = [1, 2, 3]\nprint(nums * 2)",
  "options": [
    "[1, 2, 3, 1, 2, 3]",
    "[2, 4, 6]",
    "[1, 2, 3, 2]",
    "Error"
  ],
  "correct_answer": 0,
  "difficulty": "medium",
  "hint": "List multiplication in Python creates repetitions, not element-wise multiplication",
  "explanation": "In Python, `list * n` repeats the list n times. So `[1,2,3] * 2` creates `[1,2,3,1,2,3]`. For element-wise multiplication, use list comprehension or NumPy.",
  "reference": "Python Official Docs: Sequence Types - list"
}
```

**Note**: Shubham's cards INCLUDE the `code` field for programming examples!

---

## API Endpoints

### Payal's Endpoints
- `GET /api/ai/modules-payal` - Get available subjects
- `GET /api/ai/modules-payal/<subject>/topics` - Get topics for a subject
- `POST /api/ai/generate-payal/<deck_id>` - Generate cards for deck

### Shubham's Endpoints
- `GET /api/ai/modules` - Get available modules
- `GET /api/ai/modules/<module>/topics` - Get topics for a module
- `POST /api/ai/generate-shubham/<deck_id>` - Generate cards for deck

---

## Technical Implementation

### Files Modified/Created

1. **ai_generator_payal.py** (NEW)
   - `PayalFlashcardGenerator` class
   - `PAYAL_SUBJECTS` dictionary with Maharashtra Board syllabus
   - Academic-focused prompt engineering
   - NO code field in output

2. **app.py**
   - Imported `PayalFlashcardGenerator` and `PAYAL_SUBJECTS`
   - Added 6 new API endpoints (3 for Payal, 3 for Shubham)
   - Deck-specific generation routes

3. **templates/deck_detail.html**
   - Two-button interface (Payal vs Shubham)
   - Updated `openAIGeneratorModal(generatorType)` function
   - Modal title changes based on generator
   - API routing based on generator type

### JavaScript Flow

```javascript
// User clicks button
openAIGeneratorModal('payal') or openAIGeneratorModal('shubham')
  ↓
// Modal stores generator type
modal.dataset.generatorType = 'payal' or 'shubham'
  ↓
// Load appropriate modules
fetch('/api/ai/modules-payal') or fetch('/api/ai/modules')
  ↓
// User selects subject/module and topic
  ↓
// Generate cards
fetch(`/api/ai/generate-payal/${deckId}`) or 
fetch(`/api/ai/generate-shubham/${deckId}`)
  ↓
// Cards inserted into deck (with or without code field)
```

---

## Math & Code Rendering

Both generators support:

### Math Rendering (LaTeX with KaTeX)
- **Inline Math**: `$E = mc^2$` → $E = mc^2$
- **Display Math**: `$$x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$$` → Centered equation

### Code Rendering
- **Inline Code**: `` `variable` `` → `variable`
- **Code Blocks**:
  ```
  ```python
  def hello():
      print("Hello, World!")
  ```
  ```

---

## Tips for Best Results

### For Payal's Generator:
1. **Be Specific**: Choose exact topics for focused practice
2. **Exam Focus**: Generator automatically aligns with MHT-CET/JEE/NEET patterns
3. **Difficulty Levels**:
   - Easy: Direct recall, NCERT Level 1
   - Medium: Application-based, typical exam questions
   - Hard: Advanced application, JEE/NEET advanced level
4. **Math Notation**: Cards use proper LaTeX formatting for formulas

### For Shubham's Generator:
1. **Code Examples**: Most cards include code snippets
2. **Practical Focus**: Questions test actual programming knowledge
3. **Multiple Topics**: Can select specific topics or generate from all
4. **Language-Specific**: Questions are tailored to the selected language

---

## Troubleshooting

### Generator Not Loading Subjects
- Check if Flask server is running
- Verify GEMINI_API_KEY is set in environment
- Check browser console for API errors

### No Cards Generated
- Ensure you selected a subject/module
- Check if number of cards is between 1-100
- Verify you have permission to edit the deck

### Wrong Generator Used
- Pay attention to button colors (Blue = Payal, Green = Shubham)
- Modal title shows which generator is active
- Generated cards will reflect the selected generator's format

---

## Future Enhancements

Potential improvements:
- [ ] Add more exam focus options (NEET-only, JEE-only, Board-only)
- [ ] Custom difficulty distribution
- [ ] Bulk topic selection
- [ ] Preview cards before adding to deck
- [ ] Export generated cards to PDF
- [ ] Add more programming languages to Shubham's generator

---

## Contact & Support

For issues or feature requests, please check:
- DEVELOPMENT.md - Development guidelines
- FEATURE_GUIDE.md - Feature documentation
- USER_GUIDE.md - General user guide

---

**Last Updated**: January 2025
**Version**: 2.0 - Dual Generator System
