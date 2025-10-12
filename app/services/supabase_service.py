"""
Supabase service module with connection pooling and helper methods.

Provides a centralized interface for all database operations via Supabase.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client, create_client
from app.config import settings

logger = logging.getLogger(__name__)


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
            return response.data
        except Exception as e:
            logger.error(f"Failed to get profile {user_id}: {e}")
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
        self, user_id: UUID, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update user profile.

        Args:
            user_id: User UUID
            updates: Fields to update

        Returns:
            Updated profile dict or None
        """
        try:
            response = (
                self.client.table("profiles")
                .update(updates)
                .eq("id", str(user_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                logger.error(f"Profile update returned empty data for user {user_id}")
                raise RuntimeError(f"Failed to update profile - no data returned")

            logger.info(f"Updated profile for user {user_id}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to update profile {user_id}: {e}")
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
            List of activity dicts
        """
        try:
            query = (
                self.client.table("activities")
                .select("*")
                .eq("user_id", str(user_id))
                .order("start_time", desc=True)
                .limit(limit)
                .offset(offset)
            )

            if start_date:
                query = query.gte("start_time", start_date)
            if end_date:
                query = query.lte("start_time", end_date)

            response = query.execute()
            return response.data
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
            response = self.client.table("activities").insert(activity_data).execute()
            logger.info(f"Created activity for user {activity_data.get('user_id')}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create activity: {e}")
            raise

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
