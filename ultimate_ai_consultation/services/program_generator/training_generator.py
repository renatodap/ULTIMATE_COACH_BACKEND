"""
Training Program Generator

Creates periodized resistance training programs based on:
- Available training days
- Experience level
- Goal (strength, hypertrophy, endurance)
- Volume landmarks (MEV/MAV/MRV)
- Evidence-based exercise selection
"""

from typing import List, Dict, Literal, Optional
from dataclasses import dataclass
from enum import Enum
import math


class ExperienceLevel(str, Enum):
    """Training experience level"""

    BEGINNER = "beginner"  # <1 year consistent training
    INTERMEDIATE = "intermediate"  # 1-3 years
    ADVANCED = "advanced"  # 3+ years


class TrainingSplit(str, Enum):
    """Training split type"""

    FULL_BODY = "full_body"  # 2-3x/week
    UPPER_LOWER = "upper_lower"  # 4x/week
    PUSH_PULL_LEGS = "push_pull_legs"  # 6x/week
    UPPER_LOWER_6X = "upper_lower_6x"  # 6x/week (U/L/U/L/U/L)


class IntensityZone(str, Enum):
    """Primary training focus"""

    STRENGTH = "strength"  # 1-5 reps, 85-95% 1RM
    HYPERTROPHY = "hypertrophy"  # 6-12 reps, 67-85% 1RM
    ENDURANCE = "endurance"  # 12-20+ reps, <67% 1RM


@dataclass
class Exercise:
    """Single exercise prescription"""

    name: str
    muscle_groups: List[str]  # Primary targets
    sets: int
    rep_range: str  # e.g., "8-12", "3-5", "12-15"
    rest_seconds: int
    rir: int  # Reps in reserve (0-3)
    notes: str  # Technique cues, progression notes
    is_compound: bool  # Compound vs isolation


@dataclass
class WorkoutSession:
    """Single training session"""

    session_number: int
    session_name: str  # e.g., "Full Body A", "Push Day"
    exercises: List[Exercise]
    estimated_duration_minutes: int
    notes: str


@dataclass
class TrainingProgram:
    """Complete training program"""

    split_type: TrainingSplit
    sessions_per_week: int
    weekly_sessions: List[WorkoutSession]
    weekly_volume_per_muscle: Dict[str, int]  # Muscle group -> sets/week
    deload_week: int  # Which week to deload
    progression_notes: str
    safety_modifications: List[str]


# Volume Landmarks (Renaissance Periodization)
# Sets per muscle group per week
VOLUME_LANDMARKS = {
    "chest": {"MEV": 10, "MAV": 16, "MRV": 22},
    "back": {"MEV": 12, "MAV": 18, "MRV": 25},
    "shoulders": {"MEV": 8, "MAV": 14, "MRV": 20},
    "quads": {"MEV": 8, "MAV": 14, "MRV": 20},
    "hamstrings": {"MEV": 6, "MAV": 12, "MRV": 18},
    "glutes": {"MEV": 6, "MAV": 12, "MRV": 18},
    "biceps": {"MEV": 6, "MAV": 12, "MRV": 18},
    "triceps": {"MEV": 6, "MAV": 12, "MRV": 18},
    "calves": {"MEV": 6, "MAV": 12, "MRV": 18},
}


