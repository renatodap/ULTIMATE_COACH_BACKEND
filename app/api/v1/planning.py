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
from app.services.daily_adjuster_service import DailyAdjusterService
from app.services.daily_adjustment_service import daily_adjustment_service
from app.services.reassessment_service import reassessment_service
from app.services.adjustment_approval_service import adjustment_approval_service
from app.models.adjustment_preferences import (
    ApproveAdjustmentRequest,
    RejectAdjustmentRequest,
    UndoAdjustmentRequest,
    UpdateAdjustmentPreferences,
)


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


@router.get("/calendar/full")
async def get_calendar_full(
    user_id: str = Query(...),
    date_str: Optional[str] = Query(None, alias="date"),
    range_: Literal["day", "week"] = Query("week", alias="range"),
):
    """
    Returns calendar events enriched with plan details to minimize round trips.

    For training/multimodal: includes session_instances row and exercise_plan_items or parameters_json.
    For meal: includes meal_instances row and meal_item_plan items.
    """
    db = SupabaseService()
    client = db.client
    try:
        if date_str:
            start = date.fromisoformat(date_str)
        else:
            start = date.today()
        end = start if range_ == "day" else start + timedelta(days=6)

        events = (
            client.table("calendar_events")
            .select("*")
            .eq("user_id", user_id)
            .gte("date", start.isoformat())
            .lte("date", end.isoformat())
            .order("date", desc=False)
            .execute()
        ).data

        # Collect ref_ids
        sess_ids = [e["ref_id"] for e in events if e.get("ref_table") == "session_instances"]
        meal_ids = [e["ref_id"] for e in events if e.get("ref_table") == "meal_instances"]

        sess_map: Dict[str, Any] = {}
        meal_map: Dict[str, Any] = {}

        if sess_ids:
            srows = client.table("session_instances").select("*").in_("id", sess_ids).execute().data
            for s in srows:
                sess_map[s["id"]] = s
            # exercises per session
            ex_rows = client.table("exercise_plan_items").select("*").in_("session_instance_id", sess_ids).execute().data
            # group
            ex_map: Dict[str, List[Dict[str, Any]]] = {}
            for ex in ex_rows:
                ex_map.setdefault(ex["session_instance_id"], []).append(ex)
            # attach exercises where applicable
            for sid, s in sess_map.items():
                if s.get("session_kind") == "resistance":
                    s["exercises"] = ex_map.get(sid, [])

        if meal_ids:
            mrows = client.table("meal_instances").select("*").in_("id", meal_ids).execute().data
            for m in mrows:
                meal_map[m["id"]] = m
            mi_rows = client.table("meal_item_plan").select("*").in_("meal_instance_id", meal_ids).execute().data
            items_map: Dict[str, List[Dict[str, Any]]] = {}
            for it in mi_rows:
                items_map.setdefault(it["meal_instance_id"], []).append(it)
            for mid, m in meal_map.items():
                m["items"] = items_map.get(mid, [])

        # Enrich events
        enriched = []
        for e in events:
            ref_table = e.get("ref_table")
            ref_id = e.get("ref_id")
            out = dict(e)
            if ref_table == "session_instances":
                out["plan"] = sess_map.get(ref_id)
            elif ref_table == "meal_instances":
                out["plan"] = meal_map.get(ref_id)
            enriched.append(out)

        return {"events": enriched}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/programs/current")
