"""
Plan Logs Attachment API (separate folder)

Endpoints to link already-logged activities/meals to planned instances.
Keeps separation from existing Activities/Meals endpoints.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.supabase_service import SupabaseService
from app.services.activity_service import activity_service
from app.services.nutrition_service import nutrition_service
from app.models.activities import CreateActivityRequest
from app.models.nutrition import CreateMealRequest
from app.services.adherence_service import AdherenceService


router = APIRouter()


class AttachActivityRequest(BaseModel):
    user_id: str = Field(...)
    activity_id: str = Field(...)
    planned_session_instance_id: str = Field(...)
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)


@router.post("/attach_activity")
async def attach_activity(req: AttachActivityRequest):
    db = SupabaseService()
    client = db.client
    try:
        # Validate ownership (RLS also enforces it)
        act = (
            client.table("activities").select("id, user_id").eq("id", req.activity_id).single().execute()
        ).data
        if not act or act.get("user_id") != req.user_id:
            raise HTTPException(status_code=404, detail="Activity not found for user")

        upd = {
            "planned_session_instance_id": req.planned_session_instance_id,
        }
        if req.similarity_score is not None:
            upd["similarity_score"] = req.similarity_score

        res = client.table("activities").update(upd).eq("id", req.activity_id).execute()
        return {"updated": True, "activity": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class AttachMealRequest(BaseModel):
    user_id: str = Field(...)
    meal_id: str = Field(...)
    planned_meal_instance_id: str = Field(...)
    adherence_json: Optional[Dict[str, Any]] = None


@router.post("/attach_meal")
async def attach_meal(req: AttachMealRequest):
    db = SupabaseService()
    client = db.client
    try:
        meal = (
            client.table("meals").select("id, user_id").eq("id", req.meal_id).single().execute()
        ).data
        if not meal or meal.get("user_id") != req.user_id:
            raise HTTPException(status_code=404, detail="Meal not found for user")

        upd = {
            "planned_meal_instance_id": req.planned_meal_instance_id,
        }
        if req.adherence_json is not None:
            upd["adherence_json"] = req.adherence_json

        res = client.table("meals").update(upd).eq("id", req.meal_id).execute()
        return {"updated": True, "meal": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class LogAndAttachActivityRequest(CreateActivityRequest):
    user_id: str = Field(...)
    planned_session_instance_id: str = Field(...)
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    status: Optional[str] = Field(None, description="completed|similar|skipped")
    adherence_json: Optional[Dict[str, Any]] = None


@router.post("/log_and_attach_activity")
async def log_and_attach_activity(req: LogAndAttachActivityRequest):
    db = SupabaseService()
    client = db.client
    try:
        # Create the activity via service
        act = await activity_service.create_activity(
            user_id=req.user_id,
            category=req.category,
            activity_name=req.activity_name,
            start_time=req.start_time,
            end_time=req.end_time,
            duration_minutes=req.duration_minutes,
            calories_burned=req.calories_burned,
            intensity_mets=req.intensity_mets,
            metrics=req.metrics,
            notes=req.notes,
        )
        # Attach to planned session
        upd = {"planned_session_instance_id": req.planned_session_instance_id}
        if req.similarity_score is not None:
            upd["similarity_score"] = req.similarity_score
        client.table("activities").update(upd).eq("id", act["id"]).execute()
        # Optionally mark adherence in one shot
        if req.status in ("completed", "similar", "skipped"):
            adh = AdherenceService()
            adh_rec = adh.set_adherence(
                user_id=req.user_id,
                planned_entity_type="session",
                planned_entity_id=req.planned_session_instance_id,
                status=req.status,  # type: ignore[arg-type]
                actual_ref_type="activity",
                actual_ref_id=act["id"],
                adherence_json=req.adherence_json,
                similarity_score=req.similarity_score,
            )
            return {"activity": act, "attached": True, "adherence": adh_rec}
        return {"activity": act, "attached": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class LogAndAttachMealRequest(CreateMealRequest):
    user_id: str = Field(...)
    planned_meal_instance_id: str = Field(...)
    adherence_json: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, description="completed|similar|skipped")


@router.post("/log_and_attach_meal")
async def log_and_attach_meal(req: LogAndAttachMealRequest):
    db = SupabaseService()
    client = db.client
    try:
        meal = await nutrition_service.create_meal(
            user_id=req.user_id,
            name=req.name,
            meal_type=req.meal_type,
            logged_at=req.logged_at,
            notes=req.notes,
            items=req.items,
            source=req.source,
            ai_confidence=req.ai_confidence,
        )
        upd = {"planned_meal_instance_id": req.planned_meal_instance_id}
        if req.adherence_json is not None:
            upd["adherence_json"] = req.adherence_json
        client.table("meals").update(upd).eq("id", str(meal.id)).execute()
        # Optionally mark adherence in one shot
        if req.status in ("completed", "similar", "skipped"):
            adh = AdherenceService()
            adh_rec = adh.set_adherence(
                user_id=req.user_id,
                planned_entity_type="meal",
                planned_entity_id=req.planned_meal_instance_id,
                status=req.status,  # type: ignore[arg-type]
                actual_ref_type="meal",
                actual_ref_id=str(meal.id),
                adherence_json=req.adherence_json,
                similarity_score=None,
            )
            return {"meal": meal.model_dump(), "attached": True, "adherence": adh_rec}
        return {"meal": meal.model_dump(), "attached": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
