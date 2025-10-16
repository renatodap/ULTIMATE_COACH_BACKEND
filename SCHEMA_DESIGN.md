# SHARPENED Backend - Database Schema Design

> **Visual Database Architecture** - Complete system overview with relationships

---

## 🎯 Schema Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SHARPENED BACKEND SCHEMA                         │
│                                                                          │
│  Core Systems:                                                           │
│  ├─ 👤 User Management (auth, profiles, onboarding)                     │
│  ├─ 💬 AI Consultation (keys, sessions, extracted data)                 │
│  ├─ 📋 Program Generation (programs, sessions, meals)                   │
│  ├─ 📅 Daily Planning (calendar, overrides, adherence)                  │
│  ├─ 🍽️  Nutrition Tracking (meals, foods, quick meals)                  │
│  └─ 💪 Activity Tracking (activities, templates, exercise sets)         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Core Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                              auth.users                                  │
│                           (Supabase Auth)                                │
│                         ┌──────────────┐                                 │
│                         │  id (UUID)   │                                 │
│                         │  email       │                                 │
│                         │  created_at  │                                 │
│                         └──────┬───────┘                                 │
│                                │                                         │
│                    ┌───────────┼───────────────────┐                    │
│                    │           │                   │                    │
│         ┌──────────▼───┐  ┌───▼──────┐  ┌─────────▼──────┐             │
│         │   profiles   │  │ consultation│  │   programs    │             │
│         │              │  │   sessions  │  │               │             │
│         │ • demographics│  │             │  │ • immutable   │             │
│         │ • goals      │  │ • progress  │  │ • versioned   │             │
│         │ • preferences│  │ • state     │  │ • full_bundle │             │
│         └──────────────┘  └─────┬───────┘  └───────┬───────┘             │
│                                 │                   │                    │
│                    ┌────────────┼───────────────────┤                    │
│                    │            │                   │                    │
│         ┌──────────▼─────┐  ┌──▼──────────┐  ┌─────▼──────────┐         │
│         │ consultation_  │  │  session_   │  │  meal_         │         │
│         │ keys/usage     │  │  instances  │  │  instances     │         │
│         └────────────────┘  └──────┬──────┘  └──────┬─────────┘         │
│                                    │                 │                   │
│                         ┌──────────┼─────────────────┤                   │
│                         │          │                 │                   │
│              ┌──────────▼───┐  ┌──▼──────────┐  ┌───▼──────────┐        │
│              │ exercise_plan│  │  calendar_  │  │ meal_item_   │        │
│              │ _items       │  │  events     │  │ plan         │        │
│              └──────────────┘  └──────┬──────┘  └──────────────┘        │
│                                       │                                  │
│                            ┌──────────┼──────────┐                       │
│                            │          │          │                       │
│                  ┌─────────▼───┐  ┌───▼────┐  ┌─▼──────────┐            │
│                  │ adherence_  │  │  day_  │  │ plan_      │            │
│                  │ records     │  │override│  │ change_    │            │
│                  └─────────────┘  └────────┘  │ events     │            │
│                                               └────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 System Breakdown

