# Consultation Adapter - COMPLETE ✅

## Summary

The consultation adapter successfully bridges consultation data from external systems into the internal `UserProfile` domain model used by the Phase 1 program generator. This critical integration layer enables the system to generate personalized training and nutrition programs from consultation transcripts.

---

## What Was Accomplished

### 1. **Complete Consultation Adapter (`api/adapters/consultation_adapter.py`)**

A comprehensive, production-ready adapter with the following capabilities:

#### ✅ Core Features
- **Intelligent Goal Mapping**: Maps consultation improvement goals to internal `Goal` enum (FAT_LOSS, MUSCLE_GAIN, RECOMP, MAINTENANCE, PERFORMANCE)
- **Experience Level Detection**: Determines training experience from modality proficiency and years of experience
- **Training Focus Inference**: Infers intensity zone (STRENGTH, HYPERTROPHY, ENDURANCE) from goals and modalities
- **Schedule Optimization**: Extracts training schedule, handles time constraints, validates session counts (2-6 per week)
- **Activity Factor Calculation**: Determines TDEE multiplier based on training frequency and modality types
- **Dietary Preference Mapping**: Maps dietary modes (vegan, vegetarian, pescatarian, etc.) with inference from typical foods
- **Medical Information Extraction**: Safely extracts medical conditions, medications, and injuries with conservative doctor clearance logic
- **Target Weight & Timeline**: Parses target metrics, infers safe rates of change based on goals
- **Food Allergy Detection**: Keyword-based allergen extraction from difficulties and constraints

#### ✅ Robustness Features
- **Validation**: Pre-transformation validation with detailed warnings
- **Sensible Defaults**: Applies evidence-based defaults when consultation data is incomplete
- **Warning System**: Returns comprehensive list of warnings for transparency
- **Error Handling**: Raises `ConsultationValidationError` for critical missing data
- **Logging**: Detailed logging for debugging and monitoring

#### ✅ Mapping Intelligence
- **Keyword-Based Inference**: Analyzes goal descriptions for implicit keywords when explicit mapping fails
- **Priority-Based Selection**: Uses goal priority to determine primary goal
- **Constraint Awareness**: Respects time difficulties, non-negotiables, and medical restrictions
- **Day Normalization**: Handles various day name formats (Mon, Monday, mon, etc.)

### 2. **Fixed UserProfile Dataclass**

Fixed Python dataclass field ordering issues in `services/program_generator/plan_generator.py`:
- Moved `primary_goal` to required fields section (before optional fields)
- Added `Optional` typing to all list fields with None defaults
- Ensures proper dataclass initialization

### 3. **Fixed CompletePlan Dataclass**

Reorganized `CompletePlan` to comply with dataclass field ordering:
- All required fields first
- All optional fields with defaults last
- Maintains backward compatibility with existing generator code

### 4. **Comprehensive Test Suite**

Created `test_consultation_adapter.py` with 6 test cases covering:

1. **Complete Consultation**: Full data transformation with all fields
2. **Minimal Consultation**: Tests default application with sparse data
3. **Fat Loss Goal**: Verifies goal mapping and target weight extraction
4. **Generation Options**: Tests dietary overrides and option passing
5. **Medical Extraction**: Validates medical information parsing
6. **Type Compatibility**: Verifies all enum types are correctly mapped

**Test Results**: ✅ **ALL TESTS PASSED**

---

## Files Created/Modified

### Created
1. `api/adapters/consultation_adapter.py` (923 lines) - Complete adapter implementation
2. `api/adapters/__init__.py` (17 lines) - Package initialization
3. `test_consultation_adapter.py` (390 lines) - Comprehensive test suite
4. `CONSULTATION_ADAPTER_COMPLETE.md` (this file) - Documentation

### Modified
1. `services/program_generator/plan_generator.py` - Fixed dataclass field ordering
   - `UserProfile` class (lines 39-87)
   - `CompletePlan` class (lines 90-113)

---

## Usage Examples

### Basic Usage

```python
from api.schemas.inputs import ConsultationTranscript, UserDemographics, ImprovementGoalInput
from api.adapters import consultation_to_user_profile

# Build consultation transcript
consultation = ConsultationTranscript(
    user_id="user-123",
    session_id="session-456",
    demographics=UserDemographics(
        user_id="user-123",
        age=28,
        sex_at_birth="male",
        weight_kg=82.0,
        height_cm=178.0,
    ),
    improvement_goals=[
        ImprovementGoalInput(
            goal_type="muscle_gain",
            description="Gain lean muscle",
            priority=10,
            timeline_weeks=16,
        )
    ],
)

# Transform to UserProfile
profile, warnings = consultation_to_user_profile(consultation)

# Check warnings
if warnings:
    for warning in warnings:
        print(f"Warning: {warning}")

# Use profile with generator
from services.program_generator import PlanGenerator
generator = PlanGenerator()
plan, plan_warnings = generator.generate_complete_plan(profile)
```

