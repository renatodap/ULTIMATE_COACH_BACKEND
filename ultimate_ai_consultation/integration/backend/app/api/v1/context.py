"""
Context API endpoints.

Provides access to user context logs, informal activities, and context timeline.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import os
from supabase import create_client, Client

from app.models.context import (
    ContextLog,
    ContextSummary,
    MessageContextResult
)

router = APIRouter()

# Initialize Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)


@router.get("/timeline/{user_id}", response_model=dict)
async def get_context_timeline(
    user_id: UUID,
    days_back: int = Query(14, ge=1, le=90, description="Number of days to look back")
):
    """
    Get user's context timeline for a period.

    Returns all context events (stress, travel, injury, informal activities)
    along with summary statistics.
    """

    try:
        # Calculate start date
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        # Get context logs
        result = supabase.table("user_context_log")\
            .select("*")\
            .eq("user_id", str(user_id))\
            .gte("created_at", start_date)\
            .order("created_at", desc=True)\
            .execute()

        # Get aggregated summary using SQL function
        summary_result = supabase.rpc(
            "get_user_context_for_period",
            {"p_user_id": str(user_id), "p_days_back": days_back}
        ).execute()

        # Build period summary
        period_summary = {}
        if summary_result.data:
            for item in summary_result.data:
                period_summary[item["context_type"]] = {
                    "count": item["count"],
                    "avg_severity": item["avg_severity"],
                    "avg_sentiment": item["avg_sentiment"]
                }

        return {
            "context_logs": result.data if result.data else [],
            "period_summary": period_summary,
            "total_events": len(result.data) if result.data else 0,
            "period_days": days_back
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching context timeline: {str(e)}")


@router.get("/informal-activities/{user_id}")
async def get_informal_activities(
    user_id: UUID,
    days_back: int = Query(14, ge=1, le=90)
):
    """
    Get informal activities extracted from coach chat.

    These are activities that were auto-detected (e.g., "played tennis").
    """

    try:
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        # Get activities with source='coach_chat' and informal_log=true
        result = supabase.table("activities")\
            .select("*")\
            .eq("user_id", str(user_id))\
            .eq("source", "coach_chat")\
            .gte("start_time", start_date)\
            .order("start_time", desc=True)\
            .execute()

        # Filter for informal logs
        informal_activities = [
            activity for activity in (result.data or [])
            if activity.get("metrics", {}).get("informal_log")
        ]

        return {
            "activities": informal_activities,
            "total": len(informal_activities),
            "period_days": days_back
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching informal activities: {str(e)}")


@router.get("/summary/{user_id}")
async def get_context_summary(
    user_id: UUID,
    days_back: int = Query(14, ge=1, le=90)
):
    """
    Get a high-level summary of user's context.

    Returns counts and flags for different context types.
    """

    try:
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        # Get all context for period
        result = supabase.table("user_context_log")\
            .select("context_type, severity, affects_training")\
            .eq("user_id", str(user_id))\
            .gte("created_at", start_date)\
            .execute()

        context_data = result.data if result.data else []

        # Aggregate by type
        summary = {
            "total_events": len(context_data),
            "stress_events": len([c for c in context_data if c["context_type"] == "stress"]),
            "high_stress_events": len([c for c in context_data if c["context_type"] == "stress" and c.get("severity") == "high"]),
            "travel_events": len([c for c in context_data if c["context_type"] == "travel"]),
            "injury_events": len([c for c in context_data if c["context_type"] in ["injury", "illness"]]),
            "informal_activities": len([c for c in context_data if c["context_type"] == "informal_activity"]),
            "events_affecting_training": len([c for c in context_data if c.get("affects_training")]),
            "period_days": days_back
        }

        # Determine if context is significant
        summary["significant_context"] = (
            summary["high_stress_events"] > 3 or
            summary["travel_events"] > 0 or
            summary["injury_events"] > 0
        )

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching context summary: {str(e)}")


@router.post("/log")
async def log_context_manually(
    user_id: UUID,
    context_type: str,
    description: str,
    severity: Optional[str] = None,
    affects_training: bool = False,
    affects_nutrition: bool = False
):
    """
    Manually log a context event.

    Allows users to explicitly log life events that might affect their program.
    """

    try:
        # Validate context_type
        valid_types = ["stress", "energy", "sleep", "travel", "injury", "illness", "motivation", "life_event"]
        if context_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid context_type. Must be one of: {valid_types}")

        # Validate severity if provided
        if severity and severity not in ["low", "moderate", "high"]:
            raise HTTPException(status_code=400, detail="Severity must be: low, moderate, or high")

        # Insert into context log
        result = supabase.table("user_context_log").insert({
            "user_id": str(user_id),
            "context_type": context_type,
            "severity": severity,
            "description": description,
            "affects_training": affects_training,
            "affects_nutrition": affects_nutrition,
            "extraction_confidence": 1.0,  # Manually logged = 100% confidence
            "extraction_model": "manual_entry"
        }).execute()

        return {
            "success": True,
            "context_id": result.data[0]["id"] if result.data else None,
            "message": "Context logged successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging context: {str(e)}")


@router.get("/affects-training/{user_id}")
async def get_training_affecting_context(
    user_id: UUID,
    days_back: int = Query(14, ge=1, le=90)
):
    """
    Get only context that affects training.

    Useful for reassessment logic to quickly check if adjustments are needed.
    """

    try:
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        result = supabase.table("user_context_log")\
            .select("*")\
            .eq("user_id", str(user_id))\
            .eq("affects_training", True)\
            .gte("created_at", start_date)\
            .order("created_at", desc=True)\
            .execute()

        return {
            "context_logs": result.data if result.data else [],
            "total": len(result.data) if result.data else 0,
            "period_days": days_back
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching training context: {str(e)}")


@router.delete("/{context_id}")
async def delete_context_log(
    context_id: UUID,
    user_id: UUID = Query(..., description="User ID for authorization")
):
    """
    Delete a context log entry.

    User can remove context entries they logged incorrectly.
    """

    try:
        # Verify ownership
        check = supabase.table("user_context_log")\
            .select("id")\
            .eq("id", str(context_id))\
            .eq("user_id", str(user_id))\
            .execute()

        if not check.data:
            raise HTTPException(status_code=404, detail="Context log not found or unauthorized")

        # Delete
        supabase.table("user_context_log")\
            .delete()\
            .eq("id", str(context_id))\
            .execute()

        return {"success": True, "message": "Context log deleted"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting context: {str(e)}")
