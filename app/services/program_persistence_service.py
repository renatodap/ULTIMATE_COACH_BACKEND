"""
Program Persistence Service

Persists a generated ProgramBundle (from ultimate_ai_consultation) into:
- programs (snapshot + provenance)
- session_instances + exercise_plan_items
- meal_instances + meal_item_plan
- calendar_events (denormalized for fast UI)

This service assumes Supabase/Postgres tables created by migration 036.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta
import structlog

from app.services.supabase_service import SupabaseService

logger = structlog.get_logger()


class ProgramPersistenceService:
    def __init__(self, db: Optional[SupabaseService] = None) -> None:
        self.db = db or SupabaseService()

    def _ensure(self, ok: bool, msg: str) -> None:
        if not ok:
            raise RuntimeError(msg)

    def save_program_bundle(self, user_id: str, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persist ProgramBundle JSON and normalize into plan tables.

        Args:
            user_id: UUID string
            bundle: ProgramBundle.model_dump() style dict

        Returns:
            Inserted program row
        """
        client = self.db.client

        # 1) programs
        program_row = {
            "user_id": user_id,
            "primary_goal": bundle.get("primary_goal"),
            "program_start_date": bundle.get("program_start_date"),
            "program_duration_weeks": bundle.get("program_duration_weeks"),
            "version": bundle.get("version"),
            "next_reassessment_date": bundle.get("next_reassessment_date"),
            "tdee": bundle.get("tdee_result"),
            "macros": bundle.get("macro_targets"),
            "safety": bundle.get("safety_report"),
            "feasibility": bundle.get("feasibility_report"),
            "provenance": bundle.get("provenance"),
            "full_bundle": bundle,
        }
        pr = client.table("programs").insert(program_row).execute()
        program = pr.data[0]
        program_id = program["id"]

        # 2) session_instances + exercise_plan_items
        tp = bundle.get("training_plan") or {}
        sessions: List[Dict[str, Any]] = tp.get("weekly_sessions") or []
        # Map day_of_week string to 1..7 index
        dow_to_idx = {"monday":1,"tuesday":2,"wednesday":3,"thursday":4,"friday":5,"saturday":6,"sunday":7}
        start_date_str = bundle.get("program_start_date")
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else datetime.now()
        # replicate across 2 weeks
        for week in [1,2]:
            for s in sessions:
                day = (s.get("day_of_week") or "monday").lower()
                day_idx = dow_to_idx.get(day, 1)
                inst = {
                    "program_id": program_id,
                    "week_index": week,
                    "day_index": day_idx,
                    "day_of_week": day,
                    "time_of_day": s.get("time_of_day"),
                    "session_kind": "resistance",
                    "session_name": s.get("session_name"),
                    "estimated_duration_minutes": s.get("estimated_duration_minutes"),
                    "notes": s.get("notes"),
                }
                ir = client.table("session_instances").insert(inst).execute()
                instance_id = ir.data[0]["id"]

                for idx, ex in enumerate(s.get("exercises") or []):
                    epi = {
                        "session_instance_id": instance_id,
                        "order_index": idx,
                        "name": ex.get("exercise_name"),
                        "muscle_groups": ex.get("muscle_groups_primary"),
                        "sets": ex.get("sets"),
                        "rep_range": ex.get("rep_range"),
                        "rest_seconds": ex.get("rest_seconds"),
                        "rir": ex.get("rir"),
                        "is_compound": None,
                        "notes": ex.get("instructions"),
                    }
                    client.table("exercise_plan_items").insert(epi).execute()

        # 3) multimodal sessions → session_instances rows (replicate across 2 weeks)
        for week in [1,2]:
            for ms in bundle.get("multimodal_sessions_weekly") or []:
                day = (ms.get("day_of_week") or "monday").lower()
                day_idx = dow_to_idx.get(day, 1)
                inst = {
                    "program_id": program_id,
                    "week_index": week,
                    "day_index": day_idx,
                    "day_of_week": day,
                    "time_of_day": ms.get("time_of_day"),
                    "start_hour": ms.get("start_hour"),
                    "end_hour": ms.get("end_hour"),
                    "session_kind": ms.get("session_kind"),
                    "modality": ms.get("modality"),
                    "session_name": ms.get("modality"),
                    "estimated_duration_minutes": ms.get("duration_minutes"),
                    "parameters_json": {
                        "intervals": ms.get("intervals"),
                        "drills": ms.get("drills"),
                    },
                    "notes": ms.get("notes"),
                }
                client.table("session_instances").insert(inst).execute()

        # 4) meal_instances + items for 14 days (flatten day 1 only or all)
        np = bundle.get("nutrition_plan") or {}
        daily = np.get("daily_meal_plans") or []
        for day_idx, d in enumerate(daily, start=1):
            for order, meal in enumerate(d.get("meals") or []):
                mi = {
                    "program_id": program_id,
                    "week_index": 1 + (day_idx - 1) // 7,
                    "day_index": ((day_idx - 1) % 7) + 1,
                    "day_name": None,
                    "order_index": order,
                    "meal_type": meal.get("meal_time"),
                    "meal_name": meal.get("meal_name"),
                    "targets_json": {
                        "calories": meal.get("total_calories"),
                        "protein_g": meal.get("total_protein_g"),
                        "carbs_g": meal.get("total_carbs_g"),
                        "fat_g": meal.get("total_fat_g"),
                    },
                    "totals_json": d.get("daily_totals"),
                    "notes": meal.get("notes"),
                }
                mir = client.table("meal_instances").insert(mi).execute()
                meal_instance_id = mir.data[0]["id"]
                for i, food in enumerate(meal.get("foods") or []):
                    mip = {
                        "meal_instance_id": meal_instance_id,
                        "order_index": i,
                        "food_name": food.get("food_name"),
                        "serving_size": food.get("serving_size"),
                        "serving_unit": food.get("serving_unit"),
                        "targets_json": {
                            "calories": food.get("calories"),
                            "protein_g": food.get("protein_g"),
                            "carbs_g": food.get("carbs_g"),
                            "fat_g": food.get("fat_g"),
                            "fiber_g": food.get("fiber_g"),
                        },
                    }
                    client.table("meal_item_plan").insert(mip).execute()

        # 5) calendar events (denormalized) for full 14 days
        # Sessions
        sess_rows = (
            client.table("session_instances").select("id, week_index, day_index, day_of_week, time_of_day, session_kind, modality, session_name, estimated_duration_minutes")
            .eq("program_id", program_id)
            .execute()
        ).data
        # Compute date from program_start_date + offset
        def date_for(week_index: int, day_index: int) -> str:
            offset = (week_index - 1) * 7 + (day_index - 1)
            return (start_date + timedelta(days=offset)).date().isoformat()
        for sr in sess_rows:
            ev = {
                "user_id": user_id,
                "program_id": program_id,
                "date": date_for(sr.get("week_index"), sr.get("day_index")),
                "event_type": "multimodal" if sr.get("session_kind") != "resistance" else "training",
                "ref_table": "session_instances",
                "ref_id": sr.get("id"),
                "title": sr.get("session_name") or sr.get("session_kind"),
                "details": {"day_of_week": sr.get("day_of_week"), "time_of_day": sr.get("time_of_day")},
            }
            client.table("calendar_events").insert(ev).execute()

        # Meal events: create one per meal on its corresponding date
        meal_rows = (
            client.table("meal_instances").select("id, week_index, day_index, meal_type, meal_name, targets_json")
            .eq("program_id", program_id)
            .execute()
        ).data
        for mr in meal_rows:
            ev = {
                "user_id": user_id,
                "program_id": program_id,
                "date": date_for(mr.get("week_index"), mr.get("day_index")),
                "event_type": "meal",
                "ref_table": "meal_instances",
                "ref_id": mr.get("id"),
                "title": mr.get("meal_name") or mr.get("meal_type"),
                "details": mr.get("targets_json") or {},
            }
            client.table("calendar_events").insert(ev).execute()

        return program
