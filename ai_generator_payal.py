"""
AI Flashcard Generator for Payal
Specialized for Maharashtra State Board (Class 11 & 12)
Exam Focus: MHT-CET, JEE, NEET
"""

from typing import Dict, List, Optional
import google.generativeai as genai
import os
import json

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Payal's Subject Structure
PAYAL_SUBJECTS = {
    "Physics": {
        "class_11": [
            "Units and Measurements",
            "Mathematical Methods",
            "Motion in a Plane",
            "Laws of Motion",
            "Gravitation",
            "Mechanical Properties of Solids",
            "Thermal Properties of Matter",
            "Sound",
            "Optics",
            "Electrostatics",
            "Current Electricity",
            "Magnetism",
            "Electromagnetic Waves",
            "Semiconductors"
        ],
        "class_12": [
            "Rotational Dynamics",
            "Mechanical Properties of Fluids",
            "Kinetic Theory of Gases and Radiation",
            "Thermodynamics",
            "Oscillations",
            "Superposition of Waves",
            "Wave Optics",
            "Electrostatics",
            "Current Electricity",
            "Magnetic Fields",
            "Magnetic Materials",
            "Electromagnetic Induction",
            "AC Circuits",
            "Dual Nature of Radiation and Matter",
            "Structure of Atoms and Nuclei",
            "Semiconductor Devices"
        ]
    },
    "Chemistry": {
        "class_11": [
            "Basic Concepts of Chemistry",
            "Analytical Chemistry",
            "Atomic Structure",
            "Chemical Bonding",
            "Redox Reactions",
            "Periodic Table",
            "States of Matter",
            "Chemical Equilibrium",
            "Organic Chemistry Fundamentals",
            "Hydrocarbons",
            "Chemistry in Daily Life"
        ],
        "class_12": [
            "Solid State",
            "Solutions",
            "Ionic Equilibria",
            "Chemical Thermodynamics",
            "Electrochemistry",
            "Chemical Kinetics",
            "Transition and Inner Transition Elements",
            "Coordination Compounds",
            "Halogen Derivatives",
            "Alcohols, Phenols and Ethers",
            "Aldehydes, Ketones and Carboxylic Acids",
            "Amines",
            "Biomolecules",
            "Polymers"
        ]
    },
    "Mathematics": {
        "class_11": [
            "Trigonometry - I",
            "Trigonometry - II",
            "Determinants and Matrices",
            "Straight Line",
            "Circle",
            "Conic Sections",
            "Probability",
            "Complex Numbers",
            "Sequences and Series",
            "Permutations and Combinations",
            "Sets and Relations",
            "Functions",
            "Limits",
            "Differentiation"
        ],
        "class_12": [
            "Mathematical Logic",
            "Matrices",
            "Trigonometric Functions",
            "Pair of Straight Lines",
            "Vectors",
            "Three Dimensional Geometry",
            "Line and Plane",
            "Linear Programming",
            "Differentiation",
            "Applications of Derivative",
            "Indefinite Integration",
            "Definite Integration",
            "Differential Equations",
            "Probability Distributions",
            "Binomial Distribution"
        ]
    },
    "Biology": {
        "class_11": [
            "Living World",
            "Systematics of Living Organisms",
            "Kingdom Plantae",
            "Kingdom Animalia",
            "Cell Structure and Organization",
            "Biomolecules",
            "Cell Division",
            "Plant Tissues and Anatomy",
            "Morphology of Flowering Plants",
            "Animal Tissues",
            "Study of Cockroach",
            "Photosynthesis",
            "Respiration and Energy Transfer",
            "Human Nutrition",
            "Excretion and Osmoregulation",
            "Skeleton and Movement"
        ],
        "class_12": [
            "Reproduction in Lower and Higher Plants",
            "Reproduction in Lower and Higher Animals",
            "Inheritance and Variation",
            "Molecular Basis of Inheritance",
            "Origin and Evolution of Life",
            "Plant Water Relations",
            "Plant Growth and Mineral Nutrition",
            "Respiration and Circulation",
            "Control and Coordination",
            "Human Health and Diseases",
            "Enhancement in Food Production",
            "Biotechnology",
            "Organisms and Populations",
            "Ecosystems and Energy Flow",
            "Biodiversity and Conservation"
        ]
    }
}

