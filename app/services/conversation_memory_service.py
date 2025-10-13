"""
Conversation Memory Service - 3-TIER MEMORY ARCHITECTURE

Provides conversation context using intelligent retrieval:
- TIER 1: Last 10 messages (always included - working memory)
- TIER 2: Keyword-matched messages from 11-50 (important context)
- TIER 3: Semantic search (via tool, not here)

This ensures AI remembers:
- Recent conversation (Tier 1)
- Important user info like allergies, injuries, goals (Tier 2)
- Anything from history when asked (Tier 3 - tool-based)
"""

import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Keywords that indicate IMPORTANT user information
# These trigger automatic retrieval from message history
IMPORTANT_KEYWORDS = [
    # Medical/Health
    r'\b(allerg\w*|injur\w*|hurt|pain|doctor|prescribed|condition|disease|diagnos\w*)\b',

    # Physical limitations
    r'\b(can\'t|cannot|unable|avoid|shouldn\'t|bad knee|bad back|bad shoulder)\b',

    # Dietary restrictions
    r'\b(vegan|vegetarian|kosher|halal|gluten|lactose|intoleran\w*|sensitivity)\b',

    # Goals (important for personalization)
    r'\b(goal|target|want to|trying to|aiming|objective|plan to)\b',

    # Strong preferences
    r'\b(hate|love|favorite|prefer|always|never)\b',

    # Life context
    r'\b(pregnant|breastfeed|work schedule|shift work|travel\w*)\b',
]

# Compile regex patterns
IMPORTANT_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in IMPORTANT_KEYWORDS]


class ConversationMemoryService:
    """
    3-Tier conversation memory for smart context retrieval.

    TIER 1: Working memory (last 10 messages)
    TIER 2: Important context (keyword-matched from 11-50)
    TIER 3: Long-term semantic search (tool-based, not here)
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def get_conversation_context(
        self,
        user_id: str,
        conversation_id: str,
        current_message: str,
        token_budget: int = 1200
    ) -> Dict[str, Any]:
        """
        Get conversation context using 3-tier strategy.

        TIER 1: Last 10 messages (always included - working memory)
        TIER 2: Keyword-matched important messages from 11-50
        TIER 3: Semantic search (handled via tool, not here)

        Args:
            user_id: User UUID
            conversation_id: Conversation UUID
            current_message: Current user message (for keyword detection)
            token_budget: Max tokens for context (default 1200)

        Returns:
            {
                "recent_messages": [...],  # Tier 1
                "important_context": [...],  # Tier 2
                "token_count": int,
                "message_count": int,
                "has_important_keywords": bool
            }
        """
        logger.info(f"[ConversationMemory] 💭 3-tier retrieval for {conversation_id[:8]}...")

        try:
            # ================================================================
            # TIER 1: Working Memory (Last 10 messages - ALWAYS included)
            # ================================================================
            tier1_response = self.supabase.table("coach_messages")\
                .select("id, role, content, created_at")\
                .eq("conversation_id", conversation_id)\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()

            if not tier1_response.data:
                logger.info("[ConversationMemory] No previous messages found")
                return {
                    "recent_messages": [],
                    "important_context": [],
                    "token_count": 0,
                    "message_count": 0,
                    "has_important_keywords": False
                }

            # Reverse to chronological order
            tier1_messages = list(reversed(tier1_response.data))
            tier1_tokens = sum(len(m["content"]) // 4 for m in tier1_messages)

            logger.info(
                f"[ConversationMemory] ✅ Tier 1: {len(tier1_messages)} messages, "
                f"{tier1_tokens} tokens"
            )

            # ================================================================
            # TIER 2: Important Context (Keyword matching in messages 11-50)
            # ================================================================
            tier2_messages = []
            tier2_tokens = 0
            has_important_keywords = self._has_important_keywords(current_message)

            if has_important_keywords and tier1_tokens < token_budget - 200:
                logger.info("[ConversationMemory] 🔍 Current message has important keywords - checking history")

                # Get messages 11-50
                tier2_response = self.supabase.table("coach_messages")\
                    .select("id, role, content, created_at")\
                    .eq("conversation_id", conversation_id)\
                    .order("created_at", desc=True)\
                    .range(10, 49)\
                    .execute()

                if tier2_response.data:
                    # Filter for messages with important keywords
                    for msg in tier2_response.data:
                        if self._has_important_keywords(msg["content"]):
                            tier2_messages.append(msg)

                            # Check token budget
                            msg_tokens = len(msg["content"]) // 4
                            if tier1_tokens + tier2_tokens + msg_tokens > token_budget:
                                break
                            tier2_tokens += msg_tokens

                    # Reverse to chronological
                    tier2_messages = list(reversed(tier2_messages))

                    logger.info(
                        f"[ConversationMemory] ✅ Tier 2: Found {len(tier2_messages)} important messages, "
                        f"{tier2_tokens} tokens"
                    )

            # ================================================================
            # Format Response
            # ================================================================
            total_tokens = tier1_tokens + tier2_tokens

            return {
                "recent_messages": tier1_messages,
                "important_context": tier2_messages,
                "token_count": total_tokens,
                "message_count": len(tier1_messages) + len(tier2_messages),
                "has_important_keywords": has_important_keywords,
                "tier1_count": len(tier1_messages),
                "tier2_count": len(tier2_messages)
            }

        except Exception as e:
            logger.error(f"[ConversationMemory] ❌ Failed to get context: {e}", exc_info=True)
            return {
                "recent_messages": [],
                "important_context": [],
                "token_count": 0,
                "message_count": 0,
                "has_important_keywords": False
            }

    def _has_important_keywords(self, text: str) -> bool:
        """
        Check if text contains important keywords.

        Returns True if text mentions allergies, injuries, goals, etc.
        """
        for pattern in IMPORTANT_PATTERNS:
            if pattern.search(text):
                return True
        return False

    async def get_conversation_summary(
        self,
        conversation_id: str
    ) -> Optional[str]:
        """
        Get conversation summary (if available).

        For long conversations (>20 messages), we generate summaries
        to save tokens on future requests.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Summary text or None
        """
        try:
            # TODO: Implement conversation summarization
            # Query conversation_summaries table
            # Return most recent summary

            return None
        except Exception as e:
            logger.error(f"[ConversationMemory] Failed to get summary: {e}")
            return None


# Singleton
_conversation_memory: Optional[ConversationMemoryService] = None

def get_conversation_memory_service(supabase_client=None) -> ConversationMemoryService:
    """Get singleton ConversationMemoryService instance."""
    global _conversation_memory
    if _conversation_memory is None:
        if supabase_client is None:
            from app.services.supabase_service import get_service_client
            supabase_client = get_service_client()
        _conversation_memory = ConversationMemoryService(supabase_client)
    return _conversation_memory
