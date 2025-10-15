"""
Adherence Service

Records user-marked adherence for planned sessions/meals and updates calendar status.

User determines: completed | similar | skipped. Optionally links an actual activity/meal.
"""

from typing import Optional, Literal, Dict, Any
import structlog
from app.services.supabase_service import SupabaseService

logger = structlog.get_logger()

Status = Literal['completed','similar','skipped']


class AdherenceService:
    def __init__(self, db: Optional[SupabaseService] = None) -> None:
        self.db = db or SupabaseService()

    def set_adherence(
        self,
        user_id: str,
        planned_entity_type: Literal['session','meal'],
        planned_entity_id: str,
        status: Status,
        actual_ref_type: Optional[Literal['activity','meal']] = None,
        actual_ref_id: Optional[str] = None,
        adherence_json: Optional[Dict[str, Any]] = None,
        similarity_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create an adherence record and update calendar event status.
        """
        client = self.db.client

        rec = {
            "user_id": user_id,
            "planned_entity_type": planned_entity_type,
            "planned_entity_id": planned_entity_id,
            "status": status,
            "similarity_score": similarity_score,
            "adherence_json": adherence_json or {},
            "actual_ref_type": actual_ref_type,
            "actual_ref_id": actual_ref_id,
        }
        ar = client.table("adherence_records").insert(rec).execute()
        record = ar.data[0]

        # Update calendar event status for this ref
        event_type = 'training' if planned_entity_type == 'session' else 'meal'
        # Assuming unique event per ref_id per day; set latest matching to status
        client.table("calendar_events").update({"status": status}) \
            .eq("ref_table", 'session_instances' if planned_entity_type=='session' else 'meal_instances') \
            .eq("ref_id", planned_entity_id).execute()

        # Optionally update planned instance state
        if planned_entity_type == 'session':
            new_state = 'completed' if status == 'completed' else ('modified' if status == 'similar' else 'skipped')
            client.table("session_instances").update({"state": new_state}).eq("id", planned_entity_id).execute()

        return record

