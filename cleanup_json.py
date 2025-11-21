#!/usr/bin/env python3
"""
Clean up sanfoundry_python_all_questions.json by removing questions with missing data
and renumbering the remaining questions sequentially.
"""
import json

print("Loading sanfoundry_python_all_questions.json...")
with open('sanfoundry_python_all_questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total questions before cleanup: {len(data)}")

# Track statistics
removed_reasons = {
    'empty_options_and_no_explanation': 0,
    'missing_answer': 0,
    'missing_question': 0,
}

valid_questions = []

for question in data:
    # Check for missing critical fields
    if not question.get('question', '').strip():
        removed_reasons['missing_question'] += 1
        continue
    
    if not question.get('answer', '').strip():
        removed_reasons['missing_answer'] += 1
        continue
    
    # Check if options is empty dict AND explanation is missing/empty
    options = question.get('options', {})
    explanation = question.get('explanation', '').strip()
    
    if (not options or (isinstance(options, dict) and not options)) and not explanation:
        removed_reasons['empty_options_and_no_explanation'] += 1
        continue
    
    # Valid question - keep it
    valid_questions.append(question)

print(f"\nRemoval breakdown:")
for reason, count in removed_reasons.items():
    if count > 0:
        print(f"  - {reason}: {count}")

print(f"\nTotal valid questions: {len(valid_questions)}")
print(f"Total removed: {len(data) - len(valid_questions)}")

# Renumber questions sequentially
for idx, question in enumerate(valid_questions, start=1):
    question['number'] = idx

# Save cleaned data
with open('sanfoundry_python_all_questions.json', 'w', encoding='utf-8') as f:
    json.dump(valid_questions, f, indent=2, ensure_ascii=False)

print(f"\n✅ Cleaned file saved with {len(valid_questions)} valid questions")
print(f"Questions are now numbered 1 to {len(valid_questions)}")