### With Generation Options

```python
from api.schemas.inputs import GenerationOptions, DietaryMode

options = GenerationOptions(
    dietary_mode=DietaryMode.VEGAN,
    program_duration_weeks=12,
    equipment_available=EquipmentAvailability.HOME_GYM_BASIC,
)

profile, warnings = consultation_to_user_profile(consultation, options)
```

### Validation Only

```python
from api.adapters import validate_consultation_data

warnings = validate_consultation_data(consultation)
if warnings:
    print("Consultation needs attention:")
    for w in warnings:
        print(f"  - {w}")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    External System                              │
│          (Consultation Database / Conversation Service)         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ ConsultationTranscript
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Consultation Adapter                          │
│  - Validates completeness                                       │
│  - Maps goals, experience, focus, schedule                      │
│  - Extracts medical, dietary, availability                      │
│  - Applies sensible defaults                                    │
│  - Returns warnings                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ UserProfile
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Phase 1 Generator                             │
│  - Safety Validation                                            │
│  - TDEE Calculation                                             │
│  - Macro Distribution                                           │
│  - Constraint Solving                                           │
│  - Training Program Generation                                  │
│  - Meal Plan Assembly                                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ CompletePlan
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Output Schema / Database Storage                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Type Mappings

### Goal Mapping
| Consultation Goal Type | Internal Goal Enum |
|------------------------|-------------------|
| `fat_loss`, `weight_loss`, `cutting`, `shredding` | `Goal.FAT_LOSS` |
| `muscle_gain`, `muscle_building`, `bulking`, `mass_gain`, `hypertrophy` | `Goal.MUSCLE_GAIN` |
| `recomp`, `body_recomposition`, `toning` | `Goal.RECOMP` |
| `maintenance`, `maintain`, `health` | `Goal.MAINTENANCE` |
| `strength`, `performance` | `Goal.MUSCLE_GAIN` |
| `endurance` | `Goal.MAINTENANCE` |

### Experience Level Mapping
| Proficiency String | Experience Level |
|--------------------|-----------------|
| `beginner`, `novice`, `new`, `starting` | `ExperienceLevel.BEGINNER` |
| `intermediate`, `moderate`, `experienced` | `ExperienceLevel.INTERMEDIATE` |
| `advanced`, `expert`, `elite`, `professional` | `ExperienceLevel.ADVANCED` |

### Intensity Zone Mapping
| Modality | Intensity Zone |
|----------|---------------|
| `powerlifting`, `strongman`, `olympic_weightlifting` | `IntensityZone.STRENGTH` |
| `bodybuilding`, `physique`, `hypertrophy`, `general_fitness` | `IntensityZone.HYPERTROPHY` |
| `endurance`, `marathon`, `cycling`, `triathlon` | `IntensityZone.ENDURANCE` |

### Activity Factor Mapping
| Sessions/Week | Activity Factor |
|---------------|----------------|
| 0-2 | `ActivityFactor.LIGHTLY_ACTIVE` (1.375x) |
| 3-4 | `ActivityFactor.MODERATELY_ACTIVE` (1.55x) |
| 5 | `ActivityFactor.VERY_ACTIVE` (1.725x) |
| 6+ | `ActivityFactor.EXTRA_ACTIVE` (1.9x) |

### Dietary Preference Mapping
| Dietary Mode | Dietary Preference |
|--------------|-------------------|
| `omnivore`, `flexible` | `DietaryPreference.NONE` |
| `vegetarian` | `DietaryPreference.VEGETARIAN` |
| `vegan` | `DietaryPreference.VEGAN` |
| `pescatarian` | `DietaryPreference.PESCATARIAN` |

---

## Default Behavior

When consultation data is incomplete, the adapter applies these defaults:

- **Goal**: `MAINTENANCE` (safest default)
- **Experience**: `INTERMEDIATE` (middle ground)
- **Intensity**: `HYPERTROPHY` (most versatile)
- **Sessions/Week**: `4` (evidence-based optimal frequency)
- **Available Days**: `["monday", "tuesday", "wednesday", "thursday", "friday"]`
- **Activity Factor**: Based on sessions/week mapping
- **Dietary Preference**: `NONE` (flexible)
- **Timeline**: `12 weeks` (from GenerationOptions or default)
- **Doctor Clearance**: `False` if age <16 or >65, or if medical conditions/medications present

---

## Validation Rules

### Critical (Raises Exception)
- **Missing demographics**: Must have age, sex, weight, height

### Warnings (Logged but Continues)
- No improvement goals specified
- No training history or modalities
- No training availability specified
- Could not map goal type
- Missing target weight (inferred from goal)
- Time constraints detected
- Medical conditions without doctor clearance

---

## Testing

Run the comprehensive test suite:

```bash
python test_consultation_adapter.py
```

Expected output:
```
================================================================================
✅ ALL TESTS PASSED!
================================================================================