### 1️⃣ User Management System

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER MANAGEMENT                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  auth.users (Supabase)                                           │
│  └─► profiles                                                    │
│       ├─ Demographics: age, sex, height, weight                  │
│       ├─ Goals: primary_goal, experience_level                   │
│       ├─ Activity: workout_frequency, activity_level             │
│       ├─ Nutrition: dietary_preference, meals_per_day            │
│       ├─ Targets: daily_calorie_goal, protein/carbs/fat          │
│       └─ Flags: onboarding_completed, consultation_completed     │
│                                                                  │
│  Key Fields:                                                     │
│  • id (FK → auth.users.id)                                       │
│  • onboarding_completed (boolean)                                │
│  • consultation_completed (boolean)                              │
│  • estimated_tdee, daily_calorie_goal                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2️⃣ AI Consultation System

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI CONSULTATION FLOW                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Step 1: Key Validation                                                 │
│  ┌────────────────────┐         ┌─────────────────────┐                │
│  │ consultation_keys  │────────►│ consultation_key_   │                │
│  │                    │         │ usage               │                │
│  │ • key_value        │         │                     │                │
│  │ • max_uses         │         │ • ip_address        │                │
│  │ • expires_at       │         │ • user_agent        │                │
│  │ • assigned_user_id │         │ • redeemed_at       │                │
│  └────────────────────┘         └─────────────────────┘                │
│                                                                          │
│  Step 2: Conversation Session                                           │
│  ┌──────────────────────────┐                                           │
│  │ consultation_sessions    │                                           │
│  │                          │                                           │
│  │ • session_id (UUID)      │                                           │
│  │ • user_id                │                                           │
│  │ • consultation_key       │                                           │
│  │ • current_section (1-7)  │                                           │
│  │ • progress_percentage    │                                           │
│  │ • completed_at           │                                           │
│  └────────────┬─────────────┘                                           │
│               │                                                          │
│               ├──► consultation_messages (chat history)                 │
│               │                                                          │
│               └──► Extracted Data Tables (9 tables):                    │
│                    ├─ user_training_modalities                          │
│                    ├─ user_familiar_exercises                           │
│                    ├─ user_training_availability                        │
│                    ├─ user_preferred_meal_times                         │
│                    ├─ user_typical_meal_foods                           │
│                    ├─ user_improvement_goals                            │
│                    ├─ user_difficulties                                 │
│                    ├─ user_non_negotiables                              │
│                    └─ user_upcoming_events                              │
│                                                                          │
│  Step 3: Program Generation Trigger                                     │
│  consultation_sessions.completed_at = NOW()                             │
│  └──► POST /consultation/{session_id}/complete                          │
│        └──► generate_program_from_consultation()                        │
│             └──► store in programs table                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 3️⃣ Program Generation & Storage

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PROGRAM GENERATION SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Input Source: Consultation OR Onboarding                               │
│  Generator: ultimate_ai_consultation/api/generate_program.py            │
│                                                                          │
│  ┌──────────────────────────────────────────────────┐                   │
│  │              programs (immutable)                │                   │
│  │  ──────────────────────────────────────────────  │                   │
│  │  • id (UUID)                                     │                   │
│  │  • user_id                                       │                   │
│  │  • primary_goal                                  │                   │
│  │  • program_start_date                            │                   │
│  │  • program_duration_weeks (2, 12, etc.)          │                   │
│  │  • next_reassessment_date                        │                   │
│  │                                                  │                   │
│  │  JSONB Fields:                                   │                   │
│  │  • tdee: {tdee_kcal, bmr_kcal, multiplier}      │                   │
│  │  • macros: {protein_g, carbs_g, fat_g}          │                   │
│  │  • safety: {warnings[], constraints[]}           │                   │
│  │  • feasibility: {score, issues[]}                │                   │
│  │  • full_bundle: complete ProgramBundle           │                   │
│  └────────────────────┬─────────────────────────────┘                   │
│                       │                                                  │
│         ┌─────────────┼─────────────────┐                               │
│         │             │                 │                               │
│  ┌──────▼───────┐  ┌──▼─────────┐  ┌───▼──────────┐                    │
│  │ session_     │  │ meal_      │  │ calendar_    │                    │
│  │ instances    │  │ instances  │  │ events       │                    │
│  │              │  │            │  │              │                    │
│  │ • week_index │  │ • week_idx │  │ (denormalized│                    │
│  │ • day_index  │  │ • day_idx  │  │  view)       │                    │
│  │ • session_   │  │ • meal_    │  │              │                    │
│  │   kind       │  │   type     │  │ • date       │                    │
│  │ • duration   │  │ • totals   │  │ • ref_table  │                    │
│  └──────┬───────┘  └──────┬─────┘  │ • ref_id     │                    │
│         │                 │        └──────────────┘                    │
│  ┌──────▼───────┐  ┌──────▼─────┐                                       │
│  │ exercise_    │  │ meal_item_ │                                       │
│  │ plan_items   │  │ plan       │                                       │
│  │              │  │            │                                       │
│  │ • order      │  │ • food_    │                                       │
│  │ • name       │  │   name     │                                       │
│  │ • sets/reps  │  │ • serving  │                                       │
│  │ • rest_sec   │  │ • targets  │                                       │
│  └──────────────┘  └────────────┘                                       │
│                                                                          │
│  Storage Service: ProgramStorageService                                 │
│  └─► store_program_bundle()                                             │
│       ├─ Creates programs row                                           │
│       ├─ Creates session_instances (N rows)                             │
│       ├─ Creates exercise_plan_items (M rows)                           │
│       ├─ Creates meal_instances (P rows)                                │
│       ├─ Creates meal_item_plan (Q rows)                                │
│       └─ Creates calendar_events (R rows, denormalized)                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 4️⃣ Daily Planning & Adaptive System

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ADAPTIVE PLANNING SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Daily Flow:                                                             │
│                                                                          │
│  1. User logs context                                                   │
│     ┌─────────────────────┐                                             │
│     │ user_context_log    │                                             │
│     │                     │                                             │
│     │ • date              │                                             │
│     │ • sleep_hours       │                                             │
│     │ • sleep_quality     │                                             │
│     │ • stress_level      │                                             │
│     │ • soreness_level    │                                             │
│     │ • energy_level      │                                             │
│     │ • injury_notes      │                                             │
│     └──────────┬──────────┘                                             │
│                │                                                         │
│  2. System analyzes triggers                                            │
│                │                                                         │
│     ┌──────────▼──────────────────────────────────┐                     │
│     │ DailyAdjustmentService.analyze_and_adjust() │                     │
│     │                                              │                     │
│     │ Checks:                                      │                     │
│     │ • Poor sleep (< 6 hours or quality < 5)     │                     │
│     │ • High stress (> 7/10)                       │                     │
│     │ • High soreness (> 7/10)                     │                     │
│     │ • Injury (injury_notes present)              │                     │
│     │ • Low adherence (< 70% completion)           │                     │
│     └──────────┬──────────────────────────────────┘                     │
│                │                                                         │
│  3. Creates adjustment                                                  │
│                │                                                         │
│     ┌──────────▼──────────┐                                             │
│     │ day_overrides       │                                             │
│     │                     │                                             │
│     │ • date              │                                             │
│     │ • reason_code       │                                             │
│     │ • modifications:    │                                             │
│     │   {                 │                                             │
│     │     calorie_adj: -200,                                            │
│     │     volume_adj: -2,                                               │
│     │     intensity: 0.8                                                │
│     │   }                 │                                             │
│     │ • status (pending/  │                                             │
│     │   approved/rejected)│                                             │
│     └─────────────────────┘                                             │
│                                                                          │
│  4. User approves/rejects                                               │
│     └─► AdjustmentApprovalService                                       │
│         ├─ approve_adjustment()                                         │
│         ├─ reject_adjustment()                                          │
│         └─ undo_adjustment()                                            │
│                                                                          │
│  5. Track adherence                                                     │
│     ┌─────────────────────┐                                             │
│     │ adherence_records   │                                             │
│     │                     │                                             │
│     │ • planned_entity_   │                                             │
│     │   type (session/    │                                             │
│     │   meal)             │                                             │
│     │ • status (completed/│                                             │
│     │   similar/skipped)  │                                             │
│     │ • similarity_score  │                                             │
│     └─────────────────────┘                                             │
│                                                                          │
│  6. Bi-weekly reassessment                                              │
│     ┌──────────────────────────────────┐                                │
│     │ ReassessmentService              │                                │
│     │                                  │                                │
│     │ Every 14 days:                   │                                │
│     │ 1. Aggregate adherence data      │                                │
│     │ 2. Calculate weight change       │                                │
│     │ 3. Run PID controllers:          │                                │
│     │    • CaloriePIDController        │                                │
│     │    • VolumePIDController         │                                │
│     │ 4. Determine adjustments         │                                │
│     │ 5. Create plan_change_events     │                                │
│     │ 6. Update program targets        │                                │
│     └──────────────────────────────────┘                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 5️⃣ User Activity Tracking

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACTIVITY TRACKING                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐                                        │
│  │ activities           │                                        │
│  │                      │                                        │
│  │ • user_id            │                                        │
│  │ • category:          │                                        │
│  │   - cardio_steady    │                                        │
│  │   - cardio_interval  │                                        │
│  │   - strength         │                                        │
│  │   - sports           │                                        │
│  │   - flexibility      │                                        │
│  │ • start_time         │                                        │
│  │ • end_time           │                                        │
│  │ • duration_minutes   │                                        │
│  │ • calories_burned    │                                        │
│  │ • intensity_mets     │                                        │
│  │                      │                                        │
│  │ • metrics (JSONB):   │                                        │
│  │   Cardio: {distance, │                                        │
│  │            pace, hr} │                                        │
│  │   Strength: {        │                                        │
│  │     exercises[]      │                                        │
│  │   }                  │                                        │
│  │   Sports: {sport,    │                                        │
│  │            score}    │                                        │
│  └────────┬─────────────┘                                        │
│           │                                                      │
│  ┌────────▼────────────┐                                         │
│  │ exercise_sets       │                                         │
│  │                     │                                         │
│  │ • activity_id       │                                         │
│  │ • exercise_name     │                                         │
│  │ • set_number        │                                         │
│  │ • reps              │                                         │
│  │ • weight_kg         │                                         │
│  │ • rpe               │                                         │
│  └─────────────────────┘                                         │
│                                                                  │
│  ┌─────────────────────┐                                         │
│  │ activity_templates  │                                         │
│  │                     │                                         │
│  │ • user_id           │                                         │
│  │ • template_name     │                                         │
│  │ • category          │                                         │
│  │ • template_data     │                                         │
│  │   (JSONB)           │                                         │
│  └─────────────────────┘                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 6️⃣ Nutrition Tracking

