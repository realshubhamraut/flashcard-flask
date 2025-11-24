# Code and Math Rendering in MemFlash

## Overview

MemFlash now supports **automatic rendering** of:
- **Inline code** using backticks: `` `code` ``
- **Code blocks** using triple backticks: ` ```code``` `
- **Inline math formulas** using single dollar signs: `$formula$`
- **Block math formulas** using double dollar signs: `$$formula$$`

This works in:
- ✅ Questions
- ✅ Options (A, B, C, D)
- ✅ Explanations
- ✅ Hints
- ✅ References

---

## How to Use in JSON Files

### 1. Inline Code

Wrap code in single backticks:

```json
{
  "question": "What does the `range()` function do in Python?",
  "options": [
    "Returns a list",
    "Returns a `range` object",
    "Returns `None`",
    "Returns a tuple"
  ],
  "description": "The `range()` function returns a `range` object, not a list."
}
```

**Renders as:**
- Question: What does the <code>range()</code> function do in Python?
- Option B: Returns a <code>range</code> object

---

### 2. Code Blocks

Use triple backticks (optionally with language):

```json
{
  "question": "What does this code print?\n\n```python\nfor i in range(3):\n    print(i * 2)\n```",
  "options": ["0, 2, 4", "2, 4, 6", "0, 1, 2", "1, 2, 3"],
  "correct_answer": 0,
  "description": "The code prints 0, 2, 4 because:\n\n```python\nrange(3) → [0, 1, 2]\ni * 2 → [0, 2, 4]\n```"
}
```

**Renders as:**

<pre><code class="language-python">for i in range(3):
    print(i * 2)
</code></pre>

---

### 3. Inline Math Formulas

Use single dollar signs `$...$`:

```json
{
  "question": "What is the solution to $ax^2 + bx + c = 0$?",
  "options": [
    "$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$",
    "$x = \\frac{b}{2a}$",
    "$x = -\\frac{b}{a}$",
    "$x = \\sqrt{b^2 - 4ac}$"
  ],
  "correct_answer": 0,
  "hint": "Use the discriminant $\\Delta = b^2 - 4ac$"
}
```

**Renders as:** (using KaTeX)
- Question: What is the solution to *ax² + bx + c = 0*?
- Option A: *x = (-b ± √(b² - 4ac)) / 2a*

---

### 4. Block Math Formulas

Use double dollar signs `$$...$$` for centered, display-mode math:

```json
{
  "description": "The quadratic formula is:\n\n$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$\n\nThis solves $ax^2 + bx + c = 0$."
}
```

**Renders as:** (centered and larger)

```
       -b ± √(b² - 4ac)
   x = ─────────────────
            2a
```

---

## LaTeX Math Syntax Examples

### Common Symbols

| LaTeX | Renders | Description |
|-------|---------|-------------|
| `$x^2$` | x² | Superscript |
| `$x_i$` | xᵢ | Subscript |
| `$\frac{a}{b}$` | a/b | Fraction |
| `$\sqrt{x}$` | √x | Square root |
| `$\pm$` | ± | Plus-minus |
| `$\times$` | × | Multiply |
| `$\div$` | ÷ | Divide |
| `$\leq$` | ≤ | Less than or equal |
| `$\geq$` | ≥ | Greater than or equal |
| `$\neq$` | ≠ | Not equal |
| `$\pi$` | π | Pi |
| `$\Delta$` | Δ | Delta |
| `$\alpha$` | α | Alpha |
| `$\beta$` | β | Beta |
| `$\theta$` | θ | Theta |
| `$\sum$` | Σ | Summation |
| `$\int$` | ∫ | Integral |

### Physics Formulas

