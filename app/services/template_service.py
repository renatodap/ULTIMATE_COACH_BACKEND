"""
Activity Template Service

Handles CRUD operations for activity templates.
Templates are user-defined patterns for recurring workouts with auto-matching capability.
"""

import structlog
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, date
from fastapi import HTTPException, status

from app.services.supabase_service import SupabaseService

logger = structlog.get_logger()


class TemplateService:
    """
    Service for managing activity templates.

    Features:
    - CRUD operations for templates
    - Create from existing activity
    - Usage statistics and analytics
    - Template-activity relationship management
    """

    def __init__(self):
        self.db = SupabaseService()

    async def list_templates(
        self,
        user_id: UUID,
        activity_type: Optional[str] = None,
        is_active: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        List user's activity templates.

        Args:
            user_id: User UUID
            activity_type: Filter by activity type (optional)
            is_active: Show only active templates (default: True)
            limit: Max templates to return
            offset: Pagination offset

        Returns:
            Tuple of (templates list, total count)
        """
        try:
            logger.info(
                "listing_templates",
                user_id=str(user_id),
                activity_type=activity_type,
                is_active=is_active,
                limit=limit
            )

            # Build query
            query = self.db.supabase.table('activity_templates') \
                .select('*', count='exact') \
                .eq('user_id', str(user_id)) \
                .eq('is_active', is_active) \
                .order('use_count', desc=True) \
                .order('last_used_at', desc=True) \
                .range(offset, offset + limit - 1)

            # Apply activity type filter if provided
            if activity_type:
                query = query.eq('activity_type', activity_type)

            result = query.execute()

            templates = result.data
            total = result.count or 0

            logger.info(
                "templates_listed",
                user_id=str(user_id),
                count=len(templates),
                total=total
            )

            return templates, total

        except Exception as e:
            logger.error(
                "list_templates_failed",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch templates"
            )

    async def get_template(
        self,
        template_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get a single template by ID.

        Args:
            template_id: Template UUID
            user_id: User UUID (for ownership verification)

        Returns:
            Template dict

        Raises:
            HTTPException 404: Template not found
            HTTPException 403: Not authorized
        """
        try:
            logger.info(
                "fetching_template",
                template_id=str(template_id),
                user_id=str(user_id)
            )

            result = self.db.supabase.table('activity_templates') \
                .select('*') \
                .eq('id', str(template_id)) \
                .execute()

            if not result.data:
                logger.warning(
                    "template_not_found",
                    template_id=str(template_id),
                    user_id=str(user_id)
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Template not found"
                )

            template = result.data[0]

            # Verify ownership
            if template['user_id'] != str(user_id):
                logger.warning(
                    "template_access_denied",
                    template_id=str(template_id),
                    user_id=str(user_id),
                    owner_id=template['user_id']
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this template"
                )

            return template

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "fetch_template_failed",
                template_id=str(template_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch template"
            )

    async def create_template(
        self,
        user_id: UUID,
        template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new activity template.

        Args:
            user_id: User UUID
            template_data: Template fields

        Returns:
            Created template dict

        Raises:
            HTTPException 409: Template name already exists for user
        """
        try:
            logger.info(
                "creating_template",
                user_id=str(user_id),
                template_name=template_data.get('template_name')
            )

            # Check for duplicate name
            existing = self.db.supabase.table('activity_templates') \
                .select('id') \
                .eq('user_id', str(user_id)) \
                .eq('template_name', template_data['template_name']) \
                .eq('is_active', True) \
                .execute()

            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Template '{template_data['template_name']}' already exists"
                )

            # Add user_id
            template_data['user_id'] = str(user_id)

            # Insert template
            result = self.db.supabase.table('activity_templates') \
                .insert(template_data) \
                .execute()

            if not result.data:
                raise Exception("Failed to insert template")

            template = result.data[0]

            logger.info(
                "template_created",
                template_id=template['id'],
                user_id=str(user_id)
            )

            return template

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "create_template_failed",
                user_id=str(user_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create template"
            )

    async def create_from_activity(
        self,
        user_id: UUID,
        activity_id: UUID,
        template_name: str,
        auto_match_enabled: bool = True,
        require_gps_match: bool = False
    ) -> Dict[str, Any]:
        """
        Create template from existing activity.

        Auto-populates expected values from activity data.

        Args:
            user_id: User UUID
            activity_id: Activity UUID to copy from
            template_name: Name for the new template
            auto_match_enabled: Enable auto-matching
            require_gps_match: Require GPS route match

        Returns:
            Created template dict
        """
        try:
            logger.info(
                "creating_template_from_activity",
                user_id=str(user_id),
                activity_id=str(activity_id),
                template_name=template_name
            )

            # Fetch source activity
            activity_result = self.db.supabase.table('activities') \
                .select('*') \
                .eq('id', str(activity_id)) \
                .eq('user_id', str(user_id)) \
                .is_('deleted_at', 'null') \
                .execute()

            if not activity_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Activity not found"
                )

            activity = activity_result.data[0]

            # Build template from activity data
            template_data = {
                'template_name': template_name,
                'activity_type': activity['activity_type'],
                'description': f"Created from activity on {activity['start_time'][:10]}",
                'icon': self._get_default_icon(activity['activity_type']),

                # Expected ranges from activity
                'expected_distance_m': activity.get('distance_meters'),
                'expected_duration_minutes': activity.get('duration_minutes'),

                # Copy pre-filled data
                'default_exercises': activity.get('exercises', []),
                'default_metrics': activity.get('metrics', {}),
                'default_notes': activity.get('notes'),

                # Auto-matching config
                'auto_match_enabled': auto_match_enabled,
                'require_gps_match': require_gps_match,

                # Time-based matching from activity
                'typical_start_time': datetime.fromisoformat(activity['start_time']).time().isoformat(),

                # Reference
                'created_from_activity_id': str(activity_id)
            }

            # Create template
            template = await self.create_template(user_id, template_data)

            logger.info(
                "template_created_from_activity",
                template_id=template['id'],
                activity_id=str(activity_id)
            )

            return template

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "create_from_activity_failed",
                user_id=str(user_id),
                activity_id=str(activity_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create template from activity"
            )

    async def update_template(
        self,
        template_id: UUID,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing template.

        Args:
            template_id: Template UUID
            user_id: User UUID (for ownership verification)
            updates: Fields to update

        Returns:
            Updated template dict

        Raises:
            HTTPException 404: Template not found
            HTTPException 403: Not authorized
            HTTPException 409: Template name conflict
        """
        try:
            # Verify ownership
            existing = await self.get_template(template_id, user_id)

            # Check for name conflict if name is being updated
            if 'template_name' in updates and updates['template_name'] != existing['template_name']:
                conflict = self.db.supabase.table('activity_templates') \
                    .select('id') \
                    .eq('user_id', str(user_id)) \
                    .eq('template_name', updates['template_name']) \
                    .eq('is_active', True) \
                    .neq('id', str(template_id)) \
                    .execute()

                if conflict.data:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Template '{updates['template_name']}' already exists"
                    )

            # Add updated_at
            updates['updated_at'] = datetime.utcnow().isoformat()

            logger.info(
                "updating_template",
                template_id=str(template_id),
                user_id=str(user_id),
                fields=list(updates.keys())
            )

            # Update template
            result = self.db.supabase.table('activity_templates') \
                .update(updates) \
                .eq('id', str(template_id)) \
                .execute()

            if not result.data:
                raise Exception("Failed to update template")

            template = result.data[0]

            logger.info(
                "template_updated",
                template_id=str(template_id),
                user_id=str(user_id)
            )

            return template

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "update_template_failed",
                template_id=str(template_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update template"
            )

    async def delete_template(
        self,
        template_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a template (soft delete by setting is_active=false).

        Args:
            template_id: Template UUID
            user_id: User UUID (for ownership verification)

        Returns:
            True if deleted successfully

        Raises:
            HTTPException 404: Template not found
            HTTPException 403: Not authorized
        """
        try:
            # Verify ownership
            await self.get_template(template_id, user_id)

            logger.info(
                "deleting_template",
                template_id=str(template_id),
                user_id=str(user_id)
            )

            # Soft delete
            result = self.db.supabase.table('activity_templates') \
                .update({
                    'is_active': False,
                    'updated_at': datetime.utcnow().isoformat()
                }) \
                .eq('id', str(template_id)) \
                .execute()

            success = bool(result.data)

            if success:
                logger.info(
                    "template_deleted",
                    template_id=str(template_id),
                    user_id=str(user_id)
                )
            else:
                logger.warning(
                    "template_delete_failed",
                    template_id=str(template_id),
                    user_id=str(user_id)
                )

            return success

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "delete_template_failed",
                template_id=str(template_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete template"
            )

    async def get_template_stats(
        self,
        template_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Calculate usage statistics for template.

        Returns aggregated metrics from all activities using this template.

        Args:
            template_id: Template UUID
            user_id: User UUID (for ownership verification)

        Returns:
            Stats dict with aggregated metrics
        """
        try:
            # Verify ownership
            template = await self.get_template(template_id, user_id)

            logger.info(
                "calculating_template_stats",
                template_id=str(template_id)
            )

            # Get all activities using this template
            activities_result = self.db.supabase.table('activities') \
                .select('*') \
                .eq('template_id', str(template_id)) \
                .eq('user_id', str(user_id)) \
                .is_('deleted_at', 'null') \
                .order('start_time', desc=False) \
                .execute()

            activities = activities_result.data

            if not activities:
                return {
                    'template_id': str(template_id),
                    'total_uses': 0,
                    'avg_duration_minutes': None,
                    'avg_distance_m': None,
                    'avg_calories': None,
                    'trend_pace_percent': None,
                    'trend_consistency_score': None,
                    'best_activity_id': None,
                    'best_performance_date': None,
                    'best_performance_metric': None,
                    'first_used': None,
                    'last_used': None,
                    'days_since_last_use': None
                }

            # Calculate aggregates
            total_uses = len(activities)
            avg_duration = sum(a['duration_minutes'] for a in activities) / total_uses

            # Distance average (if applicable)
            distances = [a['distance_meters'] for a in activities if a.get('distance_meters')]
            avg_distance = sum(distances) / len(distances) if distances else None

            # Calories average
            avg_calories = sum(a.get('calories', 0) for a in activities) / total_uses

            # Find best performance (fastest pace if distance activity)
            best_activity = None
            best_metric = None
            if distances:
                # Calculate pace for each
                paced_activities = [
                    (a, a['duration_minutes'] / (a['distance_meters'] / 1000))
                    for a in activities if a.get('distance_meters')
                ]
                if paced_activities:
                    best_activity, best_pace = min(paced_activities, key=lambda x: x[1])
                    best_metric = f"Fastest pace: {int(best_pace)}:{int((best_pace % 1) * 60):02d}/km"

            # Pace trend (compare last 5 vs first 5)
            trend_pace = None
            if len(distances) >= 10:
                first_5_pace = sum(
                    a['duration_minutes'] / (a['distance_meters'] / 1000)
                    for a in activities[:5] if a.get('distance_meters')
                ) / 5
                last_5_pace = sum(
                    a['duration_minutes'] / (a['distance_meters'] / 1000)
                    for a in activities[-5:] if a.get('distance_meters')
                ) / 5
                trend_pace = ((last_5_pace - first_5_pace) / first_5_pace) * 100

            # Consistency score (how regular)
            first_date = datetime.fromisoformat(activities[0]['start_time'])
            last_date = datetime.fromisoformat(activities[-1]['start_time'])
            days_span = (last_date - first_date).days
            consistency = (total_uses / (days_span / 7)) if days_span > 0 else 0
            consistency_score = min(100, consistency * 50)  # 2x per week = 100 score

            # Days since last use
            days_since = (datetime.utcnow() - last_date).days

            return {
                'template_id': str(template_id),
                'total_uses': total_uses,
                'avg_duration_minutes': round(avg_duration, 1),
                'avg_distance_m': round(avg_distance, 1) if avg_distance else None,
                'avg_calories': round(avg_calories, 1),
                'trend_pace_percent': round(trend_pace, 1) if trend_pace else None,
                'trend_consistency_score': round(consistency_score, 1),
                'best_activity_id': best_activity['id'] if best_activity else None,
                'best_performance_date': best_activity['start_time'] if best_activity else None,
                'best_performance_metric': best_metric,
                'first_used': activities[0]['start_time'],
                'last_used': activities[-1]['start_time'],
                'days_since_last_use': days_since
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "template_stats_failed",
                template_id=str(template_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to calculate template stats"
            )

    async def get_template_activities(
        self,
        template_id: UUID,
        user_id: UUID,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get all activities that used this template.

        Args:
            template_id: Template UUID
            user_id: User UUID (for ownership verification)
            limit: Max activities to return

        Returns:
            List of activity dicts
        """
        try:
            # Verify ownership
            await self.get_template(template_id, user_id)

            logger.info(
                "fetching_template_activities",
                template_id=str(template_id),
                limit=limit
            )

            result = self.db.supabase.table('activities') \
                .select('*') \
                .eq('template_id', str(template_id)) \
                .eq('user_id', str(user_id)) \
                .is_('deleted_at', 'null') \
                .order('start_time', desc=True) \
                .limit(limit) \
                .execute()

            activities = result.data

            logger.info(
                "template_activities_fetched",
                template_id=str(template_id),
                count=len(activities)
            )

            return activities

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "fetch_template_activities_failed",
                template_id=str(template_id),
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch template activities"
            )

    def _get_default_icon(self, activity_type: str) -> str:
        """Get default emoji icon for activity type."""
        icons = {
            'running': '🏃',
            'cycling': '🚴',
            'swimming': '🏊',
            'strength_training': '💪',
            'yoga': '🧘',
            'walking': '🚶',
            'hiking': '🥾',
            'sports': '⚽',
            'flexibility': '🤸',
            'cardio_steady_state': '🏃',
            'cardio_interval': '⚡',
            'other': '🏋️'
        }
        return icons.get(activity_type, '🏋️')


# Global singleton instance
template_service = TemplateService()
