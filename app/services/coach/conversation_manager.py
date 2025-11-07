"""
Conversation Manager Service

Manages all conversation operations: CRUD, history, vectorization.

Responsibilities:
- Create/retrieve conversations
- Save messages
- Get conversation history
- Vectorize messages for similarity search
- Extract and store context

Extracted from unified_coach_service.py (2,658 lines).

Usage:
    manager = ConversationManager(supabase, conversation_memory)
    conversation = await manager.get_or_create(user_id, conversation_id)
    await manager.save_messages(conversation_id, user_msg, ai_msg)
"""

import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.errors import DatabaseError, ConversationNotFoundError

logger = structlog.get_logger()


class ConversationManager:
    """
    Manages conversation lifecycle and storage.

    Handles: Database operations, vectorization, history retrieval.
    """

    def __init__(self, supabase_client, conversation_memory_service=None):
        """
        Initialize conversation manager.

        Args:
            supabase_client: Supabase client for database
            conversation_memory_service: Service for vectorization (optional)
        """
        self.supabase = supabase_client
        self.conversation_memory = conversation_memory_service
        self.logger = logger

    async def get_or_create(
        self,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get existing conversation or create new one.

        Args:
            user_id: User UUID
            conversation_id: Optional conversation UUID

        Returns:
            Conversation dict

        Raises:
            DatabaseError: On database error
        """
        if conversation_id:
            return await self._get_conversation(conversation_id, user_id)
        else:
            return await self._create_conversation(user_id)

    async def _get_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get existing conversation.

        Args:
            conversation_id: Conversation UUID
            user_id: User UUID (for ownership verification)

        Returns:
            Conversation dict

        Raises:
            ConversationNotFoundError: If conversation not found
            DatabaseError: On database error
        """
        try:
            result = self.supabase.table("coach_conversations")\
                .select("*")\
                .eq("id", conversation_id)\
                .eq("user_id", user_id)\
                .single()\
                .execute()

            if not result.data:
                raise ConversationNotFoundError(
                    message=f"Conversation {conversation_id} not found",
                    conversation_id=conversation_id
                )

            self.logger.info(
                "conversation_retrieved",
                conversation_id=conversation_id,
                user_id=user_id
            )

            return result.data

        except ConversationNotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                "get_conversation_failed",
                conversation_id=conversation_id,
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(
                message="Failed to get conversation",
                conversation_id=conversation_id
            )

    async def _create_conversation(self, user_id: str) -> Dict[str, Any]:
        """
        Create new conversation.

        Args:
            user_id: User UUID

        Returns:
            Created conversation dict

        Raises:
            DatabaseError: On database error
        """
        try:
            result = self.supabase.table("coach_conversations").insert({
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()

            if not result.data:
                raise DatabaseError(message="Failed to create conversation")

            conversation = result.data[0]

            self.logger.info(
                "conversation_created",
                conversation_id=conversation["id"],
                user_id=user_id
            )

            return conversation

        except Exception as e:
            self.logger.error(
                "create_conversation_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(message="Failed to create conversation")

    async def get_history(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get conversation message history.

        Args:
            conversation_id: Conversation UUID
            limit: Maximum number of messages

        Returns:
            List of messages ordered by creation time
        """
        try:
            result = self.supabase.table("coach_messages")\
                .select("id, role, content, created_at, metadata")\
                .eq("conversation_id", conversation_id)\
                .order("created_at", desc=False)\
                .limit(limit)\
                .execute()

            messages = result.data if result.data else []

            self.logger.debug(
                "history_retrieved",
                conversation_id=conversation_id,
                message_count=len(messages)
            )

            return messages

        except Exception as e:
            self.logger.error(
                "get_history_failed",
                conversation_id=conversation_id,
                error=str(e),
                exc_info=True
            )
            return []  # Return empty list on error

    async def save_messages(
        self,
        conversation_id: str,
        user_message: str,
        ai_message: str,
        user_metadata: Optional[Dict] = None,
        ai_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Save both user and AI messages.

        Args:
            conversation_id: Conversation UUID
            user_message: User's message text
            ai_message: AI's response text
            user_metadata: Optional user message metadata
            ai_metadata: Optional AI message metadata

        Returns:
            Dict with both message IDs

        Raises:
            DatabaseError: On database error
        """
        try:
            # Save user message
            user_msg_id = await self._save_message(
                conversation_id,
                role="user",
                content=user_message,
                metadata=user_metadata
            )

            # Save AI message
            ai_msg_id = await self._save_message(
                conversation_id,
                role="assistant",
                content=ai_message,
                metadata=ai_metadata
            )

            # Update conversation timestamp
            await self._update_conversation_timestamp(conversation_id)

            self.logger.info(
                "messages_saved",
                conversation_id=conversation_id,
                user_message_id=user_msg_id,
                ai_message_id=ai_msg_id
            )

            return {
                "user_message_id": user_msg_id,
                "ai_message_id": ai_msg_id
            }

        except Exception as e:
            self.logger.error(
                "save_messages_failed",
                conversation_id=conversation_id,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(message="Failed to save messages")

    async def _save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save a single message.

        Args:
            conversation_id: Conversation UUID
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata

        Returns:
            Message ID

        Raises:
            DatabaseError: On database error
        """
        result = self.supabase.table("coach_messages").insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        if not result.data:
            raise DatabaseError(message=f"Failed to save {role} message")

        return result.data[0]["id"]

    async def _update_conversation_timestamp(self, conversation_id: str):
        """Update conversation's updated_at timestamp."""
        try:
            self.supabase.table("coach_conversations")\
                .update({"updated_at": datetime.utcnow().isoformat()})\
                .eq("id", conversation_id)\
                .execute()
        except Exception as e:
            self.logger.warning(
                "update_timestamp_failed",
                conversation_id=conversation_id,
                error=str(e)
            )

    async def vectorize_message(
        self,
        conversation_id: str,
        message_id: str,
        message_text: str
    ) -> None:
        """
        Vectorize message for similarity search (background task).

        Args:
            conversation_id: Conversation UUID
            message_id: Message UUID
            message_text: Message content to vectorize
        """
        if not self.conversation_memory:
            self.logger.warning("vectorization_skipped_no_service")
            return

        try:
            # Create embedding
            embedding = await self.conversation_memory.create_embedding(message_text)

            # Store embedding
            await self.conversation_memory.store_embedding(
                conversation_id,
                message_id,
                embedding
            )

            self.logger.debug(
                "message_vectorized",
                conversation_id=conversation_id,
                message_id=message_id
            )

        except Exception as e:
            # Don't fail on vectorization errors
            self.logger.warning(
                "vectorization_failed",
                conversation_id=conversation_id,
                message_id=message_id,
                error=str(e)
            )

    async def extract_and_store_context(
        self,
        user_id: str,
        conversation_id: str,
        message_text: str
    ) -> None:
        """
        Extract and store conversation context.

        This is for future context retrieval and personalization.

        Args:
            user_id: User UUID
            conversation_id: Conversation UUID
            message_text: Message text to analyze
        """
        try:
            # TODO: Implement context extraction
            # Could use LLM to extract entities, preferences, goals, etc.
            self.logger.debug(
                "context_extraction_placeholder",
                user_id=user_id,
                conversation_id=conversation_id
            )

        except Exception as e:
            self.logger.warning(
                "context_extraction_failed",
                conversation_id=conversation_id,
                error=str(e)
            )

    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        Soft delete a conversation.

        Args:
            conversation_id: Conversation UUID
            user_id: User UUID (for ownership verification)

        Returns:
            True if successful

        Raises:
            DatabaseError: On database error
        """
        try:
            result = self.supabase.table("coach_conversations")\
                .update({"deleted_at": datetime.utcnow().isoformat()})\
                .eq("id", conversation_id)\
                .eq("user_id", user_id)\
                .execute()

            if not result.data:
                raise DatabaseError(message="Conversation not found or already deleted")

            self.logger.info(
                "conversation_deleted",
                conversation_id=conversation_id,
                user_id=user_id
            )

            return True

        except Exception as e:
            self.logger.error(
                "delete_conversation_failed",
                conversation_id=conversation_id,
                error=str(e),
                exc_info=True
            )
            raise DatabaseError(message="Failed to delete conversation")


# Factory function for easy initialization
def get_conversation_manager(supabase_client, conversation_memory_service=None):
    """
    Create ConversationManager instance.

    Args:
        supabase_client: Supabase client
        conversation_memory_service: Conversation memory service (optional)

    Returns:
        ConversationManager instance
    """
    return ConversationManager(supabase_client, conversation_memory_service)
