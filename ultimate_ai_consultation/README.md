# ULTIMATE AI CONSULTATION - Adaptive Program Generation

> **Integrates with ULTIMATE_COACH_BACKEND for adaptive, evidence-based fitness & nutrition programming**

## Overview

This module extends ULTIMATE COACH with:
- **Feasibility Engine**: Mathematical validation of goals vs constraints
- **Program Generation**: Evidence-based workout & meal plans from consultation data
- **Adaptive Controller**: Bi-weekly reassessment with PID loops
- **Confidence Tracking**: Multi-modal logging with statistical intervals
- **Safety Validation**: Non-bypassable medical and age gates

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  ULTIMATE_COACH_BACKEND (Existing)                         │
│  ├─ ConsultationAIService (conversational intake)          │
│  ├─ UnifiedCoachService (daily check-ins)                  │
│  ├─ Database (foods, meals, activities, consultation data) │
│  └─ Coach Conversations (chat history)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  ultimate_ai_consultation (This Module)                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ services/solver/                                       │ │
│  │  └─ Constraint satisfaction (OR-Tools CP-SAT)         │ │
│  │     Input: Consultation data                           │ │
│  │     Output: Feasible params OR A/B/C trade-offs       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ services/programmer/                                   │ │
│  │  ├─ Evidence-based microcycle templates               │ │
│  │  ├─ Nutrition calculator (TDEE, macros)               │ │
│  │  └─ Meal assembler (uses existing foods DB)           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ services/adaptive/                                     │ │
│  │  ├─ Data aggregator (meals, activities, metrics)      │ │
│  │  ├─ PID controllers (calories, volume, intensity)     │ │
│  │  └─ Sentiment analyzer (from coach messages)          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ services/validators/                                   │ │
│  │  ├─ Safety gate (medical, age)                        │ │
│  │  ├─ Domain rules (volume ramps, deload timing)        │ │
│  │  └─ Adherence risk scorer                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Integration with ULTIMATE_COACH_BACKEND

### 1. Database

New tables added via migration:
```sql
plan_versions       -- Generated plans with full parameters
feasibility_checks  -- Solver validation results
plan_adjustments    -- Adaptive loop modifications
```

Existing tables enhanced:
```sql
-- Add confidence tracking
ALTER TABLE meals ADD COLUMN confidence NUMERIC(3,2);
ALTER TABLE activities ADD COLUMN confidence NUMERIC(3,2);
ALTER TABLE body_metrics ADD COLUMN confidence NUMERIC(3,2);
```

### 2. API Endpoints

New routes in `ULTIMATE_COACH_BACKEND/app/api/v1/programs.py`:
```python
POST   /api/v1/programs/generate         # Generate initial plan
GET    /api/v1/programs/{plan_id}        # Get plan details
POST   /api/v1/programs/{plan_id}/adjust # Trigger reassessment
GET    /api/v1/programs/{plan_id}/versions # Plan history
```

### 3. Service Integration

Backend calls this module:
```python
from ultimate_ai_consultation.services.solver import feasibility_check
from ultimate_ai_consultation.services.programmer import generate_program
from ultimate_ai_consultation.services.adaptive import reassess_plan
```

## Quick Start

### Installation

```bash
# Install dependencies
cd ultimate_ai_consultation
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with Anthropic API key and Supabase credentials

# Run database migration (in ULTIMATE_COACH_BACKEND)
psql $DATABASE_URL < integration/migrations/001_adaptive_system.sql
```

### Usage

```python
from ultimate_ai_consultation.services.solver import ConstraintSolver
from ultimate_ai_consultation.services.programmer import ProgramGenerator

# 1. Validate feasibility
solver = ConstraintSolver()
result = await solver.check_feasibility(
    user_id="user-uuid",
    consultation_data={...}
)

if not result['feasible']:
    # Show user A/B/C trade-offs
    print(result['trade_offs'])

# 2. Generate program
generator = ProgramGenerator()
plan = await generator.generate(
    user_id="user-uuid",
    plan_params=result['plan_params']
)
```

## Core Principles

### 1. Evidence-Based Templates

All training programs based on validated protocols:
- **Strength**: Texas Method, 5/3/1, Linear Progression
- **Hypertrophy**: Renaissance Periodization volume landmarks
- **Endurance**: Norwegian Method (80/20 polarized)
- **Sport-Specific**: Researched protocols

### 2. Deterministic Core

LLM for conversation, math for decisions:
- Constraint solver: Pure optimization (no LLM)
- Nutrition calculator: Ensemble equations (Katch-McArdle, Mifflin-St Jeor)
- Volume progression: Evidence-based ramp rates (<20%/week)
- Deload timing: Fixed protocols (every 4-6 weeks)

### 3. Safety First

Non-bypassable gates:
- Medical red flags (cardiac, pregnancy without clearance, eating disorders)
- Age-appropriate programming (no aggressive cuts for <18, fall risk >65)
- Calorie bounds (-25% to +20% TDEE)
- Volume caps (MEV to MRV per muscle group)

