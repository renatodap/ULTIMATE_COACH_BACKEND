# Personalized Coaching Architecture

## 🎯 System Overview

SHARPENED uses **personalized system prompts** as its core differentiator. Instead of generic coaching, each user gets a unique 500-800 word coaching persona that:
- Understands their psychology and past failures
- Adapts to their actual behavior (not just what they say)
- Evolves weekly based on usage patterns
- Costs ~$0.05 per generation with intelligent change detection

---

## 🏗️ Architecture Layers

### **Layer 1: Database Schema**
```
profiles table:
├── conversational_profile (TEXT)       # 200-word psychological profile
├── coaching_system_prompt (TEXT)       # 500-800 word personalized prompt
├── behavioral_data (JSONB)             # Usage metrics (adherence, streaks)
├── system_prompt_version (INT)         # Version tracking
├── last_prompt_update (TIMESTAMPTZ)    # Last update timestamp
└── consultation_enabled (BOOLEAN)      # Access control flag

coach_conversations table:
└── system_prompt_version_used (INT)    # Which version was used
```

### **Layer 2: Services (Modular)**
```
SystemPromptGenerator (singleton)
├── generate_initial_prompt()           # From consultation data
└── update_prompt_from_behavior()       # Weekly updates

BehavioralTracker (singleton)
├── calculate_metrics()                 # 30-day analysis
├── _calculate_logging_metrics()        # Streaks, consistency
├── _calculate_adherence_metrics()      # Days in target
└── _detect_failure_patterns()          # Weekend overeating, etc.

ConsultationAIService
├── start_consultation()                # Gated behind consultation_enabled
├── process_message()                   # Natural conversation
└── generate_conversational_profile()   # 200-word psychological profile
```

### **Layer 3: Configuration (Zero Hard-Coded Values)**
```python
app/config/personalized_coaching.py

PersonalizedCoachingConfig:
├── ADHERENCE_CHANGE_THRESHOLD = 0.10     # 10% change triggers update
├── LOGGING_CHANGE_THRESHOLD = 0.10       # 10% change triggers update
├── STREAK_CHANGE_THRESHOLD = 7           # 7 days change triggers update
├── BEHAVIORAL_ANALYSIS_DAYS = 30         # Analysis window
├── MIN_DAYS_BETWEEN_UPDATES = 7          # Weekly updates
├── PROMPT_UPDATE_DAY = "sun"             # Sunday
├── PROMPT_UPDATE_HOUR = 3                # 3am
└── ENABLE_CHANGE_DETECTION = true        # Cost optimization
```

**Everything configurable via environment variables:**
```bash
export ADHERENCE_CHANGE_THRESHOLD=0.15
export PROMPT_UPDATE_DAY=mon
export MIN_DAYS_BETWEEN_UPDATES=14
```

### **Layer 4: Background Jobs**
```
background_jobs_service (singleton)
├── run_weekly_prompt_updates()         # Sunday 3am (configurable)
│   ├── Get users needing updates (>7 days old)
│   ├── Calculate behavioral metrics
│   ├── Check if changed significantly (cost optimization)
│   └── Regenerate prompt if needed
└── All schedules configurable via env vars
```

---

## 🔄 Complete User Flow

### **1. User Signs Up (Minimal)**
- Frontend: 5 fields (name, email, age, weight, goal)
- Backend: Creates user profile with `consultation_enabled=false`

### **2. Admin Enables Consultation**
```sql
UPDATE profiles
SET consultation_enabled = true
WHERE email = 'user@example.com';
```

### **3. User Starts Consultation**
```
POST /api/v1/consultation/start
├── Check consultation_enabled flag (403 if false)
├── Create consultation session
└── Return session_id
```

### **4. User Chats with Consultation AI**
```
POST /api/v1/consultation/message
├── Process message via Claude
├── Extract structured data (training, meals, goals, challenges)
└── Save to database
```

