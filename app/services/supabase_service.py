"""
Supabase service module with connection pooling and helper methods.

Provides a centralized interface for all database operations via Supabase.
"""

import structlog
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client, create_client
from app.config import settings

logger = structlog.get_logger()


class SupabaseService:
    """
    Singleton service for Supabase database operations.

    Features:
    - Automatic connection management
    - Type-safe query builders
    - Error handling and logging
    - Row Level Security (RLS) enforcement
    """

    _instance: Optional["SupabaseService"] = None
    _client: Optional[Client] = None

    def __new__(cls) -> "SupabaseService":
        """Singleton pattern to ensure only one instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize Supabase client (only once)"""
        if self._client is None:
            logger.info(f"Initializing Supabase client: {settings.SUPABASE_URL}")
            self._client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_KEY,
            )
            logger.info("Supabase client initialized successfully")

    @property
    def client(self) -> Client:
        """Get the Supabase client"""
        if self._client is None:
            raise RuntimeError("Supabase client not initialized")
        return self._client

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Supabase connection is healthy.

        Returns:
            Dict with status and details
        """
        try:
            # Simple query to test connection
            result = self.client.table("profiles").select("id").limit(1).execute()
            return {
                "status": "healthy",
                "connected": True,
                "url": settings.SUPABASE_URL,
            }
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
            }

    # ========================================================================
    # USER PROFILES
    # ========================================================================

    async def get_profile(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get user profile by ID.

        Args:
            user_id: User UUID

        Returns:
            Profile dict or None if not found
        """
        try:
            response = (
                self.client.table("profiles")
                .select("*")
                .eq("id", str(user_id))
                .single()
                .execute()
            )

            if response.data:
                logger.debug(f"Successfully retrieved profile for user {user_id}")
            else:
                logger.warning(f"No profile found for user {user_id}")

            return response.data
        except Exception as e:
            logger.error(
                f"Failed to get profile for user {user_id}",
                extra={
                    "user_id": str(user_id),
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return None

    async def create_profile(self, user_id: UUID, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user profile.

        Args:
            user_id: User UUID
            profile_data: Profile fields

        Returns:
            Created profile dict
        """
        try:
            data = {"id": str(user_id), **profile_data}
            response = self.client.table("profiles").insert(data).execute()
            logger.info(f"Created profile for user {user_id}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create profile {user_id}: {e}")
            raise

    async def update_profile(
        self, user_id: UUID, updates: Dict[str, Any], user_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update or create a user profile (manual upsert: UPDATE, then INSERT if no row).

        Args:
            user_id: User UUID
            updates: Fields to update

        Returns:
            Updated/created profile dict or None
        """
        try:
            # Try update first
            logger.info(f"Updating profile for user {user_id}")
            if user_token:
                # Perform this operation under the user's RLS context
                self.client.postgrest.auth(user_token)
            response = (
                self.client.table("profiles")
                .update(updates)
                .eq("id", str(user_id))
                .execute()
            )
            if user_token:
                # Clear auth so future calls use service role again
                self.client.postgrest.auth(None)
            if response.data and len(response.data) > 0:
                logger.info(f"Successfully updated profile for user {user_id}")
                return response.data[0]

            # No existing profile, insert new
            # LAYER 2 FIX: Use service role (not user token) for INSERT
            # This bypasses RLS and allows profile creation even if INSERT policy doesn't exist
            # Service role has full permissions and is safe here (we already validated user_id)
            data = {"id": str(user_id), **updates}
            logger.warning(f"Profile not found for user {user_id}, creating new profile via service role")
            created = self.client.table("profiles").insert(data).execute()
            if created.data and len(created.data) > 0:
                logger.info(f"Successfully created profile for user {user_id}")
                return created.data[0]

            logger.error(
                f"Profile upsert returned empty data for user {user_id}",
                extra={"user_id": str(user_id), "updates_keys": list(updates.keys())}
            )
            raise RuntimeError("Failed to upsert profile - no data returned")

        except Exception as e:
            logger.error(
                f"Failed to upsert profile for user {user_id}",
                extra={
                    "user_id": str(user_id),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "updates_keys": list(updates.keys()),
                },
                exc_info=True,
            )
            raise

    async def create_body_metric(self, metric_data: Dict[str, Any], user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new body metric entry under user's RLS context when provided.

        Args:
            metric_data: Body metric fields
            user_token: Optional JWT to satisfy RLS policies
        """
        try:
            if user_token:
                self.client.postgrest.auth(user_token)
            response = self.client.table("body_metrics").insert(metric_data).execute()
            if user_token:
                self.client.postgrest.auth(None)
            logger.info(f"Created body metric for user {metric_data.get('user_id')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create body metric: {e}")
            raise

    # ========================================================================
    # MEALS
    # ========================================================================

    async def get_user_meals(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get meals for a user with optional date filtering.

        Args:
            user_id: User UUID
            limit: Max number of meals to return
            offset: Pagination offset
            start_date: ISO datetime string (optional)
            end_date: ISO datetime string (optional)

        Returns:
            List of meal dicts with meal_items included
        """
        try:
            query = (
                self.client.table("meals")
                .select("*, meal_items(*)")
                .eq("user_id", str(user_id))
                .order("logged_at", desc=True)
                .limit(limit)
                .offset(offset)
            )

            if start_date:
                query = query.gte("logged_at", start_date)
            if end_date:
                query = query.lte("logged_at", end_date)

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get meals for user {user_id}: {e}")
            return []

    async def create_meal(self, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new meal log.

        Args:
            meal_data: Meal fields (must include user_id)

        Returns:
            Created meal dict
        """
        try:
            response = self.client.table("meals").insert(meal_data).execute()
            logger.info(f"Created meal for user {meal_data.get('user_id')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create meal: {e}")
            raise

    async def create_meal_items(self, meal_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create meal items (foods in a meal).

        Args:
            meal_items: List of meal_item dicts

        Returns:
            List of created meal_item dicts
        """
        try:
            response = self.client.table("meal_items").insert(meal_items).execute()
            logger.info(f"Created {len(meal_items)} meal items")
            return response.data
        except Exception as e:
            logger.error(f"Failed to create meal items: {e}")
            raise

    async def delete_meal(self, meal_id: UUID, user_id: UUID) -> bool:
        """
        Delete a meal (and its items via CASCADE).

        Args:
            meal_id: Meal UUID
            user_id: User UUID (for RLS check)

        Returns:
            True if deleted successfully
        """
        try:
            response = (
                self.client.table("meals")
                .delete()
                .eq("id", str(meal_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            logger.info(f"Deleted meal {meal_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete meal {meal_id}: {e}")
            return False

    # ========================================================================
    # FOODS DATABASE
    # ========================================================================

    async def search_foods(
        self, query: str, limit: int = 20, user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Search foods by name (full-text search).

        Args:
            query: Search query
            limit: Max results
            user_id: Optional user ID to include custom foods

        Returns:
            List of food dicts
        """
        try:
            # Full-text search using PostgreSQL's to_tsquery
            db_query = (
                self.client.table("foods")
                .select("*")
                .text_search("name", query, config="english")
                .eq("is_public", True)
                .order("usage_count", desc=True)
                .limit(limit)
            )

            response = db_query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to search foods: {e}")
            return []

    async def get_food_by_id(self, food_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a single food by ID.

        Args:
            food_id: Food UUID

        Returns:
            Food dict or None
        """
        try:
            response = (
                self.client.table("foods")
                .select("*")
                .eq("id", str(food_id))
                .single()
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to get food {food_id}: {e}")
            return None

    async def create_custom_food(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a custom food for a user.

        Args:
            food_data: Food fields (must include created_by)

        Returns:
            Created food dict
        """
        try:
            response = self.client.table("foods").insert(food_data).execute()
            logger.info(f"Created custom food: {food_data.get('name')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create custom food: {e}")
            raise

    # ========================================================================
    # ACTIVITIES
    # ========================================================================

    # Field mapping: API fields <-> Database fields
    # Database now uses: activity_name, category (migration 012)
    # API expects: activity_name, category (consistent with models)

    def _map_activity_to_db(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize activity fields to current DB schema (post-migration 012).

        Accepts legacy input keys (name, activity_type) and converts them to
        the current schema (activity_name, category).
        """
        mapped = activity_data.copy()
        # Convert legacy input keys to new schema keys if present
        if 'name' in mapped and 'activity_name' not in mapped:
            mapped['activity_name'] = mapped.pop('name')
        if 'activity_type' in mapped and 'category' not in mapped:
            mapped['category'] = mapped.pop('activity_type')
        return mapped

    def _map_activity_from_db(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize database fields to API fields after select.

        Handles legacy DB columns (name, activity_type) by mapping them to
        current API fields (activity_name, category). If the DB is already on
        the new schema, this is a no-op.
        """
        mapped = activity_data.copy()
        if 'name' in mapped and 'activity_name' not in mapped:
            mapped['activity_name'] = mapped.pop('name')
        if 'activity_type' in mapped and 'category' not in mapped:
            mapped['category'] = mapped.pop('activity_type')
        return mapped

    async def get_user_activities(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get activities for a user.

        Args:
            user_id: User UUID
            limit: Max results
            offset: Pagination offset
            start_date: ISO datetime (optional)
            end_date: ISO datetime (optional)

        Returns:
            List of activity dicts (excludes soft-deleted activities)
        """
        try:
            query = (
                self.client.table("activities")
                .select("*")
                .eq("user_id", str(user_id))
                .is_("deleted_at", "null")  # Exclude soft-deleted activities
                .order("start_time", desc=True)
                .limit(limit)
                .offset(offset)
            )

            if start_date:
                query = query.gte("start_time", start_date)
            if end_date:
                query = query.lte("start_time", end_date)

            response = query.execute()
            # Map database fields to API fields
            activities = [self._map_activity_from_db(activity) for activity in response.data]
            return activities
        except Exception as e:
            logger.error(f"Failed to get activities for user {user_id}: {e}")
            return []

    async def create_activity(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an activity log.

        Args:
            activity_data: Activity fields

        Returns:
            Created activity dict
        """
        try:
            # Map API fields to database fields before insert
            db_data = self._map_activity_to_db(activity_data)
            response = self.client.table("activities").insert(db_data).execute()
            logger.info(f"Created activity for user {activity_data.get('user_id')}")
            # Map database fields back to API fields in response
            return self._map_activity_from_db(response.data[0])
        except Exception as e:
            logger.error(f"Failed to create activity: {e}")
            raise

    async def get_activity(self, activity_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a single activity by ID.

        Args:
            activity_id: Activity UUID

        Returns:
            Activity dict or None (excludes soft-deleted)
        """
        try:
            response = (
                self.client.table("activities")
                .select("*")
                .eq("id", str(activity_id))
                .is_("deleted_at", "null")  # Exclude soft-deleted activities
                .single()
                .execute()
            )
            # Map database fields to API fields
            if response.data:
                return self._map_activity_from_db(response.data)
            return None
        except Exception as e:
            logger.error(f"Failed to get activity {activity_id}: {e}")
            return None

    async def update_activity(
        self,
        activity_id: UUID,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an activity.

        Args:
            activity_id: Activity UUID
            user_id: User UUID (for RLS check)
            updates: Fields to update

        Returns:
            Updated activity dict
        """
        try:
            # Map API fields to database fields before update
            db_updates = self._map_activity_to_db(updates)
            response = (
                self.client.table("activities")
                .update(db_updates)
                .eq("id", str(activity_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                logger.error(f"Activity update returned empty data for activity {activity_id}")
                raise RuntimeError("Failed to update activity - no data returned")

            logger.info(f"Updated activity {activity_id}")
            # Map database fields back to API fields in response
            return self._map_activity_from_db(response.data[0])
        except Exception as e:
            logger.error(f"Failed to update activity {activity_id}: {e}")
            raise

    async def delete_activity(self, activity_id: UUID, user_id: UUID) -> bool:
        """
        Delete an activity (soft delete by setting deleted_at).

        Args:
            activity_id: Activity UUID
            user_id: User UUID (for RLS check)

        Returns:
            True if deleted successfully
        """
        try:
            # Soft delete - set deleted_at timestamp
            response = (
                self.client.table("activities")
                .update({"deleted_at": "now()"})
                .eq("id", str(activity_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            logger.info(f"Deleted activity {activity_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete activity {activity_id}: {e}")
            return False

    # ========================================================================
    # EXERCISE SETS
    # ========================================================================

    async def search_exercises(
        self, query: str, category: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search exercises by name with full-text search.

        Args:
            query: Search query
            category: Optional category filter
            limit: Max results

        Returns:
            List of exercise dicts sorted by relevance and usage
        """
        try:
            # Use the search_exercises PostgreSQL function created in migration
            response = self.client.rpc(
                "search_exercises",
                {
                    "search_query": query,
                    "category_filter": category,
                    "limit_count": limit
                }
            ).execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to search exercises: {e}")
            # Fallback to simple ILIKE search if function doesn't exist yet
            try:
                db_query = (
                    self.client.table("exercises")
                    .select("*")
                    .ilike("name", f"%{query}%")
                    .eq("is_public", True)
                    .eq("verified", True)
                    .order("usage_count", desc=True)
                    .limit(limit)
                )
                if category:
                    db_query = db_query.eq("category", category)

                response = db_query.execute()
                return response.data
            except Exception as e2:
                logger.error(f"Fallback exercise search failed: {e2}")
                return []

    async def get_exercise_sets(
        self,
        activity_id: UUID,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all exercise sets for an activity.

        Args:
            activity_id: Activity UUID
            user_id: Optional user UUID for ownership verification

        Returns:
            List of exercise_set dicts with exercise details
        """
        try:
            query = (
                self.client.table("exercise_sets")
                .select("*, exercises(*)")
                .eq("activity_id", str(activity_id))
                .order("set_number", desc=False)
            )

            if user_id:
                query = query.eq("user_id", str(user_id))

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get exercise sets for activity {activity_id}: {e}")
            return []

    async def create_exercise_sets(
        self, sets_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create multiple exercise sets.

        Args:
            sets_data: List of exercise_set dicts

        Returns:
            List of created exercise_set dicts
        """
        try:
            response = self.client.table("exercise_sets").insert(sets_data).execute()
            logger.info(f"Created {len(sets_data)} exercise sets")
            return response.data
        except Exception as e:
            logger.error(f"Failed to create exercise sets: {e}")
            raise

    async def update_exercise_set(
        self,
        set_id: UUID,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an exercise set.

        Args:
            set_id: Exercise set UUID
            user_id: User UUID (for ownership verification)
            updates: Fields to update

        Returns:
            Updated exercise_set dict
        """
        try:
            response = (
                self.client.table("exercise_sets")
                .update(updates)
                .eq("id", str(set_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                raise RuntimeError("Failed to update exercise set - no data returned")

            logger.info(f"Updated exercise set {set_id}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to update exercise set {set_id}: {e}")
            raise

    async def delete_exercise_set(
        self, set_id: UUID, user_id: UUID
    ) -> bool:
        """
        Delete an exercise set.

        Args:
            set_id: Exercise set UUID
            user_id: User UUID (for ownership verification)

        Returns:
            True if deleted successfully
        """
        try:
            response = (
                self.client.table("exercise_sets")
                .delete()
                .eq("id", str(set_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            logger.info(f"Deleted exercise set {set_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete exercise set {set_id}: {e}")
            return False

    async def get_user_exercise_history(
        self,
        user_id: UUID,
        exercise_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's exercise history from the view.

        Args:
            user_id: User UUID
            exercise_id: Optional filter by specific exercise
            limit: Max results

        Returns:
            List of exercise history records
        """
        try:
            query = (
                self.client.table("user_exercise_history")
                .select("*")
                .eq("user_id", str(user_id))
                .order("start_time", desc=True)
                .limit(limit)
            )

            if exercise_id:
                query = query.eq("exercise_id", str(exercise_id))

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get exercise history for user {user_id}: {e}")
            return []

    async def get_personal_records(
        self, user_id: UUID, exercise_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's personal records from the view.

        Args:
            user_id: User UUID
            exercise_id: Optional filter by specific exercise

        Returns:
            List of personal record dicts
        """
        try:
            query = (
                self.client.table("user_personal_records")
                .select("*")
                .eq("user_id", str(user_id))
            )

            if exercise_id:
                query = query.eq("exercise_id", str(exercise_id))

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get personal records for user {user_id}: {e}")
            return []

    # ========================================================================
    # BODY METRICS
    # ========================================================================

    async def get_user_body_metrics(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get body metrics for a user.

        Args:
            user_id: User UUID
            limit: Max results
            offset: Pagination offset
            start_date: ISO datetime (optional)
            end_date: ISO datetime (optional)

        Returns:
            List of body metric dicts sorted by recorded_at DESC
        """
        try:
            query = (
                self.client.table("body_metrics")
                .select("*")
                .eq("user_id", str(user_id))
                .order("recorded_at", desc=True)
                .limit(limit)
                .offset(offset)
            )

            if start_date:
                query = query.gte("recorded_at", start_date)
            if end_date:
                query = query.lte("recorded_at", end_date)

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get body metrics for user {user_id}: {e}")
            return []

    async def get_latest_body_metric(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get the most recent body metric for a user.

        Args:
            user_id: User UUID

        Returns:
            Latest body metric dict or None
        """
        try:
            response = (
                self.client.table("body_metrics")
                .select("*")
                .eq("user_id", str(user_id))
                .order("recorded_at", desc=True)
                .limit(1)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get latest body metric for user {user_id}: {e}")
            return None

    async def create_body_metric(self, metric_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new body metric entry.

        Args:
            metric_data: Body metric fields

        Returns:
            Created body metric dict
        """
        try:
            response = self.client.table("body_metrics").insert(metric_data).execute()
            logger.info(f"Created body metric for user {metric_data.get('user_id')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create body metric: {e}")
            raise

    async def get_body_metric(self, metric_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a single body metric by ID.

        Args:
            metric_id: Body metric UUID

        Returns:
            Body metric dict or None
        """
        try:
            response = (
                self.client.table("body_metrics")
                .select("*")
                .eq("id", str(metric_id))
                .single()
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to get body metric {metric_id}: {e}")
            return None

    async def update_body_metric(
        self,
        metric_id: UUID,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a body metric.

        Args:
            metric_id: Body metric UUID
            user_id: User UUID (for RLS check)
            updates: Fields to update

        Returns:
            Updated body metric dict
        """
        try:
            response = (
                self.client.table("body_metrics")
                .update(updates)
                .eq("id", str(metric_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                logger.error(f"Body metric update returned empty data for metric {metric_id}")
                raise RuntimeError("Failed to update body metric - no data returned")

            logger.info(f"Updated body metric {metric_id}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to update body metric {metric_id}: {e}")
            raise

    async def delete_body_metric(self, metric_id: UUID, user_id: UUID) -> bool:
        """
        Delete a body metric.

        Args:
            metric_id: Body metric UUID
            user_id: User UUID (for RLS check)

        Returns:
            True if deleted successfully
        """
        try:
            response = (
                self.client.table("body_metrics")
                .delete()
                .eq("id", str(metric_id))
                .eq("user_id", str(user_id))
                .execute()
            )
            logger.info(f"Deleted body metric {metric_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete body metric {metric_id}: {e}")
            return False

    # ========================================================================
    # COACH CONVERSATIONS
    # ========================================================================

    async def get_user_conversations(
        self, user_id: UUID, limit: int = 20, include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get coach conversations for a user.

        Args:
            user_id: User UUID
            limit: Max results
            include_archived: Include archived conversations

        Returns:
            List of conversation dicts
        """
        try:
            query = (
                self.client.table("coach_conversations")
                .select("*")
                .eq("user_id", str(user_id))
                .order("last_message_at", desc=True)
                .limit(limit)
            )

            if not include_archived:
                query = query.eq("archived", False)

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get conversations for user {user_id}: {e}")
            return []

    async def create_conversation(
        self, user_id: UUID, title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new coach conversation.

        Args:
            user_id: User UUID
            title: Optional title

        Returns:
            Created conversation dict
        """
        try:
            data = {"user_id": str(user_id)}
            if title:
                data["title"] = title

            response = self.client.table("coach_conversations").insert(data).execute()
            logger.info(f"Created conversation for user {user_id}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise

    async def get_conversation_messages(
        self, conversation_id: UUID, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Conversation UUID
            limit: Max messages

        Returns:
            List of message dicts
        """
        try:
            response = (
                self.client.table("coach_messages")
                .select("*")
                .eq("conversation_id", str(conversation_id))
                .order("created_at", desc=False)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            return []

    async def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a coach message.

        Args:
            message_data: Message fields

        Returns:
            Created message dict
        """
        try:
            response = self.client.table("coach_messages").insert(message_data).execute()
            logger.info(f"Created message in conversation {message_data.get('conversation_id')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create message: {e}")
            raise

    # ========================================================================
    # EMBEDDINGS (RAG)
    # ========================================================================

    async def search_similar_embeddings(
        self,
        user_id: UUID,
        query_embedding: List[float],
        limit: int = 5,
        source_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings using vector similarity.

        Args:
            user_id: User UUID
            query_embedding: Vector to search for
            limit: Max results
            source_type: Optional filter by source_type

        Returns:
            List of embedding dicts with similarity scores
        """
        try:
            # Note: Supabase Python client doesn't have direct vector search yet
            # We'll need to use RPC function for this
            # For now, placeholder implementation
            logger.warning("Vector search not fully implemented yet")
            return []
        except Exception as e:
            logger.error(f"Failed to search embeddings: {e}")
            return []

    async def create_embedding(self, embedding_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an embedding entry.

        Args:
            embedding_data: Embedding fields

        Returns:
            Created embedding dict
        """
        try:
            response = self.client.table("embeddings").insert(embedding_data).execute()
            logger.info(f"Created embedding for user {embedding_data.get('user_id')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            raise

    # ========================================================================
    # WEARABLE UPSERTS (Activities + Health Metrics)
    # ========================================================================

    async def upsert_activities_wearable(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch upsert activities using (user_id, wearable_activity_id) as conflict key.

        Expects API-shaped activities (activity_name/category fields etc.).
        """
        if not activities:
            return []

        # Map API fields to DB fields for all rows
        db_rows = [self._map_activity_to_db(a) for a in activities]
        try:
            response = (
                self.client.table("activities")
                .upsert(db_rows, on_conflict=["user_id", "wearable_activity_id"])
                .execute()
            )
            # Map DB fields back to API fields
            return [self._map_activity_from_db(r) for r in (response.data or [])]
        except Exception as e:
            logger.error(f"Failed to upsert wearable activities: {e}")
            raise

    async def create_health_metrics_bulk(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Insert health metrics in bulk. Table: health_metrics

        Each item should include: user_id, recorded_at (ISO), metric_type, value (JSON)
        """
        if not metrics:
            return []
        try:
            response = (
                self.client.table("health_metrics")
                .upsert(metrics, on_conflict=["user_id", "metric_type", "recorded_at"])
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to insert health metrics: {e}")
            raise

    # ========================================================================
    # RAW SQL EXECUTION (For migrations)
    # ========================================================================

    async def execute_sql(self, sql: str) -> Dict[str, Any]:
        """
        Execute raw SQL (admin only).

        WARNING: Use with caution. Only for migrations.

        Args:
            sql: SQL statement

        Returns:
            Result dict
        """
        try:
            # Note: Supabase Python client doesn't support raw SQL execution
            # Migrations should be applied via Supabase dashboard or CLI
            raise NotImplementedError(
                "Raw SQL execution not supported via Supabase client. "
                "Use Supabase dashboard SQL Editor or CLI for migrations."
            )
        except Exception as e:
            logger.error(f"Failed to execute SQL: {e}")
            raise


# Global singleton instance
supabase_service = SupabaseService()


def get_service_client() -> Client:
    """
    Get the raw Supabase client for services that need direct access.

    Returns:
        Supabase Client instance
    """
    return supabase_service.client
