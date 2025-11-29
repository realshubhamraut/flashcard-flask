"""
AI Flashcard Generator for Payal
Specialized for Maharashtra State Board (Class 11 & 12)
Exam Focus: MHT-CET, JEE, NEET
"""

from typing import Dict, List, Optional
import importlib.metadata as _std_metadata
try:
    import importlib_metadata as _backport_metadata
except ImportError:  # pragma: no cover - optional dependency
    _backport_metadata = None
import os
import json
import re

# Compat shim for Python <3.10 where packages_distributions is missing
if not hasattr(_std_metadata, 'packages_distributions'):
    if _backport_metadata and hasattr(_backport_metadata, 'packages_distributions'):
        _std_metadata.packages_distributions = _backport_metadata.packages_distributions  # type: ignore[attr-defined]
    else:
        def _empty_packages_distributions():
            return {}

        _std_metadata.packages_distributions = _empty_packages_distributions  # type: ignore[attr-defined]

import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

PAYAL_CLASS_LABELS = {
    "class_11": "Class 11",
    "class_12": "Class 12"
}

PAYAL_CLASS_ORDER = ["class_11", "class_12"]

PAYAL_CLASS_LABEL_TO_KEY = {label: key for key, label in PAYAL_CLASS_LABELS.items()}

PAYAL_SUBJECT_ORDER = [
    "Physics",
    "Chemistry",
    "Mathematics",
    "Biology"
]

