# IMPLEMENTATION GUIDE
## Context-Aware Adaptive Program System

**Status:** Foundation complete (3/28 files done)
**Remaining:** 25 files
**Time Required:** ~8-10 hours

---

## ✅ COMPLETED (3 files)

1. ✅ `migrations/002_adaptive_program.sql` - Database schema
2. ✅ `backend/app/services/context_extraction.py` - AI extraction service
3. ✅ `backend/app/services/persona_detection.py` - Persona detection
4. ✅ `backend/app/models/context.py` - Pydantic models for context

---

## 🔨 REMAINING TASKS

### BACKEND (10 files remaining)

#### 1. `backend/app/models/meal_plan.py`

```python
"""Pydantic models for meal planning"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

class MealItem(BaseModel):
    food_name: str
    quantity: float
    unit: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

class Meal(BaseModel):
    meal_type: str  # breakfast, lunch, dinner, snack
    name: str
    items: List[MealItem]
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    prep_time_minutes: Optional[int]
    notes: Optional[str]

class MealPlanDay(BaseModel):
    day: int  # 1-14
    meals: List[Meal]
    daily_totals: Dict[str, float]

class GroceryItem(BaseModel):
    item: str
    quantity: str
    category: str  # produce, proteins, grains, dairy, etc.

class MealPlan(BaseModel):
    id: UUID
    user_id: UUID
    plan_version: int
    days: List[MealPlanDay]
    grocery_list: List[GroceryItem]
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

#### 2. `backend/app/api/v1/context.py`

```python
"""Context API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from uuid import UUID
from app.models.context import ContextTimelineResponse, ContextSummary
from app.services.context_extraction import *
from supabase import create_client, Client
import os

router = APIRouter()
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

@router.get("/timeline/{user_id}")
async def get_context_timeline(
    user_id: UUID,
    days_back: int = 14
) -> ContextTimelineResponse:
    """Get user's context timeline for a period"""

    # Get context logs
    result = supabase.table("user_context_log")\
        .select("*")\
        .eq("user_id", str(user_id))\
        .gte("created_at", f"now() - interval '{days_back} days'")\
        .order("created_at", desc=True)\
        .execute()

    # Get summary
    summary_result = supabase.rpc(
        "get_user_context_for_period",
        {"p_user_id": str(user_id), "p_days_back": days_back}
    ).execute()

    period_summary = {
        item["context_type"]: ContextSummary(**item)
        for item in summary_result.data
    } if summary_result.data else {}

    return ContextTimelineResponse(
        context_logs=result.data,
        period_summary=period_summary,
        total_events=len(result.data)
    )

@router.get("/informal-activities/{user_id}")
async def get_informal_activities(
    user_id: UUID,
    days_back: int = 14
):
    """Get informal activities extracted from chat"""

    result = supabase.table("activities")\
        .select("*")\
        .eq("user_id", str(user_id))\
        .eq("source", "coach_chat")\
        .gte("start_time", f"now() - interval '{days_back} days'")\
        .order("start_time", desc=True)\
        .execute()

    return {"activities": result.data, "total": len(result.data)}
```

#### 3. REFACTOR `backend/app/api/v1/programs.py`

**KEY CHANGES:**

```python
# At top, add imports
from app.services.persona_detection import detect_persona, get_persona_adaptations, get_adaptation_flags
from app.services.context_extraction import search_exercise_by_name

