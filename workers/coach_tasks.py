"""
Coach Background Tasks

Celery tasks for coach-related background processing:
- Message vectorization (RAG embeddings)
- Conversation analytics
- Embedding cleanup (archive old/unimportant)
- Importance score updates

These run asynchronously to keep message responses fast.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import openai
import os

from app.core.celery_app import celery_app
from app.services.supabase_service import get_service_client

logger = logging.getLogger(__name__)

# OpenAI client for embeddings
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Embedding model
EMBEDDING_MODEL = "text-embedding-3-small"  # 384 dimensions, $0.02/M tokens
EMBEDDING_DIMENSIONS = 384


# ============================================================================
# MESSAGE VECTORIZATION
# ============================================================================

@celery_app.task(name="coach.vectorize_message", max_retries=3)
def vectorize_message(message_id: str, message_content: str, user_id: str):
    """
    Generate and store embedding for a coach message.

    **Why we need this:**
    - Enables semantic search over conversation history
    - Powers "find similar conversations" feature
    - Allows AI to retrieve relevant context from past discussions

    **Cost:**
    - OpenAI text-embedding-3-small: $0.02/M tokens
    - Average message (100 tokens): $0.000002 (0.0002 cents)
    - Negligible compared to Claude costs ($0.10-0.15/msg)

    **When called:**
    - After every assistant message
    - Runs in background (doesn't block response)

    **Cleanup strategy:**
    - Importance scoring prevents unlimited growth
    - Old, low-importance embeddings archived after 90 days
    - Archived embeddings excluded from search

    Args:
        message_id: UUID of coach message
        message_content: Text content to embed
        user_id: User UUID (for filtering later)
    """
    try:
        logger.info(f"[VectorizeTask] 🧠 Vectorizing message {message_id[:8]}...")

        # Generate embedding
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=message_content,
            dimensions=EMBEDDING_DIMENSIONS
        )

        embedding = response.data[0].embedding
        tokens_used = response.usage.total_tokens

        # Cost calculation
        cost_per_token = 0.02 / 1_000_000  # $0.02 per 1M tokens
        cost_usd = tokens_used * cost_per_token

        logger.info(
            f"[VectorizeTask] ✅ Embedding generated: {tokens_used} tokens, "
            f"${cost_usd:.6f}"
        )

        # Store in database
        supabase = get_service_client()
        supabase.table("coach_message_embeddings").insert({
            "message_id": message_id,
            "embedding": embedding,
            "importance_score": 0.5,  # Neutral - will be updated by importance task
            "is_archived": False,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd
        }).execute()

        logger.info(f"[VectorizeTask] 💾 Embedding stored in DB")

        return {
            "success": True,
            "message_id": message_id,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd
        }

    except Exception as e:
        logger.error(f"[VectorizeTask] ❌ Vectorization failed: {e}", exc_info=True)
        raise


# ============================================================================
# CONVERSATION ANALYTICS
# ============================================================================

@celery_app.task(name="coach.update_conversation_analytics", max_retries=2)
def update_conversation_analytics(conversation_id: str):
    """
    Update conversation metadata after new message.

    **Updates:**
    - updated_at timestamp (for "most recent" sorting)
    - message_count (cached for performance)
    - last_message_preview (for conversation list)

    **Why cached:**
    - Avoids COUNT(*) queries on coach_messages for every list request
    - Much faster conversation list loading

    Args:
        conversation_id: UUID of conversation
    """
    try:
        logger.info(f"[AnalyticsTask] 📊 Updating conversation {conversation_id[:8]}...")

        supabase = get_service_client()

        # Get message count
        count_response = supabase.table("coach_messages")\
            .select("id", count="exact")\
            .eq("conversation_id", conversation_id)\
            .execute()

        message_count = count_response.count or 0

        # Get last assistant message for preview
        last_msg_response = supabase.table("coach_messages")\
            .select("content")\
            .eq("conversation_id", conversation_id)\
            .eq("role", "assistant")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()

        last_message_preview = None
        if last_msg_response.data:
            content = last_msg_response.data[0]["content"]
            last_message_preview = content[:200]  # First 200 chars

        # Update conversation
        supabase.table("coach_conversations").update({
            "updated_at": datetime.utcnow().isoformat(),
            "message_count": message_count,
            "last_message_preview": last_message_preview
        }).eq("id", conversation_id).execute()

        logger.info(
            f"[AnalyticsTask] ✅ Updated: {message_count} messages"
        )

        return {
            "success": True,
            "conversation_id": conversation_id,
            "message_count": message_count
        }

    except Exception as e:
        logger.error(f"[AnalyticsTask] ❌ Analytics update failed: {e}", exc_info=True)
        raise


# ============================================================================
# EMBEDDING CLEANUP
# ============================================================================

@celery_app.task(name="coach.archive_old_embeddings")
def archive_old_embeddings(days_threshold: int = 90, importance_threshold: float = 0.3):
    """
    Archive old, low-importance embeddings to prevent database bloat.

    **Strategy:**
    - Embeddings older than 90 days with importance < 0.3 → archived
    - Archived embeddings excluded from similarity search
    - Keeps database size manageable without losing data

    **Importance score factors:**
    - Age: -0.1 per 30 days (older = less important)
    - Engagement: +0.2 if has follow-up messages
    - Favorited: +0.3 if conversation archived by user
    - Semantic relevance: +0.1 if frequently retrieved

    **Run schedule:**
    - Weekly (cron: 0 3 * * 0)
    - Runs at 3 AM on Sundays (low traffic)

    **Example:**
    - Message from 120 days ago: age_score = -0.4
    - No follow-ups: engagement_score = 0
    - Not favorited: favorite_score = 0
    - Total: 0.5 - 0.4 = 0.1 → ARCHIVED

    Args:
        days_threshold: Archive embeddings older than this many days
        importance_threshold: Archive embeddings below this importance score
    """
    try:
        logger.info(
            f"[CleanupTask] 🧹 Archiving embeddings older than {days_threshold} days "
            f"with importance < {importance_threshold}"
        )

        supabase = get_service_client()

        # Call database function
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

        result = supabase.rpc("archive_old_embeddings", {
            "p_cutoff_date": cutoff_date.isoformat(),
            "p_importance_threshold": importance_threshold
        }).execute()

        archived_count = result.data or 0

        logger.info(
            f"[CleanupTask] ✅ Archived {archived_count} embeddings"
        )

        return {
            "success": True,
            "archived_count": archived_count,
            "cutoff_date": cutoff_date.isoformat()
        }

    except Exception as e:
        logger.error(f"[CleanupTask] ❌ Cleanup failed: {e}", exc_info=True)
        raise


@celery_app.task(name="coach.update_embedding_importance")
def update_embedding_importance(message_id: Optional[str] = None):
    """
    Update importance scores for embeddings.

    **When to run:**
    - Per-message: After new follow-up in conversation (real-time)
    - Batch: Daily for all embeddings (cron)

    **Scoring logic:**
    See calculate_embedding_importance() function in DB migration 020.

    Args:
        message_id: Specific message to update (None = update all)
    """
    try:
        if message_id:
            logger.info(f"[ImportanceTask] 📈 Updating importance for {message_id[:8]}...")
        else:
            logger.info("[ImportanceTask] 📈 Batch updating all importance scores...")

        supabase = get_service_client()

        if message_id:
            # Update single message
            result = supabase.rpc("calculate_embedding_importance", {
                "p_message_id": message_id
            }).execute()

            new_score = result.data

            logger.info(
                f"[ImportanceTask] ✅ Message {message_id[:8]}: "
                f"new importance = {new_score:.2f}"
            )

            return {
                "success": True,
                "message_id": message_id,
                "importance_score": new_score
            }

        else:
            # Batch update all embeddings
            # Get all message IDs
            messages_response = supabase.table("coach_message_embeddings")\
                .select("message_id")\
                .eq("is_archived", False)\
                .execute()

            message_ids = [msg["message_id"] for msg in messages_response.data]

            updated_count = 0
            for msg_id in message_ids:
                try:
                    supabase.rpc("calculate_embedding_importance", {
                        "p_message_id": msg_id
                    }).execute()
                    updated_count += 1
                except Exception as e:
                    logger.warning(f"Failed to update {msg_id}: {e}")
                    continue

            logger.info(
                f"[ImportanceTask] ✅ Batch update complete: {updated_count}/{len(message_ids)} updated"
            )

            return {
                "success": True,
                "updated_count": updated_count,
                "total_count": len(message_ids)
            }

    except Exception as e:
        logger.error(f"[ImportanceTask] ❌ Importance update failed: {e}", exc_info=True)
        raise


# ============================================================================
# CACHE WARMING (OPTIONAL)
# ============================================================================

@celery_app.task(name="coach.warm_user_cache")
def warm_user_cache(user_id: str):
    """
    Pre-load frequently accessed data into cache for a user.

    **What we cache:**
    - User profile (goals, macros, restrictions)
    - Recent meals (last 7 days)
    - Recent activities (last 7 days)
    - Body measurements (latest)

    **When to run:**
    - After user login
    - After first message of the day
    - Manually via admin API

    **Cache TTL:**
    - Profile: 1 hour (changes infrequently)
    - Meals/activities: 5 minutes (changes frequently)
    - Measurements: 1 hour

    **Benefit:**
    - First tool call hits cache instead of DB
    - Reduces tool execution time from 200ms → 5ms
    - Better user experience (faster responses)

    Args:
        user_id: User UUID
    """
    try:
        logger.info(f"[CacheWarmTask] 🔥 Warming cache for user {user_id[:8]}...")

        supabase = get_service_client()

        # This is a nice-to-have feature
        # For MVP, we can skip this and just rely on lazy loading

        # TODO: Implement cache warming
        # 1. Fetch user profile → cache.set(f"profile:{user_id}", data, ttl=3600)
        # 2. Fetch recent meals → cache.set(f"meals:{user_id}", data, ttl=300)
        # 3. Fetch recent activities → cache.set(f"activities:{user_id}", data, ttl=300)
        # 4. Fetch latest measurements → cache.set(f"measurements:{user_id}", data, ttl=3600)

        logger.info("[CacheWarmTask] ✅ Cache warmed (MVP: skipped)")

        return {
            "success": True,
            "user_id": user_id,
            "note": "MVP: Cache warming not implemented yet"
        }

    except Exception as e:
        logger.error(f"[CacheWarmTask] ❌ Cache warming failed: {e}", exc_info=True)
        raise


# ============================================================================
# SCHEDULED TASKS (Celery Beat)
# ============================================================================

# Add to celery beat schedule in celery_app.py:
#
# CELERY_BEAT_SCHEDULE = {
#     "archive-old-embeddings": {
#         "task": "coach.archive_old_embeddings",
#         "schedule": crontab(hour=3, minute=0, day_of_week=0),  # 3 AM Sunday
#     },
#     "update-all-importance-scores": {
#         "task": "coach.update_embedding_importance",
#         "schedule": crontab(hour=2, minute=0),  # 2 AM daily
#         "kwargs": {"message_id": None}  # Batch update
#     },
# }
