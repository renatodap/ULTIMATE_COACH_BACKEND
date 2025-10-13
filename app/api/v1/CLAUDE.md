# API v1 Endpoints

## 📍 Location
`app/api/v1/`

---

# Onboarding API

**File:** `onboarding.py`

## 🎯 Purpose
Collects comprehensive user data during initial onboarding and calculates personalized macro targets using scientific formulas.

## 📋 Endpoints

### POST `/api/v1/onboarding/complete`

**Purpose:** Complete onboarding and save all user data + calculated targets

**Authentication:** Required (JWT via httpOnly cookie)

**Request Body:**
```json
{
  // Goals & Experience
  "primary_goal": "lose_weight",          // lose_weight | build_muscle | maintain | improve_performance
  "experience_level": "beginner",         // beginner | intermediate | advanced
  "workout_frequency": 3,                 // 0-7 workouts per week

  // Physical Stats (ALWAYS IN METRIC)
  "age": 25,                              // 13-120
  "biological_sex": "male",               // male | female
  "height_cm": 178.0,                     // 100-300 cm
  "current_weight_kg": 82.0,              // 30-300 kg
  "goal_weight_kg": 77.0,                 // 30-300 kg

  // Activity Level
  "activity_level": "moderately_active",  // sedentary | lightly_active | moderately_active | very_active | extremely_active

  // Dietary Profile
  "dietary_preference": "none",           // none | vegetarian | vegan | pescatarian | keto | paleo
  "food_allergies": [],                   // Array of strings
  "foods_to_avoid": [],                   // Array of strings
  "meals_per_day": 3,                     // 1-8

  // Lifestyle
  "sleep_hours": 7.5,                     // 4-12
  "stress_level": "medium",               // low | medium | high
  "cooks_regularly": true,                // boolean

  // Preferences
  "unit_system": "imperial",              // metric | imperial (for display only)
  "timezone": "America/New_York"          // IANA timezone
}
```

**Response:**
```json
{
  "profile": {
    // Updated profile with all onboarding data
    "id": "uuid",
    "email": "user@example.com",
    "age": 25,
    "biological_sex": "male",
    "height_cm": 178.0,
    "current_weight_kg": 82.0,
    "goal_weight_kg": 77.0,
    // ... 20+ other fields
    "onboarding_completed": true,
    "onboarding_completed_at": "2025-10-12T15:30:00Z"
  },
  "targets": {
    "bmr": 1845,                          // Basal Metabolic Rate (kcal/day)
    "tdee": 2860,                         // Total Daily Energy Expenditure (kcal/day)
    "daily_calories": 2360,               // Adjusted for goal (deficit/surplus)
    "daily_protein_g": 164,               // Protein target
    "daily_carbs_g": 236,                 // Carbs target
    "daily_fat_g": 78,                    // Fat target
    "explanation": {
      "bmr": "Your BMR is 1845 kcal/day based on Mifflin-St Jeor formula...",
      "tdee": "With moderately active lifestyle, your TDEE is 2860 kcal/day...",
      "calories": "To lose weight, we're setting a 500 kcal daily deficit...",
      "protein": "2.0g per kg bodyweight for muscle preservation...",
      "fats": "25% of calories for hormone health...",
      "carbs": "Remainder of calories for energy...",
      "goal_context": "Estimated 0.5 kg weight loss per week..."
    }
  },
  "message": "Onboarding completed successfully! Your personalized targets are ready."
}
```

**Processing Flow:**
1. **Validate Input** - Pydantic validates all fields with constraints
2. **Calculate BMR** - Uses Mifflin-St Jeor formula:
   - Male: `(10 × weight_kg) + (6.25 × height_cm) - (5 × age) + 5`
   - Female: `(10 × weight_kg) + (6.25 × height_cm) - (5 × age) - 161`
3. **Calculate TDEE** - BMR × activity multiplier:
   - Sedentary: 1.2
   - Lightly Active: 1.375
   - Moderately Active: 1.55
   - Very Active: 1.725
   - Extremely Active: 1.9
4. **Adjust for Goal**:
   - Lose weight: TDEE - 500 kcal (0.5kg/week loss)
   - Gain muscle: TDEE + 300 kcal (lean bulk)
   - Maintain: TDEE (no adjustment)
   - Improve performance: TDEE + 200 kcal (slight surplus)
5. **Calculate Macros**:
   - Protein: 2.0g/kg bodyweight (muscle preservation)
   - Fat: 25% of calories (hormone health)
   - Carbs: Remaining calories
6. **Update Profile** - Saves all 20+ fields to database
7. **Set Flag** - `onboarding_completed = true`
8. **Return Response** - Profile + targets with explanations

**Error Responses:**
- `400 Bad Request` - Invalid input (e.g., age too low, goal weight unrealistic)
- `500 Internal Server Error` - Failed to update profile

---

### GET `/api/v1/onboarding/status`

**Purpose:** Check if user has completed onboarding

**Authentication:** Required

**Response:**
```json
{
  "onboarding_completed": true,
  "onboarding_completed_at": "2025-10-12T15:30:00Z"
}
```