Consultation adapter is fully functional and type-safe.
Ready for integration with Phase 1 generator.
```

---

## Integration Checklist

- [x] Consultation input schemas defined (`api/schemas/inputs.py`)
- [x] Consultation adapter implemented (`api/adapters/consultation_adapter.py`)
- [x] Adapter exposed via package `__init__.py`
- [x] UserProfile dataclass fixed (field ordering)
- [x] CompletePlan dataclass fixed (field ordering)
- [x] Comprehensive tests created and passing
- [x] Type compatibility verified
- [x] Documentation complete

### Next Steps (Phase 2)

1. **Main API Endpoint**: Create `generate_program_from_consultation()` function
2. **Output Schema**: Define program output format
3. **Error Handling**: Add comprehensive error responses
4. **Integration Tests**: End-to-end tests with real generator
5. **Performance**: Profile and optimize transformation pipeline

---

## Dependencies

- **Required Packages**:
  - `pydantic` (input validation)
  - `ortools` (constraint solver, installed during setup)

- **Internal Modules**:
  - `api.schemas.inputs` (consultation schemas)
  - `services.program_generator.plan_generator` (UserProfile, PlanGenerator)
  - `libs.calculators.macros` (Goal enum)
  - `libs.calculators.tdee` (ActivityFactor enum)
  - `services.program_generator.training_generator` (ExperienceLevel, IntensityZone)
  - `services.program_generator.meal_assembler` (DietaryPreference)

---

## Known Limitations & Future Enhancements

### Current Limitations
1. **Medical Extraction**: Uses simple keyword matching (could use NLP)
2. **Food Allergy Detection**: Limited to common allergens
3. **Target Weight Parsing**: Basic regex (could parse more formats)
4. **Dietary Inference**: Keyword-based (could analyze meal patterns)

### Future Enhancements
1. **ML-Based Goal Detection**: Train classifier on goal descriptions
2. **NLP Medical Extraction**: Use entity recognition for medical info
3. **Smart Defaults**: Learn user-specific defaults from historical data
4. **Confidence Scores**: Return confidence for inferred values
5. **Alternative Profiles**: Generate multiple profile variations for comparison

---

## Maintenance Notes

### Updating Mappings
To add new goal types, experience levels, or modalities:
1. Update the respective `_build_*_mappings()` method in `ConsultationAdapter`
2. Add test case to `test_consultation_adapter.py`
3. Update this documentation

### Modifying Defaults
Default values are defined in:
- `ConsultationAdapter._determine_*()` methods (runtime defaults)
- `UserProfile` dataclass (structural defaults)

### Adding Validation Rules
Add new validation logic to:
- `ConsultationAdapter._validate_consultation()` (pre-transformation)
- Individual `_determine_*()` methods (field-specific validation)

---

## Contact & Support

For questions or issues with the consultation adapter:
1. Check test suite output for specific error details
2. Review warning messages from transformation
3. Verify consultation data completeness
4. Ensure all required enum values are mapped

---

## Changelog

### Version 1.0.0 (Current)
- ✅ Initial implementation
- ✅ Complete goal, experience, intensity, schedule mapping
- ✅ Medical, dietary, availability extraction
- ✅ Comprehensive test suite
- ✅ Documentation complete
- ✅ All tests passing
- ✅ Type-safe and production-ready

---

**Status**: ✅ **COMPLETE AND READY FOR INTEGRATION**

The consultation adapter is fully functional, comprehensively tested, and ready to be integrated with the Phase 1 program generator. All type mappings are verified, default behavior is sensible, and the warning system provides full transparency.
