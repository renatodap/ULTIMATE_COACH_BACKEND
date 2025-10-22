# Integration Guide: Ultimate AI Consultation → ULTIMATE_COACH_BACKEND

This guide explains how to integrate the adaptive consultation system into your existing ULTIMATE COACH stack.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Database Migration](#database-migration)
3. [Backend Integration](#backend-integration)
4. [Service Layer](#service-layer)
5. [API Endpoints](#api-endpoints)
6. [Frontend Integration](#frontend-integration)
7. [Testing](#testing)
8. [Deployment](#deployment)

---

## Quick Start

### Prerequisites

- ULTIMATE_COACH_BACKEND running and accessible
- PostgreSQL database with existing schema
- Python 3.11+
- Anthropic API key (for any LLM features)

### Installation

```bash
# 1. Navigate to consultation directory
cd ultimate_ai_consultation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials (same as ULTIMATE_COACH_BACKEND)

# 4. Run database migration
cd ../ULTIMATE_COACH_BACKEND
psql $DATABASE_URL -f ../ultimate_ai_consultation/integration/migrations/001_adaptive_system.sql
```

---

## Database Migration

### New Tables Created

The migration adds three new tables:

```sql
plan_versions         -- Complete generated programs (training + nutrition)
feasibility_checks    -- Constraint solver validation results
plan_adjustments      -- Bi-weekly reassessment modifications
```

### Existing Tables Enhanced

Adds confidence tracking to:

```sql
-- meals table
ALTER TABLE meals ADD COLUMN confidence NUMERIC(3,2);
ALTER TABLE meals ADD COLUMN data_source TEXT;
ALTER TABLE meals ADD COLUMN ci_lower_kcal NUMERIC(10,2);
ALTER TABLE meals ADD COLUMN ci_upper_kcal NUMERIC(10,2);

-- activities table
ALTER TABLE activities ADD COLUMN confidence NUMERIC(3,2);
ALTER TABLE activities ADD COLUMN data_source_type TEXT;

-- body_metrics table (created if doesn't exist)
```

### Verification

After migration, verify:

```sql
-- Check new tables exist
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('plan_versions', 'feasibility_checks', 'plan_adjustments');

-- Check new columns
SELECT column_name FROM information_schema.columns
WHERE table_name = 'meals' AND column_name = 'confidence';
```

---

## Backend Integration

### Option 1: Module Import (Recommended)

Add `ultimate_ai_consultation` to your Python path:

```python
# ULTIMATE_COACH_BACKEND/app/main.py
import sys
sys.path.insert(0, "../ultimate_ai_consultation")

# Now you can import
from services.solver.constraint_solver import ConstraintSolver
from services.validators.safety_gate import SafetyValidator
from libs.calculators.tdee import calculate_tdee
from libs.calculators.macros import MacroCalculator, Goal
```

### Option 2: Package Installation (Production)

```bash
# In ultimate_ai_consultation/
pip install -e .

# Or build wheel
python -m build
pip install dist/ultimate_ai_consultation-*.whl
```

### Option 3: Submodule (Git)

```bash
# In ULTIMATE_COACH_BACKEND/
git submodule add ../ultimate_ai_consultation modules/consultation
```

---

## Service Layer

### Create Wrapper Service

Create `ULTIMATE_COACH_BACKEND/app/services/program_service.py`:

```python
"""
Program Generation Service

Orchestrates feasibility checking, safety validation, and program generation.
"""

import sys
sys.path.insert(0, "../../ultimate_ai_consultation")

from typing import Dict, Optional
from uuid import UUID
import logging

from services.validators.safety_gate import SafetyValidator
from libs.calculators.tdee import calculate_tdee
from libs.calculators.macros import MacroCalculator, Goal
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)


class ProgramService:
    """
    Wraps consultation system for use in ULTIMATE_COACH_BACKEND.
    """

    def __init__(self):
        self.safety = SafetyValidator()
        self.macro_calc = MacroCalculator()
        self.db = supabase_service

    async def generate_initial_plan(
        self,
        user_id: str,
        consultation_session_id: str
    ) -> Dict:
        """
        Generate initial plan from completed consultation.

        Args:
            user_id: User UUID
            consultation_session_id: Completed consultation session

        Returns:
            Dict with plan_version_id and program details
        """
        # 1. Fetch consultation data
        consultation_data = await self._get_consultation_data(
            user_id, consultation_session_id
        )

        # 2. Get user profile
        profile = await self._get_user_profile(user_id)

        # 3. Safety validation
        safety_result = self.safety.validate(
            age=profile["age"],
            sex_at_birth=profile["sex_at_birth"],
            weight_kg=profile["weight_kg"],
            height_cm=profile["height_cm"],
            medical_conditions=consultation_data.get("medical_conditions", []),
            medications=consultation_data.get("medications", []),
            recent_surgeries=consultation_data.get("recent_surgeries"),
            pregnancy_status=consultation_data.get("pregnancy_status"),
            doctor_clearance=consultation_data.get("doctor_clearance", False),
            goal=consultation_data["primary_goal"],
        )

        if not safety_result.passed:
            logger.warning(f"Safety check failed for user {user_id}")
            return {
                "success": False,
                "blocked": True,
                "reason": safety_result.reason,
                "recommendations": safety_result.recommendations,
            }

        # 4. Calculate TDEE
        tdee_result = calculate_tdee(
            age=profile["age"],
            sex_at_birth=profile["sex_at_birth"],
            weight_kg=profile["weight_kg"],
            height_cm=profile["height_cm"],
            sessions_per_week=consultation_data["training_sessions_per_week"],
            body_fat_percent=profile.get("body_fat_percent"),
        )

        # 5. Calculate macros
        goal_enum = Goal[consultation_data["primary_goal"].upper()]
        macros = self.macro_calc.calculate(
            tdee=tdee_result.tdee_mean,
            goal=goal_enum,
            weight_kg=profile["weight_kg"],
            body_fat_percent=profile.get("body_fat_percent"),
            training_sessions_per_week=consultation_data["training_sessions_per_week"],
            age=profile["age"],
            sex_at_birth=profile["sex_at_birth"],
        )

        # 6. TODO: Run constraint solver (Phase 1)
        # 7. TODO: Generate training program (Phase 1)
        # 8. TODO: Generate nutrition program (Phase 1)

        # For now, store basic plan
        plan_params = {
            "tdee": tdee_result.tdee_mean,
            "calories": macros.calories,
            "protein_g": macros.protein_g,
            "carbs_g": macros.carbs_g,
            "fat_g": macros.fat_g,
            "safety_modifications": safety_result.modifications,
        }

        # Save to plan_versions
        plan_version = await self._create_plan_version(
            user_id=user_id,
            consultation_session_id=consultation_session_id,
            plan_params=plan_params,
            macros=macros,
            tdee_result=tdee_result,
            safety_result=safety_result,
        )

        return {
            "success": True,
            "plan_version_id": plan_version["id"],
            "tdee": tdee_result.tdee_mean,
            "macros": {
                "calories": macros.calories,
                "protein": macros.protein_g,
                "carbs": macros.carbs_g,
                "fat": macros.fat_g,
            },
            "warnings": safety_result.recommendations if safety_result.modifications else [],
        }

    async def _get_consultation_data(self, user_id: str, session_id: str) -> Dict:
        """Fetch and aggregate consultation data."""
        # Fetch from your existing consultation tables
        # (user_training_modalities, user_familiar_exercises, etc.)
        pass

    async def _get_user_profile(self, user_id: str) -> Dict:
        """Fetch user profile."""
        profile = self.db.client.table("profiles")\
            .select("*")\
            .eq("id", user_id)\
            .single()\
            .execute()
        return profile.data

    async def _create_plan_version(
        self,
        user_id: str,
        consultation_session_id: str,
        plan_params: Dict,
        macros,
        tdee_result,
        safety_result,
    ) -> Dict:
        """Create plan_version record."""
        # Get next version number
        existing = self.db.client.table("plan_versions")\
            .select("version_number")\
            .eq("user_id", user_id)\
            .order("version_number", desc=True)\
            .limit(1)\
            .execute()

        version_number = (existing.data[0]["version_number"] + 1) if existing.data else 1

        # Create record
        plan_data = {
            "user_id": user_id,
            "version_number": version_number,
            "status": "draft",
            "consultation_session_id": consultation_session_id,
            "primary_goal": plan_params.get("goal", "maintenance"),
            "plan_params": plan_params,
            "training_program": [],  # TODO: Generate in Phase 1
            "nutrition_program": [],  # TODO: Generate in Phase 1
            "rationale": "\n".join(macros.rationale),
            "assumptions": [
                f"TDEE: {tdee_result.tdee_mean} ± {(tdee_result.tdee_ci_upper - tdee_result.tdee_mean)} kcal",
                f"Confidence: {tdee_result.confidence:.0%}",
                *tdee_result.notes,
            ],
            "confidence": {
                "tdee": tdee_result.confidence,
                "adherence_prediction": 0.80,  # Default estimate
            },
        }

        result = self.db.client.table("plan_versions")\
            .insert(plan_data)\
            .execute()

        return result.data[0]
```

---

## API Endpoints

Create `ULTIMATE_COACH_BACKEND/app/api/v1/programs.py`:

```python
"""
Program API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.services.program_service import ProgramService

router = APIRouter(prefix="/programs", tags=["programs"])


class GeneratePlanRequest(BaseModel):
    consultation_session_id: str


class GeneratePlanResponse(BaseModel):
    success: bool
    plan_version_id: Optional[str] = None
    blocked: bool = False
    reason: Optional[str] = None
    recommendations: list[str] = []
    tdee: Optional[int] = None
    macros: Optional[dict] = None


@router.post("/generate", response_model=GeneratePlanResponse)
async def generate_plan(
    request: GeneratePlanRequest,
    current_user = Depends(get_current_user)
):
    """
    Generate initial program from completed consultation.

    Performs:
    1. Safety validation
    2. TDEE calculation
    3. Macro calculation
    4. Constraint solving (TODO)
    5. Program generation (TODO)
    """
    service = ProgramService()
    result = await service.generate_initial_plan(
        user_id=current_user["id"],
        consultation_session_id=request.consultation_session_id
    )

    if not result["success"]:
        return GeneratePlanResponse(
            success=False,
            blocked=result.get("blocked", False),
            reason=result.get("reason"),
            recommendations=result.get("recommendations", [])
        )

    return GeneratePlanResponse(
        success=True,
        plan_version_id=result["plan_version_id"],
        tdee=result["tdee"],
        macros=result["macros"],
        recommendations=result.get("warnings", [])
    )


@router.get("/{plan_version_id}")
async def get_plan(
    plan_version_id: str,
    current_user = Depends(get_current_user)
):
    """Get plan details."""
    # TODO: Implement
    pass


@router.post("/{plan_version_id}/adjust")
async def adjust_plan(
    plan_version_id: str,
    current_user = Depends(get_current_user)
):
    """Trigger bi-weekly reassessment and adjustment."""
    # TODO: Implement (Phase 2)
    pass
```

Register in `ULTIMATE_COACH_BACKEND/app/main.py`:

```python
from app.api.v1 import programs

app.include_router(programs.router, prefix="/api/v1")
```

---

## Frontend Integration

### 1. Add API Client Methods

In `ULTIMATE_COACH_FRONTEND/lib/api/programs.ts`:

```typescript
export interface GeneratePlanRequest {
  consultation_session_id: string;
}

export interface GeneratePlanResponse {
  success: boolean;
  plan_version_id?: string;
  blocked?: boolean;
  reason?: string;
  recommendations?: string[];
  tdee?: number;
  macros?: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
  };
}

export async function generatePlan(
  request: GeneratePlanRequest
): Promise<GeneratePlanResponse> {
  const response = await fetch('/api/v1/programs/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to generate plan: ${response.statusText}`);
  }

  return response.json();
}
```

### 2. Create Plan View Component

In `ULTIMATE_COACH_FRONTEND/app/programs/[id]/page.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

export default function PlanPage() {
  const params = useParams();
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch plan details
    fetch(`/api/v1/programs/${params.id}`, {
      credentials: 'include',
    })
      .then((res) => res.json())
      .then((data) => {
        setPlan(data);
        setLoading(false);
      });
  }, [params.id]);

  if (loading) return <div>Loading plan...</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Your Program</h1>

      {/* Nutrition Overview */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-4 rounded shadow">
          <div className="text-sm text-gray-600">Calories</div>
          <div className="text-2xl font-bold">{plan.macros.calories}</div>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <div className="text-sm text-gray-600">Protein</div>
          <div className="text-2xl font-bold">{plan.macros.protein}g</div>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <div className="text-sm text-gray-600">Carbs</div>
          <div className="text-2xl font-bold">{plan.macros.carbs}g</div>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <div className="text-sm text-gray-600">Fat</div>
          <div className="text-2xl font-bold">{plan.macros.fat}g</div>
        </div>
      </div>

      {/* Training Program (TODO) */}
      {/* Meal Plan (TODO) */}
    </div>
  );
}
```

---

## Testing

### Unit Tests

```bash
# In ultimate_ai_consultation/
pytest tests/unit/ -v

# Test specific module
pytest tests/unit/test_tdee.py -v
pytest tests/unit/test_macros.py -v
pytest tests/unit/test_safety.py -v
```

### Integration Tests

```bash
# Requires database
pytest tests/integration/ -v
```

### Example Test

`tests/unit/test_safety.py`:

```python
import pytest
from services.validators.safety_gate import SafetyValidator, SafetyLevel


def test_cardiac_condition_blocks_without_clearance():
    """Cardiac condition without clearance should block."""
    validator = SafetyValidator()

    result = validator.validate(
        age=45,
        sex_at_birth="male",
        weight_kg=80,
        height_cm=175,
        medical_conditions=["heart disease"],
        medications=[],
        recent_surgeries=None,
        pregnancy_status=None,
        doctor_clearance=False,
        goal="muscle_gain"
    )

    assert not result.passed
    assert result.level == SafetyLevel.BLOCKED
    assert any("cardiac" in v["message"].lower() for v in result.violations)
```

---

## Deployment

### Production Checklist

- [ ] Run migration in production database
- [ ] Set `ENVIRONMENT=production` in .env
- [ ] Verify `ENABLE_SAFETY_GATE=true` (NEVER disable!)
- [ ] Configure Sentry DSN for error tracking
- [ ] Set up monitoring for plan generation failures
- [ ] Test safety gates with edge cases
- [ ] Verify consultation → plan flow end-to-end

### Monitoring

Key metrics to track:

```python
# Log these in production
- plan_generation_success_rate
- plan_generation_duration_ms
- safety_blocks_count (by reason)
- safety_warnings_count
- average_tdee_confidence
- consultation_to_plan_conversion_rate
```

---

## Next Steps

1. ✅ Complete Phase 1 (MVP):
   - Constraint solver implementation
   - Training program generator
   - Meal assembler

2. Phase 2 (Adaptive Loop):
   - Bi-weekly reassessment service
   - PID controllers
   - Plan adjustment endpoint

3. Phase 3 (Enhanced Logging):
   - Vision API integration
   - Confidence tracking updates
   - Budget optimizer

---

## Support

Questions? Check:
- `docs/SYSTEM_DESIGN.md` for architecture details
- `schemas/` for data structures
- Existing backend patterns in `ULTIMATE_COACH_BACKEND/app/services/`