# Maharashtra Board Class 11 & 12 Syllabus Context
MAHARASHTRA_SYLLABUS_CONTEXT = """
PAYAL'S ACADEMIC PROFILE:
- Board: Maharashtra State Board of Secondary and Higher Secondary Education
- Current Level: Class 11 & 12 (FYJC & SYJC) - Science Stream
- Target Exams: MHT-CET, JEE Main, NEET

SYLLABUS COVERAGE:
Class 11 (FYJC):
- Physics: Units & Measurements, Mathematical Methods, Motion in Plane, Laws of Motion, Gravitation, Mechanical Properties of Solids, Thermal Properties, Sound, Optics, Electrostatics, Current Electricity, Magnetism, EM Waves, Semiconductors
- Chemistry: Basic Concepts, Analytical Chemistry, Analytical Techniques, Atomic Structure, Chemical Bonding, Redox Reactions, Periodic Table, Groups 1-2-13-14-15, States of Matter, Adsorption & Colloids, Chemical Equilibrium, Nuclear Chemistry, Organic Chemistry Basics, Hydrocarbons, Chemistry in Daily Life
- Mathematics: Trigonometry (I & II), Determinants & Matrices, Straight Line, Circle, Conic Sections, Measures of Dispersion, Probability, Complex Numbers, Sequences & Series, Permutations & Combinations, Binomial Theorem, Sets & Relations, Functions, Limits, Continuity, Differentiation
- Biology: Living World, Systematics, Kingdom Plantae, Kingdom Animalia, Cell Structure, Biomolecules, Cell Division, Plant & Animal Tissues, Morphology, Cockroach Study, Photosynthesis, Respiration, Human Nutrition, Excretion, Skeleton & Movement

Class 12 (SYJC):
- Physics: Rotational Dynamics, Mechanical Properties of Fluids, Kinetic Theory & Radiation, Thermodynamics, Oscillations, Superposition of Waves, Wave Optics, Electrostatics, Current Electricity, Magnetic Fields, Magnetic Materials, EM Induction, AC Circuits, Dual Nature, Atomic & Nuclear Structure, Semiconductor Devices
- Chemistry: Solid State, Solutions, Ionic Equilibria, Chemical Thermodynamics, Electrochemistry, Chemical Kinetics, Groups 16-17-18, Transition & Inner Transition Elements, Coordination Compounds, Halogen Derivatives, Alcohols/Phenols/Ethers, Aldehydes/Ketones/Carboxylic Acids, Amines, Biomolecules, Polymers, Green Chemistry & Nanochemistry
- Mathematics: Mathematical Logic, Matrices, Trigonometric Functions, Pair of Straight Lines, Vectors, Line & Plane, Linear Programming, Differentiation, Applications of Derivatives, Integration (Indefinite & Definite), Differential Equations, Probability Distributions, Binomial Distribution
- Biology: Reproduction in Plants & Animals, Inheritance & Variation, Molecular Basis of Inheritance, Evolution, Plant Water Relations, Plant Growth & Mineral Nutrition, Respiration & Circulation, Control & Coordination, Health & Diseases, Food Production Enhancement, Biotechnology, Organisms & Populations, Ecosystems, Biodiversity & Conservation

EXAM-SPECIFIC FOCUS:
MHT-CET: Maharashtra State Board syllabus, application-based, MCQs, moderate difficulty
JEE Main: NCERT + advanced concepts, problem-solving, numerical ability, moderate to hard
NEET: Biology-heavy, NCERT-based, conceptual + application, moderate difficulty
"""


class PayalFlashcardGenerator:
    """Generate exam-focused MCQs for Payal's preparation"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def generate_cards(
        self, 
        topic: str, 
        subject: str,
        num_cards: int = 10,
        difficulty: str = "medium",
        exam_focus: str = "MHT-CET"
    ) -> List[Dict]:
        """
        Generate flashcards for Payal
        
        Args:
            topic: Specific topic (e.g., "Rotational Dynamics", "Chemical Bonding")
            subject: Subject name (Physics, Chemistry, Mathematics, Biology)
            num_cards: Number of cards to generate
            difficulty: easy, medium, or hard
            exam_focus: MHT-CET, JEE, or NEET
        
        Returns:
            List of flashcard dictionaries
        """
        
        prompt = f"""
{MAHARASHTRA_SYLLABUS_CONTEXT}

Generate {num_cards} high-quality Multiple Choice Questions (MCQs) for Payal.

TOPIC: {topic}
SUBJECT: {subject}
DIFFICULTY: {difficulty}
EXAM FOCUS: {exam_focus}

CRITICAL REQUIREMENTS:
1. Questions MUST be aligned with Maharashtra State Board curriculum
2. Questions MUST be relevant for {exam_focus} exam pattern
3. For Physics/Chemistry: Include numerical/application-based questions
4. For Biology: Focus on conceptual understanding and diagrams/processes
5. For Mathematics: Include formula-based and problem-solving questions
6. Use proper scientific notation and mathematical symbols (use LaTeX format with $ signs)
7. Include helpful hints that guide without giving away the answer
8. Provide detailed explanations with step-by-step solutions
9. Add reliable reference sources (textbook chapters, NCERT sections, etc.)

