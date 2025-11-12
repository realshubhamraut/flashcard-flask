#!/usr/bin/env python3
"""
Script to identify and report questions with missing options in the JSON file.
Questions with answer letters (a, b, c, d) but empty options dict need to be fixed.
"""

import json

def find_missing_options(json_file):
    """Find questions that have answer letters but no option texts."""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    missing_options = []
    
    for i, question in enumerate(data):
        options = question.get('options', {})
        answer = question.get('answer', '')
        
        # Check if answer is a letter but options is empty
        if answer in ['a', 'b', 'c', 'd'] and not options:
            missing_options.append({
                'index': i,
                'number': question.get('number'),
                'question': question.get('question', '')[:100],
                'answer': answer,
                'source_url': question.get('source_url', '')
            })
    
    return missing_options

def main():
    json_file = 'sanfoundry_python_all_questions.json'
    
    print(f"Analyzing {json_file}...")
    missing = find_missing_options(json_file)
    
    print(f"\nFound {len(missing)} questions with missing options:\n")
    
    for item in missing[:20]:  # Show first 20
        print(f"Question #{item['number']}: {item['question']}")
        print(f"  Answer: {item['answer']}")
        print(f"  Source: {item['source_url']}")
        print()
    
    if len(missing) > 20:
        print(f"... and {len(missing) - 20} more\n")
    
    print(f"\nTotal: {len(missing)} questions need manual fixing")
    print("These questions have answer letters but no option texts in the JSON.")
    print("You need to manually add the options from the source URLs.")

if __name__ == '__main__':
    main()
