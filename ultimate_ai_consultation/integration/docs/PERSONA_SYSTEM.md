# 🧠 PERSONA SYSTEM
## Context-Aware User Classification

**Last Updated:** October 14, 2025
**Version:** 1.0

---

## Overview

The Persona System is the intelligence layer that makes ULTIMATE COACH truly adaptive. Instead of one-size-fits-all programming, we detect which of 10 personas the user matches and customize:

- **Training frequency** (3-6 sessions/week)
- **Session duration** (20-75 minutes)
- **Exercise selection** (home-friendly, gym-only, travel-friendly)
- **System prompt tone** (encouraging, scientific, safety-focused)
- **Reassessment sensitivity** (strict vs flexible)

---

## The 10 Personas

### 1. 9-to-5 Hustler

**Profile:**
- Age: 25-40
- Works 40-60 hour weeks
- Limited time windows (early morning or evening)
- Access to commercial gym
- Goal: Maximize results in minimal time

**Adaptations:**
```python
sessions_per_week: 4-5
session_duration_minutes: 45-60
exercises_per_session: 5-6
intensity_target: "RPE 7-9"
equipment: ["gym_full", "barbell", "machines"]
flexibility_required: False
skip_friendly: False
```

**System Prompt Additions:**
```
This user is a busy professional with limited time windows.
- Create efficient 45-60min workouts
- Focus on compound movements for maximum ROI
- Schedule workouts around 6am or 6pm
- Use encouraging, results-focused language
- Emphasize time efficiency
```

**Example User:**
> "I work 9-5 in finance. Can only train before work or right after. Want to get strong but don't have all day in the gym."

---

### 2. Busy Parent

**Profile:**
- Age: 30-50
- Has young children (0-12 years old)
- Unpredictable schedule
- Likely has home gym or needs bodyweight options
- Goal: Stay healthy despite chaos

**Adaptations:**
```python
sessions_per_week: 3-4
session_duration_minutes: 25-35
exercises_per_session: 4
intensity_target: "RPE 5-7"
equipment: ["home_gym", "dumbbells", "bodyweight"]
flexibility_required: True
skip_friendly: True  # Understands life happens
```

**System Prompt Additions:**
```
This user is a busy parent with unpredictable schedule.
- Create SHORT 20-30min workouts
- ALL workouts must be home-friendly
- Use encouraging, non-guilt language
- Celebrate small wins
- Build in flexibility for missed sessions
- Suggest "kid-friendly" alternatives (park workouts, playing with kids)
```

**Example User:**
> "I have 3 kids under 8. Can't always make it to the gym. Have dumbbells at home. Just want to stay fit and not lose myself."

---

### 3. College Athlete

**Profile:**
- Age: 18-24
- Was a college athlete, now graduated
- Misses structure and competition
- Has high training capacity
- Goal: Maintain athletic performance

**Adaptations:**
```python
sessions_per_week: 5-6
session_duration_minutes: 60-75
exercises_per_session: 6-8
intensity_target: "RPE 8-10"
equipment: ["gym_full", "barbell", "plyometrics"]
flexibility_required: False
skip_friendly: False
```

**System Prompt Additions:**
```
This user is a former college athlete with high work capacity.
- Program like an athlete (periodization, progressive overload)
- Use sport-specific terminology
- Include explosive/plyometric work
- Challenge them consistently
- Track PRs and performance metrics closely
```

**Example User:**
> "I played D1 football. Miss the structure and competing. Want to stay in peak shape."

---

### 4. Homebody Lifter

**Profile:**
- Age: 20-45
- Loves lifting, doesn't love commercial gyms
- Has invested in home gym equipment
- Knowledgeable about training
- Goal: Build muscle/strength at home

**Adaptations:**
```python
sessions_per_week: 4-5
session_duration_minutes: 60-75
exercises_per_session: 6-7
intensity_target: "RPE 7-9"
equipment: ["home_gym", "barbell", "rack", "dumbbells"]
flexibility_required: False
skip_friendly: False
```

**System Prompt Additions:**
```
This user has a well-equipped home gym and loves lifting.
- Program like a bodybuilding/powerlifting split
- Assume good exercise technique knowledge
- Use standard barbell progressions
- Focus on muscle/strength development
- No need to over-explain basics
```