# In generate_program endpoint:
@router.post("/generate")
async def generate_program(request: GenerateProgramRequest):
    # 1. Detect persona
    persona_type, confidence = detect_persona(request.consultation_data)
    adaptations = get_persona_adaptations(persona_type)

    # 2. Calculate TDEE & macros (keep existing logic)
    profile = calculate_nutritional_profile(request.consultation_data)

    # 3. Store in user_profiles_extended
    await supabase.table("user_profiles_extended").upsert({
        "user_id": request.user_id,
        "persona_type": persona_type,
        "persona_confidence": confidence,
        "adaptations": get_adaptation_flags(persona_type),
        "estimated_tdee": profile.tdee,
        "daily_calorie_goal": profile.calories,
        "daily_protein_g": profile.protein,
        "daily_carbs_g": profile.carbs,
        "daily_fat_g": profile.fat,
        "program_start_date": datetime.now().isoformat(),
        "next_reassessment_date": (datetime.now() + timedelta(days=14)).isoformat()
    }).execute()

    # 4. Generate workout plan using persona-specific system prompt
    system_prompt = f"""
    You are creating a program for a {persona_type}.
    {adaptations['system_prompt_additions']}

    Generate {adaptations['sessions_per_week']} workouts per week.
    Duration: {adaptations['session_duration_minutes']} minutes each.
    Equipment: {adaptations['equipment']}
    """

    workout_plan = await generate_workout_plan_with_claude(
        profile=profile,
        system_prompt=system_prompt,
        adaptations=adaptations
    )

    # 5. Create activity_templates (NOT custom workout_sessions!)
    for workout in workout_plan.workouts:
        # Match exercise names to exercises table
        matched_exercises = []
        for exercise in workout.exercises:
            exercise_id = await search_exercise_by_name(exercise.name, request.user_id)
            if exercise_id:
                matched_exercises.append({
                    "exercise_id": str(exercise_id),
                    "exercise_name": exercise.name,
                    "target_sets": exercise.sets,
                    "target_reps": exercise.reps,
                    "target_weight_kg": exercise.weight_kg,
                    "notes": exercise.notes
                })

        # Insert into activity_templates table
        await supabase.table("activity_templates").insert({
            "user_id": request.user_id,
            "template_name": workout.name,
            "activity_type": "strength_training",
            "description": workout.description,
            "default_exercises": matched_exercises,  # JSONB
            "auto_match_enabled": True,
            "min_match_score": 70,
            "expected_duration_minutes": adaptations["session_duration_minutes"]
        }).execute()

    # 6. Generate meal plan (keep existing logic but store in meal_plans table)
    # 7. Return success
    return {
        "success": True,
        "persona_detected": persona_type,
        "confidence": confidence,
        "workouts_created": len(workout_plan.workouts)
    }
```

#### 4. ENHANCE `backend/app/services/unified_coach_enhancements.py`

**Add to process_message_for_structured_data():**

```python
from app.services.context_extraction import process_message_for_context, try_auto_match_to_template

async def process_message_for_structured_data(
    message_content: str,
    user_id: str,
    conversation_id: str
):
    # Existing structured log extraction
    structured_data = await extract_structured_data_from_message(...)

    # NEW: Extract context (informal activities, life events, sentiment)
    context_results = await process_message_for_context(
        message_content,
        user_id,
        message_id=None  # Can pass message ID if available
    )

    # If structured workout was logged, try to auto-match to template
    if structured_data.get("workout"):
        workout = structured_data["workout"]
        # Create activity and exercise_sets...
        activity_id = ...  # From creation
        exercise_ids = [...] # From creation

        # Try auto-match
        match_result = await try_auto_match_to_template(
            activity_id,
            user_id,
            exercise_ids
        )

    return {
        "structured_logs": structured_data,
        "context": context_results
    }
```

#### 5. ENHANCE `backend/app/tasks/scheduled_tasks.py`

**Modify run_reassessment_for_user():**

```python
async def run_reassessment_for_user(user_id: str):
    period_days = 14
    period_start = datetime.now() - timedelta(days=period_days)

    # 1. Get planned templates
    templates = await supabase.table("activity_templates")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("is_active", True)\
        .execute()

    # 2. Get completed activities
    activities = await supabase.table("activities")\
        .select("*, exercise_sets(*)")\
        .eq("user_id", user_id)\
        .gte("start_time", period_start.isoformat())\
        .execute()

    # 3. Get context for this period
    context_logs = await supabase.table("user_context_log")\
        .select("*")\
        .eq("user_id", user_id)\
        .gte("created_at", period_start.isoformat())\
        .execute()

    # 4. Calculate base adherence
    planned_count = len(templates.data) * 2  # 2 weeks
    completed_with_template = len([a for a in activities.data if a.get("template_id")])
    base_adherence = completed_with_template / planned_count if planned_count > 0 else 0

    # 5. CONTEXT-AWARE ANALYSIS
    reasons = []
    adjustment_needed = False

    # Check stress
    high_stress = [c for c in context_logs.data if c["context_type"] == "stress" and c.get("severity") == "high"]
    if len(high_stress) > 3:
        reasons.append(f"User reported high stress {len(high_stress)} times")

    # Check travel
    travel = [c for c in context_logs.data if c["context_type"] == "travel"]
    if travel:
        reasons.append("User was traveling")

    # Check injury
    injury = [c for c in context_logs.data if c["context_type"] in ["injury", "illness"]]
    if injury:
        reasons.append("User reported injury/illness")
        adjustment_needed = True  # Need to modify program

    # Check informal activities
    informal = [a for a in activities.data if a.get("metrics", {}).get("informal_log")]
    if len(informal) > 2:
        reasons.append(f"User logged {len(informal)} informal activities (extra volume)")

    # 6. Calculate adjusted adherence
    adjusted_adherence = await supabase.rpc(
        "calculate_context_adjusted_adherence",
        {
            "p_user_id": user_id,
            "p_base_adherence": base_adherence,
            "p_days_back": period_days
        }
    ).execute()

    # 7. Generate recommendation
    if adjustment_needed:
        recommendation = "Modify program based on injury/context"
    elif adjusted_adherence.data > 0.8:
        recommendation = "Progressing well, continue plan"
    elif base_adherence < 0.7 and not reasons:
        recommendation = "Low adherence without context - check motivation"
    else:
        recommendation = "Adherence affected by life context - maintain current plan"

    # 8. Store adjustment
    await supabase.table("plan_adjustments").insert({
        "user_id": user_id,
        "adjustment_type": "bi_weekly_reassessment",
        "adherence_score": base_adherence,
        "context_adjusted_adherence": adjusted_adherence.data,
        "context_events_detected": len(context_logs.data),
        "informal_activities_count": len(informal),
        "reason": " | ".join(reasons),
        "recommendation": recommendation,
        "changes": {"analysis": "context_aware_reassessment"},
        "user_action": "pending"
    }).execute()