**Use Case:** Frontend checks this after login to determine redirect

---

### GET `/api/v1/onboarding/preview-targets`

**Purpose:** Preview calculated macro targets without saving (for Step 6 UI)

**Authentication:** Required

**Query Parameters:**
- `age` (int)
- `biological_sex` (string)
- `height_cm` (float)
- `current_weight_kg` (float)
- `goal_weight_kg` (float)
- `activity_level` (string)
- `primary_goal` (string)
- `experience_level` (string, optional)

**Response:**
```json
{
  "bmr": 1845,
  "tdee": 2860,
  "daily_calories": 2360,
  "daily_protein_g": 164,
  "daily_carbs_g": 236,
  "daily_fat_g": 78,
  "explanation": { ... }
}
```

**Use Case:** Show user their targets before they finalize onboarding (future enhancement)

---

## 🗄️ Database Schema

**Table:** `profiles`

**Onboarding Fields Added:**
```sql
-- Physical Stats (CANONICAL - always metric)
age                     INTEGER CHECK (age >= 13 AND age <= 120)
biological_sex          TEXT CHECK (biological_sex IN ('male', 'female'))
height_cm               NUMERIC(5, 2) CHECK (height_cm >= 100 AND height_cm <= 300)
current_weight_kg       NUMERIC(5, 2) CHECK (current_weight_kg >= 30 AND current_weight_kg <= 300)
goal_weight_kg          NUMERIC(5, 2) CHECK (goal_weight_kg >= 30 AND goal_weight_kg <= 300)

-- Activity & Lifestyle
activity_level          TEXT CHECK (activity_level IN (...))
workout_frequency       INTEGER CHECK (workout_frequency >= 0 AND workout_frequency <= 7)
sleep_hours             NUMERIC(3, 1) CHECK (sleep_hours >= 4 AND sleep_hours <= 12)
stress_level            TEXT CHECK (stress_level IN ('low', 'medium', 'high'))

-- Dietary Profile
dietary_preference      TEXT CHECK (dietary_preference IN (...))
food_allergies          TEXT[] DEFAULT '{}'
foods_to_avoid          TEXT[] DEFAULT '{}'
meals_per_day           INTEGER CHECK (meals_per_day >= 1 AND meals_per_day <= 8)
cooks_regularly         BOOLEAN DEFAULT TRUE

-- Calculated Targets (saved for reference)
estimated_tdee          INTEGER
daily_calorie_goal      INTEGER
daily_protein_goal      NUMERIC(5, 1)
daily_carbs_goal        NUMERIC(5, 1)
daily_fat_goal          NUMERIC(5, 1)

-- Metadata
macros_last_calculated_at   TIMESTAMPTZ
macros_calculation_reason   TEXT  -- "initial_onboarding", "weight_update", etc.
```

**Indexes:**
- `idx_profiles_onboarding` - Fast lookup for incomplete onboarding
- `idx_profiles_id_onboarding` - Common query pattern

**Migration:** `migrations/002_onboarding_data.sql`

---

## 🧪 Testing

**Manual Test Flow:**
1. POST signup with new user
2. POST `/onboarding/complete` with valid data
3. Verify database updated (all 20+ fields)
4. Verify `onboarding_completed = true`
5. Verify macro calculations are correct
6. GET `/users/me` - should show onboarding data
7. GET `/onboarding/status` - should show completed

**Test Cases:**
- ✅ Valid data → saves correctly
- ✅ Invalid age → 400 error
- ✅ Goal weight too extreme → 400 error
- ✅ Missing required fields → 422 error
- ✅ BMR calculation accurate for male/female
- ✅ TDEE multipliers correct
- ✅ Macro targets sum to total calories

---

## 🔗 Related Files

**Backend:**
- `app/services/macro_calculator.py` - BMR/TDEE/macro formulas
- `app/services/supabase_service.py` - Profile update logic
- `app/models/auth.py` - User response models
- `migrations/002_onboarding_data.sql` - Database schema

**Frontend:**
- `app/onboarding/page.tsx` - Onboarding UI
- `lib/api/onboarding.ts` - API client
- `lib/hooks/useOnboardingCheck.ts` - Enforcement hook

---

## 💡 Future Enhancements

1. **Macro Recalculation**:
   - Endpoint to recalculate when weight/activity changes
   - Automatic recalculation every 2 weeks
   - Track calculation history

2. **Onboarding Updates**:
   - Allow users to update onboarding data later
   - Show what changed and new targets
   - Track updates for AI coach context

3. **Advanced Goals**:
   - Body recomposition (lose fat + gain muscle)
   - Performance-specific (strength vs endurance)
   - Medical conditions (diabetes, PCOS, etc.)

4. **Validation Improvements**:
   - More realistic goal weight ranges
   - Warn if aggressive deficit (> 1kg/week)
   - Suggest safer alternatives

5. **AI Enhancements**:
   - Use GPT-4 to generate personalized explanations
   - Suggest meal plans based on preferences
   - Recommend workout splits based on experience
