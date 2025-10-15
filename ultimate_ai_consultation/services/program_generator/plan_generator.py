"""
Plan Generator - Unified Training & Nutrition Programs

Orchestrates the complete program generation pipeline:
1. Validate feasibility with constraint solver
2. Generate training program
3. Generate meal plan
4. Combine into 14-day integrated program
5. Store in database
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

from libs.calculators.tdee import TDEECalculator, TDEEResult, ActivityFactor
from libs.calculators.macros import MacroCalculator, MacroTargets as CalcMacroTargets, Goal
from services.validators.safety_gate import SafetyValidator, SafetyLevel, SafetyCheckResult
from services.solver.constraint_solver import (
    ConstraintSolver,
    FeasibilityStatus,
    SolverResult,
)
from .training_generator import (
    TrainingGenerator,
    TrainingProgram,
    ExperienceLevel,
    IntensityZone,
)
from .meal_assembler import (
    MealAssembler,
    DailyMealPlan,
    MacroTargets as MealMacroTargets,
    DietaryPreference,
)
from .modality_planner import (
    ModalityPlanner,
    ModalityPreference as PlannerModalityPreference,
    FacilityAccess as PlannerFacilityAccess,
    MultimodalSessionInternal,
)


@dataclass
class UserProfile:
    """Complete user profile from consultation"""

    # Demographics (required)
    user_id: str
    age: int
    sex_at_birth: str
    weight_kg: float
    height_cm: float
    primary_goal: Goal  # FAT_LOSS, MUSCLE_GAIN, RECOMP, MAINTENANCE (required)
    
    # Demographics (optional)
    body_fat_percentage: Optional[float] = None

    # Goals
    target_weight_kg: Optional[float] = None
    timeline_weeks: Optional[int] = 12

    # Training preferences
    sessions_per_week: int = 4
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    training_focus: IntensityZone = IntensityZone.HYPERTROPHY
    available_days: Optional[List[str]] = None

    # Nutrition preferences
    dietary_preference: DietaryPreference = DietaryPreference.NONE
    food_allergies: Optional[List[str]] = None

    # Activity
    activity_factor: ActivityFactor = ActivityFactor.MODERATELY_ACTIVE

    # Medical/Safety
    medical_conditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    injuries: Optional[List[str]] = None
    doctor_clearance: bool = False

    # Multimodal preferences (optional)
    modality_preferences: Optional[List[PlannerModalityPreference]] = None
    facility_access: Optional[List[PlannerFacilityAccess]] = None

    def __post_init__(self):
        if self.available_days is None:
            self.available_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        if self.food_allergies is None:
            self.food_allergies = []
        if self.medical_conditions is None:
            self.medical_conditions = []
        if self.medications is None:
            self.medications = []
        if self.injuries is None:
            self.injuries = []


@dataclass
class CompletePlan:
    """Complete 14-day training + nutrition program"""

    # Required fields
    plan_id: str
    user_id: str
    version: int
    created_at: datetime
    goal: Goal
    tdee_result: TDEEResult
    daily_calorie_target: int
    macro_targets: CalcMacroTargets
    rate_of_change_kg_per_week: float  # Positive = gain, negative = loss
    training_program: TrainingProgram
    meal_plans: List[DailyMealPlan]
    feasibility_result: SolverResult
    safety_result: SafetyCheckResult
    
    # Optional fields with defaults
    duration_days: int = 14
    training_sessions_per_week: int = 4
    notes: str = ""
    next_reassessment_date: Optional[datetime] = None
    multimodal_sessions_weekly: Optional[List[MultimodalSessionInternal]] = None


class PlanGenerator:
    """Generates complete 14-day training + nutrition programs"""

    def __init__(self):
        self.tdee_calculator = TDEECalculator()
        self.macro_calculator = MacroCalculator()
        self.safety_validator = SafetyValidator()
        self.constraint_solver = ConstraintSolver()
        self.training_generator = TrainingGenerator()
        self.meal_assembler = MealAssembler()
        self.modality_planner = ModalityPlanner()

    def generate_complete_plan(
        self, profile: UserProfile, plan_version: int = 1
    ) -> Tuple[CompletePlan, List[str]]:
        """
        Generate complete 14-day program from user profile.

        Returns:
            (CompletePlan, warnings) - Complete program and any warning messages

        Raises:
            ValueError: If plan is unsafe or infeasible
        """
        warnings = []

        # Step 1: Safety Validation (non-bypassable)
        safety_result = self._validate_safety(profile)
        if safety_result.level == SafetyLevel.BLOCKED:
            raise ValueError(
                f"Cannot generate plan due to safety concerns: {safety_result.message}"
            )
        if safety_result.level == SafetyLevel.WARNING:
            warnings.append(f"Safety warning: {safety_result.message}")

        # Step 2: Calculate TDEE
        tdee_result = self._calculate_tdee(profile)

        # Step 3: Calculate target calories based on goal
        target_calories, rate_of_change = self._calculate_calorie_target(
            tdee=tdee_result.tdee_mean,
            goal=profile.primary_goal,
            timeline_weeks=profile.timeline_weeks,
            current_weight=profile.weight_kg,
            target_weight=profile.target_weight_kg,
        )

        # Step 4: Calculate macro targets
        macro_targets = self._calculate_macros(
            calories=target_calories,
            goal=profile.primary_goal,
            weight_kg=profile.weight_kg,
            training_sessions_per_week=profile.sessions_per_week,
        )

        # Step 5: Feasibility check with constraint solver
        feasibility_result = self._check_feasibility(
            profile=profile,
            target_calories=target_calories,
            tdee_result=tdee_result,
        )

        if feasibility_result.status == FeasibilityStatus.INFEASIBLE:
            error_msg = f"Plan is infeasible: {feasibility_result.message}\n"
            if feasibility_result.trade_offs:
                error_msg += "Suggested trade-offs:\n"
                for i, option in enumerate(feasibility_result.trade_offs, 1):
                    error_msg += f"  Option {i}: {option.description}\n"
            raise ValueError(error_msg)

        if feasibility_result.status == FeasibilityStatus.SUBOPTIMAL:
            warnings.append(f"Plan is suboptimal: {feasibility_result.message}")

        # Step 6: Generate training program
        training_program = self._generate_training_program(profile)

        # Step 7: Generate 14-day meal plan
        meal_plans = self._generate_meal_plans(
            profile=profile, macro_targets=macro_targets
        )

        # Step 7b: Generate weekly multimodal sessions (optional)
        multimodal_sessions = None
        if profile.modality_preferences:
            multimodal_sessions = self.modality_planner.plan_week(
                preferences=profile.modality_preferences,
                available_days=profile.available_days or [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ],
                resistance_sessions_per_week=profile.sessions_per_week,
                facility_access=profile.facility_access,
                age=profile.age,
            )

        # Step 8: Create complete plan
        plan = CompletePlan(
            plan_id=f"plan_{profile.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_id=profile.user_id,
            version=plan_version,
            created_at=datetime.now(),
            goal=profile.primary_goal,
            duration_days=14,
            training_sessions_per_week=profile.sessions_per_week,
            tdee_result=tdee_result,
            daily_calorie_target=target_calories,
            macro_targets=macro_targets,
            rate_of_change_kg_per_week=rate_of_change,
            training_program=training_program,
            meal_plans=meal_plans,
            feasibility_result=feasibility_result,
            safety_result=safety_result,
            notes=self._generate_plan_notes(profile, safety_result, feasibility_result),
            next_reassessment_date=datetime.now() + timedelta(days=14),
            multimodal_sessions_weekly=multimodal_sessions,
        )

        return plan, warnings

    def _validate_safety(self, profile: UserProfile) -> SafetyCheckResult:
        """Run safety validation"""
        return self.safety_validator.validate(
            age=profile.age,
            sex_at_birth=profile.sex_at_birth,
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            medical_conditions=profile.medical_conditions or [],
            medications=profile.medications or [],
            recent_surgeries=None,
            pregnancy_status=None,
            doctor_clearance=profile.doctor_clearance,
            goal=profile.primary_goal.value,
            target_calorie_deficit_pct=None,
            training_intensity=None,
        )

    def _calculate_tdee(self, profile: UserProfile) -> TDEEResult:
        """Calculate TDEE with ensemble method"""
        return self.tdee_calculator.calculate(
            age=profile.age,
            sex_at_birth=profile.sex_at_birth,
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            activity_level=profile.activity_factor,
            body_fat_percent=profile.body_fat_percentage,
        )

    def _calculate_calorie_target(
        self,
        tdee: float,
        goal: Goal,
        timeline_weeks: int,
        current_weight: float,
        target_weight: Optional[float],
    ) -> Tuple[int, float]:
        """
        Calculate daily calorie target and expected rate of change.

        Returns:
            (daily_calories, kg_per_week) - Target calories and rate of change
        """
        if goal == Goal.MAINTENANCE:
            return int(tdee), 0.0

        elif goal == Goal.FAT_LOSS:
            # Safe rate: 0.5-1% bodyweight per week
            safe_rate_kg_per_week = current_weight * 0.007  # 0.7% per week
            calories_deficit_per_week = safe_rate_kg_per_week * 7700  # 7700 kcal per kg
            daily_deficit = calories_deficit_per_week / 7

            # Cap at 25% below TDEE (safety limit from evidence base)
            max_deficit = tdee * 0.25
            actual_deficit = min(daily_deficit, max_deficit)

            target_calories = int(tdee - actual_deficit)
            actual_rate = -(actual_deficit * 7) / 7700  # Negative for loss

            return target_calories, actual_rate

        elif goal == Goal.MUSCLE_GAIN:
            # Conservative lean gain: 0.25-0.5% bodyweight per week
            safe_rate_kg_per_week = current_weight * 0.004  # 0.4% per week
            calories_surplus_per_week = safe_rate_kg_per_week * 7700
            daily_surplus = calories_surplus_per_week / 7

            # Cap at 15% above TDEE
            max_surplus = tdee * 0.15
            actual_surplus = min(daily_surplus, max_surplus)

            target_calories = int(tdee + actual_surplus)
            actual_rate = (actual_surplus * 7) / 7700  # Positive for gain

            return target_calories, actual_rate

        else:  # RECOMP
            # Slight deficit on rest days, slight surplus on training days
            # Average to maintenance
            return int(tdee), 0.0

    def _calculate_macros(
        self,
        calories: int,
        goal: Goal,
        weight_kg: float,
        training_sessions_per_week: int,
    ) -> CalcMacroTargets:
        """Calculate macro targets"""
        return self.macro_calculator.calculate(
            tdee=calories,
            goal=goal,
            weight_kg=weight_kg,
            body_fat_percent=None,
            training_sessions_per_week=training_sessions_per_week,
        )

    def _check_feasibility(
        self, profile: UserProfile, target_calories: int, tdee_result: TDEEResult
    ) -> SolverResult:
        """Validate plan feasibility with constraint solver (CP-SAT)."""
        # Safe calorie bounds
        min_safe_calories = 1200 if profile.sex_at_birth.lower() == "female" else 1500
        max_safe_calories = int(tdee_result.tdee_ci_upper * 1.2)

        # Map available days (strings) to indices 1..7 (Mon..Sun)
        day_map = {
            "monday": 1,
            "tuesday": 2,
            "wednesday": 3,
            "thursday": 4,
            "friday": 5,
            "saturday": 6,
            "sunday": 7,
        }
        available_days_idx = [day_map.get(d.lower(), 1) for d in (profile.available_days or ["monday", "wednesday", "friday"])]

        # Experience to years
        exp_years = {
            ExperienceLevel.BEGINNER: 0.5,
            ExperienceLevel.INTERMEDIATE: 2.0,
            ExperienceLevel.ADVANCED: 4.0,
        }.get(profile.experience_level, 1.0)

        # Call solver with comprehensive arguments and sensible defaults
        return self.constraint_solver.solve(
            age=profile.age,
            sex_at_birth=profile.sex_at_birth,
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            body_fat_percent=profile.body_fat_percentage,
            primary_goal=profile.primary_goal,
            target_weight_kg=profile.target_weight_kg,
            target_weight_change_kg_per_week=None,  # derived implicitly by calorie range
            timeline_weeks=profile.timeline_weeks,
            sessions_per_week_min=profile.sessions_per_week,
            sessions_per_week_max=profile.sessions_per_week,
            session_duration_min_minutes=45,
            session_duration_max_minutes=120,
            available_equipment=["full_gym"],
            training_experience_years=exp_years,
            tdee_result=tdee_result,
            dietary_restrictions=profile.food_allergies or [],
            budget_per_week=None,
            available_days=available_days_idx,
            preferred_training_times=["evening"],
            prefer_higher_frequency=True,
            prefer_shorter_sessions=False,
            complexity_tolerance="moderate",
        )

    def _generate_training_program(self, profile: UserProfile) -> TrainingProgram:
        """Generate training program"""
        return self.training_generator.generate_program(
            sessions_per_week=profile.sessions_per_week,
            experience_level=profile.experience_level,
            primary_goal=profile.training_focus,
            age=profile.age,
            medical_restrictions=profile.injuries,
        )

    def _generate_meal_plans(
        self, profile: UserProfile, macro_targets: CalcMacroTargets
    ) -> List[DailyMealPlan]:
        """Generate 14-day meal plan"""
        # Convert CalcMacroTargets to MealMacroTargets
        meal_targets = MealMacroTargets(
            calories=macro_targets.calories,
            protein_g=macro_targets.protein_g,
            carbs_g=macro_targets.carbs_g,
            fat_g=macro_targets.fat_g,
            fiber_g=30,  # Standard fiber target
        )

        return self.meal_assembler.generate_14_day_meal_plan(
            targets=meal_targets,
            training_days_per_week=profile.sessions_per_week,
            dietary_preference=profile.dietary_preference,
            allergies=profile.food_allergies,
        )

    def _generate_plan_notes(
        self,
        profile: UserProfile,
        safety_result: SafetyCheckResult,
        feasibility_result: SolverResult,
    ) -> str:
        """Generate summary notes for the plan"""
        notes = []

        # Goal summary
        goal_desc = {
            Goal.FAT_LOSS: "fat loss while preserving muscle",
            Goal.MUSCLE_GAIN: "lean muscle gain",
            Goal.RECOMP: "body recomposition (simultaneous fat loss and muscle gain)",
            Goal.MAINTENANCE: "maintaining current physique",
        }
        notes.append(f"Goal: {goal_desc.get(profile.primary_goal, 'general fitness')}")

        # Training summary
        notes.append(
            f"Training: {profile.sessions_per_week}x/week {profile.training_focus.value} focus"
        )

        # Safety modifications
        if safety_result.modifications:
            notes.append(f"Safety modifications: {', '.join(safety_result.modifications)}")

        # Feasibility notes
        if feasibility_result.diagnostics:
            notes.append("Feasibility notes: " + "; ".join(d.message for d in feasibility_result.diagnostics))

        return " | ".join(notes)

    def export_plan_to_json(self, plan: CompletePlan) -> str:
        """Export plan to JSON for database storage"""
        # Convert dataclasses to dicts (recursive)
        plan_dict = {
            "plan_id": plan.plan_id,
            "user_id": plan.user_id,
            "version": plan.version,
            "created_at": plan.created_at.isoformat(),
            "goal": plan.goal.value,
            "duration_days": plan.duration_days,
            "training_sessions_per_week": plan.training_sessions_per_week,
            "tdee_result": asdict(plan.tdee_result),
            "daily_calorie_target": plan.daily_calorie_target,
            "macro_targets": asdict(plan.macro_targets),
            "rate_of_change_kg_per_week": plan.rate_of_change_kg_per_week,
            "training_program": self._training_program_to_dict(plan.training_program),
            "meal_plans": [self._meal_plan_to_dict(mp) for mp in plan.meal_plans],
            "feasibility_result": self._solver_result_to_dict(plan.feasibility_result),
            "safety_result": asdict(plan.safety_result),
            "notes": plan.notes,
            "next_reassessment_date": (
                plan.next_reassessment_date.isoformat() if plan.next_reassessment_date else None
            ),
        }

        return json.dumps(plan_dict, indent=2)

    def _training_program_to_dict(self, program: TrainingProgram) -> dict:
        """Convert TrainingProgram to dict"""
        return {
            "split_type": program.split_type.value,
            "sessions_per_week": program.sessions_per_week,
            "weekly_sessions": [
                {
                    "session_number": session.session_number,
                    "session_name": session.session_name,
                    "exercises": [
                        {
                            "name": ex.name,
                            "muscle_groups": ex.muscle_groups,
                            "sets": ex.sets,
                            "rep_range": ex.rep_range,
                            "rest_seconds": ex.rest_seconds,
                            "rir": ex.rir,
                            "notes": ex.notes,
                            "is_compound": ex.is_compound,
                        }
                        for ex in session.exercises
                    ],
                    "estimated_duration_minutes": session.estimated_duration_minutes,
                    "notes": session.notes,
                }
                for session in program.weekly_sessions
            ],
            "weekly_volume_per_muscle": program.weekly_volume_per_muscle,
            "deload_week": program.deload_week,
            "progression_notes": program.progression_notes,
            "safety_modifications": program.safety_modifications,
        }

    def _meal_plan_to_dict(self, meal_plan: DailyMealPlan) -> dict:
        """Convert DailyMealPlan to dict"""
        return {
            "day_number": meal_plan.day_number,
            "training_day": meal_plan.training_day,
            "meals": [
                {
                    "meal_id": meal.meal_id,
                    "meal_type": meal.meal_type.value,
                    "meal_name": meal.meal_name,
                    "components": [
                        {
                            "food_name": comp.food.name,
                            "servings": comp.servings,
                            "calories": comp.calories,
                            "protein_g": comp.protein_g,
                            "carbs_g": comp.carbs_g,
                            "fat_g": comp.fat_g,
                        }
                        for comp in meal.components
                    ],
                    "total_calories": meal.total_calories,
                    "total_protein_g": meal.total_protein_g,
                    "total_carbs_g": meal.total_carbs_g,
                    "total_fat_g": meal.total_fat_g,
                    "total_fiber_g": meal.total_fiber_g,
                    "prep_notes": meal.prep_notes,
                }
                for meal in meal_plan.meals
            ],
            "daily_totals": meal_plan.daily_totals,
            "adherence_to_targets": meal_plan.adherence_to_targets,
        }

    def _solver_result_to_dict(self, result: SolverResult) -> dict:
        """Convert SolverResult to dict"""
        return {
            "status": result.status.value,
            "message": result.message,
            "solution": result.solution,
            "diagnostics": [
                {"category": d.category, "severity": d.severity, "message": d.message}
                for d in result.diagnostics
            ],
            "trade_offs": [
                {
                    "option_label": opt.option_label,
                    "description": opt.description,
                    "relaxed_constraints": opt.relaxed_constraints,
                    "impact": opt.impact,
                }
                for opt in result.trade_offs
            ]
            if result.trade_offs
            else [],
        }
