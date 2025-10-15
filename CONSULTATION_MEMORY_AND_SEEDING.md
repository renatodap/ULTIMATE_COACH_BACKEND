# Consultation Memory System & Database Seeding

**Created**: 2025-10-12
**Purpose**: Prevent duplicate questions and prepare system for production

---

## Problem 1: Preventing Duplicate Questions

### The Issue
```
❌ WITHOUT MEMORY:
Coach: "What's your primary goal?"
User: "Build muscle"
Coach: "Got it. What's your primary goal?"  ← DUPLICATE!
```

### The Solution: Three-Layer Memory System

#### Layer 1: **Conversation History**
Store every message so LLM knows what was already said.

**Implementation**: `consultation_messages` table (Migration 005)
```sql
CREATE TABLE consultation_messages (
  id UUID PRIMARY KEY,
  session_id UUID → consultation_sessions,
  user_id UUID → auth.users,
  role TEXT CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT,
  extracted_data JSONB,  -- What got saved to DB
  tool_calls JSONB,      -- For debugging
  created_at TIMESTAMPTZ
);
```

#### Layer 2: **Progress Summary**
Know what data has already been collected.

**Implementation**: `get_consultation_progress(session_id)` function
```sql
SELECT get_consultation_progress('session-uuid');

-- Returns:
{
  "training_modalities_count": 1,
  "familiar_exercises_count": 5,
  "training_availability_count": 4,
  ...
  "training_modalities": [
    {"modality_name": "Powerlifting", "is_primary": true, ...}
  ],
  "familiar_exercises": [
    {"exercise_name": "Barbell Back Squat", "comfort_level": 4, ...},
    ...
  ],
  ...
}
```

#### Layer 3: **Enhanced System Prompt**
Include both history AND progress summary in LLM context.

**Updated System Prompt**:
```python
def _build_system_prompt(self, section: str, progress: dict) -> str:
    base = """You are an expert fitness coach conducting a consultation.

CONVERSATION MEMORY:
You have access to the full conversation history below. NEVER ask questions
you've already asked. If the user mentioned something earlier, reference it:
  ✅ "Earlier you mentioned powerlifting..."
  ❌ "What's your training style?" (if already asked)

DATA ALREADY COLLECTED:
{progress_summary}

If the user has already provided data in a category, DO NOT ask for it again.
Instead, move to the next question or ask for additional details.

Example:
- If training_modalities_count > 0: DON'T ask "What training do you do?"
- Instead: "Do you do any OTHER types of training besides {modality_name}?"

RULES:
1. Check progress summary BEFORE asking questions
2. Reference conversation history when relevant
3. Ask follow-up questions, not duplicate questions
4. If unsure, ask user to clarify EXISTING answer, don't start over
"""

    progress_summary = json.dumps(progress, indent=2)
    return base.replace("{progress_summary}", progress_summary) + section_prompts[section]
```

---

## Implementation: Updated ConsultationAIService

### Updated Methods

```python
async def process_message(self, user_id: str, session_id: str, message: str):
    """Process message with full conversation context."""

    # 1. Load conversation history
    history = await self._get_conversation_history(session_id)

    # 2. Load progress summary (what data is already collected)
    progress = await self._get_consultation_progress(session_id)

    # 3. Build system prompt with BOTH history and progress
    system_prompt = self._build_system_prompt(
        section=current_section,
        progress=progress  # ← NEW
    )

    # 4. Format messages for Claude (includes full history)
    messages = self._format_messages(history) + [
        {"role": "user", "content": message}
    ]

    # 5. Call Claude
    response = self.anthropic.messages.create(
        model=self.model,
        system=system_prompt,  # Includes progress context
        messages=messages,      # Includes conversation history
        tools=self._get_tools()
    )

    # 6. Save message to history
    await self._save_user_message(session_id, user_id, message)
    await self._save_assistant_message(session_id, user_id, response_text, extracted)


async def _get_conversation_history(self, session_id: str) -> List[Dict]:
    """Load ALL messages for this session."""
    response = self.db.client.table("consultation_messages")\
        .select("*")\
        .eq("session_id", session_id)\
        .order("created_at")\
        .execute()

    return response.data


async def _get_consultation_progress(self, session_id: str) -> Dict:
    """Get summary of data already collected."""
    result = self.db.client.rpc("get_consultation_progress", {
        "p_session_id": session_id
    }).execute()

    return result.data if result.data else {}


async def _save_user_message(self, session_id: str, user_id: str, message: str):
    """Save user message to history."""
    self.db.client.table("consultation_messages").insert({
        "session_id": session_id,
        "user_id": user_id,
        "role": "user",
        "content": message
    }).execute()


async def _save_assistant_message(
    self,
    session_id: str,
    user_id: str,
    message: str,
    extracted_items: List[Dict]
):
    """Save assistant message with extracted data."""
    self.db.client.table("consultation_messages").insert({
        "session_id": session_id,
        "user_id": user_id,
        "role": "assistant",
        "content": message,
        "extracted_data": json.dumps(extracted_items),
        "ai_model": self.model
    }).execute()


def _format_messages(self, history: List[Dict]) -> List[Dict]:
    """Format database messages for Claude API."""
    formatted = []
    for msg in history:
        formatted.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    return formatted
```

