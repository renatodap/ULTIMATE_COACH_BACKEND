# 🐛 Known Issues & Fixes

**Status**: Comprehensive audit complete
**Date**: Current
**Confidence**: Issues found will prevent deployment without fixes

---

## ⚠️ **CRITICAL ISSUES** (Must Fix Before Deploy)

### 1. **Frontend: localStorage Not Available in React Native**

**File**: `integration/frontend/src/services/programApi.ts:42`

**Problem**:
```typescript
const token = localStorage.getItem('auth_token'); // ❌ localStorage doesn't exist in React Native
```

**Fix**:
```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Replace line 41-46 with:
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

**Dependencies to add**:
```bash
npm install @react-native-async-storage/async-storage
```

---

### 2. **Backend: Database Field Name Inconsistency**

**File**: `integration/backend/app/api/v1/programs.py:164`

**Problem**:
```python
"data": plan_json,  # ❌ Field name doesn't match schema
```

The migration uses `plan_data` but the code uses `data`.

**Fix**: Choose one consistently:
```python
# Option A: Use "plan_data" everywhere
"plan_data": plan_json,

# Option B: Update all references to use "data"
# Then update SQL functions to use "data" instead of "plan_data"
```

**Recommendation**: Use `plan_data` to match the migration schema.

---

### 3. **Backend: Incomplete Grocery List Endpoint**

**File**: `integration/backend/app/api/v1/programs.py:619-656`

**Problem**:
```python
grocery_list = grocery_gen.generate_grocery_list(
    meal_plans=[],  # ❌ Empty list - won't work
    bulk_buying=True
)
```

**Fix**:
```python
# Either:
# A) Store grocery list in database during generation
# B) Regenerate from plan_data JSON

# Recommended Fix A:
@router.get("/{user_id}/grocery-list")
async def get_grocery_list(user_id: str, supabase=Depends(get_supabase_client)):
    plan = await get_active_plan(user_id, supabase)
    grocery_data = plan['plan_data'].get('grocery_list', {})

    if not grocery_data:
        raise HTTPException(status_code=404, detail="Grocery list not generated")

    return grocery_data
```

---

### 4. **Backend: SQL Index Syntax Error**

**File**: `integration/backend/database/functions.sql:474, 477, 480`

**Problem**:
```sql
CREATE INDEX IF NOT EXISTS idx_meals_user_date
    ON meals(user_id, created_at::DATE);  -- ❌ Can't index casted expressions directly
```

**Fix**:
```sql
-- Use functional index syntax:
CREATE INDEX IF NOT EXISTS idx_meals_user_date
    ON meals(user_id, (created_at::DATE));

CREATE INDEX IF NOT EXISTS idx_activities_user_date
    ON activities(user_id, (created_at::DATE));

CREATE INDEX IF NOT EXISTS idx_body_metrics_user_date
    ON body_metrics(user_id, (recorded_at::DATE));
```

---

### 5. **Backend: Missing Database Field**

**File**: `integration/backend/app/api/v1/programs.py:260, 305`

**Problem**:
```python
.eq("is_active", True)  # ❌ Migration uses "status" not "is_active"
```

**Fix**:
```python
# Replace all instances of:
.eq("is_active", True)

# With:
.eq("status", "active")
```

**Count**: 4 occurrences in programs.py

---

## ⚠️ **HIGH PRIORITY ISSUES** (Will Cause Runtime Errors)

### 6. **Frontend: Missing gap Style Property**

**Files**: Multiple component files

**Problem**:
```typescript
style={{ flexDirection: 'row', gap: 8 }}  // ❌ 'gap' not supported in React Native StyleSheet
```

**Fix**:
```typescript
// Replace with marginHorizontal on children or View wrappers
<View style={{ flexDirection: 'row' }}>
  <View style={{ marginRight: 8 }}>...</View>
  <View>...</View>
</View>
```

**Affected files**:
- `AdjustmentCard.tsx:26`
- `ProgressScreen.tsx:37`

---

### 7. **Backend: Import Path Dependency**

**File**: `integration/backend/app/api/v1/programs.py:28-38`

**Problem**:
```python
from ultimate_ai_consultation.services.program_generator import ...
# ❌ Requires ULTIMATE_AI_CONSULTATION_PATH to be in sys.path
```

**Fix**:
Add to programs.py before imports:
```python
import sys
import os
from pathlib import Path

# Add ultimate_ai_consultation to path
ultimate_ai_path = os.getenv("ULTIMATE_AI_CONSULTATION_PATH")
if ultimate_ai_path and ultimate_ai_path not in sys.path:
    sys.path.insert(0, ultimate_ai_path)
```

---

### 8. **Backend: Supabase Query Syntax**

**File**: `integration/backend/app/api/v1/programs.py:257-262`

**Problem**:
```python
result = supabase.table("plan_versions")\
    .select("*")\
    .eq("user_id", user_id)\
    .eq("status", "active")\
    .single()\  # ❌ .single() might raise exception if no result
    .execute()
```

**Fix**:
```python
result = supabase.table("plan_versions")\
    .select("*")\
    .eq("user_id", user_id)\
    .eq("status", "active")\
    .maybe_single()\  # Returns None instead of error
    .execute()

if not result.data:
    raise HTTPException(status_code=404, detail="No active plan found")