**Example User:**
> "Built a home gym during COVID. Have squat rack, barbell, dumbbells up to 100lb. Love training at home. Want hypertrophy program."

---

### 5. Long-Haul Trucker

**Profile:**
- Age: 30-60
- On the road 3-5 days/week
- Limited equipment access (truck stops, hotel gyms)
- Sedentary job with irregular schedule
- Goal: Combat sedentary lifestyle, stay healthy

**Adaptations:**
```python
sessions_per_week: 3-4
session_duration_minutes: 30-40
exercises_per_session: 4-5
intensity_target: "RPE 5-7"
equipment: ["bodyweight", "resistance_bands", "light_dumbbells"]
flexibility_required: True
skip_friendly: True
```

**System Prompt Additions:**
```
This user travels frequently with minimal equipment access.
- Create bodyweight-focused workouts
- All exercises must work in hotel rooms or truck stops
- Include mobility work for long sitting hours
- Be extremely flexible about missed sessions
- Focus on consistency over intensity
- Suggest quick movement breaks during drives
```

**Example User:**
> "I drive trucks cross-country. Gone 4-5 days a week. Hotel gyms suck. Need something I can do anywhere to stay healthy."

---

### 6. Elderly Upgrader

**Profile:**
- Age: 60-85
- Doctor recommended resistance training
- May have mobility limitations
- Concerned about safety
- Goal: Maintain independence, bone density, fall prevention

**Adaptations:**
```python
sessions_per_week: 3
session_duration_minutes: 35-45
exercises_per_session: 4-5
intensity_target: "RPE 4-6"  # Lower intensity
equipment: ["machines", "light_dumbbells", "bodyweight"]
safety_first: True
balance_work_required: True
```

**System Prompt Additions:**
```
This user is older and prioritizes safety and functional fitness.
- Safety and proper form are HIGHEST priority
- Include balance work in EVERY session
- Use machine-based exercises when possible (safer)
- Start conservatively, progress slowly
- Use respectful, non-intimidating language
- Focus on functional movements (stairs, carrying groceries)
- Celebrate maintenance as success
```

**Example User:**
> "I'm 68. Doctor said I need resistance training for bone density. Never lifted before. Want to stay independent and avoid falls."

---

### 7. Young Biohacker

**Profile:**
- Age: 20-35
- Tracks everything (HRV, sleep, macros, training volume)
- Loves optimization and science
- Follows fitness influencers
- Goal: Maximum performance and longevity

**Adaptations:**
```python
sessions_per_week: 5-6
session_duration_minutes: 60-75
exercises_per_session: 6-8
intensity_target: "RPE 7-9"
equipment: ["gym_full", "wearables"]
tracking_obsessed: True
```

**System Prompt Additions:**
```
This user is science-focused and loves data.
- Use scientific terminology (hypertrophy, periodization, RPE)
- Reference research when possible
- Track ALL metrics (volume, tonnage, PRs, RPE)
- Program with periodization principles
- Explain the "why" behind programming decisions
- Adjust based on HRV/sleep data if provided
```

**Example User:**
> "I track HRV, sleep, macros. Wear Whoop. Read all the studies. Want an evidence-based program that maximizes hypertrophy and longevity."

---

### 8. Consistency Struggler

**Profile:**
- Age: 25-50
- Has started and stopped many programs
- Struggles with motivation
- All-or-nothing mindset
- Goal: Build sustainable habit, not perfection

**Adaptations:**
```python
sessions_per_week: 3  # Start minimal
session_duration_minutes: 30-40
exercises_per_session: 4
intensity_target: "RPE 5-7"
flexibility_required: True
skip_friendly: True
habit_building_focus: True
```

**System Prompt Additions:**
```
This user struggles with consistency. Focus on habit building.
- Start with MINIMAL viable program (3x/week)
- Use extremely encouraging, non-judgmental language
- NEVER guilt about missed sessions
- Celebrate showing up, not perfection
- "Something is better than nothing" mentality
- Suggest ridiculously easy alternatives if they're struggling
- Frame exercise as self-care, not punishment
```

**Example User:**
> "I've started programs 10 times. Always stop after 2-3 weeks. All or nothing mindset. Need help building a habit I can stick with."

---

### 9. Social Starter

