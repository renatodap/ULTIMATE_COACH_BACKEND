# Feature Design: Manual Meal Logging

**Version:** 2.0 (Production Refactor)
**Status:** Design Complete
**Last Updated:** 2025-10-12

---

## 1. Overview

Manual meal logging allows users to search for foods, select serving sizes, and create meal entries with automatic nutrition calculation. This is the foundation for nutrition tracking before adding AI-powered features.

---

## 2. User Stories

### Primary User Stories

**US-1: Search for Foods**
- **As a** user logging a meal
- **I want to** search for foods by name
- **So that** I can quickly find what I ate

**Acceptance Criteria:**
- Search returns results after 2+ characters
- Results show food name, brand, and common serving size
- Results include both public foods and my custom foods
- Search is fast (<500ms) and debounced

**US-2: Log a Meal**
- **As a** user
- **I want to** add multiple foods to a meal with quantities
- **So that** I can track what I ate

**Acceptance Criteria:**
- Can select meal type (breakfast, lunch, dinner, snack, other)
- Can add multiple foods to one meal
- Can choose serving size (scoop, cup, oz, piece, grams)
- Can specify quantity (0.5, 1, 2, etc.)
- Nutrition totals calculated automatically
- Can add optional notes
- Can set custom timestamp

**US-3: View Meal History**
- **As a** user
- **I want to** see all my logged meals
- **So that** I can track my nutrition over time

**Acceptance Criteria:**
- Shows meals grouped by date
- Shows meal type, foods, and nutrition totals
- Can filter by date range
- Can edit or delete meals
- Fast loading with pagination

**US-4: Create Custom Food**
- **As a** user
- **I want to** add a food that's not in the database
- **So that** I can log everything I eat

**Acceptance Criteria:**
- Can enter food name, brand
- Must specify serving size with grams per serving
- Must enter nutrition per serving
- Custom foods are private to me
- Can use custom food in meal logging

### Secondary User Stories

**US-5: View Daily Nutrition Stats**
- **As a** user
- **I want to** see my daily nutrition summary
- **So that** I can track progress toward goals

**US-6: Quick Actions**
- **As a** user
- **I want to** duplicate or delete meals quickly
- **So that** logging is efficient

---

## 3. User Flows

### Flow 1: Log a Meal (Happy Path)

```
1. User navigates to Nutrition tab
2. User taps "Log Meal" button
3. User selects meal type (breakfast)
4. User taps "Add Food"
5. User types "chicken breast" in search
6. Search shows results (Grilled Chicken Breast, Raw Chicken Breast, etc.)
7. User selects "Grilled Chicken Breast"
8. Modal shows serving options:
   - 1 medium breast (174g) [DEFAULT]
   - 100g
   - 1 oz (28g)
9. User selects "1 medium breast"
10. User adjusts quantity to 1.5
11. User taps "Add to Meal"
12. Food appears in meal with nutrition preview
13. User repeats for "brown rice" (1 cup)
14. User sees meal totals: 520 cal, 58g protein, 45g carbs, 8g fat
15. User taps "Log Meal"
16. Success toast: "Breakfast logged! 520 calories"
17. User returns to nutrition dashboard
```

### Flow 2: Create Custom Food

```
1. User searches for "grandma's protein cookies"
2. No results found
3. User taps "Create Custom Food"
4. User fills form:
   - Name: "Grandma's Protein Cookies"
   - Brand: (blank)
   - Serving: 1 cookie
   - Grams per serving: 25g
   - Calories: 120
   - Protein: 8g
   - Carbs: 12g
   - Fat: 4g
5. User taps "Create"
6. Food saved and appears in search results
7. User can now log it in meals
```

### Flow 3: View & Edit Meal History

```
1. User navigates to Nutrition > History
2. Sees meals grouped by date (today, yesterday, etc.)
3. User taps on breakfast from yesterday
4. Modal shows meal details with all foods
5. User taps "Edit"
6. Can adjust quantities or remove foods
7. User taps "Save"
8. Meal updated, totals recalculated
```

---

## 4. Component Hierarchy

```
NutritionPage
├── NutritionStats (daily summary card)
├── MealHistoryList
│   ├── MealCard (per meal)
│   │   ├── MealHeader (type, time, calories)
│   │   ├── FoodItemsList
│   │   │   └── FoodItem (name, quantity, macros)
│   │   └── MealActions (edit, delete, duplicate)
│   └── LoadMoreButton
└── FloatingActionButton (+ Log Meal)

LogMealModal
├── MealTypeSelector (breakfast, lunch, dinner, snack)
├── FoodSearchBar (debounced search)
├── FoodResultsList
│   └── FoodCard (name, brand, tap to add)
├── AddedFoodsList
│   └── AddedFoodItem (with quantity controls)
├── MealTotalsCard (calories, protein, carbs, fat)
└── LogMealButton

AddFoodModal
├── FoodDetails (nutrition per 100g)
├── ServingSizeSelector (dropdown)
├── QuantityInput (numeric with +/- buttons)
├── NutritionPreview (calculated for quantity)
└── AddButton

CreateCustomFoodModal
├── BasicInfoForm (name, brand)
├── ServingDefinition (size, unit, grams)
├── NutritionForm (calories, protein, carbs, fat, fiber)
└── CreateButton
```

