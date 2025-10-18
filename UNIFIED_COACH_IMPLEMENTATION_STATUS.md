# Unified Coach Implementation Status

**Last Updated:** 2025-10-18
**Phase:** Week 1-2 (Core Functionality + Smart Matching)

---

## ✅ **COMPLETED FEATURES**

### **1. Dual Confidence System** ✅
**Files Modified:**
- `app/services/log_extraction_service.py` (lines 57-196, 226-254)

**What Was Done:**
- Enhanced LLM extraction prompt to return TWO separate confidence scores:
  - `classification_confidence`: How sure this is a log (meal/activity/measurement)
  - `nutrition_confidence`: How accurate the nutrition data is
- Added `confidence_breakdown` with three sub-scores:
  - `quantity_precision` (0-1): How precise is the amount?
  - `food_identification` (0-1): How well can we identify the food?
  - `preparation_detail` (0-1): Do we know cooking method/preparation?
- Backward compatible: Still returns generic `confidence` field

**How It Works:**
```python
# Example extraction result:
{
  "log_type": "meal",
  "classification_confidence": 0.95,  # 95% sure it's a meal
  "nutrition_confidence": 0.45,       # 45% sure about nutrition (LOW!)
  "confidence_breakdown": {
    "quantity_precision": 0.3,  # Vague amount ("some chicken")
    "food_identification": 0.8,  # We know it's chicken
    "preparation_detail": 0.5   # No cooking method specified
  },
  "structured_data": {...}
}
```

---

### **2. Common Units Support** ✅
**Files Modified:**
- `app/services/log_extraction_service.py` (lines 93-110)

**What Was Done:**
- Enhanced extraction to recognize common units:
  - **Pieces**: "2 bananas", "3 eggs", "1 chicken breast"
  - **Cups**: "1 cup rice", "2 cups milk"
  - **Scoops**: "1 scoop protein powder"
  - **Tablespoons/Slices**: "2 tbsp peanut butter", "3 slices bread"
- LLM now extracts:
  ```json
  {
    "name": "banana",
    "quantity": 2,
    "unit": "pieces",
    "estimated_grams": 240,  // 2 × 120g
    "estimated": false
  }
  ```
- Includes typical gram estimates for common foods:
  - Banana (piece): 120g
  - Egg (piece): 50g
  - Chicken breast (piece): 200g
  - Rice (cup cooked): 200g
  - Protein powder (scoop): 30g

**Next Step:** Meal item transformer needs to convert these units to proper serving_id lookups from `food_servings` table

---

### **3. 60% Nutrition Confidence Check** ✅
**Files Modified:**
- `app/services/unified_coach_service.py` (lines 1090-1133, 1284-1371)

**What Was Done:**
- Added confidence check in `_handle_log_mode()`:
  ```python
  if log_type == "meal" and nutrition_conf < 0.6:
      # Don't create quick_entry_log
      # Instead, ask clarification questions
  ```
- Created `_build_clarification_questions()` helper method that:
  - Analyzes confidence breakdown to identify what's missing
  - Generates targeted questions based on specific uncertainties
  - Returns clarification message instead of log preview

**Example Flow:**
```
User: "I ate some chicken"

Extraction:
- classification_confidence: 0.95 (definitely a meal)
- nutrition_confidence: 0.35 (very uncertain)
- Breakdown: quantity_precision=0.2, preparation_detail=0.5

Coach Response:
"I detected you ate chicken, but I need more details to log it accurately:

• How much chicken did you have?
• How was the chicken cooked? (grilled, fried, baked, etc.)

Can you help me out? This will make sure your log is accurate! 💪"

---

User: "300g grilled chicken breast"

Extraction:
- classification_confidence: 0.95
- nutrition_confidence: 0.92 (excellent!)

Coach Response:
[Shows confirmation card]
```

---

### **4. Time-Aware Progress Calculation Utility** ✅
**Files Created:**
- `app/utils/time_aware_progress.py` (new file, 356 lines)