```

---

## 🔶 **MEDIUM PRIORITY ISSUES** (May Cause Issues)

### 9. **Frontend: Chart Library Compatibility**

**File**: `integration/frontend/src/components/WeightChart.tsx`

**Problem**:
```typescript
import { LineChart } from 'react-native-chart-kit';
// Version-specific API - may have breaking changes
```

**Fix**:
Pin version in package.json:
```json
"react-native-chart-kit": "6.12.0"
```

---

### 10. **Backend: Missing Error Handling**

**File**: `integration/backend/app/services/unified_coach_enhancements.py:52`

**Problem**:
```python
response = anthropic.messages.create(...)
# ❌ No timeout, no retry logic
```

**Fix**:
```python
import anthropic

try:
    response = anthropic.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1000,
        messages=[{"role": "user", "content": extraction_prompt}],
        temperature=0.0,
        timeout=10.0,  # Add timeout
    )
except anthropic.APITimeoutError:
    return {"extraction_confidence": 0.0, "error": "timeout"}
except Exception as e:
    return {"extraction_confidence": 0.0, "error": str(e)}
```

---

### 11. **Backend: Type Mismatch**

**File**: `integration/backend/app/models/program.py:178`

**Problem**:
```python
class ProgramSummary(BaseModel):
    created_at: datetime  # Backend returns ISO string, not datetime
```

**Fix**:
```python
created_at: str  # Or use validator to parse ISO string
```

---

### 12. **Frontend: Navigation Type Safety**

**Files**: All screen files

**Problem**:
```typescript
navigation: any  // ❌ No type safety
```

**Fix**:
```typescript
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  ProgramDashboard: undefined;
  Workout: { workout: WorkoutSession };
  // ... other screens
};

type Props = {
  userId: string;
  navigation: NativeStackNavigationProp<RootStackParamList, 'ProgramDashboard'>;
};
```

---

## 🔷 **LOW PRIORITY ISSUES** (Polish/Optimization)

### 13. **Backend: No Request Validation**

**Files**: Multiple endpoint files

**Issue**: Missing input validation for user_id format

**Fix**: Add validators:
```python
from pydantic import validator, UUID4

@validator('user_id')
def validate_user_id(cls, v):
    try:
        UUID4(v)
    except:
        raise ValueError("Invalid user_id format")
    return v
```

---

### 14. **Frontend: No Loading States**

**Files**: Multiple screen components

**Issue**: Abrupt transitions without skeletons

**Recommendation**: Add skeleton loaders from `react-native-skeletons`

---

### 15. **Backend: SQL N+1 Query**

**File**: `integration/backend/database/functions.sql:190-194`

**Issue**: Subquery in SELECT can be slow

**Optimization**:
```sql
-- Use JOIN instead of subquery
LEFT JOIN (SELECT ...) expected_workouts ON TRUE
```

---

## 📋 **VERIFICATION CHECKLIST**

Before deploying, verify:

### Backend
- [ ] Fix `is_active` → `status` (4 places)
- [ ] Fix `data` → `plan_data` (3 places)
- [ ] Fix SQL index syntax (3 places)
- [ ] Add sys.path setup for imports
- [ ] Fix `.single()` → `.maybe_single()`
- [ ] Complete grocery list endpoint
- [ ] Add Anthropic API timeout

### Frontend
- [ ] Replace `localStorage` with `AsyncStorage`
- [ ] Remove `gap` style property (2 places)
- [ ] Pin chart library version
- [ ] Add navigation types
- [ ] Test on both iOS and Android

### Database
- [ ] Run migration first
- [ ] Then run functions.sql with fixes
- [ ] Verify all functions compile
- [ ] Test queries with sample data

---

## 🚀 **DEPLOYMENT SEQUENCE**

1. **Backend Fixes** (2-3 hours)
   ```bash
   # Fix programs.py (7 changes)
   # Fix functions.sql (3 changes)
   # Test endpoints
   ```

2. **Frontend Fixes** (1-2 hours)
   ```bash
   # Fix programApi.ts (AsyncStorage)
   # Fix component styles (gap removal)
   # Test on device
   ```

3. **Integration Testing** (2 hours)
   ```bash
   # Generate program
   # View dashboard
   # Complete workout
   # Check progress
   ```

**Total estimated debug time**: 5-7 hours

---

## 💯 **CONFIDENCE LEVELS**

| Category | Confidence | Notes |
|----------|------------|-------|
| **Critical Issues** | 100% | Will fail without fixes |
| **High Priority** | 95% | Will cause runtime errors |
| **Medium Priority** | 80% | May cause issues under load |
| **Low Priority** | 60% | Polish items |

---

## ✅ **QUICK FIX SCRIPT**

Create `integration/fixes.sh`:

```bash
#!/bin/bash

echo "Applying critical fixes..."

# Fix 1: Backend is_active → status
sed -i 's/.eq("is_active", True)/.eq("status", "active")/g' integration/backend/app/api/v1/programs.py

# Fix 2: Backend data → plan_data
sed -i 's/"data": plan_json/"plan_data": plan_json/g' integration/backend/app/api/v1/programs.py
sed -i "s/plan\['data'\]/plan['plan_data']/g" integration/backend/app/api/v1/programs.py

# Fix 3: SQL indexes
sed -i 's/ON meals(user_id, created_at::DATE)/ON meals(user_id, (created_at::DATE))/g' integration/backend/database/functions.sql

echo "Critical fixes applied. Manual verification needed for:"
echo "- programApi.ts: localStorage → AsyncStorage"
echo "- Component styles: remove gap property"
echo "- Test all endpoints"
```

---

## 🎯 **BOTTOM LINE**

**Original claim**: 6 hours integration time
**Reality**: 6 hours + 5-7 hours debugging = **11-13 hours total**

**Revised confidence**: 85% this will work after applying fixes above.

The architecture is solid. The code is well-structured. But there are **7 critical bugs** that WILL prevent deployment. After fixing these, you'll have a working system.
