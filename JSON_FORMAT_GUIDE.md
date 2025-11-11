# JSON Import Format Guide

## Supported Formats

The flashcard app supports **two JSON formats** for importing decks:

---

## Format 1: Simple Array (Recommended for Quick Imports)

**Best for:** Quick imports where you just want to upload cards

**How it works:** The deck name is automatically generated from your filename.

**Example file:** `python_quiz.json`

```json
[
  {
    "question": "What is the output of the following code?",
    "code": "print(len(list(range(1, 6, 2))))",
    "hint": "Check how range works with step.",
    "options": ["1", "2", "3", "Error"],
    "correct_answer": "3",
    "description": "range(1, 6, 2) yields 1, 3, 5; len is 3.",
    "reference": "https://docs.python.org/3/library/stdtypes.html#typesseq-range"
  },
  {
    "question": "Which keyword is used to skip the current iteration?",
    "hint": "break exits loop; continue skips to next iteration.",
    "options": ["break", "continue", "pass", "skip"],
    "correct_answer": "continue",
    "description": "continue jumps to the loop's next iteration.",
    "reference": "https://docs.python.org/3/reference/simple_stmts.html"
  }
]
```

**Key Features:**
- ✅ Direct array of cards
- ✅ `correct_answer` as **string value** (matches exact option text)
- ✅ Deck name derived from filename (e.g., "Python Quiz" from `python_quiz.json`)

---

## Format 2: Full Deck Object

**Best for:** When you want custom deck name and description

**Example file:** `my_deck.json`

```json
{
  "name": "Python Programming Fundamentals",
  "description": "Essential Python concepts for beginners",
  "cards": [
    {
      "question": "What is a list in Python?",
      "hint": "It's a built-in mutable data structure",
      "options": [
        "A key-value pair structure",
        "An ordered, mutable collection of items",
        "A function decorator",
        "A class attribute"
      ],
      "correct_answer": 1,
      "description": "A list is an ordered, mutable collection...",
      "reference": "https://docs.python.org/3/tutorial/datastructures.html",
      "code": "my_list = [1, 2, 3]\nprint(my_list[0])  # Output: 1"
    }
  ]
}
```

**Key Features:**
- ✅ Custom deck name and description
- ✅ `correct_answer` as **integer index** (0, 1, 2, 3...)
- ✅ More structured metadata

---

## Field Reference

### Required Fields
- **question** - The question text

### Optional Fields
- **hint** - Helpful hint (hidden until user clicks)
- **code** - Code snippet with syntax highlighting
- **options** - Array of answer choices (for multiple choice)
- **correct_answer** - Correct answer (see below)
- **description** - Detailed explanation shown after answering
- **reference** - URL or text reference

---

## Understanding `correct_answer`

### Format 1 (Simple Array): String Value
```json
{
  "options": ["Option A", "Option B", "Option C"],
  "correct_answer": "Option B"
}
```
✅ The app finds "Option B" in options and uses its index (1)

### Format 2 (Full Object): Integer Index
```json
{
  "options": ["Option A", "Option B", "Option C"],
  "correct_answer": 1
}
```
✅ Index 1 = second option = "Option B"

**Both work!** The app automatically detects which format you're using.

---

## Examples from Your Data

### Your Format (Working Now! ✅)
```json
[
  {
    "question": "What will be printed?",
    "code": "for i in range(3):\n    print(i, end=' ')\nelse:\n    print()",
    "hint": "The else in for-else runs only if no break occurs.",
    "options": ["0 1 2", "0 1", "1 2", "Nothing"],
    "correct_answer": "0 1 2",
    "description": "No break triggers else after loop completes normally.",
    "reference": ""
  }
]
```

This will:
1. Create a deck named from your filename
2. Find "0 1 2" in options array (index 0)
3. Store index 0 as the correct answer

---

## Tips

1. **Empty strings are OK** - Empty `code` or `reference` fields are fine
2. **Whitespace matters** - Make sure `correct_answer` string matches option exactly
3. **Newlines in code** - Use `\n` for line breaks in code snippets
4. **No options?** - Omit `options` and `correct_answer` for open-ended questions

---

## Sample Files Included

Check the `sample_decks/` folder:
- `python_fundamentals.json` - Format 2 example
- `web_development.json` - Format 2 example  
- `python_quiz_simple.json` - Format 1 example (your format!)

---

## Troubleshooting

**Import fails?**
- Validate JSON syntax at [jsonlint.com](https://jsonlint.com)
- Check that `correct_answer` string exactly matches an option
- Ensure file ends with `.json`

**Correct answer not recognized?**
- Verify exact string match (case-sensitive)
- Check for extra spaces or characters
- Use integer index instead if easier

**Can't find uploaded deck?**
- Check the home page - it should appear in the deck list
- Look for success message after upload
- Check browser console for errors