**What Was Done:**
- Created comprehensive time-aware progress calculator
- Accounts for time of day when evaluating if user is on track
- Prevents coach from saying "you're behind!" at 6 AM when user just started eating

**Key Functions:**
1. `calculate_time_aware_progress()`:
   - Converts UTC to user's local timezone
   - Calculates expected progress through eating window (6 AM - 10 PM default)
   - Returns deviation: actual - expected

2. `interpret_progress()`:
   - Categorizes deviation into human-readable status
   - Returns: "ahead_of_schedule", "on_track", "slightly_behind", etc.

3. `generate_message_suggestion()`:
   - Creates appropriate coach message based on interpretation
   - Examples:
     - 6 AM, 500 cal eaten: "You're crushing it! Great start!"
     - 2 PM, 500 cal eaten: "Time to fuel up! You need 2500 more calories."
     - 10 PM, 2800 cal eaten: "Solid day! 93% of your goal."

**Example Usage:**
```python
from app.utils.time_aware_progress import calculate_time_aware_progress
from datetime import datetime
import pytz

result = calculate_time_aware_progress(
    user_id=user_id,
    current_time_utc=datetime.utcnow(),
    actual_calories=500,
    goal_calories=3000,
    user_timezone="America/Sao_Paulo",
    eating_start_hour=6,
    eating_end_hour=22
)

# At 6 AM:
{
    "actual_progress": 0.167,  # 16.7%
    "expected_progress": 0.0,  # 0% (haven't started eating yet)
    "deviation": +0.167,  # AHEAD of schedule!
    "interpretation": "ahead_of_schedule",
    "message_suggestion": "You're crushing it! 500 cal logged already..."
}

# At 2 PM:
{
    "actual_progress": 0.167,
    "expected_progress": 0.50,  # Should be 50% through by 2 PM
    "deviation": -0.333,  # BEHIND schedule
    "interpretation": "significantly_behind",
    "message_suggestion": "Time to fuel up! You need 2500 more calories..."
}
```

---

## 🚧 **IN PROGRESS / TODO**

### **5. Smart Food Matching with User History** 🟡
**Priority:** HIGH
**Files to Modify:**
- `app/services/meal_item_transformer.py`
- `app/services/tool_service.py` (search_food_database)

**What Needs to Be Done:**
1. **User History Priority:**
   - Query `meal_items` to get user's frequently logged foods
   - Weight search results by:
     - Frequency (how often user logs this food)
     - Recency (when last logged)
     - Exact name match vs synonym

2. **Common Units → Serving ID Matching:**
   - When extraction says `{quantity: 2, unit: "pieces"}`:
     - Search `food_servings` for matching `serving_unit = "piece"`
     - Use `serving_id` instead of generic gram conversion
     - Display: "2 bananas" not "240g banana"

3. **Enhanced Search Algorithm:**
   ```python
   def smart_food_search(food_name, quantity, unit, user_id):
       # Priority 1: User's frequent foods (weighted by frequency × recency)
       user_foods = get_user_frequent_foods(user_id, food_name, limit=5)

       # Priority 2: Exact matches in food database
       exact_matches = search_foods(food_name, exact=True)

       # Priority 3: Fuzzy matches with ranking
       fuzzy_matches = search_foods(food_name, fuzzy=True)

       # Priority 4: Synonym matches
       synonyms = get_synonyms(food_name)  # "chicken" → "frango", "pollo"
       synonym_matches = search_foods(synonyms)

       # Combine and rank
       return rank_results(user_foods + exact_matches + fuzzy_matches)
   ```

**Estimated Time:** 4-6 hours

---

### **6. Custom Food Creation Flow** 🟡
**Priority:** MEDIUM
**Files to Modify:**
- `app/services/unified_coach_service.py`
- `app/services/nutrition_service.py` (custom food helper)

**What Needs to Be Done:**
1. **Detection:**
   - When food search returns NO confident matches
   - Or nutrition_confidence < 0.6 due to "missing food"

