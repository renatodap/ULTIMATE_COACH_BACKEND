"""
Planning & Adaptive API (v1)

Endpoints for:
- Persisting generated programs
- Fetching calendar events
- Marking adherence (completed/similar/skipped)
- Recording plan changes (swap/edit/move/cancel/reschedule)
- Getting today's overrides

Note: For brevity, this uses simple user_id parameters. In production, derive user_id
from auth token (RLS still protects per-user data at DB level).
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.supabase_service import SupabaseService
from app.services.program_persistence_service import ProgramPersistenceService
from app.services.adherence_service import AdherenceService


router = APIRouter()


class SaveProgramRequest(BaseModel):
    user_id: str = Field(..., description="User UUID")
    bundle: Dict[str, Any] = Field(..., description="ProgramBundle as dict")


@router.post("/programs/save")
async def save_program(req: SaveProgramRequest):
    svc = ProgramPersistenceService()
    try:
        program = svc.save_program_bundle(req.user_id, req.bundle)
        return {"program": program}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/calendar")
async def get_calendar(
    user_id: str = Query(...),
    date_str: Optional[str] = Query(None, alias="date"),
    range_: Literal["day", "week"] = Query("week", alias="range"),
):
    db = SupabaseService()
    client = db.client
    try:
        if date_str:
            start = date.fromisoformat(date_str)
        else:
            start = date.today()
        end = start if range_ == "day" else start + timedelta(days=6)

        rows = (
            client.table("calendar_events")
            .select("*")
            .eq("user_id", user_id)
            .gte("date", start.isoformat())
            .lte("date", end.isoformat())
            .order("date", desc=False)
            .execute()
        ).data
        return {"events": rows}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class AdherenceRequest(BaseModel):
    user_id: str
    planned_entity_type: Literal["session", "meal"]
    planned_entity_id: str
    status: Literal["completed", "similar", "skipped"]
    actual_ref_type: Optional[Literal["activity", "meal"]] = None
    actual_ref_id: Optional[str] = None
    adherence_json: Optional[Dict[str, Any]] = None
    similarity_score: Optional[float] = None


@router.post("/adherence")
async def set_adherence(req: AdherenceRequest):
    svc = AdherenceService()
    try:
        rec = svc.set_adherence(
            user_id=req.user_id,
            planned_entity_type=req.planned_entity_type,
            planned_entity_id=req.planned_entity_id,
            status=req.status,
            actual_ref_type=req.actual_ref_type,
            actual_ref_id=req.actual_ref_id,
            adherence_json=req.adherence_json,
            similarity_score=req.similarity_score,
        )
        return {"adherence": rec}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PlanChangeRequest(BaseModel):
    user_id: str
    program_id: str
    planned_entity_type: Literal["session", "meal"]
    planned_entity_id: str
    change_type: Literal["swap", "move", "edit", "cancel", "reschedule"]
    reason_code: Optional[str] = None
    reason_text: Optional[str] = None
    new_entity: Optional[Dict[str, Any]] = None  # minimal fields per type


@router.post("/plan_changes")
async def plan_changes(req: PlanChangeRequest):
    db = SupabaseService()
    client = db.client
    try:
        new_entity_id = None
        diff_json = {}
        ref_table = "session_instances" if req.planned_entity_type == "session" else "meal_instances"

        # If new_entity provided, create it and supersede old
        if req.new_entity:
            if req.planned_entity_type == "session":
                # Minimal required fields: day_of_week, time_of_day, session_kind, session_name
                payload = {
                    "program_id": req.program_id,
                    "week_index": req.new_entity.get("week_index", 1),
                    "day_index": req.new_entity.get("day_index", 1),
                    "day_of_week": (req.new_entity.get("day_of_week") or "monday").lower(),
                    "time_of_day": req.new_entity.get("time_of_day"),
                    "session_kind": req.new_entity.get("session_kind", "resistance"),
                    "modality": req.new_entity.get("modality"),
                    "session_name": req.new_entity.get("session_name"),
                    "estimated_duration_minutes": req.new_entity.get("estimated_duration_minutes"),
                    "parameters_json": req.new_entity.get("parameters_json") or {},
                    "notes": req.new_entity.get("notes"),
                }
                ir = client.table("session_instances").insert(payload).execute()
                new_entity_id = ir.data[0]["id"]
            else:
                payload = {
                    "program_id": req.program_id,
                    "week_index": req.new_entity.get("week_index", 1),
                    "day_index": req.new_entity.get("day_index", 1),
                    "meal_type": req.new_entity.get("meal_type"),
                    "meal_name": req.new_entity.get("meal_name"),
                    "targets_json": req.new_entity.get("targets_json") or {},
                    "notes": req.new_entity.get("notes"),
                }
                ir = client.table("meal_instances").insert(payload).execute()
                new_entity_id = ir.data[0]["id"]

            # Supersede old
            client.table(ref_table).update({"state": "superseded"}).eq("id", req.planned_entity_id).execute()
            diff_json = {"replaced_with": new_entity_id, "new_entity": req.new_entity}

        # Create plan change event
        ev = {
            "program_id": req.program_id,
            "user_id": req.user_id,
            "change_type": req.change_type,
            "planned_entity_type": req.planned_entity_type,
            "planned_entity_id": req.planned_entity_id,
            "new_entity_id": new_entity_id,
            "reason_code": req.reason_code,
            "reason_text": req.reason_text,
            "diff_json": diff_json,
        }
        er = client.table("plan_change_events").insert(ev).execute()
        return {"change_event": er.data[0], "new_entity_id": new_entity_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/overrides/today")
async def get_overrides_today(user_id: str = Query(...)):
    db = SupabaseService()
    client = db.client
    try:
        today = date.today().isoformat()
        rows = (
            client.table("day_overrides").select("*")
            .eq("user_id", user_id)
            .eq("date", today)
            .order("created_at", desc=True)
            .execute()
        ).data
        return {"date": today, "overrides": rows}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