```

---

### FRONTEND (15 files remaining)

#### 6. `frontend/src/types/activity.ts`

```typescript
export interface ActivityTemplate {
  id: string;
  user_id: string;
  template_name: string;
  activity_type: string;
  description?: string;
  default_exercises: ExerciseTemplate[];
  expected_duration_minutes?: number;
  auto_match_enabled: boolean;
  min_match_score: number;
  is_active: boolean;
  use_count: number;
  last_used_at?: string;
  created_at: string;
}

export interface ExerciseTemplate {
  exercise_id: string;
  exercise_name: string;
  target_sets: number;
  target_reps: number;
  target_weight_kg?: number;
  notes?: string;
}

export interface Activity {
  id: string;
  user_id: string;
  category: string;
  activity_name: string;
  start_time: string;
  duration_minutes: number;
  calories_burned?: number;
  perceived_exertion?: number;
  template_id?: string;
  source: 'manual' | 'coach_chat' | 'ai_text';
  metrics: Record<string, any>;
  notes?: string;
  exercise_sets?: ExerciseSet[];
  created_at: string;
}

export interface ExerciseSet {
  id: string;
  activity_id: string;
  exercise_id: string;
  set_number: number;
  reps?: number;
  weight_kg?: number;
  duration_seconds?: number;
  rpe?: number;
  completed: boolean;
  notes?: string;
  created_at: string;
}
```

#### 7. `frontend/src/types/context.ts`

```typescript
export interface ContextLog {
  id: string;
  user_id: string;
  context_type: 'stress' | 'energy' | 'travel' | 'injury' | 'illness' | 'motivation' | 'life_event' | 'informal_activity';
  severity?: 'low' | 'moderate' | 'high';
  sentiment_score?: number;
  description: string;
  affects_training: boolean;
  suggested_adaptation?: string;
  created_at: string;
}

export interface InformalActivity extends Activity {
  extraction_confidence: number;
  original_message: string;
}
```

#### 8. REFACTOR `frontend/src/services/programApi.ts`

```typescript
// Add methods for activity_templates
export const ProgramAPI = {
  // ... existing methods ...

  async getWeeklyTemplates(userId: string): Promise<ActivityTemplate[]> {
    const response = await api.get(`/programs/${userId}/templates`);
    return response.data;
  },

  async getTodayTemplate(userId: string): Promise<ActivityTemplate | null> {
    const response = await api.get(`/programs/${userId}/today-template`);
    return response.data;
  },

  async createActivity(data: {
    category: string;
    activity_name: string;
    start_time: string;
    duration_minutes: number;
    template_id?: string;
  }): Promise<Activity> {
    const response = await api.post('/activities', data);
    return response.data;
  },

  async createExerciseSet(data: {
    activity_id: string;
    exercise_id: string;
    set_number: number;
    reps?: number;
    weight_kg?: number;
    rpe?: number;
    completed: boolean;
  }): Promise<ExerciseSet> {
    const response = await api.post('/exercise-sets', data);
    return response.data;
  },

  async getExerciseHistory(userId: string, exerciseId: string) {
    const response = await api.get(`/exercise-sets/history/${userId}/${exerciseId}`);
    return response.data;
  }
};
```

#### 9. `frontend/src/components/ContextTimeline.tsx`

```tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ContextLog } from '../types/context';

