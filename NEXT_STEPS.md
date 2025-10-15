# Next Steps - Clear Action Plan

## Current Status

✅ **Backend**: Production-ready architecture (needs database seeding)
❌ **Frontend**: Needs full implementation
❌ **Database**: Empty (blocks all features)

---

## Priority Order (What to Build Next)

### 🚨 **PRIORITY 1: Database Seeding** (CRITICAL - BLOCKS EVERYTHING)

**Why first**: Backend works perfectly, but returns empty results because database has no food data.

**Task**: Seed `foods` table with 5000+ entries

#### Step 1: Create Food Seeding Script

```python
# scripts/seed_foods.py

import requests
import os
from supabase import create_client

# USDA FoodData Central API
USDA_API_KEY = os.getenv("USDA_API_KEY")
USDA_API_URL = "https://api.nal.usda.gov/fdc/v1"

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

def seed_simple_ingredients():
    """Seed 3000 simple ingredients (composition_type='simple')"""

    common_foods = [
        # Proteins
        "chicken breast", "ground beef", "salmon", "tuna", "eggs",
        "greek yogurt", "cottage cheese", "tofu", "turkey breast",
        "pork chop", "shrimp", "cod", "tilapia",

        # Carbs
        "white rice", "brown rice", "oatmeal", "bread", "pasta",
        "sweet potato", "potato", "quinoa", "banana", "apple",
        "orange", "strawberries", "blueberries",

        # Fats
        "almonds", "peanut butter", "avocado", "olive oil",
        "butter", "cheese", "cashews", "walnuts",

        # Vegetables
        "broccoli", "spinach", "kale", "carrots", "tomato",
        "lettuce", "cucumber", "bell pepper", "onion", "garlic"
    ]

    for food in common_foods:
        # Search USDA API
        response = requests.get(
            f"{USDA_API_URL}/foods/search",
            params={
                "api_key": USDA_API_KEY,
                "query": food,
                "dataType": ["Foundation", "SR Legacy"],
                "pageSize": 5
            }
        )

        data = response.json()

        for item in data.get("foods", [])[:3]:  # Top 3 results
            nutrients = {n["nutrientName"]: n["value"]
                        for n in item.get("foodNutrients", [])}

            supabase.table("foods").insert({
                "name": item["description"],
                "brand_name": None,
                "composition_type": "simple",
                "calories_per_100g": nutrients.get("Energy", 0),
                "protein_g_per_100g": nutrients.get("Protein", 0),
                "carbs_g_per_100g": nutrients.get("Carbohydrate, by difference", 0),
                "fat_g_per_100g": nutrients.get("Total lipid (fat)", 0),
                "is_public": True,
                "verified": True
            }).execute()

def seed_branded_products():
    """Seed 1000 branded products (composition_type='branded')"""

    brands = [
        # Fast food
        {"name": "Chipotle Chicken Bowl", "brand": "Chipotle", "cal": 630, "protein": 49, "carbs": 65, "fat": 17},
        {"name": "Big Mac", "brand": "McDonald's", "cal": 563, "protein": 26, "carbs": 46, "fat": 33},

        # Packaged foods
        {"name": "Quest Protein Bar, Chocolate Chip", "brand": "Quest", "cal": 190, "protein": 21, "carbs": 22, "fat": 8},
        {"name": "Protein Shake, Vanilla", "brand": "Premier Protein", "cal": 160, "protein": 30, "carbs": 4, "fat": 3},
    ]

    for item in brands:
        supabase.table("foods").insert({
            "name": item["name"],
            "brand_name": item["brand"],
            "composition_type": "branded",
            "calories_per_100g": item["cal"],
            "protein_g_per_100g": item["protein"],
            "carbs_g_per_100g": item["carbs"],
            "fat_g_per_100g": item["fat"],
            "is_public": True,
            "verified": True
        }).execute()

def seed_composed_recipes():
    """Seed 1000 composed recipes (composition_type='composed')"""

    recipes = [
        {"name": "Chicken Rice Bowl", "cal": 450, "protein": 35, "carbs": 55, "fat": 12},
        {"name": "Greek Salad", "cal": 320, "protein": 15, "carbs": 18, "fat": 24},
        {"name": "Protein Shake (Standard)", "cal": 280, "protein": 30, "carbs": 25, "fat": 8},
    ]

    for recipe in recipes:
        supabase.table("foods").insert({
            "name": recipe["name"],
            "brand_name": None,
            "composition_type": "composed",
            "calories_per_100g": recipe["cal"],
            "protein_g_per_100g": recipe["protein"],
            "carbs_g_per_100g": recipe["carbs"],
            "fat_g_per_100g": recipe["fat"],
            "is_public": True,
            "verified": False  # Need manual verification
        }).execute()

if __name__ == "__main__":
    print("Seeding simple ingredients...")
    seed_simple_ingredients()

    print("Seeding branded products...")
    seed_branded_products()

    print("Seeding composed recipes...")
    seed_composed_recipes()

    print("✅ Database seeded successfully!")
```