---

## 5. API Integration Points

### Backend Endpoints

```
GET  /api/v1/foods/search?q={query}&limit=20
     → Returns: { foods: Food[], total: number }

GET  /api/v1/foods/{food_id}
     → Returns: Food (with servings array)

POST /api/v1/foods/custom
     Body: { name, brand_name, serving_size, serving_unit,
             grams_per_serving, calories, protein_g, carbs_g, fat_g }
     → Returns: Food

POST /api/v1/meals
     Body: { meal_type, logged_at?, notes?, items: [
       { food_id, serving_id, quantity }
     ]}
     → Returns: Meal (with calculated totals)

GET  /api/v1/meals?start_date={date}&end_date={date}&limit=50&offset=0
     → Returns: { meals: Meal[], total: number }

GET  /api/v1/meals/{meal_id}
     → Returns: Meal (with items)

DELETE /api/v1/meals/{meal_id}
     → Returns: 204 No Content

GET  /api/v1/nutrition/stats?date={YYYY-MM-DD}
     → Returns: NutritionStats (consumed vs goals)
```

### Error Codes (NEW)

```typescript
enum NutritionErrorCode {
  // Search
  SEARCH_QUERY_TOO_SHORT = 'NUTRITION_001',
  SEARCH_FAILED = 'NUTRITION_002',

  // Food
  FOOD_NOT_FOUND = 'NUTRITION_101',
  FOOD_ACCESS_DENIED = 'NUTRITION_102',
  INVALID_SERVING = 'NUTRITION_103',

  // Meal
  MEAL_NOT_FOUND = 'NUTRITION_201',
  MEAL_EMPTY = 'NUTRITION_202',
  MEAL_ITEM_INVALID = 'NUTRITION_203',
  NUTRITION_CALC_FAILED = 'NUTRITION_204',

  // Custom Food
  CUSTOM_FOOD_INVALID_SERVING = 'NUTRITION_301',
  CUSTOM_FOOD_DUPLICATE = 'NUTRITION_302',
}
```

---

## 6. State Management

### Global State (React Context)

```typescript
interface NutritionContextValue {
  // Current meal being logged
  currentMeal: {
    meal_type: MealType
    items: MealItemInput[]
    notes?: string
    logged_at?: Date
  } | null

  // Actions
  startMeal: (type: MealType) => void
  addFoodToMeal: (food: Food, serving: FoodServing, quantity: number) => void
  removeFoodFromMeal: (index: number) => void
  updateFoodQuantity: (index: number, quantity: number) => void
  saveMeal: () => Promise<Meal>
  cancelMeal: () => void

  // Meal history
  meals: Meal[]
  isLoadingMeals: boolean
  loadMeals: (dateRange?: DateRange) => Promise<void>
  deleteMeal: (id: string) => Promise<void>

  // Daily stats
  dailyStats: NutritionStats | null
  loadDailyStats: (date: string) => Promise<void>
}
```

### Local Component State

- Search query & results (FoodSearchBar)
- Modal open/closed states
- Form validation errors
- Loading states per action

---

## 7. Data Models

### TypeScript Types (with Zod validation)