# Payal's Subject Structure (textbook order)
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
            "Electric Current Through Conductors",
            "Magnetism",
            "Electromagnetic Waves and Communication System",
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
            "Magnetic Fields due to Electric Current",
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
            "Some Basic Concepts of Chemistry",
            "Introduction to Analytical Chemistry",
            "Basic Analytical Techniques",
            "Structure of Atom",
            "Chemical Bonding",
            "Redox Reactions",
            "Modern Periodic Table",
            "Elements of Group 1 and 2",
            "Elements of Group 13, 14 and 15",
            "States of Matter",
            "Adsorption and Colloids",
            "Chemical Equilibrium",
            "Nuclear Chemistry and Radioactivity",
            "Basic Principles of Organic Chemistry",
            "Hydrocarbons",
            "Chemistry in Everyday Life"
        ],
        "class_12": [
            "Solid State",
            "Solutions",
            "Ionic Equilibria",
            "Chemical Thermodynamics",
            "Electrochemistry",
            "Chemical Kinetics",
            "Elements of Groups 16, 17 and 18",
            "Transition and Inner Transition Elements",
            "Coordination Compounds",
            "Halogen Derivatives",
            "Alcohols, Phenols and Ethers",
            "Aldehydes, Ketones and Carboxylic Acids",
            "Amines",
            "Biomolecules",
            "Introduction to Polymer Chemistry",
            "Green Chemistry and Nanochemistry"
        ]
    },
    "Mathematics": {
        "class_11": [
            "Angle and its Measurement",
            "Trigonometry - I",
            "Trigonometry - II",
            "Determinants and Matrices",
            "Straight Line",
            "Circle",
            "Conic Sections",
            "Measures of Dispersion",
            "Probability",
            "Complex Numbers",
            "Sequences and Series",
            "Permutations and Combination",
            "Method of Induction and Binomial Theorem",
            "Sets and Relations",
            "Functions",
            "Limits",
            "Continuity",
            "Differentiation"
        ],
        "class_12": [
            "Mathematical Logic",
            "Matrices",
            "Trigonometric Functions",
            "Pair of Straight Lines",
            "Vectors",
            "Line and Plane",
            "Linear Programming",
            "Differentiation",
            "Applications of Derivatives",
            "Indefinite Integration",
            "Definite Integration",
            "Application of Definite Integration",
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
            "Animal Tissue",
            "Study of Animal Type - Cockroach",
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
            "Enhancement of Food Production",
            "Biotechnology",
            "Organisms and Populations",
            "Ecosystems and Energy Flow",
            "Biodiversity, Conservation and Environmental Issues"
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


INVALID_ESCAPE_RE = re.compile(r'\\(?!["\\/bfnrtu])')


class PayalFlashcardGenerator:
    """Generate exam-focused MCQs for Payal's preparation"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
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
    "explanation": "Clear explanation with proper formatting.\\n\\nFor step-by-step solutions:\\n1. State the given data\\n2. Write the formula: $formula$\\n3. Substitute values and solve\\n\\nUse line breaks for clarity, NOT markdown bold/italic.",
    "reference": "Maharashtra Board Class X Physics Ch.Y, NCERT Physics Part-I Section Z"
  }}
]

IMPORTANT FORMATTING RULES:
- Use $ for inline math: $E = mc^2$
- Use $$ for block equations: $$x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$$
- Escape backslashes in LaTeX: \\frac, \\sqrt, \\pi, etc.
- correct_answer is 0-indexed (0=A, 1=B, 2=C, 3=D)
- NO markdown formatting (**, *, etc.) - use plain text with line breaks
- Use \\n\\n for paragraph breaks in explanations
- Use simple numbered points (1., 2., 3.) or bullet points (•) for lists
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

            raw_content = self._extract_response_text(response)
            if not raw_content:
                print("Generation Error: Empty response from Gemini")
                return []

            # Remove markdown fences and clean payload before parsing
            content = self._strip_code_fences(raw_content).strip()

            # Parse JSON with fallbacks for minor formatting glitches
            cards = self._loads_with_fallbacks(content)
            
            # Validate and clean cards
            validated_cards = []
            for card in cards:
                if self._validate_card(card):
                    validated_cards.append(self._clean_card(card))
            
            return validated_cards
            
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response: {raw_content[:500] if 'raw_content' in locals() else ''}")
            return []
        except Exception as e:
            print(f"Generation Error: {e}")
            return []

    def _extract_response_text(self, response) -> str:
        """Safely extract text from Gemini response, even when finish_reason is truncated."""
        try:
            text = response.text
            if text:
                return text
        except Exception:
            pass

        for candidate in getattr(response, 'candidates', []) or []:
            content = getattr(candidate, 'content', None)
            parts = getattr(content, 'parts', []) if content else []
            for part in parts:
                text = getattr(part, 'text', None)
                if text:
                    return text
        return ''

    def _strip_code_fences(self, text: str) -> str:
        text = text.strip()
        if text.startswith('```'):
            parts = text.split('```')
            for part in parts:
                candidate = part.strip()
                if not candidate:
                    continue
                if candidate.startswith('json'):
                    candidate = candidate[4:].strip()
                return candidate
        return text

    def _strip_to_json_array(self, text: str) -> str:
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
        return text

    def _sanitize_invalid_escapes(self, text: str) -> str:
        return INVALID_ESCAPE_RE.sub(lambda _: r'\\', text)

    def _repair_json_string(self, text: str) -> str:
        if not text:
            return text

        result = []
        in_string = False
        i = 0
        valid_escapes = '"\\/bfnrtu'

        while i < len(text):
            ch = text[i]
            prev = text[i - 1] if i > 0 else ''

            if ch == '"' and prev != '\\':
                in_string = not in_string
                result.append(ch)
                i += 1
                continue

            if in_string:
                if ch in ('\n', '\r'):
                    result.append('\\n')
                    i += 1
                    continue

                if ch == '\\':
                    if i + 1 >= len(text):
                        result.append('\\\\')
                        i += 1
                        continue

                    nxt = text[i + 1]

                    if nxt in valid_escapes:
                        result.append('\\')
                        result.append(nxt)
                        i += 2
                        continue

                    if nxt in ('\n', '\r'):
                        result.append('\\n')
                        i += 2
                        continue

                    # Unknown escape like \left -> ensure the backslash is escaped
                    result.append('\\\\')
                    i += 1
                    continue

            result.append(ch)
            i += 1

        return ''.join(result)

    def _loads_with_fallbacks(self, content: str) -> List[Dict]:
        attempts = []
        attempts.append(content)
        trimmed = self._strip_to_json_array(content)
        if trimmed != content:
            attempts.append(trimmed)
        repaired = self._repair_json_string(trimmed)
        if repaired != trimmed:
            attempts.append(repaired)
        sanitized = self._sanitize_invalid_escapes(repaired)
        if sanitized != trimmed:
            attempts.append(sanitized)

        last_error = None
        for attempt in attempts:
            if not attempt:
                continue
            try:
                return json.loads(attempt)
            except json.JSONDecodeError as exc:
                last_error = exc
                try:
                    return json.loads(attempt, strict=False)
                except json.JSONDecodeError as exc2:
                    last_error = exc2
                    continue
        if last_error:
            raise last_error
        raise json.JSONDecodeError('Unable to parse JSON response', content, 0)
    
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