```
┌─────────────────────────────────────────────────────────────────┐
│                     NUTRITION TRACKING                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                                │
│  │ foods        │  ← Shared food database                        │
│  │              │                                                │
│  │ • name       │                                                │
│  │ • brand      │                                                │
│  │ • servings[] │                                                │
│  └──────┬───────┘                                                │
│         │                                                        │
│  ┌──────▼───────────┐       ┌─────────────────┐                 │
│  │ custom_foods     │       │ quick_meals     │                 │
│  │                  │       │                 │                 │
│  │ • user_id        │       │ • user_id       │                 │
│  │ • name           │       │ • meal_name     │                 │
│  │ • nutrition      │       │ • total_cals    │                 │
│  └──────────────────┘       │ • components[]  │                 │
│                             └─────────────────┘                 │
│                                                                  │
│  ┌──────────────────┐                                            │
│  │ meals            │  ← User meal logs                          │
│  │                  │                                            │
│  │ • user_id        │                                            │
│  │ • logged_at      │                                            │
│  │ • meal_type      │                                            │
│  │ • foods[]        │                                            │
│  │ • total_cals     │                                            │
│  │ • total_protein  │                                            │
│  │ • total_carbs    │                                            │
│  │ • total_fat      │                                            │
│  └──────────────────┘                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Key Relationships

### Primary Foreign Keys

```
profiles.id               → auth.users.id
consultation_sessions     → auth.users.id
programs                  → auth.users.id
session_instances         → programs.id
exercise_plan_items       → session_instances.id
meal_instances            → programs.id
meal_item_plan            → meal_instances.id
calendar_events           → programs.id + auth.users.id
day_overrides             → programs.id + auth.users.id
adherence_records         → auth.users.id
plan_change_events        → programs.id + auth.users.id
activities                → auth.users.id
meals                     → auth.users.id
```

### Soft References (UUID strings in JSONB or TEXT)

```
calendar_events.ref_id    → session_instances.id OR meal_instances.id
adherence_records         → session_instances.id OR meal_instances.id
                            (via planned_entity_id)
