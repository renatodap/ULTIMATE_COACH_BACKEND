"""
Modality Planner

Generates weekly multimodal sessions (endurance/HIIT/sport), based on user preferences,
availability, and sensible load constraints. This is a first-phase implementation designed
to run alongside the existing resistance training plan without changing it.

Scope (Phase A):
- Read modality preferences (running, cycling, tennis, hiit, etc.)
- Allocate target sessions/week per modality within available days
- Build simple structured sessions:
  - Endurance: intervals/tempo/easy/long runs or rides with HR/RPE targets
  - HIIT: classic work/rest templates by modality
  - Sport (tennis): drills + optional match-play block
- Output sessions as generic models for API transformation

Design notes:
- We avoid extending the CP-SAT solver at this stage; allocation is heuristic with
  basic spacing and load heuristics.
- Nutrition periodization remains unchanged in Phase A; we attach notes for high-load days.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class SessionKind(str, Enum):
    ENDURANCE = "endurance"
    HIIT = "hiit"
    SPORT = "sport"


@dataclass
class ModalityPreference:
    modality: str  # running, cycling, tennis, hiit
    priority: int = 5
    target_sessions_per_week: Optional[int] = None
    min_duration_minutes: Optional[int] = None
    max_duration_minutes: Optional[int] = None
    facility_needed: Optional[str] = None
    intensity_preference: Optional[str] = None  # low/moderate/high


@dataclass
class FacilityAccess:
    facility_type: str  # court, track, pool, bike, rower
    days_available: List[str]
    notes: Optional[str] = None


@dataclass
class Interval:
    work_minutes: float
    rest_minutes: Optional[float] = None
    target: Optional[str] = None


@dataclass
class Drill:
    name: str
    duration_minutes: int
    focus: Optional[str] = None


@dataclass
class MultimodalSessionInternal:
    session_kind: SessionKind
    modality: str
    day_of_week: Optional[str]
    duration_minutes: int
    intensity_target: Optional[str] = None
    intervals: Optional[List[Interval]] = None
    drills: Optional[List[Drill]] = None
    notes: Optional[str] = None


class ModalityPlanner:
    """Heuristic weekly planner for multimodal sessions."""

    def __init__(self):
        self.weekdays = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]

    def plan_week(
        self,
        preferences: List[ModalityPreference],
        available_days: List[str],
        resistance_sessions_per_week: int,
        facility_access: Optional[List[FacilityAccess]] = None,
        age: Optional[int] = None,
    ) -> List[MultimodalSessionInternal]:
        """Generate 1-week schedule of multimodal sessions.

        Simple approach:
        - Cap total multimodal sessions to avoid overloading (e.g., ≤ 3 if lifting 4x)
        - Spread high-intensity sessions (HIIT) away from heavy lifting days when possible
        - Respect facility constraints naively (only schedule tennis when a court day exists)
        """
        facility_access = facility_access or []
        available_days = [d.lower() for d in available_days] or self.weekdays
        max_extra_sessions = max(0, 6 - resistance_sessions_per_week)  # leave recovery headroom

        # Normalize preferences and sort by priority
        prefs = [p for p in preferences if p.target_sessions_per_week and p.target_sessions_per_week > 0]
        prefs.sort(key=lambda p: p.priority, reverse=True)

        planned: List[MultimodalSessionInternal] = []

        # Helper: next available day not saturated
        def pick_day(prefer_weekend: bool = False) -> Optional[str]:
            candidates = [d for d in available_days]
            if prefer_weekend:
                candidates = [d for d in candidates if d in ["saturday", "sunday"]] + [
                    d for d in candidates if d not in ["saturday", "sunday"]
                ]
            # avoid stacking two extras same day
            for d in candidates:
                if sum(1 for s in planned if s.day_of_week == d) == 0:
                    return d
            # fallback: allow stacking if necessary
            return candidates[0] if candidates else None

        # Facility filter
        def day_has_facility(day: str, facility: Optional[str]) -> bool:
            if not facility:
                return True
            for f in facility_access:
                if f.facility_type.lower() == facility.lower() and day in [x.lower() for x in f.days_available]:
                    return True
            return False

        total_slots_remaining = max_extra_sessions
        for pref in prefs:
            if total_slots_remaining <= 0:
                break
            sessions_for_mod = min(pref.target_sessions_per_week or 0, total_slots_remaining)
            for i in range(sessions_for_mod):
                # choose a day
                prefer_weekend = pref.modality in ["cycling", "long_run", "hiking"]
                day = pick_day(prefer_weekend)
                if not day:
                    continue
                if not day_has_facility(day, pref.facility_needed):
                    # try another day
                    alt = next((d for d in self.weekdays if d in available_days and day_has_facility(d, pref.facility_needed)), None)
                    day = alt or day

                session = self._build_session(pref, day)
                planned.append(session)
                total_slots_remaining -= 1
                if total_slots_remaining <= 0:
                    break

        return planned

    def _build_session(self, pref: ModalityPreference, day: str) -> MultimodalSessionInternal:
        modality = pref.modality.lower()
        intensity = (pref.intensity_preference or "moderate").lower()

        # Duration heuristic
        min_d = pref.min_duration_minutes or 30
        max_d = pref.max_duration_minutes or (90 if modality in ["running", "cycling"] else 45)
        duration = min(max_d, max(min_d, 30 if intensity == "low" else (40 if intensity == "moderate" else 50)))

        if modality in ["running", "cycling", "rower", "rowing", "swimming"]:
            kind = SessionKind.ENDURANCE
            if intensity == "high":
                intervals = [
                    Interval(work_minutes=4, rest_minutes=2, target="Z4/Z5 or RPE 8") for _ in range(5)
                ]
                return MultimodalSessionInternal(
                    session_kind=kind,
                    modality="running" if modality == "rower" else modality,
                    day_of_week=day,
                    duration_minutes=duration,
                    intensity_target="Intervals",
                    intervals=intervals,
                    notes="High-intensity intervals; avoid the day before heavy lower-body lifting.",
                )
            elif intensity == "low":
                return MultimodalSessionInternal(
                    session_kind=kind,
                    modality=modality,
                    day_of_week=day,
                    duration_minutes=duration,
                    intensity_target="Z1/Z2 or RPE 3-4",
                    notes="Easy aerobic base; conversational pace.",
                )
            else:
                return MultimodalSessionInternal(
                    session_kind=kind,
                    modality=modality,
                    day_of_week=day,
                    duration_minutes=duration,
                    intensity_target="Tempo (Z3 or RPE 6-7)",
                    notes="Steady tempo; build aerobic threshold.",
                )

        if modality in ["hiit", "metcon"]:
            kind = SessionKind.HIIT
            intervals = [Interval(work_minutes=0.5, rest_minutes=0.5, target="RPE 9") for _ in range(10)]
            return MultimodalSessionInternal(
                session_kind=kind,
                modality="hiit",
                day_of_week=day,
                duration_minutes=duration,
                intensity_target="Tabata-style",
                intervals=intervals,
                notes="Keep form strict; full recovery between rounds.",
            )

        if modality in ["tennis", "basketball", "soccer"]:
            kind = SessionKind.SPORT
            drills = [
                Drill(name="Footwork Ladder", duration_minutes=10, focus="footwork"),
                Drill(name="Serve & Return", duration_minutes=15, focus="serve"),
                Drill(name="Rally Consistency", duration_minutes=15, focus="rally"),
            ]
            return MultimodalSessionInternal(
                session_kind=kind,
                modality=modality,
                day_of_week=day,
                duration_minutes=duration,
                drills=drills,
                notes="Finish with 15-30 minutes of match play if partner available.",
            )

        # default to generic endurance session
        return MultimodalSessionInternal(
            session_kind=SessionKind.ENDURANCE,
            modality=modality,
            day_of_week=day,
            duration_minutes=duration,
            intensity_target="Z2",
            notes="General aerobic session.",
        )