# Exercise Database with muscle group mappings
EXERCISE_DATABASE = {
    # Chest
    "Barbell Bench Press": {
        "muscles": ["chest", "triceps", "shoulders"],
        "compound": True,
    },
    "Incline Dumbbell Press": {"muscles": ["chest", "triceps", "shoulders"], "compound": True},
    "Cable Flyes": {"muscles": ["chest"], "compound": False},
    "Push-ups": {"muscles": ["chest", "triceps", "shoulders"], "compound": True},
    # Back
    "Barbell Rows": {"muscles": ["back", "biceps"], "compound": True},
    "Pull-ups": {"muscles": ["back", "biceps"], "compound": True},
    "Lat Pulldowns": {"muscles": ["back", "biceps"], "compound": True},
    "Seated Cable Rows": {"muscles": ["back", "biceps"], "compound": True},
    "Face Pulls": {"muscles": ["back", "shoulders"], "compound": False},
    # Shoulders
    "Overhead Press": {"muscles": ["shoulders", "triceps"], "compound": True},
    "Lateral Raises": {"muscles": ["shoulders"], "compound": False},
    "Rear Delt Flyes": {"muscles": ["shoulders", "back"], "compound": False},
    # Legs
    "Barbell Squat": {"muscles": ["quads", "glutes", "hamstrings"], "compound": True},
    "Romanian Deadlift": {"muscles": ["hamstrings", "glutes", "back"], "compound": True},
    "Leg Press": {"muscles": ["quads", "glutes"], "compound": True},
    "Bulgarian Split Squats": {"muscles": ["quads", "glutes"], "compound": True},
    "Leg Curls": {"muscles": ["hamstrings"], "compound": False},
    "Leg Extensions": {"muscles": ["quads"], "compound": False},
    "Hip Thrusts": {"muscles": ["glutes", "hamstrings"], "compound": True},
    "Calf Raises": {"muscles": ["calves"], "compound": False},
    # Arms
    "Barbell Curls": {"muscles": ["biceps"], "compound": False},
    "Hammer Curls": {"muscles": ["biceps"], "compound": False},
    "Tricep Dips": {"muscles": ["triceps", "chest"], "compound": True},
    "Tricep Pushdowns": {"muscles": ["triceps"], "compound": False},
    "Overhead Tricep Extension": {"muscles": ["triceps"], "compound": False},
}