2. **Coach Asks:**
   ```
   "I don't have 'grandma's lasagna' in my database.
   Want to:
   A) Use a similar food from the database
   B) Tell me the nutrition so I can save it for next time?"
   ```

3. **If User Chooses B:**
   - Coach asks: "How many calories per serving?"
   - Coach asks: "How much protein?"
   - Create custom food entry:
     ```python
     await nutrition_service.create_custom_food(
         user_id=user_id,
         name="Grandma's Lasagna",
         serving_size=1,
         serving_unit="serving",
         grams_per_serving=300,  # Estimated
         calories=600,  # From user
         protein_g=35,  # From user
         ...
     )
     ```
   - Next time "grandma's lasagna" → PERFECT MATCH!

**Estimated Time:** 3-4 hours

---

### **7. Dynamic Time-Aware System Prompts** 🟡
**Priority:** MEDIUM
**Files to Modify:**
- `app/services/unified_coach_service.py` (system prompt building)

**What Needs to Be Done:**
1. **Integrate time_aware_progress into Claude chat:**
   ```python
   # In _handle_claude_chat(), before building system prompt:
   from app.utils.time_aware_progress import calculate_time_aware_progress

   progress = await calculate_time_aware_progress(
       user_id=user_id,
       current_time_utc=datetime.utcnow(),
       actual_calories=daily_summary["totals"]["calories"],
       goal_calories=profile["daily_calorie_goal"],
       user_timezone=profile.get("timezone", "UTC")
   )

   # Add to system prompt:
   <today_progress>
   Calories: {actual} / {goal} ({progress['actual_progress']:.0%})
   Expected by now: {progress['expected_progress']:.0%}
   Status: {progress['interpretation']}
   Suggestion: {progress['message_suggestion']}

   CRITICAL: Use this TIME-AWARE analysis when user asks about progress!
   </today_progress>
   ```

2. **Add time-of-day coaching context:**
   ```python
   from app.utils.time_aware_progress import get_time_of_day_prompt

   time_context = get_time_of_day_prompt(
       hour=current_local_time.hour,
       user_goal=profile["primary_goal"]
   )

   # Add to system prompt:
   <time_context>
   {time_context}
   </time_context>
   ```

**Estimated Time:** 2-3 hours

---

## 🧪 **TESTING REQUIRED**

### **Test Scenarios:**

**Scenario 1: Simple Log (High Confidence)**
```
User: "I ate 300g grilled chicken breast"
Expected:
- classification_confidence > 0.9
- nutrition_confidence > 0.8
- Instant confirmation card
- Shows: "300g Grilled Chicken Breast - 495 cal, 93g protein"
```

**Scenario 2: Vague Log (Low Confidence)**
```
User: "I had some chicken"
Expected:
- classification_confidence > 0.9
- nutrition_confidence < 0.6
- NO confirmation card
- Coach asks: "How much chicken? How was it cooked?"
```

**Scenario 3: Common Units**
```
User: "I ate 2 bananas and 1 scoop protein powder"
Expected:
- Extract: [{name: "banana", quantity: 2, unit: "pieces", estimated_grams: 240}, ...]
- Convert to serving_id from food_servings table
- Display: "2 bananas (240g)" not just "240g banana"
```

**Scenario 4: Time-Aware Progress**
```
Time: 6 AM
User: "Am I on track today?"
Eaten: 500 cal / 3000 goal

Expected:
- Coach: "You're CRUSHING it! 500 cal already at 6 AM - ahead of schedule!"

---

Time: 2 PM
Same user, same 500 cal

Expected:
- Coach: "Time to fuel up! You're behind schedule - 2500 cal to go!"
```

---

## 📊 **PROGRESS SUMMARY**

**Completed:** 4/12 tasks (33%)
- ✅ Dual confidence system
- ✅ Common units extraction
- ✅ 60% confidence check
- ✅ Time-aware progress utility