### **5. User Completes Consultation**
```
POST /api/v1/consultation/{session_id}/complete
├── Generate conversational_profile (200 words)      # ~3 seconds
│   └── Meta-prompt analyzes entire conversation
├── Generate initial system prompt (500-800 words)   # ~5 seconds
│   └── Uses profile + user data + goals
├── Save both to profiles table
│   ├── conversational_profile
│   ├── coaching_system_prompt
│   ├── system_prompt_version = 1
│   └── last_prompt_update = NOW()
└── Return success (takes ~10 seconds total)
```

**RACE CONDITION HANDLED:**
- Coach gracefully falls back to generic prompt if personalized not ready
- Frontend should show "Generating your personalized coach..." loading state

### **6. User Chats with Coach**
```
POST /api/v1/coach/message
├── _build_system_prompt()
│   ├── Check database for coaching_system_prompt
│   ├── If exists: Use personalized (return with version)
│   └── If not exists: Fallback to generic
├── Track which version used
│   └── Save system_prompt_version_used to coach_conversations
└── Return coach response
```

### **7. Weekly Background Job**
```
Sunday 3am (configurable):
├── Find users with last_prompt_update > 7 days ago
├── For each user:
│   ├── Calculate behavioral_metrics (30-day window)
│   ├── Compare with stored behavioral_data
│   ├── Check if changed significantly:
│   │   ├── Adherence changed >10%? OR
│   │   ├── Logging changed >10%? OR
│   │   └── Streak changed >7 days?
│   ├── If NO significant change:
│   │   ├── Update behavioral_data (free)
│   │   └── Skip prompt regeneration (save $0.05)
│   └── If YES significant change:
│       ├── Regenerate prompt ($0.05)
│       ├── Increment system_prompt_version
│       └── Update last_prompt_update
└── Result: Prompt evolves with actual behavior
```

---

## 💰 Cost Optimization

### **Without Change Detection:**
```
10,000 users × $0.05/week = $500/week = $26,000/year
```

### **With Change Detection (10% threshold):**
Assuming 90% of users don't change significantly week-to-week:
```
10,000 users × 10% changed × $0.05 = $50/week = $2,600/year
SAVINGS: $23,400/year
```

### **Configurable Thresholds:**
```bash
# More aggressive (cheaper, less responsive)
export ADHERENCE_CHANGE_THRESHOLD=0.20  # 20% change required
export MIN_DAYS_BETWEEN_UPDATES=14      # Update every 2 weeks

# More responsive (more expensive)
export ADHERENCE_CHANGE_THRESHOLD=0.05  # 5% change triggers update
export MIN_DAYS_BETWEEN_UPDATES=3       # Update every 3 days
```

---

## 🔒 Access Control

### **Consultation Gating:**
```
consultation_enabled flag:
├── Default: false (no access)
├── Manually enabled by admin
└── Checked at /consultation/start endpoint
```

### **Why Gated?**
1. **Cost control:** Each consultation costs ~$0.10 in API calls
2. **Quality control:** Can test with beta users first
3. **Gradual rollout:** Enable for cohorts progressively
4. **Legacy support:** Keeps consultation keys working (optional)

---

## 🧩 Modular Design

### **Why This Architecture Won't Regret:**

**1. Zero Hard-Coded Values**
```python
# Bad (old):
if adherence_change < 0.10:  # What if we want to change this?

# Good (new):
if adherence_change < coaching_config.ADHERENCE_CHANGE_THRESHOLD:
```

**2. Singleton Services**
```python
# Easy to swap implementations
prompt_generator = get_system_prompt_generator()

# If you want to switch to OpenAI GPT-4:
# Just modify SystemPromptGenerator class internals
# No changes needed in 10+ call sites
```

**3. Configurable Schedules**
```python
# Bad (old):
CronTrigger(day_of_week="sun", hour=3, minute=0)  # Hard-coded

# Good (new):
schedule = coaching_config.get_prompt_update_schedule()
CronTrigger(
    day_of_week=schedule["day_of_week"],  # From env var
    hour=schedule["hour"],
    minute=schedule["minute"]
)
```

**4. Feature Flags Built In**
```python
ENABLE_AUTOMATIC_UPDATES = true   # Disable if needed
ENABLE_CHANGE_DETECTION = true    # Disable to always update
ENABLE_GENERIC_FALLBACK = true    # Disable to force personalized-only
```

