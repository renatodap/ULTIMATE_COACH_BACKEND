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
    seriousness: Optional[str] = None           # hobby | recreational | competitive
    seriousness_score: Optional[int] = None     # 1..10


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
    time_of_day: Optional[str] = None
    start_hour: Optional[int] = None
    end_hour: Optional[int] = None


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
        cardio_preference: Optional[str] = None,
        upcoming_events: Optional[List[dict]] = None,
        day_time_of_day: Optional[dict] = None,
        day_time_windows: Optional[dict] = None,
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
        # Fill default sessions from seriousness if target not provided
        filled: List[ModalityPreference] = []
        for p in (preferences or []):
            if p.target_sessions_per_week is None:
                if (p.seriousness or "").lower() == "competitive":
                    p.target_sessions_per_week = 3
                elif (p.seriousness or "").lower() in ("recreational", "serious") or (p.seriousness_score or 0) >= 7:
                    p.target_sessions_per_week = 2
                else:
                    p.target_sessions_per_week = 1
            filled.append(p)

        prefs = [p for p in filled if p.target_sessions_per_week and p.target_sessions_per_week > 0]
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

        # Taper detection: if a race event within 2 weeks, suppress high-intensity sessions
        taper = False
        if upcoming_events:
            wk = min(
                (e.get("weeks_until") for e in upcoming_events if str(e.get("event_type","")) in ["race","competition"] and e.get("weeks_until") is not None),
                default=None,
            )
            if wk is not None and wk <= 2:
                taper = True

        # simple per-day reservations of fixed windows
        day_reservations: dict = {d: [] for d in available_days}

        # Place fixed-time sessions first
        for pref in prefs:
            for tw in (getattr(pref, "fixed_time_windows", None) or []):
                d = (tw.day_of_week or available_days[0]).lower()
                if d not in day_reservations:
                    continue
                if not day_has_facility(d, pref.facility_needed):
                    continue
                day_reservations[d].append((tw.start_hour, tw.end_hour))
                duration = max(10, (tw.end_hour - tw.start_hour) * 60)
                session = self._build_session(pref, d)
                session.start_hour = tw.start_hour
                session.end_hour = tw.end_hour
                session.time_of_day = self._hour_to_tod(tw.start_hour)
                session.duration_minutes = duration
                planned.append(session)

        total_slots_remaining = max_extra_sessions - sum(1 for p in prefs for _ in (getattr(p, "fixed_time_windows", None) or []))
        for pref in prefs:
            if total_slots_remaining <= 0:
                break
            sessions_for_mod = min(pref.target_sessions_per_week or 0, total_slots_remaining)
            for _ in range(sessions_for_mod):
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
                # Apply taper adjustments to endurance/HIIT
                if taper and session.session_kind in (SessionKind.ENDURANCE, SessionKind.HIIT):
                    session.intensity_target = "Easy (Z1/Z2); tapering"
                    session.intervals = None
                    session.notes = (session.notes or "") + " Taper: reduce intensity and volume; prioritize rest."

                # Assign time-of-day if available; avoid conflicts with reservations
                tod = (getattr(pref, "preferred_time_of_day", None) or self._hour_to_tod(18)).lower()
                allowed_tods = (day_time_of_day or {}).get(day, ["morning", "afternoon", "evening"])
                if tod not in allowed_tods:
                    tod = next((t for t in ["morning","afternoon","evening"] if t in allowed_tods), "evening")
                session.time_of_day = tod
                # If explicit day windows given, try to place inside one that isn't reserved
                windows: List[TimeWindow] = (day_time_windows or {}).get(day, [])
                placed_window = None
                for w in windows:
                    if self._tod_matches_window(tod, w) and not self._overlaps_any((w.start_hour, w.end_hour), day_reservations.get(day, [])):
                        placed_window = w
                        break
                if placed_window:
                    session.start_hour = placed_window.start_hour
                    session.end_hour = placed_window.end_hour
                    day_reservations[day].append((placed_window.start_hour, placed_window.end_hour))
                planned.append(session)
                total_slots_remaining -= 1
                if total_slots_remaining <= 0:
                    break

        # Ensure everyone gets some cardio unless explicitly avoid
        has_endurance = any(s.session_kind == SessionKind.ENDURANCE for s in planned)
        if not has_endurance and (cardio_preference or "").lower() != "avoid":
            # add a default brisk walk
            day = pick_day(prefer_weekend=False) or (available_days[0] if available_days else None)
            if day:
                planned.append(
                    MultimodalSessionInternal(
                        session_kind=SessionKind.ENDURANCE,
                        modality="walking",
                        day_of_week=day,
                        duration_minutes=30,
                        intensity_target="Brisk walk (RPE 3)",
                        notes="General health cardio: 20–30 minutes brisk walking.",
                    )
                )

        return planned

    def _build_session(self, pref: ModalityPreference, day: str) -> MultimodalSessionInternal:
        modality = pref.modality.lower()
        intensity = (pref.intensity_preference or "moderate").lower()

        # Duration heuristic
        min_d = pref.min_duration_minutes or 30
        max_d = pref.max_duration_minutes or (90 if modality in ["running", "cycling"] else 45)
        duration = min(max_d, max(min_d, 30 if intensity == "low" else (40 if intensity == "moderate" else 50)))

        if modality in ["running", "cycle", "cycling", "row", "rower", "rowing", "swim", "swimming", "walk", "walking", "hiking"]:
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

        sport_keywords = {"tennis", "basketball", "soccer", "football", "hockey", "volleyball", "rugby", "climbing", "badminton"}
        if modality in sport_keywords:
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

        # default: if unknown modality name suggests movement, treat as sport; else endurance
        if len(modality) > 0 and any(c.isalpha() for c in modality):
            return MultimodalSessionInternal(
                session_kind=SessionKind.SPORT,
                modality=modality,
                day_of_week=day,
                duration_minutes=duration,
                notes="General practice session; adjust based on skill work.",
            )
        return MultimodalSessionInternal(
            session_kind=SessionKind.ENDURANCE,
            modality=modality or "cardio",
            day_of_week=day,
            duration_minutes=duration,
            intensity_target="Z2",
            notes="General aerobic session.",
        )

    def _hour_to_tod(self, hour: int) -> str:
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 17:
            return "afternoon"
        return "evening"

    def _tod_matches_window(self, tod: str, w: TimeWindow) -> bool:
        return self._hour_to_tod(w.start_hour) == tod

    def _overlaps_any(self, window: tuple, existing: List[tuple]) -> bool:
        s,e = window
        for (a,b) in existing:
            if not (e <= a or s >= b):
                return True
        return False
@dataclass
class TimeWindow:
    day_of_week: Optional[str]
    start_hour: int
    end_hour: int
