"""
Constraint Solver - Feasibility Validation & Trade-off Generation

Uses OR-Tools CP-SAT to determine if user goals are achievable given constraints.
If infeasible, generates quantified A/B/C trade-off options.

This is the mathematical brain that prevents impossible programs.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

from ortools.sat.python import cp_model

from config import settings
from libs.calculators.tdee import TDEEResult
from libs.calculators.macros import MacroTargets, Goal

logger = logging.getLogger(__name__)


class FeasibilityStatus(str, Enum):
    """Solver outcome status."""

    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class Diagnostic:
    """A single infeasibility diagnostic."""

    code: str  # Machine-readable code
    constraint: str  # Which constraint was violated
    detail: str  # Human-readable explanation
    severity: str  # "critical", "high", "moderate"


@dataclass
class TradeOffOption:
    """One option for resolving infeasibility."""

    id: str  # "A", "B", "C"
    summary: str  # One-line description
    adjustments: Dict[str, any]  # What changes
    expected_outcomes: Dict[str, any]  # What user can expect
    trade_off: str  # What they're giving up
    feasibility_score: float  # 0.0-1.0 (how close to original goal)


@dataclass
class SolverResult:
    """Complete solver output."""

    status: FeasibilityStatus
    feasible: bool
    runtime_ms: int
    iterations: Optional[int]

    # If feasible
    optimal_params: Optional[Dict[str, any]] = None

    # If infeasible
    diagnostics: List[Diagnostic] = None
    trade_offs: List[TradeOffOption] = None


class ConstraintSolver:
    """
    Validates program feasibility using constraint programming.

    Variables:
    - Training: sessions/week, duration, volume (sets per muscle group)
    - Nutrition: calories, protein, carbs, fat
    - Schedule: training days/times

    Constraints:
    - Hard: Must be satisfied (equipment, time, budget, safety)
    - Soft: Preferences (penalties for violations)

    Objective:
    Maximize goal attainment - sum(constraint violations weighted by priority)
    """

    def __init__(self):
        """Initialize solver with configuration."""
        self.timeout = settings.SOLVER_TIMEOUT_SECONDS
        self.max_threads = settings.SOLVER_MAX_THREADS

    def solve(
        self,
        # User profile
        age: int,
        sex_at_birth: str,
        weight_kg: float,
        height_cm: float,
        body_fat_percent: Optional[float],
        # Goals
        primary_goal: Goal,
        target_weight_kg: Optional[float],
        target_weight_change_kg_per_week: Optional[float],
        timeline_weeks: Optional[int],
        # Training constraints
        sessions_per_week_min: int,
        sessions_per_week_max: int,
        session_duration_min_minutes: int,
        session_duration_max_minutes: int,
        available_equipment: List[str],
        training_experience_years: float,
        # Nutrition constraints
        tdee_result: TDEEResult,
        dietary_restrictions: List[str],
        budget_per_week: Optional[float],
        # Schedule constraints
        available_days: List[int],  # 1-7 (Monday-Sunday)
        preferred_training_times: List[str],  # ["morning", "evening"]
        # Preferences (soft constraints)
        prefer_higher_frequency: bool = True,
        prefer_shorter_sessions: bool = False,
        complexity_tolerance: str = "moderate",  # "low", "moderate", "high"
    ) -> SolverResult:
        """
        Solve for feasible program parameters.

        Returns:
            SolverResult with optimal params or trade-off options
        """
        start_time = time.time()

        # Create model
        model = cp_model.CpModel()

        # ================================================================
        # DECISION VARIABLES
        # ================================================================

        # Training variables
        sessions_per_week = model.NewIntVar(
            sessions_per_week_min, sessions_per_week_max, "sessions_per_week"
        )
        session_duration = model.NewIntVar(
            session_duration_min_minutes,
            session_duration_max_minutes,
            "session_duration_minutes",
        )

        # Total weekly training time (sessions * duration)
        weekly_training_minutes = model.NewIntVar(
            0, sessions_per_week_max * session_duration_max_minutes, "weekly_training_minutes"
        )
        model.AddMultiplicationEquality(
            weekly_training_minutes, [sessions_per_week, session_duration]
        )

        # Nutrition variables (based on TDEE)
        tdee_min = tdee_result.tdee_ci_lower
        tdee_max = tdee_result.tdee_ci_upper

        # Calorie target (within TDEE range adjusted for goal)
        if primary_goal == Goal.FAT_LOSS:
            calorie_min = int(tdee_min * 0.75)  # Max 25% deficit
            calorie_max = int(tdee_max * 0.95)  # At least 5% deficit
        elif primary_goal == Goal.MUSCLE_GAIN:
            calorie_min = int(tdee_min * 1.00)  # At least at TDEE
            calorie_max = int(tdee_max * 1.20)  # Max 20% surplus
        else:  # MAINTENANCE, RECOMP, PERFORMANCE
            calorie_min = int(tdee_min * 0.95)
            calorie_max = int(tdee_max * 1.10)

        calories = model.NewIntVar(calorie_min, calorie_max, "calories")

        # Protein (g) - based on weight and goal
        if primary_goal == Goal.FAT_LOSS:
            protein_min_g_per_kg = 2.0
            protein_max_g_per_kg = 2.4
        elif primary_goal == Goal.MUSCLE_GAIN:
            protein_min_g_per_kg = 1.6
            protein_max_g_per_kg = 2.2
        else:
            protein_min_g_per_kg = 1.6
            protein_max_g_per_kg = 2.0

        protein_min = int(weight_kg * protein_min_g_per_kg)
        protein_max = int(weight_kg * protein_max_g_per_kg)
        protein = model.NewIntVar(protein_min, protein_max, "protein_g")

        # Fat (g) - hormonal floor
        fat_min = int(weight_kg * settings.MIN_FAT_G_PER_KG)
        fat_max = int(weight_kg * 1.5)  # Upper bound
        fat = model.NewIntVar(fat_min, fat_max, "fat_g")

        # Carbs (g) - derived from remaining calories
        # calories = (protein * 4) + (fat * 9) + (carbs * 4)
        # carbs = (calories - protein*4 - fat*9) / 4
        # We'll compute this as a constraint rather than variable

        # Volume variables (sets per week for major muscle groups)
        # Based on training experience and goal
        if training_experience_years < 1:
            sets_per_muscle_min = 8
            sets_per_muscle_max = 12
        elif training_experience_years < 3:
            sets_per_muscle_min = 10
            sets_per_muscle_max = 16
        else:
            sets_per_muscle_min = 12
            sets_per_muscle_max = 20

        # Example muscle groups (simplified)
        chest_sets = model.NewIntVar(sets_per_muscle_min, sets_per_muscle_max, "chest_sets")
        back_sets = model.NewIntVar(sets_per_muscle_min, sets_per_muscle_max, "back_sets")
        legs_sets = model.NewIntVar(sets_per_muscle_min, sets_per_muscle_max, "legs_sets")

        # ================================================================
        # HARD CONSTRAINTS (Must be satisfied)
        # ================================================================

        diagnostics = []

        # 1. Schedule constraint: sessions must fit in available days
        model.Add(sessions_per_week <= len(available_days))

        # 2. Safety constraint: calorie floor
        if sex_at_birth.lower() == "female":
            min_safe_calories = settings.MIN_CALORIES_FEMALE
        else:
            min_safe_calories = settings.MIN_CALORIES_MALE
        model.Add(calories >= min_safe_calories)

        # 3. Protein floor (muscle preservation)
        model.Add(protein >= protein_min)

        # 4. Fat floor (hormonal health)
        model.Add(fat >= fat_min)

        # 5. Calorie math must work out
        # We need carbs >= 0 and carbs = (calories - protein*4 - fat*9) / 4
        # This is tricky in integer programming. Let's approximate:
        # calories >= protein*4 + fat*9 + 100  (at least 25g carbs)
        protein_kcal_min = protein_min * 4
        fat_kcal_min = fat_min * 9
        model.Add(calories >= protein_kcal_min + fat_kcal_min + 100)

        # 6. Volume constraint: total weekly sets must fit in training time
        # Assume ~5 minutes per set (including rest)
        total_sets = model.NewIntVar(0, 100, "total_sets")
        model.Add(total_sets == chest_sets + back_sets + legs_sets)
        model.Add(total_sets * 5 <= weekly_training_minutes)

        # 7. Experience-based volume cap (avoid overtraining)
        max_sets = int(sets_per_muscle_max * 3)  # For 3 muscle groups
        model.Add(total_sets <= max_sets)

        # 8. Budget constraint (if specified)
        if budget_per_week:
            # Rough estimate: $1.50 per 100 calories
            estimated_weekly_cost = (calories * 7 * 1.50) / 100
            if estimated_weekly_cost > budget_per_week:
                diagnostics.append(
                    Diagnostic(
                        code="BUDGET_INSUFFICIENT",
                        constraint=f"budget <= {budget_per_week}",
                        detail=f"Estimated food cost ${estimated_weekly_cost:.0f}/week exceeds budget ${budget_per_week:.0f}/week",
                        severity="high",
                    )
                )

        # 9. Goal timeline constraint
        if target_weight_change_kg_per_week and timeline_weeks:
            required_rate = target_weight_change_kg_per_week
            # Check if calorie deficit/surplus supports this rate
            # 1 kg fat = ~7700 kcal
            # Required daily deficit/surplus = (required_rate * 7700) / 7
            required_daily_adjustment = (required_rate * 7700) / 7

            if primary_goal == Goal.FAT_LOSS:
                max_achievable_rate = (tdee_max - calorie_min) / 7700 * 7
                if abs(required_rate) > abs(max_achievable_rate):
                    diagnostics.append(
                        Diagnostic(
                            code="RATE_TOO_FAST",
                            constraint=f"rate <= {max_achievable_rate:.2f} kg/week",
                            detail=f"Target rate {required_rate:.2f} kg/week exceeds safe maximum {max_achievable_rate:.2f} kg/week",
                            severity="critical",
                        )
                    )

        # ================================================================
        # SOFT CONSTRAINTS (Preferences with penalties)
        # ================================================================

        penalty_vars = []

        # Preference: Higher frequency (if user prefers)
        if prefer_higher_frequency:
            freq_penalty = model.NewIntVar(0, 10, "freq_penalty")
            model.Add(freq_penalty == sessions_per_week_max - sessions_per_week)
            penalty_vars.append((freq_penalty, 5))  # Weight: 5

        # Preference: Shorter sessions (if user prefers)
        if prefer_shorter_sessions:
            duration_penalty = model.NewIntVar(0, 100, "duration_penalty")
            model.Add(
                duration_penalty == (session_duration - session_duration_min_minutes) // 10
            )
            penalty_vars.append((duration_penalty, 3))  # Weight: 3

        # Preference: Balanced volume across muscle groups
        balance_penalty = model.NewIntVar(0, 20, "balance_penalty")
        max_sets_var = model.NewIntVar(sets_per_muscle_min, sets_per_muscle_max, "max_sets_var")
        model.AddMaxEquality(max_sets_var, [chest_sets, back_sets, legs_sets])
        min_sets_var = model.NewIntVar(sets_per_muscle_min, sets_per_muscle_max, "min_sets_var")
        model.AddMinEquality(min_sets_var, [chest_sets, back_sets, legs_sets])
        model.Add(balance_penalty == max_sets_var - min_sets_var)
        penalty_vars.append((balance_penalty, 10))  # Weight: 10

        # ================================================================
        # OBJECTIVE FUNCTION
        # ================================================================

        # Maximize goal attainment (minimize penalties)
        total_penalty = model.NewIntVar(0, 1000, "total_penalty")
        penalty_sum = sum(var * weight for var, weight in penalty_vars)
        model.Add(total_penalty == penalty_sum)

        model.Minimize(total_penalty)

        # ================================================================
        # SOLVE
        # ================================================================

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.timeout
        solver.parameters.num_search_workers = self.max_threads

        status = solver.Solve(model)
        runtime_ms = int((time.time() - start_time) * 1000)

        # ================================================================
        # PROCESS RESULTS
        # ================================================================

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # Extract solution
            optimal_params = {
                "training": {
                    "sessions_per_week": solver.Value(sessions_per_week),
                    "session_duration_minutes": solver.Value(session_duration),
                    "weekly_training_minutes": solver.Value(weekly_training_minutes),
                    "volume_sets": {
                        "chest": solver.Value(chest_sets),
                        "back": solver.Value(back_sets),
                        "legs": solver.Value(legs_sets),
                        "total": solver.Value(total_sets),
                    },
                },
                "nutrition": {
                    "calories": solver.Value(calories),
                    "protein_g": solver.Value(protein),
                    "fat_g": solver.Value(fat),
                    # Calculate carbs from remaining calories
                    "carbs_g": (
                        solver.Value(calories)
                        - solver.Value(protein) * 4
                        - solver.Value(fat) * 9
                    )
                    // 4,
                },
                "schedule": {
                    "available_days": available_days,
                    "preferred_times": preferred_training_times,
                },
            }

            logger.info(
                f"Solver FEASIBLE: {solver.Value(sessions_per_week)}x/week, "
                f"{solver.Value(session_duration)}min sessions, "
                f"{solver.Value(calories)} kcal"
            )

            return SolverResult(
                status=FeasibilityStatus.FEASIBLE,
                feasible=True,
                runtime_ms=runtime_ms,
                iterations=solver.NumBranches(),
                optimal_params=optimal_params,
            )

        elif status == cp_model.INFEASIBLE:
            # Generate trade-offs
            logger.warning("Solver INFEASIBLE - generating trade-offs")

            trade_offs = self._generate_trade_offs(
                model=model,
                sessions_per_week_min=sessions_per_week_min,
                sessions_per_week_max=sessions_per_week_max,
                session_duration_min=session_duration_min_minutes,
                session_duration_max=session_duration_max_minutes,
                calorie_min=calorie_min,
                calorie_max=calorie_max,
                primary_goal=primary_goal,
                target_weight_change_kg_per_week=target_weight_change_kg_per_week,
                timeline_weeks=timeline_weeks,
                diagnostics=diagnostics,
            )

            return SolverResult(
                status=FeasibilityStatus.INFEASIBLE,
                feasible=False,
                runtime_ms=runtime_ms,
                iterations=None,
                diagnostics=diagnostics,
                trade_offs=trade_offs,
            )

        else:  # TIMEOUT or ERROR
            logger.error(f"Solver {status}: runtime {runtime_ms}ms")
            return SolverResult(
                status=FeasibilityStatus.TIMEOUT
                if status == cp_model.UNKNOWN
                else FeasibilityStatus.ERROR,
                feasible=False,
                runtime_ms=runtime_ms,
                iterations=None,
            )

    def _generate_trade_offs(
        self,
        model: cp_model.CpModel,
        sessions_per_week_min: int,
        sessions_per_week_max: int,
        session_duration_min: int,
        session_duration_max: int,
        calorie_min: int,
        calorie_max: int,
        primary_goal: Goal,
        target_weight_change_kg_per_week: Optional[float],
        timeline_weeks: Optional[int],
        diagnostics: List[Diagnostic],
    ) -> List[TradeOffOption]:
        """
        Generate 3 quantified trade-off options when infeasible.

        Strategy:
        - Option A: Relax goal (slower progress)
        - Option B: Relax constraints (more time/sessions)
        - Option C: Hybrid (moderate adjustments to both)
        """
        trade_offs = []

        # Option A: Keep constraints, adjust goal
        if target_weight_change_kg_per_week and timeline_weeks:
            adjusted_rate = target_weight_change_kg_per_week * 0.5  # 50% slower
            adjusted_timeline = timeline_weeks * 2  # Double time

            trade_offs.append(
                TradeOffOption(
                    id="A",
                    summary=f"Keep {sessions_per_week_min}x/week; slower progress",
                    adjustments={
                        "sessions_per_week": sessions_per_week_min,
                        "target_rate_kg_per_week": adjusted_rate,
                        "timeline_weeks": adjusted_timeline,
                    },
                    expected_outcomes={
                        "rate_kg_per_week": adjusted_rate,
                        "total_weeks": adjusted_timeline,
                    },
                    trade_off="Slower progress",
                    feasibility_score=0.7,
                )
            )

        # Option B: Keep goal, increase frequency/duration
        increased_sessions = min(sessions_per_week_max, sessions_per_week_min + 2)
        increased_duration = min(session_duration_max, session_duration_min + 20)

        trade_offs.append(
            TradeOffOption(
                id="B",
                summary=f"Increase to {increased_sessions}x/week, {increased_duration}min; keep pace",
                adjustments={
                    "sessions_per_week": increased_sessions,
                    "session_duration_minutes": increased_duration,
                },
                expected_outcomes={
                    "rate_kg_per_week": target_weight_change_kg_per_week,
                    "total_weeks": timeline_weeks,
                },
                trade_off="More time commitment",
                feasibility_score=0.85,
            )
        )

        # Option C: Hybrid - moderate adjustments to both
        moderate_rate = (
            target_weight_change_kg_per_week * 0.75 if target_weight_change_kg_per_week else None
        )
        moderate_timeline = int(timeline_weeks * 1.33) if timeline_weeks else None
        moderate_sessions = (sessions_per_week_min + sessions_per_week_max) // 2

        trade_offs.append(
            TradeOffOption(
                id="C",
                summary=f"{moderate_sessions}x/week; moderate pace adjustment",
                adjustments={
                    "sessions_per_week": moderate_sessions,
                    "target_rate_kg_per_week": moderate_rate,
                    "timeline_weeks": moderate_timeline,
                },
                expected_outcomes={
                    "rate_kg_per_week": moderate_rate,
                    "total_weeks": moderate_timeline,
                },
                trade_off="Balanced adjustment",
                feasibility_score=0.80,
            )
        )

        return trade_offs[:3]  # Return max 3 options