### 4. Explainability

Every recommendation has:
- **Rationale**: "Why did you recommend this?"
- **Data source**: "What data did you use?"
- **Confidence level**: "How confident are you?"
- **Alternative options**: "What else could I do?"

### 5. Cost Effective

Target: <$2/user/month LLM costs
- Consultation: Reuse existing ConsultationAIService (~$0.50)
- Daily check-ins: Existing UnifiedCoachService
- Reassessment: Mostly deterministic + Claude summary (~$0.15)
- Vision API: Aggressive limits (5 photos/week free tier)

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires database)
pytest tests/integration/ -v

# Red team (synthetic personas)
pytest tests/red_team/ -v
```

### Code Structure

```
ultimate_ai_consultation/
├── services/
│   ├── solver/
│   │   ├── __init__.py
│   │   ├── constraint_solver.py        # OR-Tools CP-SAT
│   │   ├── trade_off_generator.py      # A/B/C options
│   │   └── diagnostics.py              # Infeasibility reporting
│   ├── programmer/
│   │   ├── __init__.py
│   │   ├── program_generator.py        # Main orchestrator
│   │   ├── nutrition_calculator.py     # TDEE, macros
│   │   ├── meal_assembler.py           # From foods DB
│   │   └── workout_builder.py          # From templates
│   ├── adaptive/
│   │   ├── __init__.py
│   │   ├── data_aggregator.py          # Pull from DB
│   │   ├── controllers.py              # PID loops
│   │   └── sentiment_analyzer.py       # From coach messages
│   └── validators/
│       ├── __init__.py
│       ├── safety_gate.py              # Medical screening
│       ├── domain_rules.py             # Volume, progression
│       └── adherence_risk.py           # Complexity scoring
├── libs/
│   ├── calculators/
│   │   ├── tdee.py                     # Energy estimation
│   │   ├── macros.py                   # Protein, carbs, fat
│   │   └── volume_landmarks.py         # MEV, MAV, MRV
│   └── templates/
│       ├── strength/                   # Powerlifting, 5/3/1
│       ├── hypertrophy/                # RP volume landmarks
│       ├── endurance/                  # 80/20 polarized
│       └── sports/                     # Sport-specific
├── schemas/
│   ├── constraints.py                  # Pydantic models
│   ├── plan.py                         # Plan structure
│   └── assessment.py                   # Reassessment data
├── integration/
│   ├── backend_adapter.py              # FastAPI routes
│   ├── migrations/                     # SQL migrations
│   └── INTEGRATION_GUIDE.md
├── tests/
│   ├── unit/
│   ├── integration/
│   └── red_team/
│       └── personas.json               # 100 test cases
└── docs/
    ├── SYSTEM_DESIGN.md
    ├── API_REFERENCE.md
    └── EVIDENCE_BASE.md                # Research citations
```

## Roadmap

### Phase 1A: Foundation (Weeks 1-3) ✅ COMPLETE
- [x] Project structure
- [x] Database migration (001_adaptive_system.sql)
- [x] TDEE calculator (4 equations with confidence intervals)
- [x] Macro calculator (evidence-based targets)
- [x] Safety validator (non-bypassable medical gates)
- [x] Constraint solver (OR-Tools CP-SAT with trade-offs)
- [x] Evidence base documentation

### Phase 1B: Program Generation (Weeks 4-5) ✅ COMPLETE
- [x] Training program generator (Full Body, Upper/Lower, PPL splits)
- [x] Meal plan assembler (14-day plans with dietary preferences)
- [x] Unified plan generator (complete pipeline orchestration)
- [x] Grocery list generator (with cost estimates)
- [x] End-to-end demo example
- [x] Integration ready for backend

### Phase 2: Adaptive Loop (Weeks 6-8) ✅ COMPLETE
- [x] Data aggregator (pull from meals/activities/body_metrics)
- [x] PID controllers (calorie and volume adjustments)
- [x] Bi-weekly reassessment system
- [x] Sentiment analyzer (from coach messages)
- [x] Plan versioning and adjustment tracking

### Phase 3: Enhanced Features (Weeks 9-11)
- [ ] Vision API integration (with rate limits)
- [ ] Wearable data sync (HRV, RHR)
- [ ] Budget optimizer (cost-conscious meal planning)
- [ ] Template library expansion (8-10 protocols)

### Phase 4: Production (Weeks 12-14)
- [ ] Legal framework and disclaimers
- [ ] Red team testing (100 synthetic personas)
- [ ] Monitoring & alerts
- [ ] Full documentation and API reference

## Support

For questions or issues:
1. Check `docs/` directory
2. Review `integration/INTEGRATION_GUIDE.md`
3. See existing backend patterns in `ULTIMATE_COACH_BACKEND/app/services/`

## License

Proprietary - ULTIMATE COACH