class TrainingGenerator:
    """Generates evidence-based training programs"""

    def __init__(self):
        pass

    def generate_program(
        self,
        sessions_per_week: int,
        experience_level: ExperienceLevel,
        primary_goal: IntensityZone,
        age: int,
        medical_restrictions: List[str] = None,
        available_equipment: List[str] = None,
    ) -> TrainingProgram:
        """
        Generate complete training program.

        Args:
            sessions_per_week: 2-6 training days per week
            experience_level: Beginner/Intermediate/Advanced
            primary_goal: Strength/Hypertrophy/Endurance
            age: User age (affects volume/intensity recommendations)
            medical_restrictions: List of restrictions (e.g., ["no_overhead_press"])
            available_equipment: List of available equipment

        Returns:
            TrainingProgram with weekly sessions and progression plan
        """
        medical_restrictions = medical_restrictions or []
        available_equipment = available_equipment or ["full_gym"]

        # Step 1: Select training split based on frequency
        split_type = self._select_split(sessions_per_week, experience_level)

        # Step 2: Calculate target volume per muscle group
        volume_targets = self._calculate_volume_targets(experience_level, age)

        # Step 3: Generate weekly sessions
        weekly_sessions = self._generate_sessions(
            split_type=split_type,
            sessions_per_week=sessions_per_week,
            volume_targets=volume_targets,
            primary_goal=primary_goal,
            medical_restrictions=medical_restrictions,
        )

        # Step 4: Calculate actual weekly volume achieved
        actual_volume = self._calculate_actual_volume(weekly_sessions)

        # Step 5: Determine deload schedule
        deload_week = self._calculate_deload_schedule(experience_level)

        # Step 6: Generate progression notes
        progression_notes = self._generate_progression_notes(
            experience_level, primary_goal, sessions_per_week
        )

        # Step 7: Safety modifications for age/restrictions
        safety_mods = self._generate_safety_modifications(age, medical_restrictions)

        return TrainingProgram(
            split_type=split_type,
            sessions_per_week=sessions_per_week,
            weekly_sessions=weekly_sessions,
            weekly_volume_per_muscle=actual_volume,
            deload_week=deload_week,
            progression_notes=progression_notes,
            safety_modifications=safety_mods,
        )

    def _select_split(
        self, sessions_per_week: int, experience_level: ExperienceLevel
    ) -> TrainingSplit:
        """
        Select training split based on frequency and experience.

        Reference: Schoenfeld et al. (2016) - frequency meta-analysis
        """
        if sessions_per_week <= 3:
            return TrainingSplit.FULL_BODY
        elif sessions_per_week == 4:
            return TrainingSplit.UPPER_LOWER
        elif sessions_per_week == 5:
            # 5-day can be U/L/U/L/Full or PPL + Upper + Lower
            return (
                TrainingSplit.UPPER_LOWER
                if experience_level == ExperienceLevel.BEGINNER
                else TrainingSplit.PUSH_PULL_LEGS
            )
        else:  # 6+ days
            return (
                TrainingSplit.PUSH_PULL_LEGS
                if experience_level == ExperienceLevel.ADVANCED
                else TrainingSplit.UPPER_LOWER_6X
            )

    def _calculate_volume_targets(
        self, experience_level: ExperienceLevel, age: int
    ) -> Dict[str, int]:
        """
        Calculate target weekly volume per muscle group.

        Uses MEV/MAV/MRV landmarks from RP.
        """
        targets = {}

        for muscle, landmarks in VOLUME_LANDMARKS.items():
            if experience_level == ExperienceLevel.BEGINNER:
                # MEV to MEV+30%
                target = landmarks["MEV"] + int(landmarks["MEV"] * 0.15)
            elif experience_level == ExperienceLevel.INTERMEDIATE:
                # MEV+30% to MAV
                target = int((landmarks["MEV"] + landmarks["MAV"]) / 2)
            else:  # Advanced
                # MAV to MAV+30%
                target = landmarks["MAV"] + int((landmarks["MRV"] - landmarks["MAV"]) * 0.3)

            # Age modification: reduce volume for older adults
            if age >= 65:
                target = int(target * 0.75)  # 25% reduction
            elif age >= 50:
                target = int(target * 0.85)  # 15% reduction

            targets[muscle] = target

        return targets

    def _generate_sessions(
        self,
        split_type: TrainingSplit,
        sessions_per_week: int,
        volume_targets: Dict[str, int],
        primary_goal: IntensityZone,
        medical_restrictions: List[str],
    ) -> List[WorkoutSession]:
        """Generate individual workout sessions based on split type."""

        if split_type == TrainingSplit.FULL_BODY:
            return self._generate_full_body(sessions_per_week, volume_targets, primary_goal, medical_restrictions)
        elif split_type == TrainingSplit.UPPER_LOWER:
            return self._generate_upper_lower(sessions_per_week, volume_targets, primary_goal, medical_restrictions)
        elif split_type == TrainingSplit.PUSH_PULL_LEGS:
            return self._generate_ppl(volume_targets, primary_goal, medical_restrictions)
        elif split_type == TrainingSplit.UPPER_LOWER_6X:
            return self._generate_upper_lower(6, volume_targets, primary_goal, medical_restrictions)

        return []

    def _generate_full_body(
        self,
        sessions_per_week: int,
        volume_targets: Dict[str, int],
        primary_goal: IntensityZone,
        medical_restrictions: List[str],
    ) -> List[WorkoutSession]:
        """Generate full body training sessions."""
        sessions = []

        # Distribute volume across sessions
        sets_per_muscle_per_session = {
            muscle: math.ceil(target / sessions_per_week)
            for muscle, target in volume_targets.items()
        }

        # Session A
        session_a = WorkoutSession(
            session_number=1,
            session_name="Full Body A",
            exercises=[
                self._create_exercise(
                    self._maybe_substitute_exercise("Barbell Squat", medical_restrictions),
                    sets_per_muscle_per_session["quads"],
                    primary_goal,
                ),
                self._create_exercise(
                    "Barbell Bench Press", sets_per_muscle_per_session["chest"], primary_goal
                ),
                self._create_exercise(
                    "Barbell Rows", sets_per_muscle_per_session["back"], primary_goal
                ),
                self._create_exercise(
                    self._maybe_substitute_exercise("Overhead Press", medical_restrictions),
                    sets_per_muscle_per_session["shoulders"] // 2,
                    primary_goal,
                ),
                self._create_exercise(
                    "Barbell Curls", sets_per_muscle_per_session["biceps"] // 2, primary_goal
                ),
                self._create_exercise(
                    "Tricep Pushdowns",
                    sets_per_muscle_per_session["triceps"] // 2,
                    primary_goal,
                ),
            ],
            estimated_duration_minutes=75,
            notes="Focus on compound movements, maintain strict form",
        )
        sessions.append(session_a)

        # Session B (if 2-3x/week)
        if sessions_per_week >= 2:
            session_b = WorkoutSession(
                session_number=2,
                session_name="Full Body B",
                exercises=[
                    self._create_exercise(
                        self._maybe_substitute_exercise("Romanian Deadlift", medical_restrictions),
                        sets_per_muscle_per_session["hamstrings"],
                        primary_goal,
                    ),
                    self._create_exercise(
                        "Incline Dumbbell Press",
                        sets_per_muscle_per_session["chest"],
                        primary_goal,
                    ),
                    self._create_exercise(
                        "Pull-ups", sets_per_muscle_per_session["back"], primary_goal
                    ),
                    self._create_exercise(
                        "Lateral Raises",
                        sets_per_muscle_per_session["shoulders"] // 2,
                        primary_goal,
                    ),
                    self._create_exercise(
                        "Hammer Curls",
                        sets_per_muscle_per_session["biceps"] // 2,
                        primary_goal,
                    ),
                    self._create_exercise(
                        "Overhead Tricep Extension",
                        sets_per_muscle_per_session["triceps"] // 2,
                        primary_goal,
                    ),
                ],
                estimated_duration_minutes=75,
                notes="Variation day, focus on time under tension",
            )
            sessions.append(session_b)

        # Session C (if 3x/week)
        if sessions_per_week >= 3:
            session_c = WorkoutSession(
                session_number=3,
                session_name="Full Body C",
                exercises=[
                    self._create_exercise(
                        self._maybe_substitute_exercise("Leg Press", medical_restrictions),
                        sets_per_muscle_per_session["quads"],
                        primary_goal,
                    ),
                    self._create_exercise(
                        "Push-ups", sets_per_muscle_per_session["chest"], primary_goal
                    ),
                    self._create_exercise(
                        "Seated Cable Rows", sets_per_muscle_per_session["back"], primary_goal
                    ),
                    self._create_exercise(
                        "Face Pulls",
                        sets_per_muscle_per_session["shoulders"] // 2,
                        primary_goal,
                    ),
                    self._create_exercise(
                        "Hip Thrusts", sets_per_muscle_per_session["glutes"], primary_goal
                    ),
                ],
                estimated_duration_minutes=60,
                notes="Lighter day, focus on pump and mind-muscle connection",
            )
            sessions.append(session_c)

        return sessions

    def _generate_upper_lower(
        self,
        sessions_per_week: int,
        volume_targets: Dict[str, int],
        primary_goal: IntensityZone,
        medical_restrictions: List[str],
    ) -> List[WorkoutSession]:
        """Generate upper/lower split sessions."""
        sessions = []
        upper_sessions = sessions_per_week // 2
        lower_sessions = sessions_per_week - upper_sessions

        # Upper A
        upper_a = WorkoutSession(
            session_number=1,
            session_name="Upper A",
            exercises=[
                self._create_exercise("Barbell Bench Press", 4, primary_goal),
                self._create_exercise("Barbell Rows", 4, primary_goal),
                self._create_exercise(self._maybe_substitute_exercise("Overhead Press", medical_restrictions), 3, primary_goal),
                self._create_exercise("Lat Pulldowns", 3, primary_goal),
                self._create_exercise("Lateral Raises", 3, primary_goal),
                self._create_exercise("Barbell Curls", 3, primary_goal),
                self._create_exercise("Tricep Pushdowns", 3, primary_goal),
            ],
            estimated_duration_minutes=90,
            notes="Strength focus on compounds",
        )
        sessions.append(upper_a)

        # Lower A
        lower_a = WorkoutSession(
            session_number=2,
            session_name="Lower A",
            exercises=[
                self._create_exercise(self._maybe_substitute_exercise("Barbell Squat", medical_restrictions), 4, primary_goal),
                self._create_exercise(self._maybe_substitute_exercise("Romanian Deadlift", medical_restrictions), 4, primary_goal),
                self._create_exercise(self._maybe_substitute_exercise("Leg Press", medical_restrictions), 3, primary_goal),
                self._create_exercise("Leg Curls", 3, primary_goal),
                self._create_exercise("Hip Thrusts", 3, primary_goal),
                self._create_exercise("Calf Raises", 4, primary_goal),
            ],
            estimated_duration_minutes=90,
            notes="Quad and hamstring emphasis",
        )
        sessions.append(lower_a)

        if sessions_per_week >= 4:
            # Upper B
            upper_b = WorkoutSession(
                session_number=3,
                session_name="Upper B",
                exercises=[
                    self._create_exercise("Incline Dumbbell Press", 4, primary_goal),
                    self._create_exercise("Pull-ups", 4, primary_goal),
                    self._create_exercise("Cable Flyes", 3, primary_goal),
                    self._create_exercise("Seated Cable Rows", 3, primary_goal),
                    self._create_exercise("Rear Delt Flyes", 3, primary_goal),
                    self._create_exercise("Hammer Curls", 3, primary_goal),
                    self._create_exercise("Overhead Tricep Extension", 3, primary_goal),
                ],
                estimated_duration_minutes=90,
                notes="Hypertrophy focus, higher volume",
            )
            sessions.append(upper_b)

            # Lower B
            lower_b = WorkoutSession(
                session_number=4,
                session_name="Lower B",
                exercises=[
                    self._create_exercise("Bulgarian Split Squats", 4, primary_goal),
                    self._create_exercise(self._maybe_substitute_exercise("Leg Press", medical_restrictions), 4, primary_goal),
                    self._create_exercise("Leg Extensions", 3, primary_goal),
                    self._create_exercise("Leg Curls", 4, primary_goal),
                    self._create_exercise("Hip Thrusts", 3, primary_goal),
                    self._create_exercise("Calf Raises", 4, primary_goal),
                ],
                estimated_duration_minutes=85,
                notes="Unilateral work and isolation",
            )
            sessions.append(lower_b)

        return sessions

    def _generate_ppl(
        self, volume_targets: Dict[str, int], primary_goal: IntensityZone, medical_restrictions: List[str]
    ) -> List[WorkoutSession]:
        """Generate push/pull/legs split."""
        sessions = []

        # Push Day
        push = WorkoutSession(
            session_number=1,
            session_name="Push",
            exercises=[
                self._create_exercise("Barbell Bench Press", 4, primary_goal),
                self._create_exercise(self._maybe_substitute_exercise("Overhead Press", medical_restrictions), 4, primary_goal),
                self._create_exercise("Incline Dumbbell Press", 3, primary_goal),
                self._create_exercise("Lateral Raises", 4, primary_goal),
                self._create_exercise("Cable Flyes", 3, primary_goal),
                self._create_exercise("Tricep Dips", 3, primary_goal),
                self._create_exercise("Tricep Pushdowns", 3, primary_goal),
            ],
            estimated_duration_minutes=90,
            notes="Chest, shoulders, triceps",
        )
        sessions.append(push)

        # Pull Day
        pull = WorkoutSession(
            session_number=2,
            session_name="Pull",
            exercises=[
                self._create_exercise("Pull-ups", 4, primary_goal),
                self._create_exercise("Barbell Rows", 4, primary_goal),
                self._create_exercise("Lat Pulldowns", 3, primary_goal),
                self._create_exercise("Seated Cable Rows", 3, primary_goal),
                self._create_exercise("Face Pulls", 4, primary_goal),
                self._create_exercise("Barbell Curls", 3, primary_goal),
                self._create_exercise("Hammer Curls", 3, primary_goal),
            ],
            estimated_duration_minutes=90,
            notes="Back, biceps",
        )
        sessions.append(pull)

        # Leg Day
        legs = WorkoutSession(
            session_number=3,
            session_name="Legs",
            exercises=[
                self._create_exercise(self._maybe_substitute_exercise("Barbell Squat", medical_restrictions), 5, primary_goal),
                self._create_exercise(self._maybe_substitute_exercise("Romanian Deadlift", medical_restrictions), 4, primary_goal),
                self._create_exercise(self._maybe_substitute_exercise("Leg Press", medical_restrictions), 4, primary_goal),
                self._create_exercise("Leg Curls", 4, primary_goal),
                self._create_exercise("Hip Thrusts", 4, primary_goal),
                self._create_exercise("Leg Extensions", 3, primary_goal),
                self._create_exercise("Calf Raises", 5, primary_goal),
            ],
            estimated_duration_minutes=100,
            notes="Full leg development",
        )
        sessions.append(legs)

        # PPL typically runs 2x per week (6 days total)
        # Add variations for second round
        push2 = WorkoutSession(
            session_number=4,
            session_name="Push (Variation)",
            exercises=[
                self._create_exercise("Incline Dumbbell Press", 4, primary_goal),
                self._create_exercise(self._maybe_substitute_exercise("Overhead Press", medical_restrictions), 4, primary_goal),
                self._create_exercise("Cable Flyes", 4, primary_goal),
                self._create_exercise("Lateral Raises", 4, primary_goal),
                self._create_exercise("Rear Delt Flyes", 3, primary_goal),
                self._create_exercise("Overhead Tricep Extension", 3, primary_goal),
                self._create_exercise("Tricep Pushdowns", 3, primary_goal),
            ],
            estimated_duration_minutes=85,
            notes="Different exercise order/variations",
        )
        sessions.append(push2)

        pull2 = WorkoutSession(
            session_number=5,
            session_name="Pull (Variation)",
            exercises=[
                self._create_exercise("Barbell Rows", 4, primary_goal),
                self._create_exercise("Lat Pulldowns", 4, primary_goal),
                self._create_exercise("Pull-ups", 3, primary_goal),
                self._create_exercise("Seated Cable Rows", 4, primary_goal),
                self._create_exercise("Face Pulls", 4, primary_goal),
                self._create_exercise("Hammer Curls", 3, primary_goal),
                self._create_exercise("Barbell Curls", 3, primary_goal),
            ],
            estimated_duration_minutes=85,
            notes="Different exercise order/variations",
        )
        sessions.append(pull2)

        legs2 = WorkoutSession(
            session_number=6,
            session_name="Legs (Variation)",
            exercises=[
                self._create_exercise(self._maybe_substitute_exercise("Leg Press", medical_restrictions), 5, primary_goal),
                self._create_exercise("Bulgarian Split Squats", 4, primary_goal),
                self._create_exercise("Romanian Deadlift", 4, primary_goal),
                self._create_exercise("Leg Extensions", 4, primary_goal),
                self._create_exercise("Leg Curls", 4, primary_goal),
                self._create_exercise("Hip Thrusts", 4, primary_goal),
                self._create_exercise("Calf Raises", 5, primary_goal),
            ],
            estimated_duration_minutes=95,
            notes="More unilateral and machine work",
        )
        sessions.append(legs2)

        return sessions

    def _maybe_substitute_exercise(self, exercise_name: str, medical_restrictions: List[str]) -> str:
        """Choose a safer alternative for common restrictions, optionally ranked by AI."""
        restrictions = [r.lower() for r in (medical_restrictions or [])]
        candidates: List[str] = []
        context = {"exercise": exercise_name, "restrictions": restrictions}

        if exercise_name == "Barbell Squat" and any("knee" in r for r in restrictions):
            candidates = ["Leg Press", "Bulgarian Split Squats", "Hip Thrusts"]
        elif exercise_name == "Romanian Deadlift" and any("back" in r for r in restrictions):
            candidates = ["Hip Thrusts", "Leg Curls", "Leg Press"]
        elif exercise_name == "Overhead Press" and any(("overhead" in r) or ("shoulder" in r) for r in restrictions):
            candidates = ["Lateral Raises", "Rear Delt Flyes", "Incline Dumbbell Press"]
        elif exercise_name == "Leg Press" and any("hip" in r for r in restrictions):
            candidates = ["Bulgarian Split Squats", "Hip Thrusts", "Leg Extensions"]

        if not candidates:
            return exercise_name

        try:
            from services.ai.personalization import rank_exercise_substitute

            best = rank_exercise_substitute(exercise_name, candidates, context)
            return best or candidates[0]
        except Exception:
            return candidates[0]

    def _create_exercise(
        self, exercise_name: str, sets: int, primary_goal: IntensityZone
    ) -> Exercise:
        """Create an exercise prescription based on goal."""
        exercise_info = EXERCISE_DATABASE.get(exercise_name, {"muscles": [], "compound": True})

        # Set rep ranges and rest based on goal
        if primary_goal == IntensityZone.STRENGTH:
            rep_range = "3-5" if exercise_info["compound"] else "6-8"
            rest_seconds = 240  # 4 min for compounds, 3 min for isolation
            rir = 2
        elif primary_goal == IntensityZone.HYPERTROPHY:
            rep_range = "6-10" if exercise_info["compound"] else "8-12"
            rest_seconds = 120  # 2 min
            rir = 1
        else:  # ENDURANCE
            rep_range = "12-15" if exercise_info["compound"] else "15-20"
            rest_seconds = 60  # 1 min
            rir = 1

        notes = self._generate_exercise_notes(exercise_name, primary_goal)

        return Exercise(
            name=exercise_name,
            muscle_groups=exercise_info["muscles"],
            sets=sets,
            rep_range=rep_range,
            rest_seconds=rest_seconds,
            rir=rir,
            notes=notes,
            is_compound=exercise_info["compound"],
        )

    def _generate_exercise_notes(self, exercise_name: str, goal: IntensityZone) -> str:
        """Generate technique cues for exercises."""
        notes_db = {
            "Barbell Squat": "Depth to parallel or below, maintain neutral spine, drive through heels",
            "Barbell Bench Press": "Retract scapula, lower to chest, full ROM",
            "Barbell Rows": "Pull to lower chest, squeeze shoulder blades, control eccentric",
            "Pull-ups": "Full ROM, chin over bar, control descent",
            "Romanian Deadlift": "Hinge at hips, slight knee bend, feel hamstring stretch",
            "Overhead Press": "Vertical bar path, full lockout, engage core",
            "Lateral Raises": "Slight forward lean, control tempo, stop at shoulder height",
            "Leg Press": "Full ROM without rounding lower back, control descent",
            "Hip Thrusts": "Full hip extension, pause at top, squeeze glutes",
        }

        return notes_db.get(exercise_name, "Maintain strict form, control tempo")

    def _calculate_actual_volume(self, sessions: List[WorkoutSession]) -> Dict[str, int]:
        """Calculate actual weekly volume per muscle group from sessions."""
        volume_totals = {muscle: 0 for muscle in VOLUME_LANDMARKS.keys()}

        for session in sessions:
            for exercise in session.exercises:
                for muscle in exercise.muscle_groups:
                    if muscle in volume_totals:
                        # Primary muscle gets full sets, secondary muscles get partial credit
                        is_primary = muscle == exercise.muscle_groups[0]
                        multiplier = 1.0 if is_primary else 0.5
                        volume_totals[muscle] += int(exercise.sets * multiplier)

        return volume_totals

    def _calculate_deload_schedule(self, experience_level: ExperienceLevel) -> int:
        """Determine deload frequency based on experience."""
        if experience_level == ExperienceLevel.BEGINNER:
            return 6  # Deload every 6 weeks
        elif experience_level == ExperienceLevel.INTERMEDIATE:
            return 5  # Deload every 5 weeks
        else:
            return 4  # Deload every 4 weeks

    def _generate_progression_notes(
        self, experience_level: ExperienceLevel, goal: IntensityZone, sessions_per_week: int
    ) -> str:
        """Generate progression guidelines."""
        notes = []

        # Volume progression
        if experience_level == ExperienceLevel.BEGINNER:
            notes.append("Progress volume by 5-10% per week (add 1-2 sets per muscle group).")
        else:
            notes.append("Progress volume by 5% per week until reaching MAV/MRV.")

        # Load progression
        if goal == IntensityZone.STRENGTH:
            notes.append(
                "Increase weight when you hit top of rep range for all sets with good form."
            )
        else:
            notes.append(
                "Increase weight when you exceed top of rep range by 2+ reps on all sets."
            )

        # Deload protocol
        notes.append(
            "Deload: Reduce volume by 50%, maintain intensity. Take extra rest day if needed."
        )

        # Auto-regulation
        notes.append(
            "If consistently missing RIR targets or feeling run down, deload early. Listen to your body."
        )

        return " ".join(notes)

    def _generate_safety_modifications(
        self, age: int, medical_restrictions: List[str]
    ) -> List[str]:
        """Generate safety modifications based on age and restrictions."""
        mods = []

        if age >= 65:
            mods.append("Start with 50% of standard volume and progress slowly.")
            mods.append("Include balance training (single-leg work, stability exercises).")
            mods.append("Avoid maximal lifts (stay 3+ RIR).")

        if age >= 50:
            mods.append("Extra warm-up sets recommended (increase blood flow).")
            mods.append("Consider joint-friendly exercise variations.")

        if "no_overhead_press" in medical_restrictions:
            mods.append("Substitute overhead press with landmine press or machine shoulder press.")

        if "knee_issues" in medical_restrictions:
            mods.append("Reduce squat depth, prioritize leg press and split squats.")

        if "back_issues" in medical_restrictions:
            mods.append("Avoid heavy deadlifts, use Romanian deadlifts or trap bar variants.")

        if not mods:
            mods.append("No special modifications required. Follow standard progression.")

        return mods