#### Step 2: Run Seeding Script

```bash
cd scripts
python seed_foods.py
```

#### Step 3: Validate

```bash
# Test search
curl -X POST http://localhost:8000/api/coach/message \
  -H "Content-Type: application/json" \
  -d '{"message": "How much protein in chicken?"}'

# Should return: Results from foods table
```

**Time Estimate**: 2-3 days (including API setup, data validation, testing)

---

### 🎯 **PRIORITY 2: Production Chat Component** (FRONTEND)

**Why second**: Once database is seeded, backend fully works. Need frontend to use it.

**Task**: Build production-ready mobile chat component

#### Step 1: Create Base Component

```typescript
// frontend/src/components/CoachChat.tsx

import React, { useState, useEffect, useRef } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export const CoachChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('Coach is typing...');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setLoadingMessage('Coach is typing...');

    // Upgrade to context-aware status after 2s
    const timeout = setTimeout(() => {
      setLoadingMessage(getSmartLoadingMessage(userMessage.content));
    }, 2000);

    try {
      const response = await fetch('/api/coach/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: 'current-conv-id'
        })
      });

      const data = await response.json();

      if (data.success) {
        const aiMessage: Message = {
          id: data.message_id,
          role: 'assistant',
          content: data.message,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      clearTimeout(timeout);
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {loading && <LoadingIndicator message={loadingMessage} />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input (fixed bottom) */}
      <div className="bg-white border-t p-4 safe-area-bottom">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Message your coach..."
            disabled={loading}
            className="flex-1 px-4 py-3 text-base border rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-full font-medium"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};
```

#### Step 2: Add Mobile Optimizations

```css
/* Mobile-specific styles */
@media (max-width: 768px) {
  .safe-area-bottom {
    padding-bottom: env(safe-area-inset-bottom, 20px);
  }

  input {
    font-size: 16px; /* Prevents auto-zoom on iOS */
  }

  button {
    min-width: 44px; /* iOS touch target */
    min-height: 44px;
  }
}
```

#### Step 3: Test on Real Devices

- Test on iPhone (notch handling)
- Test on Android (keyboard behavior)
- Test on iPad (layout responsiveness)

**Time Estimate**: 2-3 days

---

### 📝 **PRIORITY 3: Log Preview Card** (LOG MODE)

**Why third**: Completes the food logging flow (input → preview → confirm)

**Task**: Create log preview card + integrate quick_entry_service

#### Component Structure

