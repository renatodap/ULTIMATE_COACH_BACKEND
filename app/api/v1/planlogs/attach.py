"""
Plan Logs Attachment API (separate folder)

Endpoints to link already-logged activities/meals to planned instances.
Keeps separation from existing Activities/Meals endpoints.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.supabase_service import SupabaseService


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