```json
{
  "question": "Einstein's mass-energy equivalence is:",
  "options": [
    "$E = mc^2$",
    "$E = \\frac{1}{2}mv^2$",
    "$E = mgh$",
    "$E = \\frac{mv^2}{2}$"
  ],
  "correct_answer": 0,
  "description": "Einstein's famous equation:\n\n$$E = mc^2$$\n\nWhere:\n- $E$ = Energy\n- $m$ = Mass\n- $c$ = Speed of light ($3 \\times 10^8$ m/s)"
}
```

### Chemistry Formulas

```json
{
  "question": "The molecular formula for water is:",
  "options": [
    "$H_2O$",
    "$H_2O_2$",
    "$HO_2$",
    "$H_3O$"
  ],
  "correct_answer": 0,
  "description": "Water consists of 2 hydrogen atoms and 1 oxygen atom: $H_2O$"
}
```

### Calculus

```json
{
  "description": "The derivative of $x^n$ is:\n\n$$\\frac{d}{dx}(x^n) = nx^{n-1}$$\n\nFor example:\n- $\\frac{d}{dx}(x^2) = 2x$\n- $\\frac{d}{dx}(x^3) = 3x^2$"
}
```

---

## Example Complete Card

```json
{
  "question": "What is the time complexity of binary search? Given a sorted array of size $n$:",
  "options": [
    "$O(\\log n)$",
    "$O(n)$",
    "$O(n \\log n)$",
    "$O(n^2)$"
  ],
  "correct_answer": 0,
  "description": "Binary search has **logarithmic time complexity**:\n\n$$T(n) = O(\\log_2 n)$$\n\nThis is because we eliminate half the search space at each step.\n\n```python\ndef binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n```",
  "hint": "Each comparison reduces the search space by half, so it's $\\log_2 n$"
}
```

---

## Testing Your JSON

1. Create a test deck with math and code:
   ```bash
   cp /tmp/test_math_code.json ~/Desktop/
   ```

2. Import the deck in MemFlash:
   - Go to **Import** page
   - Upload the JSON file
   - Study the deck to see rendering

3. Check that:
   - ✅ Inline code appears in monospace font with background
   - ✅ Code blocks are syntax highlighted
   - ✅ Math formulas render properly (not showing raw LaTeX)
   - ✅ Block math is centered and larger

---

## Escaping Special Characters

If you need to show literal `$` or `` ` `` without rendering:

- Escape dollar signs: `\$` → `$`
- Escape backticks: `` \` `` → `` ` ``

Example:
```json
{
  "question": "The price is \\$100, not \\$50"
}
```

---

## Technical Details

### Libraries Used

- **KaTeX** (v0.16.9) - Fast math rendering
- **Highlight.js** - Code syntax highlighting

### Files Modified

1. `templates/base.html` - Added KaTeX library
2. `templates/study.html` - Added rendering triggers
3. `static/js/content-renderer.js` - NEW: Rendering logic
4. `static/css/style.css` - Code and math styling

### Supported Everywhere

The rendering works in:
- Study mode (all modes: new, all, trippy, missed)
- Deck detail view
- Any place where card content is displayed

---

## Troubleshooting

### Math Not Rendering

**Problem:** Seeing raw `$x^2$` instead of formatted math

**Solutions:**
1. Check browser console for errors
2. Verify KaTeX loaded: Open dev tools → Network → check for katex.min.js
3. Make sure using proper LaTeX syntax

### Code Not Highlighted

**Problem:** Code blocks showing plain text

**Solutions:**
1. Use triple backticks with language: ` ```python `
2. Check Highlight.js loaded in Network tab
3. Verify code is inside triple backticks

### Formulas Look Weird

**Problem:** Formulas display but look wrong

**Solutions:**
1. Check LaTeX syntax (must escape backslashes in JSON: `\\frac` not `\frac`)
2. Use block math `$$` for complex formulas
3. Test formula on [KaTeX demo](https://katex.org/) first

---

## Sample Test File

A sample JSON file with math and code examples is available at:
```
/tmp/test_math_code.json
```

Import this to test the rendering features!