---

## Example: How Memory Prevents Duplicates

### Conversation With Memory

```
🤖 Coach: "What kind of workouts do you usually do?"

👤 User: "I lift weights 4 times a week, mainly squats bench and deadlifts"

[LLM extracts: Powerlifting modality]
[Saves to database + conversation history]

🤖 Coach: "That sounds like powerlifting-style training! How long have you been at it?"

👤 User: "About 2 years"

[LLM extracts: 2 years experience, intermediate level]
[Saves to database + conversation history]

🤖 Coach: "Got it - 2 years of powerlifting at intermediate level.
Do you do any OTHER types of training besides powerlifting?"

👤 User: "I run once a week for cardio"

---

### What's Happening Behind the Scenes:

**System Prompt Includes**:
```
DATA ALREADY COLLECTED:
{
  "training_modalities_count": 1,
  "training_modalities": [
    {"modality_name": "Powerlifting", "is_primary": true, "years_experience": 2, "proficiency_level": "intermediate"}
  ]
}

CONVERSATION HISTORY:
1. Assistant: "What kind of workouts do you usually do?"
2. User: "I lift weights 4 times a week, mainly squats bench and deadlifts"
3. Assistant: "That sounds like powerlifting-style training! How long have you been at it?"
4. User: "About 2 years"
5. Assistant: "Got it - 2 years of powerlifting at intermediate level. Do you do any OTHER types of training besides powerlifting?"
```

**LLM Reasoning**:
- ✅ Already have primary modality (Powerlifting)
- ✅ Already have experience (2 years)
- ✅ Already have proficiency (intermediate)
- ⚠️ DON'T ask about training style again
- ✅ DO ask if there are OTHER modalities
- ✅ Reference what user said: "besides powerlifting"
```

**Result**: NO DUPLICATE QUESTIONS! 🎉

---

## Problem 2: Database Seeding

### What Needs to Be Seeded?

Currently we have **migrations that CREATE tables** but most are empty:

#### ✅ Already Seeded (Migration 003 + 004):
- `training_modalities` - 12 entries
- `meal_times` - 10 entries
- `event_types` - 22 entries
- `exercises` - 150+ entries

