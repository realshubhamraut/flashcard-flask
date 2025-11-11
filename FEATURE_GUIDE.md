# Quick Feature Guide

## 🗑️ Delete Cards (NEW!)

**Where:** Small × button in top-right corner of each flashcard

**How to use:**
1. During study session, look at top-right corner of card
2. Click the small red × button
3. Confirm deletion in popup dialog
4. Card is permanently removed

**Visual:**
```
┌──────────────────────────────┐
│  Question goes here...  [×]  │ ← Click here to delete
│                              │
│  A) Option 1                 │
│  B) Option 2                 │
└──────────────────────────────┘
```

---

## 📊 Accurate Statistics (FIXED!)

**What was fixed:**
- ❌ Before: Always showed 100% accuracy
- ✅ Now: Shows YOUR actual performance

**What to check:**
- Go to **Statistics** page
- "Today's Accuracy" now reflects your actual good/easy ratings
- Each user sees only their own data

---

## ⚙️ Manual Schedule Editor (NEW!)

**Where:** Button below rating buttons (After, Hard, Good, Easy)

**How to use:**
1. Answer a card during study session
2. After viewing explanation, click **"⚙️ Edit Schedule"**
3. Modal opens with current card settings
4. Edit any field:
   - **Card State:** new → learning → review → mastered
   - **Next Review Date:** Pick exact date/time
   - **Interval:** Number of days until next review
   - **Ease Factor:** 1.3-5.0 (how fast intervals grow)
   - **Repetitions:** Success count
5. Click **"Save Changes"**

**Example Use Cases:**

### Mark as Mastered
Already know this card by heart?
- Set State: `mastered`
- Set Interval: `90` days
- Save → Won't see it for 3 months

### Reset Difficult Card
Keep forgetting this one?
- Set State: `new`
- Set Interval: `0`
- Set Repetitions: `0`
- Save → Starts fresh like brand new card

### Adjust for Vacation
Going on vacation next week?
- Set Next Review Date: `2025-01-20 09:00`
- Save → Card appears when you're back

### Slow Down Reviews
Too many cards due every day?
- Set Interval: `14` days
- Set Ease Factor: `2.0` (lower = slower growth)
- Save → Longer gaps between reviews

---

## 🎨 Visual Guide

### Delete Button
```
Normal state:        Hover state:
┌──────┐            ┌──────┐
│  [×] │            │  [×] │ ← Bigger, brighter
└──────┘            └──────┘
opacity: 0.6        opacity: 1.0
                    scale: 1.1
```

### Schedule Editor Modal
```
┌─────────────────────────────────────────────┐
│  ⚙️ Edit Card Schedule                 [×]  │
├─────────────────────────────────────────────┤
│                                             │
│  Card State:  [Review ▼]                    │
│                                             │
│  Next Review: [2025-01-15 10:00 AM]        │
│                                             │
│  Interval:    [7] days                      │
│                                             │
│  Ease Factor: [2.5] (1.3-5.0)              │
│               Controls growth speed         │
│                                             │
│  Repetitions: [3] successful reviews        │
│                                             │
├─────────────────────────────────────────────┤
│                   [Cancel] [Save Changes]   │
└─────────────────────────────────────────────┘
```

---

## 🚀 Testing Your Changes

### Test Delete Feature
1. Start a study session
2. Find the × in top-right of card
3. Click it → should ask "Are you sure?"
4. Confirm → card disappears
5. Check deck detail → total cards decreased

### Test Accuracy Fix
1. Study some cards
2. Rate some as "Good" or "Easy"
3. Rate some as "Again" or "Hard"
4. Go to Statistics page
5. Should show percentage < 100% (unless perfect!)

### Test Schedule Editor
1. Study a card
2. After answering, click "⚙️ Edit Schedule"
3. Modal should open with current values
4. Change "Interval" to 30
5. Click "Save Changes"
6. Check deck detail → card won't appear for 30 days

---

## 🔧 Keyboard Shortcuts (Coming Soon)

Ideas for future:
- `Delete` key → Delete current card
- `S` key → Open schedule editor
- `Esc` key → Close modal

---

## 💡 Pro Tips

### For Better Retention
- Don't abuse the schedule editor
- Trust the SM-2 algorithm most of the time
- Only override for special cases (vacation, known topics)

### For Difficult Cards
- Use "Again" rating first
- If still failing, then reset via schedule editor
- Consider rewriting the question/hint

### For Easy Cards
- Rate as "Easy" naturally
- Let algorithm increase interval
- Or manually set to "mastered" if trivial

---

## 🐛 Troubleshooting

**Delete button not appearing?**
- Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+F5)
- Check if CSS loaded correctly
- Try different browser

**Modal not opening?**
- Check browser console for errors (F12)
- Make sure JavaScript enabled
- Clear browser cache

**Accuracy still 100%?**
- Make sure you rated cards with different ratings
- Check you're logged in as correct user
- Try refreshing statistics page

**Schedule changes not saving?**
- Check all fields have valid values
- Ease factor must be 1.3-5.0
- Date must be in future
- Check browser console for errors

---

## 📝 API Endpoints (For Developers)

### Delete Card
```http
DELETE /api/card/<card_id>/delete
Authorization: Login required
Response: {"success": true}
```

### Get Card Progress
```http
GET /api/card/<card_id>/progress
Authorization: Login required
Response: {
  "success": true,
  "progress": {
    "state": "review",
    "due_date": "2025-01-15T10:00:00",
    "interval": 7,
    "ease_factor": 2.5,
    "repetitions": 3,
    "lapses": 0
  }
}
```

### Update Card Progress
```http
PUT /api/card/<card_id>/progress
Authorization: Login required
Body: {
  "state": "mastered",
  "interval": 90,
  "ease_factor": 2.8,
  "repetitions": 10,
  "due_date": "2025-04-15T10:00:00"
}
Response: {"success": true, "progress": {...}}
```

---

Happy studying! 🎓