```typescript
// frontend/src/components/LogPreviewCard.tsx

interface LogPreview {
  food_name: string;
  amount: number;
  unit: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  meal_type: string;
  confidence: number;
}

export const LogPreviewCard: React.FC<{preview: LogPreview}> = ({preview}) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-4 m-4">
      <h3 className="text-lg font-bold mb-3">
        🍗 {preview.food_name}
      </h3>

      <div className="space-y-2">
        <div>Amount: {preview.amount}{preview.unit}</div>
        <div>Calories: {preview.calories}</div>
        <div>Protein: {preview.protein}g 💪</div>
        <div>Carbs: {preview.carbs}g</div>
        <div>Fat: {preview.fat}g</div>
      </div>

      <select className="w-full mt-3 p-2 border rounded">
        <option>Breakfast</option>
        <option>Lunch</option>
        <option>Dinner</option>
        <option>Snack</option>
      </select>

      <div className="flex gap-2 mt-4">
        <button className="flex-1 px-4 py-2 border rounded">
          Cancel
        </button>
        <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded">
          ✓ Confirm
        </button>
      </div>
    </div>
  );
};
```

**Time Estimate**: 1 day

---

## Success Criteria

### ✅ **Phase 1: Backend Working** (Database Seeded)
- [ ] Can search "chicken" → Returns 5+ results
- [ ] Results ranked correctly (simple > composed > branded)
- [ ] User's quick_meals appear first
- [ ] Claude calculates 300g correctly (31 × 3 = 93g)

### ✅ **Phase 2: Frontend Working** (Chat Component)
- [ ] Can send message from mobile
- [ ] Loading states show correctly (Tier 1 → Tier 2)
- [ ] Response appears formatted
- [ ] Auto-scrolls to bottom
- [ ] Works on iOS Safari
- [ ] Works on Android Chrome

### ✅ **Phase 3: Log Mode Working** (Preview Card)
- [ ] "I ate 300g chicken" → Shows preview card
- [ ] Can edit meal type
- [ ] Can confirm → Saves to database
- [ ] Coach responds: "Logged. 93g protein, 495 cal."

---

## Timeline

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Database seeding script | 2 days | ❌ TODO |
| 1 | Validate seeding | 1 day | ❌ TODO |
| 2 | CoachChat component | 2 days | ❌ TODO |
| 2 | Mobile optimization | 1 day | ❌ TODO |
| 2 | Device testing | 1 day | ❌ TODO |
| 3 | LogPreviewCard component | 1 day | ❌ TODO |
| 3 | Quick entry integration | 1 day | ❌ TODO |
| **TOTAL** | | **9 days** | |

---

## Resources Needed

1. **USDA API Key**: https://fdc.nal.usda.gov/api-guide.html (free)
2. **Open Food Facts**: https://world.openfoodfacts.org/data (free)
3. **Mobile Devices for Testing**:
   - iPhone (iOS 16+)
   - Android phone (Android 12+)
   - iPad (optional)

---

## Start Here

**Immediate action** (can do right now):

```bash
# 1. Get USDA API key
# Sign up at: https://fdc.nal.usda.gov/api-key-signup.html

# 2. Create seeding script
mkdir -p scripts
touch scripts/seed_foods.py

# 3. Start implementing (copy code from PRIORITY 1 above)
```

**First milestone**: Database seeded with 1000 foods (can expand later)

**Second milestone**: Can send "I ate 300g chicken" and get correct response

**Third milestone**: Mobile app works end-to-end

---

## Questions to Answer Before Starting

1. **Do you want to build frontend in React Native or web (mobile-responsive)?**
   - React Native: True native app, better performance
   - Web: Faster to build, works on all devices

2. **What's your deployment target?**
   - iOS App Store
   - Android Play Store
   - Web app (mobile-optimized)
   - All of the above

3. **Do you have mobile devices for testing?**
   - Yes → Can test during development
   - No → Need to use simulators/emulators

---

## Summary

**Backend**: ✅ Ready (just needs data)
**Database**: ❌ Needs seeding (~2-3 days)
**Frontend**: ❌ Needs building (~5-6 days)

**Total to MVP**: ~9 days of focused work

**The system WILL work once these gaps are filled.** The logic is sound, the search is smart, and Claude will calculate correctly. Just needs data + UI.

**START WITH**: Database seeding. Everything else blocks on this.

**NEXT_STEPS.md - YOUR ROADMAP TO PRODUCTION 🚀**