#### ❌ NOT Seeded (Need minimal starter data):
- `foods` table - **EMPTY** (can't search foods!)
- `food_servings` table - **EMPTY** (can't log meals!)

### Why This Is Critical

```
❌ WITHOUT SEEDED FOODS:

User: "I eat chicken breast and rice"
LLM: [search_foods("chicken breast")]
Database: [] ← EMPTY!
LLM: "I couldn't find that food in the database"
User: [frustrated] "What foods DO you have??"

Result: CONSULTATION FAILS
```

```
✅ WITH SEEDED FOODS:

User: "I eat chicken breast and rice"
LLM: [search_foods("chicken breast")]
Database: [{id: "uuid", name: "Chicken Breast, Raw", calories_per_100g: 165, ...}]
LLM: [shows options] "I found Chicken Breast, Raw. Is that what you typically eat?"
User: "Yes"
LLM: [insert_user_typical_meal_food(food_id="uuid", ...)]

Result: SUCCESS ✅
```

---

## Solution: Seed Essential Foods

### Strategy: Seed 100-200 Most Common Foods

#### Categories to Seed:
1. **Proteins** (20-30 items)
   - Chicken breast, chicken thigh, ground beef, steak cuts
   - Fish: salmon, tuna, tilapia, cod
   - Eggs, egg whites
   - Greek yogurt, cottage cheese
   - Protein powder (whey, plant-based)

2. **Carbs** (20-30 items)
   - Rice: white, brown, jasmine, basmati
   - Pasta: spaghetti, penne
   - Bread: whole wheat, white
   - Oats, quinoa, couscous
   - Potatoes: russet, sweet potato

3. **Vegetables** (20-30 items)
   - Broccoli, spinach, kale, lettuce
   - Carrots, bell peppers, tomatoes, cucumbers
   - Onions, garlic, mushrooms
   - Green beans, asparagus, zucchini

4. **Fruits** (15-20 items)
   - Bananas, apples, oranges, berries
   - Grapes, melons, pineapple

5. **Fats** (10-15 items)
   - Olive oil, coconut oil, butter
   - Avocado, nuts (almonds, walnuts, cashews)
   - Peanut butter, almond butter
   - Seeds (chia, flax)

6. **Dairy** (10 items)
   - Milk (whole, 2%, skim)
   - Cheese (cheddar, mozzarella, feta)
   - Yogurt

7. **Snacks & Convenience** (10-15 items)
   - Protein bars
   - Rice cakes
   - Crackers
   - Deli meats

**Total**: ~150 foods covering 80% of typical meals

### Implementation: Migration 006

```sql
-- ============================================================================
-- Seed Common Foods
-- ============================================================================

-- PROTEINS
INSERT INTO foods (name, food_type, calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g, is_public, verified) VALUES
('Chicken Breast, Raw', 'ingredient', 165, 31.0, 0.0, 3.6, true, true),
('Chicken Breast, Grilled', 'ingredient', 165, 31.0, 0.0, 3.6, true, true),
('Chicken Thigh, Skinless', 'ingredient', 209, 26.0, 0.0, 10.9, true, true),
('Ground Beef, 80/20', 'ingredient', 254, 17.2, 0.0, 20.0, true, true),
('Ground Beef, 93/7 Lean', 'ingredient', 176, 20.0, 0.0, 10.0, true, true),
('Ribeye Steak', 'ingredient', 291, 24.0, 0.0, 21.8, true, true),
('Sirloin Steak', 'ingredient', 201, 26.0, 0.0, 10.0, true, true),
('Salmon, Atlantic', 'ingredient', 208, 20.4, 0.0, 13.4, true, true),
('Tuna, Canned in Water', 'ingredient', 116, 25.5, 0.0, 0.8, true, true),
('Tilapia', 'ingredient', 128, 26.2, 0.0, 2.7, true, true),
('Whole Egg, Large', 'ingredient', 143, 12.6, 0.7, 9.5, true, true),
('Egg White, Large', 'ingredient', 52, 10.9, 0.7, 0.2, true, true),
('Greek Yogurt, Nonfat', 'ingredient', 59, 10.2, 3.6, 0.4, true, true),
('Cottage Cheese, 1%', 'ingredient', 72, 12.4, 2.7, 1.0, true, true),
('Whey Protein Powder', 'ingredient', 400, 80.0, 10.0, 5.0, true, true);

-- Add servings for proteins
INSERT INTO food_servings (food_id, serving_size, serving_unit, grams_per_serving, is_default) VALUES
-- Chicken Breast (assuming first UUID)
((SELECT id FROM foods WHERE name = 'Chicken Breast, Raw'), 1, 'breast', 174, true),
((SELECT id FROM foods WHERE name = 'Chicken Breast, Raw'), 1, 'oz', 28.35, false),
((SELECT id FROM foods WHERE name = 'Chicken Breast, Raw'), 100, 'g', 100, false),

-- Whole Egg
((SELECT id FROM foods WHERE name = 'Whole Egg, Large'), 1, 'egg', 50, true),
((SELECT id FROM foods WHERE name = 'Whole Egg, Large'), 1, 'oz', 28.35, false),

-- Whey Protein
((SELECT id FROM foods WHERE name = 'Whey Protein Powder'), 1, 'scoop', 30, true),
((SELECT id FROM foods WHERE name = 'Whey Protein Powder'), 1, 'oz', 28.35, false);

-- CARBS
INSERT INTO foods (name, food_type, calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g, fiber_g_per_100g, is_public, verified) VALUES
('White Rice, Cooked', 'ingredient', 130, 2.7, 28.2, 0.3, 0.4, true, true),
('Brown Rice, Cooked', 'ingredient', 112, 2.6, 23.5, 0.9, 1.8, true, true),
('Jasmine Rice, Cooked', 'ingredient', 130, 2.7, 28.2, 0.3, 0.4, true, true),
('Oatmeal, Dry Rolled Oats', 'ingredient', 389, 16.9, 66.3, 6.9, 10.6, true, true),
('Oatmeal, Cooked', 'ingredient', 71, 2.5, 12.0, 1.5, 1.7, true, true),
('Quinoa, Cooked', 'ingredient', 120, 4.4, 21.3, 1.9, 2.8, true, true),
('Pasta, Cooked', 'ingredient', 131, 5.0, 25.1, 1.1, 1.8, true, true),
('Whole Wheat Bread', 'ingredient', 247, 13.0, 41.0, 3.4, 7.0, true, true),
('White Bread', 'ingredient', 265, 9.0, 49.0, 3.2, 2.7, true, true),
('Sweet Potato, Baked', 'ingredient', 90, 2.0, 20.7, 0.2, 3.3, true, true),
('Russet Potato, Baked', 'ingredient', 93, 2.5, 21.2, 0.1, 2.2, true, true);

-- Add servings for carbs
INSERT INTO food_servings (food_id, serving_size, serving_unit, grams_per_serving, is_default) VALUES
-- White Rice
((SELECT id FROM foods WHERE name = 'White Rice, Cooked'), 1, 'cup', 158, true),
((SELECT id FROM foods WHERE name = 'White Rice, Cooked'), 1, 'oz', 28.35, false),

-- Oatmeal (dry)
((SELECT id FROM foods WHERE name = 'Oatmeal, Dry Rolled Oats'), 0.5, 'cup', 40, true),
((SELECT id FROM foods WHERE name = 'Oatmeal, Dry Rolled Oats'), 1, 'oz', 28.35, false),

-- Sweet Potato
((SELECT id FROM foods WHERE name = 'Sweet Potato, Baked'), 1, 'medium', 150, true),
((SELECT id FROM foods WHERE name = 'Sweet Potato, Baked'), 1, 'oz', 28.35, false);

-- ... Continue for vegetables, fruits, fats, etc.
```

### Estimated Effort
- **150 foods** × 2-3 servings each = 300-450 `food_servings` entries
- **Time**: 4-6 hours to research accurate nutrition data
- **Sources**: USDA database, food labels

---

## Priority Action Plan

### Phase 1: Essential Seeding (DO NOW)
1. ✅ Apply migration 005 (`consultation_messages` table)
2. ⏭️ Create migration 006 with **50-100 most common foods**
   - Focus on: chicken, beef, eggs, rice, oats, vegetables, fruits
   - At least 2 servings per food (default + grams)
3. ⏭️ Update ConsultationAIService to use conversation history
4. ⏭️ Test consultation flow end-to-end

**Result**: System works for typical users (80% coverage)

### Phase 2: Expand Food Database (LATER)
- Add 100 more foods (branded items, restaurant chains)
- Add more serving options
- Allow users to create custom foods

### Phase 3: Production Optimization (FUTURE)
- Implement food database from USDA (10,000+ items)
- Elasticsearch for better food search
- Machine learning for automatic food matching
- Photo recognition for meal logging

---

## Summary

### ✅ How We Prevent Duplicate Questions

1. **Store conversation history** (`consultation_messages` table)
2. **Track progress** (`get_consultation_progress()` function)
3. **Include both in LLM context** (enhanced system prompt)
4. **LLM checks before asking** (rules in prompt)

### ✅ What Needs Seeding

**Critical (blocks functionality)**:
- `foods` table - Need 50-100 common foods NOW
- `food_servings` table - 2-3 servings per food

**Already seeded**:
- training_modalities ✅
- exercises ✅
- meal_times ✅
- event_types ✅

### Next Steps

1. Run migration 005 (consultation_messages)
2. Create migration 006 (seed common foods)
3. Update ConsultationAIService to load history + progress
4. Test full consultation conversation
5. Verify no duplicate questions
6. Verify food search works

**ETA**: 1 day to implement, test ready for demo