async def get_current_program(user_id: str = Query(...), include_bundle: bool = Query(False)):
    db = SupabaseService()
    client = db.client
    try:
        pr = (
            client.table("programs")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not pr.data:
            return {"program": None}
        program = pr.data[0]
        if not include_bundle:
            # remove heavy field
            program_slim = {k: v for k, v in program.items() if k != "full_bundle"}
            return {"program": program_slim}
        return {"program": program}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RunOverridesRequest(BaseModel):
    user_id: str
    program_id: str
    dry_run: bool = True


@router.post("/overrides/run")
async def run_overrides(req: RunOverridesRequest):
    try:
        svc = DailyAdjusterService()
        res = svc.adjust_today(req.user_id, req.program_id, dry_run=req.dry_run)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/calendar/summary")
async def get_calendar_summary(
    user_id: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
):
    """
    Returns per-day summary counts for planned/completed/similar/skipped and event types.
    Frontend can use this for a strip calendar or heatmap.
    """
    db = SupabaseService()
    client = db.client
    try:
        rows = (
            client.table("calendar_events")
            .select("date, event_type, status")
            .eq("user_id", user_id)
            .gte("date", start_date)
            .lte("date", end_date)
            .execute()
        ).data
        summary: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            d = r["date"]
            s = r.get("status") or "planned"
            et = r.get("event_type") or "training"
            day = summary.setdefault(d, {"counts": {"planned":0,"completed":0,"similar":0,"skipped":0,"modified":0}, "types": {"training":0,"multimodal":0,"meal":0}})
            # Count status
            if s not in day["counts"]:
                day["counts"][s] = 0
            day["counts"][s] += 1
            # Count type
            if et not in day["types"]:
                day["types"][et] = 0
            day["types"][et] += 1
        # Return as list sorted by date
        out = [
            {"date": d, **vals}
            for d, vals in sorted(summary.items(), key=lambda kv: kv[0])
        ]
        return {"summary": out}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/notifications")
async def get_notifications(
    user_id: str = Query(...),
    since: Optional[str] = Query(None),
):
    db = SupabaseService()
    client = db.client
    try:
        q = client.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True)
        if since:
            q = q.gte("created_at", since)
        rows = q.execute().data
        return {"notifications": rows}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MarkNotificationReadRequest(BaseModel):
    user_id: str
    notification_id: str


@router.post("/notifications/read")
async def mark_notification_read(req: MarkNotificationReadRequest):
    db = SupabaseService()
    client = db.client
    try:
        upd = client.table("notifications").update({"read_at": date.today().isoformat()}).eq("id", req.notification_id).eq("user_id", req.user_id).execute()
        return {"updated": True, "notification": upd.data[0] if upd.data else None}
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


# ============================================================================
# Daily Adjustments (NEW - Sprint 2)
# ============================================================================


class CreateAdjustmentRequest(BaseModel):
    """Request to create daily adjustment"""

    user_id: str = Field(..., description="User UUID")
    target_date: Optional[str] = Field(None, description="Date to adjust (YYYY-MM-DD), defaults to today")
    context: Optional[Dict[str, Any]] = Field(None, description="User context (sleep, stress, soreness)")


