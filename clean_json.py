import json
import re

print("Reading new.json...")
try:
    with open('new.json', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix common JSON issues caused by [cite_start] appearing before property names
    # Remove [cite_start] that appears before property names
    content = re.sub(r',?\s*\[cite_start\]\s*"', ',\n    "', content)
    
    # Try to parse
    data = json.loads(content)
    
    print(f"Found {len(data)} cards to clean...")
    
    # Clean each card
    for card in data:
        # Remove [cite_start] and citations from all text fields
        for key in ['hint', 'description', 'reference', 'question', 'code']:
            if key in card and card[key]:
                # Remove [cite_start] markers
                card[key] = card[key].replace('[cite_start]', '')
                # Remove citation patterns like [cite: 86] or [cite: 85, 86, 87]
                card[key] = re.sub(r'\s*\[cite:[\s\d,]+\]', '', card[key])
                # Clean up extra whitespace
                card[key] = card[key].strip()
        
        # Remove answer_code field if it exists
        if 'answer_code' in card:
            del card['answer_code']
    
    # Write back cleaned data
    print("Writing cleaned data...")
    with open('new.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully cleaned {len(data)} cards!")
    print("✅ Removed all [cite_start] markers")
    print("✅ Removed all citation references")
    print("✅ Removed answer_code fields")
    print("✅ File is ready for import!")
    
except json.JSONDecodeError as e:
    print(f"❌ JSON Error: {e}")
    print(f"   Error at line {e.lineno}, column {e.colno}")
except Exception as e:
    print(f"❌ Error: {e}")