**5. Separation of Concerns**
```
Database Schema (migrations/*.sql)
    ↓
Services (app/services/*.py)
    ↓
Configuration (app/config/personalized_coaching.py)
    ↓
Background Jobs (app/services/background_jobs.py)
    ↓
API Endpoints (app/api/v1/*.py)
```
Change one layer without touching others.

---

## 📊 Monitoring & Debugging

### **Logs to Watch:**
```
# Cost tracking
"prompt_update_started" - job initiated
"significant_behavior_change_detected" - will regenerate ($0.05)
"skipping_prompt_update_no_significant_change" - saved money
"prompts_updated" - how many regenerations

# Success tracking
"conversational_profile_generated" - consultation completed
"initial_system_prompt_generated" - first prompt created
"using_personalized_system_prompt" - coach using custom prompt
"system_prompt_updated" - weekly update succeeded

# Error tracking
"personalized_prompt_generation_failed" - investigate!
"consultation_access_denied" - user doesn't have access
```

### **Database Queries:**
```sql
-- Check who has personalized prompts
SELECT
    id,
    email,
    system_prompt_version,
    last_prompt_update,
    consultation_enabled
FROM profiles
WHERE coaching_system_prompt IS NOT NULL;

-- Check prompt usage in conversations
SELECT
    c.id,
    c.created_at,
    c.system_prompt_version_used,
    p.email
FROM coach_conversations c
JOIN profiles p ON c.user_id = p.id
WHERE c.system_prompt_version_used IS NOT NULL
ORDER BY c.created_at DESC
LIMIT 100;

-- Cost projection
SELECT
    COUNT(*) as users_with_prompts,
    COUNT(*) FILTER (
        WHERE last_prompt_update < NOW() - INTERVAL '7 days'
    ) as due_for_update,
    COUNT(*) FILTER (
        WHERE last_prompt_update < NOW() - INTERVAL '7 days'
    ) * 0.05 as estimated_cost_this_week
FROM profiles
WHERE coaching_system_prompt IS NOT NULL;
```

---

## 🚀 Future Enhancements (Easy to Add)

### **1. A/B Testing Prompt Variants**
Already have version tracking! Just need:
```python
def get_prompt_variant(user_id, version):
    # Return different prompts for A/B testing
    pass
```

### **2. Prompt Templates by User Type**
```python
PROMPT_TEMPLATES = {
    "beginner": "beginner_meta_prompt.txt",
    "advanced": "advanced_meta_prompt.txt",
    "athlete": "athlete_meta_prompt.txt"
}
```

### **3. Real-Time Updates (Instead of Weekly)**
```python
# In meal logging endpoint:
if user_just_broke_streak():
    trigger_prompt_update.delay(user_id)  # Celery task
```

### **4. Manual Prompt Regeneration**
```python
@router.post("/api/v1/users/me/regenerate-prompt")
async def regenerate_my_prompt(user = Depends(get_current_user)):
    # Allow users to request fresh prompt
    pass
```

### **5. Prompt History / Changelog**
```sql
CREATE TABLE prompt_history (
    id UUID PRIMARY KEY,
    user_id UUID,
    version INT,
    prompt TEXT,
    behavioral_data JSONB,
    created_at TIMESTAMPTZ
);
```

---

## ✅ Summary

**What You Have:**
- ✅ Modular, configurable architecture
- ✅ Zero hard-coded values
- ✅ Cost-optimized with change detection
- ✅ Gated access control
- ✅ Version tracking for debugging
- ✅ Graceful fallbacks
- ✅ Background jobs enabled
- ✅ Complete documentation

**What You Need to Do:**
1. Run migrations (see `migrations/RUN_THESE_MIGRATIONS.md`)
2. Enable `consultation_enabled` for beta users
3. Set optional env vars (if you want to tune thresholds)
4. Deploy and monitor logs

**Zero Regrets:**
- Easy to change thresholds (env vars)
- Easy to change schedules (env vars)
- Easy to swap implementations (singletons)
- Easy to add features (modular design)
- Easy to debug (version tracking + logs)
- Easy to optimize costs (change detection)

**This architecture will scale from 10 users to 100,000 users without code changes.**