@router.post("/adjustments/analyze")
async def analyze_and_adjust(req: CreateAdjustmentRequest):
    """
    Analyze user context and create day override if needed.

    This endpoint:
    1. Gathers context (adherence, sleep, stress, injuries)
    2. Identifies adjustment triggers
    3. Calculates adjustments (calories, volume)
    4. Applies safety gates
    5. Creates day_override record

    Returns:
        day_override if adjustment made, None otherwise
    """
    try:
        target_date_obj = (
            date.fromisoformat(req.target_date) if req.target_date else date.today()
        )

        override = await daily_adjustment_service.analyze_and_adjust(
            user_id=req.user_id,
            target_date=target_date_obj,
            context=req.context,
        )

        if override:
            return {
                "adjusted": True,
                "override": override,
                "message": f"Daily adjustment created: {override.get('reason_code')}",
            }
        else:
            return {
                "adjusted": False,
                "message": "No adjustment needed",
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/adjustments/{target_date}")
async def get_adjustment(
    target_date: str,
    user_id: str = Query(..., description="User UUID"),
):
    """
    Get existing day override for a specific date.

    Args:
        target_date: Date to check (YYYY-MM-DD)
        user_id: User UUID

    Returns:
        day_override if exists, None otherwise
    """
    try:
        date_obj = date.fromisoformat(target_date)

        override = await daily_adjustment_service.get_adjustment_for_date(
            user_id=user_id,
            target_date=date_obj,
        )

        if override:
            return {"override": override}
        else:
            return {"override": None, "message": "No adjustment for this date"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ApplyOverrideRequest(BaseModel):
    """Request to apply override to plan"""

    user_id: str = Field(..., description="User UUID")
    target_date: str = Field(..., description="Date of the plan (YYYY-MM-DD)")
    override_id: str = Field(..., description="Override UUID to apply")


@router.post("/adjustments/apply")
async def apply_override(req: ApplyOverrideRequest):
    """
    Apply day override to a plan (for display to user).

    This endpoint:
    1. Fetches the override
    2. Fetches today's calendar events
    3. Applies adjustments to events
    4. Returns adjusted plan

    Use case: Frontend calls this to show user their adjusted plan for the day
    """
    db = SupabaseService()
    client = db.client

    try:
        # Fetch override
        override_result = (
            client.table("day_overrides")
            .select("*")
            .eq("id", req.override_id)
            .eq("user_id", req.user_id)
            .execute()
        )

        if not override_result.data:
            raise HTTPException(status_code=404, detail="Override not found")

        override = override_result.data[0]
        target_date_obj = date.fromisoformat(req.target_date)

        # Apply override to plan
        adjusted_plan = await daily_adjustment_service.apply_override_to_plan(
            user_id=req.user_id,
            target_date=target_date_obj,
            override=override,
        )

        return adjusted_plan

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class UserContextRequest(BaseModel):
    """Request to log user context"""

    user_id: str = Field(..., description="User UUID")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    sleep_hours: Optional[float] = Field(None, description="Hours of sleep", ge=0, le=24)
    sleep_quality: Optional[int] = Field(None, description="Sleep quality (1-10)", ge=1, le=10)
    stress_level: Optional[int] = Field(None, description="Stress level (1-10)", ge=1, le=10)
    soreness_level: Optional[int] = Field(None, description="Soreness level (1-10)", ge=1, le=10)
    energy_level: Optional[int] = Field(None, description="Energy level (1-10)", ge=1, le=10)
    injury_notes: Optional[str] = Field(None, description="Injury or pain notes")
    notes: Optional[str] = Field(None, description="General notes")


@router.post("/context/log")
async def log_user_context(req: UserContextRequest):
    """
    Log user context for daily adjustments.

    Context includes:
    - Sleep hours and quality
    - Stress level
    - Soreness level
    - Energy level
    - Injury notes

    This data is used by the daily adjustment system to make intelligent adjustments.
    """
    db = SupabaseService()
    client = db.client

    try:
        # Check if context already exists for this date
        existing = (
            client.table("user_context_log")
            .select("id")
            .eq("user_id", req.user_id)
            .eq("date", req.date)
            .execute()
        )

        context_data = {
            "user_id": req.user_id,
            "date": req.date,
            "sleep_hours": req.sleep_hours,
            "sleep_quality": req.sleep_quality,
            "stress_level": req.stress_level,
            "soreness_level": req.soreness_level,
            "energy_level": req.energy_level,
            "injury_notes": req.injury_notes,
            "notes": req.notes,
        }

        if existing.data:
            # Update existing
            result = (
                client.table("user_context_log")
                .update(context_data)
                .eq("id", existing.data[0]["id"])
                .execute()
            )
        else:
            # Insert new
            result = client.table("user_context_log").insert(context_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to log context")

        return {
            "context": result.data[0],
            "message": "Context logged successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/context/{target_date}")
async def get_user_context(
    target_date: str,
    user_id: str = Query(..., description="User UUID"),
):
    """
    Get user context for a specific date.

    Returns:
        user_context_log entry if exists, None otherwise
    """
    db = SupabaseService()
    client = db.client

    try:
        result = (
            client.table("user_context_log")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", target_date)
            .execute()
        )

        if result.data:
            return {"context": result.data[0]}
        else:
            return {"context": None, "message": "No context logged for this date"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Bi-weekly Reassessment (NEW - Sprint 3)
# ============================================================================


@router.get("/reassessment/check")
async def check_reassessment_due(
    user_id: str = Query(..., description="User UUID"),
):
    """
    Check if user is due for bi-weekly reassessment.

    Returns:
        {
            "is_due": bool,
            "next_reassessment_date": str (YYYY-MM-DD) or None
        }
    """
    try:
        is_due, next_date = await reassessment_service.check_reassessment_due(user_id)

        return {
            "is_due": is_due,
            "next_reassessment_date": next_date.isoformat() if next_date else None,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RunReassessmentRequest(BaseModel):
    """Request to run bi-weekly reassessment"""

    user_id: str = Field(..., description="User UUID")
    force: bool = Field(False, description="Force reassessment even if not due")


@router.post("/reassessment/run")
async def run_reassessment(req: RunReassessmentRequest):
    """
    Run bi-weekly reassessment for user.

    This endpoint:
    1. Checks if reassessment is due (or forced)
    2. Aggregates 14 days of data (adherence, weight, context)
    3. Runs PID controllers (CaloriePIDController, VolumePIDController)
    4. Determines if program adjustments are needed
    5. Creates plan_change_events for audit trail
    6. Updates next_reassessment_date

    Returns:
        Reassessment result with:
        - aggregated_data: 14-day data summary
        - adjustments: PID controller outputs
        - needs_new_program: bool
        - next_reassessment_date: when next reassessment is due
    """
    try:
        result = await reassessment_service.run_reassessment(
            user_id=req.user_id,
            force=req.force,
        )

        if result is None:
            return {
                "reassessed": False,
                "message": "Reassessment not due yet. Use force=true to override.",
            }

        # If significant adjustments, create plan change events
        if result["needs_new_program"]:
            event_ids = await reassessment_service.create_plan_change_events(
                user_id=req.user_id,
                program_id=result["program_id"],
                adjustments=result["adjustments"],
                effective_date=date.today(),
            )
            result["plan_change_event_ids"] = event_ids

            # Apply adjustments to current program
            updated_program = await reassessment_service.apply_adjustments_to_program(
                user_id=req.user_id,
                program_id=result["program_id"],
                adjustments=result["adjustments"],
            )
            result["updated_program"] = updated_program

        return {
            "reassessed": True,
            "result": result,
            "message": "Reassessment completed successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reassessment/history")
async def get_reassessment_history(
    user_id: str = Query(..., description="User UUID"),
    limit: int = Query(10, description="Number of reassessments to return", ge=1, le=50),
):
    """
    Get history of plan change events from reassessments.

    Returns list of reassessment adjustments with:
    - Date of reassessment
    - Calorie adjustments
    - Volume adjustments
    - Reason codes

    This is useful for tracking how the program has adapted over time.
    """
    db = SupabaseService()
    client = db.client

    try:
        events = (
            client.table("plan_change_events")
            .select("*")
            .eq("user_id", user_id)
            .or_("reason_code.eq.biweekly_reassessment_nutrition,reason_code.eq.biweekly_reassessment_volume")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return {
            "reassessment_events": events.data,
            "count": len(events.data),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reassessment/summary")
async def get_reassessment_summary(
    user_id: str = Query(..., description="User UUID"),
):
    """
    Get summary of most recent reassessment data without running new reassessment.

    Aggregates last 14 days of data and shows:
    - Adherence stats
    - Weight change
    - Context averages (sleep, stress, soreness)
    - Day overrides applied

    Useful for showing user their progress before reassessment runs.
    """
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=14)

        aggregated = await reassessment_service.aggregate_data(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "summary": aggregated,
            "message": "14-day data summary",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Adjustment Approval Workflow (NEW - Sprint 4)
# ============================================================================


@router.get("/adjustments/pending")
async def get_pending_adjustments(
    user_id: str = Query(..., description="User UUID"),
):
    """
    Get all pending adjustments for user that need approval.

    Returns adjustments with status='pending' that haven't expired.
    Each adjustment includes the notification for display.

    Use case: Frontend polls this to show pending approval requests.
    """
    try:
        pending = await adjustment_approval_service.get_pending_adjustments(user_id)

        return {
            "pending_adjustments": pending,
            "count": len(pending),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/adjustments/{override_id}/approve")
async def approve_adjustment(
    override_id: str,
    req: ApproveAdjustmentRequest,
):
    """
    Approve a pending adjustment.

    Flow:
    1. Update day_override status to 'approved'
    2. Update notification (mark read, set action_taken)
    3. Create feedback record for ML learning
    4. Return updated override

    After approval, the adjustment will be applied to today's plan.
    """
    try:
        updated_override = await adjustment_approval_service.approve_adjustment(
            user_id=req.user_id,
            day_override_id=override_id,
            notes=req.notes,
        )

        return {
            "success": True,
            "message": "Adjustment approved successfully",
            "day_override": updated_override,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adjustments/{override_id}/reject")
async def reject_adjustment(
    override_id: str,
    req: RejectAdjustmentRequest,
):
    """
    Reject a pending adjustment.

    Flow:
    1. Update day_override status to 'rejected'
    2. Update notification
    3. Create feedback record for ML learning
    4. System learns from rejection to improve future suggestions

    User will see their original plan without the suggested adjustment.
    """
    try:
        updated_override = await adjustment_approval_service.reject_adjustment(
            user_id=req.user_id,
            day_override_id=override_id,
            reason=req.reason,
        )

        return {
            "success": True,
            "message": "Adjustment rejected successfully",
            "day_override": updated_override,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adjustments/{override_id}/undo")
async def undo_adjustment(
    override_id: str,
    req: UndoAdjustmentRequest,
):
    """
    Undo an approved or auto-applied adjustment.

    Flow:
    1. Check if within undo window (24 hours default)
    2. Update day_override status to 'undone'
    3. Mark as user_overridden
    4. Create feedback record
    5. Revert plan to original state

    This gives users a grace period to change their mind after approving.
    """
    try:
        updated_override = await adjustment_approval_service.undo_adjustment(
            user_id=req.user_id,
            day_override_id=override_id,
            reason=req.reason,
        )

        return {
            "success": True,
            "message": "Adjustment undone successfully",
            "day_override": updated_override,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences/adjustments")
async def get_adjustment_preferences(
    user_id: str = Query(..., description="User UUID"),
):
    """
    Get user's adjustment preferences.

    Returns per-trigger preferences (auto_apply | ask_me | disable) for:
    - Poor sleep
    - High stress
    - High soreness
    - Injury
    - Missed workout
    - Low/high adherence

    Plus global settings like grace period and undo window.
    """
    try:
        prefs = await adjustment_approval_service.get_user_preferences(user_id)

        return {
            "preferences": prefs.model_dump(),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/preferences/adjustments")
async def update_adjustment_preferences(
    user_id: str = Query(..., description="User UUID"),
    updates: UpdateAdjustmentPreferences = ...,
):
    """
    Update user's adjustment preferences.

    All fields are optional - only provided fields will be updated.

    Example:
    {
        "poor_sleep_training": "auto_apply",
        "high_stress_training": "ask_me",
        "injury_training": "ask_me",
        "auto_apply_grace_period_minutes": 60
    }
    """
    try:
        # Convert to dict and remove None values
        update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}

        if not update_dict:
            raise ValueError("No updates provided")

        updated_prefs = await adjustment_approval_service.update_user_preferences(
            user_id=user_id,
            updates=update_dict,
        )

        return {
            "success": True,
            "message": "Preferences updated successfully",
            "preferences": updated_prefs.model_dump(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Adherence Summary (NEW)
# ============================================================================


@router.get("/adherence/summary")
async def get_adherence_summary(
    user_id: str = Query(..., description="User UUID"),
    period: Literal["week", "month", "all_time"] = Query("week", description="Time period to analyze"),
):
    """
    Get comprehensive adherence summary for user.

    Calculates:
    - Overall adherence percentage (completed / planned)
    - Meal adherence vs training adherence (separate tracking)
    - Trends over time (comparing to previous period)
    - Consistency streaks (consecutive days with good adherence)
    - Most skipped items (identify patterns)

    Time periods:
    - week: Last 7 days
    - month: Last 30 days
    - all_time: Since program started

    Returns:
        Comprehensive adherence metrics with breakdown by category
    """
    try:
        db = SupabaseService()
        client = db.client

        # Determine date range
        end_date = date.today()
        if period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        else:  # all_time
            # Get program start date
            program = (
                client.table("programs")
                .select("program_start_date")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if program.data:
                start_date = date.fromisoformat(program.data[0]["program_start_date"])
            else:
                start_date = end_date - timedelta(days=30)  # Default to 30 days

        logger.info(
            "calculating_adherence_summary",
            user_id=user_id,
            period=period,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )

        # Fetch adherence records
        adherence_records = (
            client.table("adherence_records")
            .select("*")
            .eq("user_id", user_id)
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .execute()
        )

        records = adherence_records.data

        # Calculate overall adherence
        total_planned = len(records)
        completed = len([r for r in records if r["status"] == "completed"])
        similar = len([r for r in records if r["status"] == "similar"])
        skipped = len([r for r in records if r["status"] == "skipped"])

        overall_adherence = round((completed + similar) / total_planned * 100, 1) if total_planned > 0 else 0.0

        # Separate by type
        meal_records = [r for r in records if r["planned_entity_type"] == "meal"]
        training_records = [r for r in records if r["planned_entity_type"] == "session"]

        meal_completed = len([r for r in meal_records if r["status"] in ["completed", "similar"]])
        meal_adherence = round(meal_completed / len(meal_records) * 100, 1) if meal_records else 0.0

        training_completed = len([r for r in training_records if r["status"] in ["completed", "similar"]])
        training_adherence = round(training_completed / len(training_records) * 100, 1) if training_records else 0.0

        # Calculate trend (compare to previous period)
        if period == "week":
            prev_start = start_date - timedelta(days=7)
            prev_end = start_date
        elif period == "month":
            prev_start = start_date - timedelta(days=30)
            prev_end = start_date
        else:
            prev_start = None
            prev_end = None

        trend = None
        if prev_start and prev_end:
            prev_records = (
                client.table("adherence_records")
                .select("*")
                .eq("user_id", user_id)
                .gte("created_at", prev_start.isoformat())
                .lt("created_at", prev_end.isoformat())
                .execute()
            )

            prev_total = len(prev_records.data)
            prev_completed = len([r for r in prev_records.data if r["status"] in ["completed", "similar"]])
            prev_adherence = (prev_completed / prev_total * 100) if prev_total > 0 else 0.0

            trend = round(overall_adherence - prev_adherence, 1)

        # Calculate consistency streak (consecutive days with >80% adherence)
        # Group records by date
        from collections import defaultdict
        daily_adherence = defaultdict(lambda: {"completed": 0, "total": 0})

        for record in records:
            record_date = datetime.fromisoformat(record["created_at"]).date()
            daily_adherence[record_date]["total"] += 1
            if record["status"] in ["completed", "similar"]:
                daily_adherence[record_date]["completed"] += 1

        # Calculate streak
        current_streak = 0
        sorted_dates = sorted(daily_adherence.keys(), reverse=True)

        for day in sorted_dates:
            day_adherence = (daily_adherence[day]["completed"] / daily_adherence[day]["total"] * 100)
            if day_adherence >= 80:
                current_streak += 1
            else:
                break

        # Most skipped items (top 5)
        skipped_records = [r for r in records if r["status"] == "skipped"]
        skipped_by_entity = defaultdict(int)

        for record in skipped_records:
            entity_type = record["planned_entity_type"]
            entity_id = record["planned_entity_id"]
            skipped_by_entity[f"{entity_type}:{entity_id}"] += 1

        most_skipped = sorted(skipped_by_entity.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "overall": {
                "adherence_percentage": overall_adherence,
                "total_planned": total_planned,
                "completed": completed,
                "similar": similar,
                "skipped": skipped,
            },
            "by_category": {
                "meals": {
                    "adherence_percentage": meal_adherence,
                    "total_planned": len(meal_records),
                    "completed": meal_completed,
                    "skipped": len([r for r in meal_records if r["status"] == "skipped"]),
                },
                "training": {
                    "adherence_percentage": training_adherence,
                    "total_planned": len(training_records),
                    "completed": training_completed,
                    "skipped": len([r for r in training_records if r["status"] == "skipped"]),
                },
            },
            "trends": {
                "change_from_previous_period": trend,
                "direction": "improving" if trend and trend > 0 else "declining" if trend and trend < 0 else "stable",
            } if trend is not None else None,
            "streaks": {
                "current_streak_days": current_streak,
                "threshold_percentage": 80,
            },
            "patterns": {
                "most_skipped": [
                    {
                        "entity": entity.split(":")[0],
                        "count": count,
                    }
                    for entity, count in most_skipped
                ],
            },
        }

    except Exception as e:
        logger.error(
            "adherence_summary_failed",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