```typescript
import { z } from 'zod'

// Food
export const FoodServingSchema = z.object({
  id: z.string().uuid(),
  food_id: z.string().uuid(),
  serving_size: z.number().positive(),
  serving_unit: z.string().min(1),
  serving_label: z.string().optional(),
  grams_per_serving: z.number().positive(),
  is_default: z.boolean(),
  display_order: z.number().int(),
  created_at: z.string().datetime(),
})

export const FoodSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  brand_name: z.string().optional(),

  // Nutrition per 100g
  calories_per_100g: z.number().min(0),
  protein_g_per_100g: z.number().min(0),
  carbs_g_per_100g: z.number().min(0),
  fat_g_per_100g: z.number().min(0),
  fiber_g_per_100g: z.number().min(0).optional(),

  servings: z.array(FoodServingSchema),

  food_type: z.enum(['ingredient', 'dish', 'branded', 'restaurant']).optional(),
  is_public: z.boolean(),
  verified: z.boolean(),

  created_by: z.string().uuid().optional(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
})

export type Food = z.infer<typeof FoodSchema>
export type FoodServing = z.infer<typeof FoodServingSchema>

// Meal
export const MealItemSchema = z.object({
  id: z.string().uuid(),
  meal_id: z.string().uuid(),
  food_id: z.string().uuid(),
  quantity: z.number().positive(),
  serving_id: z.string().uuid(),
  grams: z.number().positive(),
  calories: z.number().min(0),
  protein_g: z.number().min(0),
  carbs_g: z.number().min(0),
  fat_g: z.number().min(0),
  display_unit: z.string(),
  display_label: z.string().optional(),
  created_at: z.string().datetime(),
})

export const MealSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  name: z.string().optional(),
  meal_type: z.enum(['breakfast', 'lunch', 'dinner', 'snack', 'other']),
  logged_at: z.string().datetime(),
  notes: z.string().optional(),

  total_calories: z.number().min(0),
  total_protein_g: z.number().min(0),
  total_carbs_g: z.number().min(0),
  total_fat_g: z.number().min(0),

  source: z.enum(['manual', 'ai_text', 'ai_voice', 'ai_photo', 'coach_chat']),
  ai_confidence: z.number().min(0).max(1).optional(),

  items: z.array(MealItemSchema),

  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
})

export type Meal = z.infer<typeof MealSchema>
export type MealItem = z.infer<typeof MealItemSchema>
```

---

## 8. Edge Cases & Error States

### Edge Cases

1. **Food with no servings**
   - Should never happen (database constraint)
   - If happens: show error, prevent logging

2. **Serving deleted while meal open**
   - Refresh servings on modal open
   - Show error if serving unavailable

3. **User deletes custom food used in past meals**
   - Keep meal_items intact (denormalized data)
   - Show "[Deleted Food]" in history

4. **Duplicate simultaneous meal logs**
   - Backend uses optimistic concurrency
   - Frontend shows latest state after save

5. **Very large quantities** (100+ servings)
   - Validate max quantity (e.g., 50)
   - Prevent accidental typos

6. **Fractional quantities** (0.33, 1.75)
   - Support up to 2 decimal places
   - UI has increment buttons (0.25, 0.5, 1)

### Error States

1. **Search fails**
   - Show inline error: "Search unavailable. Try again."
   - Retry button
   - Allow proceeding with custom food

2. **Meal save fails**
   - Show error modal: "Failed to log meal"
   - Keep meal data in state
   - Retry or save as draft

3. **Network offline**
   - Detect offline state
   - Show banner: "Offline - changes will sync when connected"
   - Queue operations (future: offline support)

4. **Food details load fails**
   - Show skeleton → error state
   - Retry button
   - Allow canceling

---

## 9. Accessibility Requirements

- **Keyboard Navigation:** Full tab order, Enter to select
- **Screen Reader:** All interactive elements labeled
- **Focus Indicators:** Visible rings on all focusable elements
- **ARIA:** Proper roles, labels, live regions for updates
- **Color Contrast:** WCAG AA (4.5:1 text, 3:1 UI)
- **Touch Targets:** Minimum 44x44px on mobile
- **Error Announcements:** Screen reader announces validation errors

---

## 10. Performance Requirements

- **Initial Load:** <2s (nutrition page)
- **Search Response:** <500ms (debounced)
- **Meal Save:** <1s
- **Page Transitions:** <200ms
- **Bundle Size:** Lazy load meal logging components (<100KB initial)

---

## 11. Security Considerations

- **Authentication:** All endpoints require valid session
- **Authorization:** Users can only access their own meals/foods
- **Input Validation:** Zod validation on frontend + backend
- **XSS Prevention:** Sanitize user input (names, notes)
- **CSRF:** httpOnly cookies with SameSite
- **Rate Limiting:** Max 100 requests/min per user (future)

---

## 12. Internationalization (i18n) Strategy

### Error Messages
- Use error codes instead of hardcoded strings
- Lookup table for translations
- Example: `t('NUTRITION_001')` → "Search query too short"

### Number Formatting
- Use Intl.NumberFormat for nutrition values
- Support different decimal separators

### Date/Time
- Use date-fns with locale support
- Show timestamps in user's timezone

### Measurement Units
- Default: Metric (grams) or Imperial (ounces) based on user preference
- Allow switching in settings

---

## 13. Success Metrics

- **Feature Adoption:** % of users who log at least 1 meal in first week
- **Engagement:** Average meals logged per active user per week
- **Time to Log:** Average time from tap "Log Meal" to save (<60s target)
- **Error Rate:** <1% of meal logs fail
- **Search Satisfaction:** % of searches that result in food selection

---

## 14. Future Enhancements

- **AI-powered food detection** from photos
- **Voice input** for meal logging
- **Meal templates** (save & reuse common meals)
- **Barcode scanning**
- **Restaurant menu integration**
- **Offline support** with sync
- **Meal sharing** between users
- **Nutrition insights** and recommendations