**Profile:**
- Age: 22-40
- New to fitness, intimidated by gym
- Wants accountability and community
- Learns best with guidance
- Goal: Build confidence and knowledge

**Adaptations:**
```python
sessions_per_week: 3
session_duration_minutes: 40-50
exercises_per_session: 4-5
intensity_target: "RPE 4-6"
equipment: ["machines", "dumbbells"]
educational: True
```

**System Prompt Additions:**
```
This user is NEW to fitness and needs education.
- Use simple, non-intimidating language
- Explain exercises with detailed form cues
- Start with machine-based exercises (easier to learn)
- Progress slowly to build confidence
- Provide lots of positive reinforcement
- Suggest fitness classes or group workouts for social aspect
- Create "beginner-friendly" variants of everything
```

**Example User:**
> "Never really worked out before. Feel intimidated by the gym. Want to get started but don't know what I'm doing."

---

### 10. Medical Referral

**Profile:**
- Age: 30-70
- Referred by doctor (pre-diabetes, hypertension, obesity)
- May have medical limitations
- Exercise is medical intervention
- Goal: Improve health markers

**Adaptations:**
```python
sessions_per_week: 3-4
session_duration_minutes: 30-45
exercises_per_session: 4-5
intensity_target: "RPE 4-6"
equipment: ["machines", "light_weights", "cardio"]
medical_considerations: True
safety_first: True
```

**System Prompt Additions:**
```
This user has medical conditions requiring careful programming.
- Safety is HIGHEST priority
- Start conservatively, progress slowly
- Include cardio for cardiovascular health
- Monitor blood pressure/glucose if mentioned
- Use encouraging, health-focused language
- Frame exercise as medicine, not punishment
- Celebrate health improvements (BP, glucose, energy)
- Suggest medical clearance before changes
```

**Example User:**
> "Doctor said I'm pre-diabetic and have high blood pressure. Told me to start exercising. Never really done this before."

---

## How Persona Detection Works

### Detection Algorithm

The `detect_persona()` function in `backend/app/services/persona_detection.py` uses a **weighted scoring system**:

1. **Keyword Matching** (40% weight)
   - Scans consultation data for persona-specific keywords
   - Examples:
     - "kids", "children" → Busy Parent
     - "college athlete", "D1" → College Athlete
     - "doctor recommended" → Medical Referral

2. **Age Range Matching** (20% weight)
   - Each persona has preferred age range
   - Boosts score if user's age falls within range

3. **Goal Alignment** (20% weight)
   - Matches stated goals to persona goals
   - Examples:
     - "build muscle" → Homebody Lifter, Young Biohacker
     - "stay healthy" → Busy Parent, Medical Referral

4. **Equipment Access** (10% weight)
   - Matches available equipment to persona needs
   - "home gym" → Homebody Lifter, Busy Parent
   - "no gym" → Long-Haul Trucker

5. **Schedule Constraints** (10% weight)
   - Matches time availability
   - "limited time" → 9-to-5 Hustler
   - "unpredictable" → Busy Parent

### Confidence Scoring

Returns persona with highest score and confidence level:

```python
{
  "persona_type": "Busy Parent",
  "confidence": 0.87,
  "reasoning": "Matched keywords: kids, home gym, unpredictable. Age 35 in range. Limited time availability."
}
```

**Confidence Thresholds:**
- **0.8-1.0**: Strong match, apply all adaptations
- **0.6-0.79**: Moderate match, apply most adaptations
- **< 0.6**: Weak match, use general program

---

## How Adaptations Are Applied

### 1. Program Generation

When `generate_program()` is called:

```python
# Detect persona
persona_result = await detect_persona(consultation_data)

# Get adaptations
adaptations = PERSONAS[persona_result['persona_type']].adaptations

# Generate activity templates based on adaptations
templates = generate_templates(
    sessions_per_week=adaptations['sessions_per_week'],
    duration=adaptations['session_duration_minutes'],
    equipment=adaptations['equipment'],
    intensity=adaptations['intensity_target']
)

# Store persona in user_profiles_extended
await store_persona(user_id, persona_result)
```

### 2. System Prompt Customization

The unified coach gets persona-specific context:

```python
system_prompt = BASE_SYSTEM_PROMPT + persona.system_prompt_additions

# Example for Busy Parent:
"""
You are a compassionate fitness coach.

This user is a busy parent with unpredictable schedule.
- Create SHORT 20-30min workouts
- Use encouraging, non-guilt language
- Celebrate small wins
"""
```