```

---

## 📋 Table Summary

| **Category** | **Tables** | **Purpose** |
|-------------|-----------|-------------|
| **Auth & Profile** | `auth.users`, `profiles` | User accounts and demographics |
| **Consultation** | `consultation_keys`, `consultation_key_usage`, `consultation_sessions`, `consultation_messages`, `user_training_modalities`, `user_familiar_exercises`, `user_training_availability`, `user_preferred_meal_times`, `user_typical_meal_foods`, `user_improvement_goals`, `user_difficulties`, `user_non_negotiables`, `user_upcoming_events` | AI consultation system (13 tables) |
| **Program Storage** | `programs`, `session_instances`, `exercise_plan_items`, `meal_instances`, `meal_item_plan` | Generated programs and plan instances |
| **Planning** | `calendar_events`, `day_overrides`, `adherence_records`, `plan_change_events`, `user_context_log`, `notifications` | Adaptive planning and adjustments |
| **Activity Tracking** | `activities`, `exercise_sets`, `activity_templates` | User workout logs |
| **Nutrition Tracking** | `foods`, `custom_foods`, `meals`, `quick_meals` | User meal logs |
| **Supporting** | `exercises`, `training_modalities`, `meal_times`, `event_types` | Reference data |

**Total Tables: ~38 tables**

---

## 🎨 Data Flow: End-to-End

```
┌────────────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY                                    │
└────────────────────────────────────────────────────────────────────────┘

