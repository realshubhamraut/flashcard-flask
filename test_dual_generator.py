#!/usr/bin/env python3
"""
Test script for dual generator system
Tests both Payal's and Shubham's generators
"""

import os
os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', '')

from ai_generator import GeminiFlashcardGenerator, SYLLABUS_MODULES
from ai_generator_payal import PayalFlashcardGenerator, PAYAL_SUBJECTS

def test_payal_generator():
    """Test Payal's generator"""
    print("=" * 60)
    print("Testing Payal's Generator (Maharashtra Board)")
    print("=" * 60)
    
    # Check subjects
    print("\nAvailable Subjects:")
    for subject in PAYAL_SUBJECTS.keys():
        class_11_count = len(PAYAL_SUBJECTS[subject].get('class_11', []))
        class_12_count = len(PAYAL_SUBJECTS[subject].get('class_12', []))
        print(f"  - {subject}: {class_11_count} Class 11 topics, {class_12_count} Class 12 topics")
    
    # Test card generation
    print("\nGenerating 2 sample cards for Physics...")
    generator = PayalFlashcardGenerator()
    
    try:
        cards = generator.generate_cards(
            topic="Rotational Dynamics",
            subject="Physics",
            num_cards=2,
            difficulty="medium",
            exam_focus="MHT-CET"
        )
        
        print(f"✅ Successfully generated {len(cards)} cards")
        
        for i, card in enumerate(cards, 1):
            print(f"\n--- Card {i} ---")
            print(f"Question: {card.get('question', 'N/A')[:100]}...")
            print(f"Options: {len(card.get('options', []))} options")
            print(f"Correct: Option {chr(65 + card.get('correct_answer', 0))}")
            print(f"Difficulty: {card.get('difficulty', 'N/A')}")
            print(f"Has Hint: {'Yes' if card.get('hint') else 'No'}")
            print(f"Has Explanation: {'Yes' if card.get('explanation') else 'No'}")
            print(f"Has Reference: {'Yes' if card.get('reference') else 'No'}")
            print(f"Has Code Field: {'Yes' if card.get('code') else '❌ NO (correct for Payal)'}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


def test_shubham_generator():
    """Test Shubham's generator"""
    print("\n" + "=" * 60)
    print("Testing Shubham's Generator (Tech & Programming)")
    print("=" * 60)
    
    # Check modules
    print("\nAvailable Modules:")
    for module, info in SYLLABUS_MODULES.items():
        topics_count = len(info.get('topics', []))
        print(f"  - {module}: {topics_count} topics")
    
    # Test card generation
    print("\nGenerating 2 sample cards for Python...")
    generator = GeminiFlashcardGenerator()
    
    try:
        result = generator.generate_flashcards(
            module_name="Python",
            topics=["Functions"],
            count=2,
            difficulty="medium"
        )
        
        if result.get('success'):
            cards = result.get('cards', [])
            print(f"✅ Successfully generated {len(cards)} cards")
            
            for i, card in enumerate(cards, 1):
                print(f"\n--- Card {i} ---")
                print(f"Question: {card.get('question', 'N/A')[:100]}...")
                print(f"Options: {len(card.get('options', []))} options")
                print(f"Correct: Option {chr(65 + card.get('correct_answer', 0))}")
                print(f"Difficulty: {card.get('difficulty', 'N/A')}")
                print(f"Has Hint: {'Yes' if card.get('hint') else 'No'}")
                print(f"Has Explanation: {'Yes' if card.get('explanation') else 'No'}")
                print(f"Has Reference: {'Yes' if card.get('reference') else 'No'}")
                print(f"Has Code Field: {'✅ YES' if card.get('code') else 'No (may be optional)'}")
        else:
            print(f"❌ Generation failed: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    print("\n🎯 DUAL GENERATOR SYSTEM TEST\n")
    
    # Test Payal's generator
    test_payal_generator()
    
    # Test Shubham's generator
    test_shubham_generator()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