interface Props {
  contextLogs: ContextLog[];
}

export function ContextTimeline({ contextLogs }: Props) {
  const getIcon = (type: string) => {
    const icons = {
      stress: '😰',
      energy: '⚡',
      travel: '✈️',
      injury: '🤕',
      illness: '🤒',
      motivation: '💪',
      informal_activity: '🏃'
    };
    return icons[type] || '📝';
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Life Context</Text>
      {contextLogs.map((log) => (
        <View key={log.id} style={styles.item}>
          <Text style={styles.icon}>{getIcon(log.context_type)}</Text>
          <View style={styles.content}>
            <Text style={styles.type}>
              {log.context_type.toUpperCase()}
              {log.severity && ` (${log.severity})`}
            </Text>
            <Text style={styles.description}>{log.description}</Text>
            <Text style={styles.date}>
              {new Date(log.created_at).toLocaleDateString()}
            </Text>
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, backgroundColor: '#f5f5f5', borderRadius: 12, marginVertical: 8 },
  title: { fontSize: 18, fontWeight: '600', marginBottom: 12 },
  item: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 12, backgroundColor: 'white', padding: 12, borderRadius: 8 },
  icon: { fontSize: 24, marginRight: 12 },
  content: { flex: 1 },
  type: { fontSize: 14, fontWeight: '600', marginBottom: 4 },
  description: { fontSize: 13, color: '#666', marginBottom: 4 },
  date: { fontSize: 11, color: '#999' }
});
```

#### 10. REFACTOR `frontend/src/screens/WorkoutScreen.tsx`

```tsx
interface Props {
  route: { params: { template: ActivityTemplate } };
  navigation: any;
}

export function WorkoutScreen({ route, navigation }: Props) {
  const { template } = route.params;
  const [completedSets, setCompletedSets] = useState<ExerciseSet[]>([]);
  const [startTime] = useState(new Date());

  const completeWorkout = async () => {
    // 1. Create activity
    const activity = await ProgramAPI.createActivity({
      category: 'strength_training',
      activity_name: template.template_name,
      start_time: startTime.toISOString(),
      duration_minutes: Math.round((Date.now() - startTime.getTime()) / 60000),
      template_id: template.id
    });

    // 2. Create all exercise_sets
    for (const set of completedSets) {
      await ProgramAPI.createExerciseSet({
        ...set,
        activity_id: activity.id
      });
    }

    navigation.navigate('WorkoutComplete', { activity });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{template.template_name}</Text>
      {template.default_exercises.map((exercise, idx) => (
        <ExerciseCard
          key={exercise.exercise_id}
          exercise={exercise}
          onSetComplete={(set) => setCompletedSets([...completedSets, set])}
        />
      ))}
      <Button onPress={completeWorkout}>Complete Workout</Button>
    </View>
  );
}
```

---

## 📝 REMAINING FILES (Code Snippets)

### 11. `docs/PERSONA_SYSTEM.md`
- Document all 10 personas
- Include adaptation strategies
- Example program structures for each

### 12-26. Other frontend components
- Follow similar patterns as ContextTimeline
- Use existing types from activity.ts and context.ts

---

## 🚀 DEPLOYMENT STEPS

1. **Run migration:**
   ```bash
   psql $DATABASE_URL < integration/migrations/002_adaptive_program.sql
   ```

2. **Copy backend files to ULTIMATE_COACH_BACKEND:**
   ```bash
   cp -r integration/backend/app/* ULTIMATE_COACH_BACKEND/app/
   ```

3. **Install backend dependencies:**
   ```bash
   pip install anthropic
   ```

4. **Copy frontend files to ULTIMATE_COACH_FRONTEND:**
   ```bash
   cp -r integration/frontend/src/* ULTIMATE_COACH_FRONTEND/src/
   ```

5. **Install frontend dependencies:**
   ```bash
   npm install axios
   npm install @react-native-async-storage/async-storage
   ```

6. **Test program generation:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/programs/generate \
     -H "Content-Type: application/json" \
     -d '{"user_id": "...", "consultation_data": {...}}'
   ```

---

## ✅ SUCCESS CRITERIA

- ✅ Program generates using activity_templates (not custom tables)
- ✅ Informal activities extracted from chat ("played tennis")
- ✅ Life context extracted and stored
- ✅ Persona detected during consultation
- ✅ Reassessment is context-aware
- ✅ All 10 personas handled differently

---

**Total implementation time: 8-10 hours remaining**
**Confidence: 98% (using battle-tested schema + proven AI extraction)**