DIFFICULTY GUIDELINES:
- Easy: Direct recall, basic concepts, NCERT Level 1
- Medium: Application-based, 2-step problems, typical exam questions
- Hard: Advanced application, multi-concept, JEE/NEET advanced level

OUTPUT FORMAT (JSON):
Return ONLY a valid JSON array with this EXACT structure:
[
  {{
    "question": "Clear, concise question with proper formatting. Use $formula$ for math (e.g., $F = ma$)",
    "options": [
      "Option A - First choice",
      "Option B - Second choice", 
      "Option C - Third choice",
      "Option D - Fourth choice"
    ],
    "correct_answer": 0,
    "difficulty": "{difficulty}",
    "hint": "Helpful hint without revealing answer. Can use $math$ notation.",
    "explanation": "Detailed step-by-step explanation. Use $$formula$$ for block equations. Show all working for numerical problems.",
    "reference": "Maharashtra Board Class X Physics Ch.Y, NCERT Physics Part-I Section Z"
  }}
]

IMPORTANT FORMATTING RULES:
- Use $ for inline math: $E = mc^2$
- Use $$ for block equations: $$x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$$
- Escape backslashes in LaTeX: \\frac, \\sqrt, \\pi, etc.
- correct_answer is 0-indexed (0=A, 1=B, 2=C, 3=D)
- NO code blocks, NO programming questions
- Focus on Physics/Chemistry/Biology/Mathematics academic content

Generate {num_cards} questions now:
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=8192,
                )
            )
            
            # Extract JSON from response
            content = response.text.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()
            
            # Parse JSON
            cards = json.loads(content)
            
            # Validate and clean cards
            validated_cards = []
            for card in cards:
                if self._validate_card(card):
                    validated_cards.append(self._clean_card(card))
            
            return validated_cards
            
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response: {content[:500]}")
            return []
        except Exception as e:
            print(f"Generation Error: {e}")
            return []
    
    def _validate_card(self, card: Dict) -> bool:
        """Validate card has required fields"""
        required = ['question', 'options', 'correct_answer', 'difficulty', 'explanation']
        
        if not all(key in card for key in required):
            return False
        
        if not isinstance(card['options'], list) or len(card['options']) != 4:
            return False
        
        if not isinstance(card['correct_answer'], int) or card['correct_answer'] not in [0, 1, 2, 3]:
            return False
        
        return True
    
    def _clean_card(self, card: Dict) -> Dict:
        """Clean and standardize card format"""
        return {
            'question': card['question'].strip(),
            'options': [opt.strip() for opt in card['options']],
            'correct_answer': card['correct_answer'],
            'difficulty': card.get('difficulty', 'medium').lower(),
            'hint': card.get('hint', '').strip(),
            'explanation': card.get('explanation', '').strip(),
            'reference': card.get('reference', '').strip()
        }
    
    def generate_topic_based_cards(
        self,
        subject: str,
        class_level: str,  # "11" or "12"
        chapter: str,
        num_cards: int = 15,
        exam_focus: str = "MHT-CET"
    ) -> List[Dict]:
        """
        Generate comprehensive chapter-wise questions
        
        Args:
            subject: Physics/Chemistry/Mathematics/Biology
            class_level: "11" or "12"
            chapter: Chapter name from Maharashtra Board
            num_cards: Total cards to generate
            exam_focus: MHT-CET/JEE/NEET
        """
        
        # Distribute difficulty
        easy = num_cards // 3
        medium = num_cards // 3
        hard = num_cards - (easy + medium)
        
        all_cards = []
        
        # Generate easy questions
        if easy > 0:
            cards = self.generate_cards(
                topic=chapter,
                subject=subject,
                num_cards=easy,
                difficulty="easy",
                exam_focus=exam_focus
            )
            all_cards.extend(cards)
        
        # Generate medium questions
        if medium > 0:
            cards = self.generate_cards(
                topic=chapter,
                subject=subject,
                num_cards=medium,
                difficulty="medium",
                exam_focus=exam_focus
            )
            all_cards.extend(cards)
        
        # Generate hard questions
        if hard > 0:
            cards = self.generate_cards(
                topic=chapter,
                subject=subject,
                num_cards=hard,
                difficulty="hard",
                exam_focus=exam_focus
            )
            all_cards.extend(cards)
        
        return all_cards


# Quick test function
if __name__ == "__main__":
    generator = PayalFlashcardGenerator()
    
    # Test generation
    cards = generator.generate_cards(
        topic="Rotational Dynamics",
        subject="Physics",
        num_cards=3,
        difficulty="medium",
        exam_focus="MHT-CET"
    )
    
    print(json.dumps(cards, indent=2))