**In Progress:** 0 tasks

**Remaining:** 8 tasks
- 🟡 Smart food matching (HIGH priority)
- 🟡 Custom food creation (MEDIUM priority)
- 🟡 Time-aware system prompts (MEDIUM priority)
- 🟡 Enable logging flow (frontend)
- 🧪 End-to-end testing (4 scenarios)

---

## 🚀 **NEXT STEPS**

### **Immediate (Next 2-4 hours):**
1. Implement smart food matching with user history
2. Update meal_item_transformer to handle common units → serving_id conversion
3. Test extraction with various unit types

### **Short-term (Next 6-8 hours):**
4. Add custom food creation flow
5. Integrate time-aware progress into system prompts
6. Enable logging flow in frontend (if blocked)
7. Create confirmation card UI component

### **Testing (Final 4-6 hours):**
8. Test all 4 scenarios thoroughly
9. Test edge cases (very vague logs, missing foods, late night eating)
10. Test time-aware progress at different times of day
11. Load testing (100 concurrent log submissions)

---

## 📝 **USAGE EXAMPLES**

### **For Coach to Handle Common Units:**
```python
# Example: User says "I ate 2 bananas"

# 1. Extraction extracts:
{
  "foods": [
    {
      "name": "banana",
      "quantity": 2,
      "unit": "pieces",
      "estimated_grams": 240
    }
  ]
}

# 2. meal_item_transformer needs to:
food = await search_food("banana", user_id)
# Find food_servings with serving_unit = "piece"
serving = next((s for s in food.servings if s.serving_unit == "piece"), None)

if serving:
    # Use serving-based logging
    item = {
        "food_id": food.id,
        "quantity": 2,  # 2 servings
        "serving_id": serving.id,
        "grams": 2 * serving.grams_per_serving,  # 2 × 120g = 240g
        "display_unit": "pieces",
        "display_label": "2 bananas"
    }
else:
    # Fall back to gram-based
    item = {
        "food_id": food.id,
        "quantity": 240,  # grams
        "serving_id": None,
        "grams": 240,
        "display_unit": "g",
        "display_label": None
    }
```

---

## ⚠️ **KNOWN ISSUES & CONSIDERATIONS**

1. **Unit Conversion Not Yet Connected:**
   - Extraction returns common units
   - But meal_item_transformer still only handles grams
   - **FIX:** Update transformer to search food_servings by unit type

2. **Custom Food Creation Not Implemented:**
   - If food not found in DB, coach should ask user for nutrition
   - **FIX:** Add custom food creation flow in unified_coach_service

3. **Time-Aware Prompts Not Integrated:**
   - Utility exists but not yet used in system prompts
   - **FIX:** Update _handle_claude_chat() to include progress data

4. **Frontend Confirmation Card:**
   - Backend ready to send `is_log_preview: true`
   - But frontend may not have confirmation modal yet
   - **FIX:** Create ConfirmationCard.tsx component

---

## 📚 **DOCUMENTATION UPDATES NEEDED**

1. Update `CLAUDE.md` with:
   - New dual confidence system
   - Common units documentation
   - Time-aware progress usage

2. Create usage guide for:
   - How to handle low-confidence logs
   - When coach asks for clarification
   - Time-aware coaching examples

3. Add API documentation for:
   - New `nutrition_confidence` field in responses
   - `waiting_for_clarification` flag
   - Time-aware progress endpoints (if exposed)

---

**Total Estimated Remaining Time:** ~20 hours
**Priority Order:**
1. Smart food matching (4-6h) - CRITICAL for UX
2. Custom food creation (3-4h) - IMPORTANT for edge cases
3. Time-aware prompts (2-3h) - QUALITY OF LIFE
4. Frontend integration (4-6h) - REQUIRED for logging
5. Testing & refinement (4-6h) - ESSENTIAL for production

---

**Status:** 🟡 **In Progress - Week 1-2 Features**
**Next Milestone:** Complete smart food matching + common units conversion