1. SIGNUP
   └─► auth.users created
       └─► profiles created

2. ONBOARDING
   └─► profiles updated (all demographic + goal fields)
       └─► onboarding_completed = true

3A. OPTION A: Start using app (without consultation)
    └─► Log meals → meals table
    └─► Log activities → activities table
    └─► Chat with AI coach → coach_conversations + coach_messages

3B. OPTION B: AI Consultation (premium)
    └─► Enter consultation key → consultation_keys validated
        └─► Start session → consultation_sessions created
            └─► Multi-turn conversation → consultation_messages
                └─► Extract structured data → 9 user_* tables
                    └─► Complete consultation → programs generated
                        ├─► session_instances created
                        ├─► exercise_plan_items created
                        ├─► meal_instances created
                        ├─► meal_item_plan created
                        └─► calendar_events created

4. DAILY USAGE
   └─► View today's plan → calendar_events
       ├─► Complete workout → activities + adherence_records
       ├─► Log meals → meals + adherence_records
       └─► Log context → user_context_log
           └─► Trigger adjustments → day_overrides

5. BI-WEEKLY REASSESSMENT
   └─► ReassessmentService runs
       ├─► Aggregate adherence_records
       ├─► Calculate weight change (body_metrics)
       ├─► Run PID controllers
       ├─► Create plan_change_events
       └─► Update programs.next_reassessment_date

6. CONTINUOUS ADAPTATION
   └─► System learns from:
       ├─► adherence_records (what user actually does)
       ├─► plan_change_events (manual modifications)
       ├─► day_overrides (approved/rejected adjustments)
       └─► user_context_log (sleep, stress, soreness)
```

---

## 🔐 Security Model

**Row Level Security (RLS) enabled on all tables:**

```sql
-- Pattern for all user-scoped tables:
CREATE POLICY "Users can only access their own data"
    ON table_name
    FOR ALL
    USING (auth.uid() = user_id);
```

**Service Role Bypass:**
- Backend uses service role key for admin operations
- RLS still enforces user isolation at query level
- Structured logging tracks all data access

---

## 📈 Scalability Considerations

### Indexes Strategy

**Critical Indexes (already in schema):**
```sql
-- User lookups
CREATE INDEX idx_profiles_user_id ON profiles(user_id);
CREATE INDEX idx_programs_user_id ON programs(user_id);

-- Date-based queries (most common)
CREATE INDEX idx_calendar_events_user_date ON calendar_events(user_id, date);
CREATE INDEX idx_activities_user_start ON activities(user_id, start_time DESC);
CREATE INDEX idx_meals_user_logged ON meals(user_id, logged_at DESC);

-- Adherence tracking
CREATE INDEX idx_adherence_records_created ON adherence_records(user_id, created_at DESC);

-- Program planning
CREATE INDEX idx_session_instances_program_week ON session_instances(program_id, week_index);
CREATE INDEX idx_meal_instances_program_week_day ON meal_instances(program_id, week_index, day_index);
```

### Partitioning Strategy (Future)

```sql
-- Partition large tables by date for performance
-- Examples:
-- - activities (by start_time)
-- - meals (by logged_at)
-- - adherence_records (by created_at)
-- - calendar_events (by date)
```

---

## 🚀 Next Steps

### Immediate Actions:
1. ✅ Run migration `039_program_planning_tables.sql`
2. ✅ Verify all 11 new tables created
3. ✅ Test consultation → program generation flow
4. ✅ Verify RLS policies working

### Future Enhancements:
- Add materialized views for common aggregations
- Implement table partitioning for high-volume tables
- Add audit triggers for sensitive operations
- Create backup/restore procedures

---

**Schema Version:** 1.0.0 (Post-Migration 039)
**Last Updated:** 2025-10-16
**Total Tables:** ~38 tables across 6 subsystems