### 3. Reassessment Logic

Bi-weekly reassessments use persona traits:

```python
if persona.skip_friendly and adherence < 50%:
    # Don't penalize, understand life is chaotic
    adjustment = "maintain"
elif persona.flexibility_required:
    # Context-adjusted adherence
    adjusted_adherence = calculate_context_adjusted_adherence(user_id)
```

---

## Adding New Personas

To add a new persona:

### 1. Define Persona in `persona_detection.py`

```python
PERSONAS["New Persona Name"] = PersonaDefinition(
    keywords=["keyword1", "keyword2"],
    age_range=(min_age, max_age),
    goals=["goal1", "goal2"],
    adaptations={
        "sessions_per_week": 4,
        "session_duration_minutes": 45,
        "exercises_per_session": 5,
        "intensity_target": "RPE 6-8",
        "equipment": ["equipment_type"],
        "system_prompt_additions": """
        Custom prompt additions here
        """
    }
)
```

### 2. Update Detection Logic

Add persona to scoring function if needed (usually automatic).

### 3. Update Documentation

Add persona to this file with full profile and example.

### 4. Test Detection

```python
from app.services.persona_detection import detect_persona

consultation_data = {
    "age": 35,
    "fitness_goals": "test goal",
    "notes": "test notes with keywords"
}

result = await detect_persona(consultation_data)
print(result)
```

---

## Persona Override

Users can manually override detected persona:

```python
# Backend endpoint
@router.post("/programs/{user_id}/override-persona")
async def override_persona(
    user_id: UUID,
    persona_type: str,
    confidence: float = 1.0
):
    """
    Manually set user's persona (admin/support use)
    """
    await db.execute("""
        UPDATE user_profiles_extended
        SET persona_type = $1,
            persona_confidence = $2,
            persona_override = TRUE
        WHERE user_id = $3
    """, persona_type, confidence, user_id)
```

---

## Persona Analytics

Track persona distribution:

```sql
SELECT
    persona_type,
    COUNT(*) as user_count,
    AVG(persona_confidence) as avg_confidence,
    AVG(adherence_30d) as avg_adherence
FROM user_profiles_extended
WHERE persona_type IS NOT NULL
GROUP BY persona_type
ORDER BY user_count DESC;
```

---

## Best Practices

### 1. Detection Quality
- Require rich consultation data for accurate detection
- Use confidence thresholds (< 0.6 = use general program)
- Allow manual override for edge cases

### 2. Adaptation Sensitivity
- Start conservative, adjust based on feedback
- Monitor adherence by persona
- Fine-tune adaptations based on real user data

### 3. System Prompt Quality
- Be specific in prompt additions
- Test different personas with same requests
- Ensure tone matches persona expectations

### 4. Avoid Stereotyping
- Personas are starting points, not constraints
- Allow user deviation from persona norms
- Adjust based on actual behavior, not just persona

---

## Testing Personas

### Test Detection

```bash
# Test all personas with sample data
python -m pytest tests/test_persona_detection.py

# Test specific persona
python scripts/test_persona.py --persona "Busy Parent"
```

### Test Adaptations

```bash
# Generate program for each persona
python scripts/generate_test_programs.py --all-personas

# Compare adherence by persona
python scripts/analyze_persona_adherence.py --days 30
```

---

## Future Enhancements

### 1. Dynamic Persona Evolution
Track user behavior over time and adjust persona classification:
- Busy Parent → 9-to-5 Hustler (kids grew up, more time available)
- Social Starter → College Athlete (got serious, increased capacity)

### 2. Hybrid Personas
Allow users to match multiple personas:
- "Busy Parent" + "Medical Referral" (60%, 40% weight)

### 3. Machine Learning Classification
Train ML model on user data to improve detection accuracy beyond rule-based system.

### 4. Persona-Specific Onboarding
Customize consultation questions based on suspected persona.

---

## Support

For questions about the Persona System:
- **Code**: `backend/app/services/persona_detection.py`
- **Tests**: `tests/test_persona_detection.py`
- **Database**: `user_profiles_extended.persona_type`

---

**Built with empathy. Powered by intelligence.**
