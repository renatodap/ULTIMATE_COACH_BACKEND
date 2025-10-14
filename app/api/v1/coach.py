"""
Coach API Endpoints

Main API for the AI fitness coach.
Handles message sending, log confirmation, and conversation management.
"""

import structlog
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from app.api.v1.schemas.coach_schemas import (
    MessageRequest,
    MessageResponse,
    ConfirmLogRequest,
    ConfirmLogResponse,
    CancelLogRequest,
    CancelLogResponse,
    ConversationListResponse,
    ConversationSummary,
    MessageListResponse,
    Message,
    ToolCall,
    ArchiveConversationRequest,
    ArchiveConversationResponse
)
from app.api.dependencies import get_current_user
from app.services.supabase_service import supabase_service
from app.services.nutrition_service import nutrition_service
from app.services.activity_service import activity_service
from app.services.body_metrics_service import body_metrics_service
from app.services.unified_coach_service import get_unified_coach_service
from uuid import UUID

logger = structlog.get_logger()

router = APIRouter(prefix="/coach", tags=["coach"])

# UnifiedCoachService will be lazily initialized on first request
# (Deferred to avoid module import errors before SDK validation)
unified_coach = None


def get_unified_coach():
    """Get UnifiedCoachService singleton (lazy initialization)."""
    global unified_coach
    if unified_coach is None:
        unified_coach = get_unified_coach_service()
    return unified_coach


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_supabase():
    """Get Supabase client."""
    return supabase_service.client


def _generate_log_confirmation_message(log_type: str, data: dict) -> str:
    """Generate confirmation message for detected log."""
    if log_type == "meal":
        items_text = ", ".join([f"{item.get('quantity', '')} {item.get('name', '')}"
                                for item in data.get("items", [])])
        return (
            f"✅ **MEAL DETECTED!**\n\n"
            f"I logged: {items_text}\n"
            f"Meal type: {data.get('meal_type', 'snack').title()}\n\n"
            f"Tap below to confirm or edit before saving!"
        )

    elif log_type == "activity":
        return (
            f"✅ **WORKOUT DETECTED!**\n\n"
            f"Activity: {data.get('activity_name', 'Activity')}\n"
            f"Duration: {data.get('duration_minutes', 0)} minutes\n"
            f"Calories: ~{data.get('calories_burned', 0)} kcal\n\n"
            f"Tap below to confirm or edit before saving!"
        )

    elif log_type == "measurement":
        weight_kg = data.get('weight_kg')
        bf_pct = data.get('body_fat_percentage')
        msg = f"✅ **MEASUREMENT DETECTED!**\n\n"
        if weight_kg:
            msg += f"Weight: {weight_kg} kg\n"
        if bf_pct:
            msg += f"Body Fat: {bf_pct}%\n"
        msg += "\nTap below to confirm or edit before saving!"
        return msg

    return "Log detected! Confirm to save."


def _generate_chat_response(message: str) -> str:
    """Generate friendly chat response."""
    # Simple responses for now - can be enhanced with AI later
    message_lower = message.lower()

    if any(word in message_lower for word in ["hello", "hi", "hey"]):
        return "Hey! 💪 Ready to crush your goals today? What can I help you with?"

    elif any(word in message_lower for word in ["progress", "how am i doing"]):
        return "I'd love to show you your progress! Check out the Dashboard tab to see your full stats and trends. 📊"

    elif any(word in message_lower for word in ["what should i eat", "meal ideas", "food"]):
        return "Great question! For meal tracking, head to the Nutrition tab. Tell me what you eat by saying something like 'I ate 3 eggs and oatmeal' and I'll log it for you! 🍽️"

    elif any(word in message_lower for word in ["workout", "exercise", "train"]):
        return "Time to get after it! 💪 Check the Activities tab to log your workouts. You can also tell me things like 'I ran 5km' and I'll track it for you!"

    else:
        return (
            "I'm here to help you track your fitness journey! You can:\n\n"
            "• Tell me what you ate: 'I had chicken and rice'\n"
            "• Log workouts: 'I ran 5km' or 'Did bench press'\n"
            "• Track measurements: 'I weigh 185 lbs'\n\n"
            "Just chat naturally and I'll help you log it! 💪"
        )


# ============================================================================
# MESSAGE ENDPOINTS
# ============================================================================

@router.post("/message")
async def send_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Send a message to the AI coach.

    Powered by UnifiedCoachService with:
    - Groq classification (fast, cheap)
    - Claude chat with agentic tools
    - Prompt injection protection
    - 3-tier memory system
    - Multi-language support
    """
    try:
        user_id = current_user["id"]

        logger.info("coach_message_received", user_id=user_id[:8])

        # Process message through UnifiedCoachService (THE BRAIN)
        coach = get_unified_coach()
        result = await coach.process_message(
            user_id=user_id,
            message=request.message,
            conversation_id=request.conversation_id,
            image_base64=None,  # Future: handle image uploads
            background_tasks=background_tasks
        )

        logger.info("coach_response_ready", user_id=user_id[:8])

        return result

    except Exception as e:
        logger.error("coach_message_failed", error=str(e), error_type=type(e).__name__, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


# ============================================================================
# QUICK ENTRY LOG ENDPOINTS
# ============================================================================

@router.post("/confirm-log", response_model=ConfirmLogResponse)
async def confirm_log(
    request: ConfirmLogRequest,
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Confirm a detected log and save to database.

    **Flow:**
    1. User sends message: "I ate 3 eggs and oatmeal"
    2. AI detects it's a log → creates quick_entry_log
    3. User confirms in UI → this endpoint is called
    4. We extract structured data and save to meals table
    5. Link quick_entry_log.meal_id → meal.id

    **Edits:**
    User can edit detected data before confirming:
    - Change quantities: "Actually I had 4 eggs, not 3"
    - Add missing items: "And I also had coffee"
    - Correct meal type: "That was lunch, not breakfast"

    **Future:**
    - Smart suggestions: "Add 100g protein powder? (common post-workout)"
    - Historical patterns: "You usually have coffee with breakfast - add it?"
    """
    try:
        user_id = current_user["id"]

        logger.info(
            f"[CoachAPI] ✅ Confirming log: {request.quick_entry_id[:8]}... "
            f"(user {user_id[:8]}...)"
        )

        # Get quick entry log
        qe_response = supabase.table("quick_entry_logs")\
            .select("*")\
            .eq("id", request.quick_entry_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()

        if not qe_response.data:
            raise HTTPException(status_code=404, detail="Quick entry log not found")

        qe = qe_response.data

        # Verify not already confirmed
        if qe["status"] != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Log already {qe['status']}"
            )

        # Apply user edits (if any)
        structured_data = qe["structured_data"]
        if request.edits:
            structured_data.update(request.edits)

        # Save to appropriate table based on log_type
        log_type = qe["log_type"]
        log_id = None

        if log_type == "meal":
            # Save to meals table
            meal = await nutrition_service.create_meal(
                user_id=user_id,
                name=structured_data.get("name"),
                meal_type=structured_data.get("meal_type", "snack"),
                logged_at=datetime.fromisoformat(structured_data.get("logged_at")) if structured_data.get("logged_at") else datetime.utcnow(),
                notes=structured_data.get("notes"),
                items=structured_data.get("items", []),
                source="coach_chat",
                ai_confidence=qe.get("confidence")
            )
            log_id = str(meal.id)

        elif log_type == "activity":
            # Save to activities table
            activity = await activity_service.create_activity(
                user_id=UUID(user_id),
                category=structured_data.get("category", "other"),
                activity_name=structured_data.get("activity_name", "Activity"),
                start_time=datetime.fromisoformat(structured_data.get("start_time")) if structured_data.get("start_time") else datetime.utcnow(),
                end_time=datetime.fromisoformat(structured_data.get("end_time")) if structured_data.get("end_time") else None,
                duration_minutes=structured_data.get("duration_minutes"),
                calories_burned=structured_data.get("calories_burned", 0),
                intensity_mets=structured_data.get("intensity_mets", 3.0),
                metrics=structured_data.get("metrics", {}),
                notes=structured_data.get("notes")
            )
            log_id = activity["id"]

        elif log_type == "measurement":
            # Save to body_metrics table
            metric = await body_metrics_service.create_body_metric(
                user_id=UUID(user_id),
                recorded_at=datetime.fromisoformat(structured_data.get("recorded_at")) if structured_data.get("recorded_at") else datetime.utcnow(),
                weight_kg=structured_data.get("weight_kg"),
                body_fat_percentage=structured_data.get("body_fat_percentage"),
                notes=structured_data.get("notes")
            )
            log_id = metric["id"]

        # Update quick_entry_log status
        supabase.table("quick_entry_logs")\
            .update({
                "status": "confirmed",
                "confirmed_at": datetime.utcnow().isoformat(),
                f"{log_type}_id": log_id
            })\
            .eq("id", request.quick_entry_id)\
            .execute()

        logger.info(
            f"[CoachAPI] ✅ Log confirmed: {log_type} → {log_id}"
        )

        return ConfirmLogResponse(
            success=True,
            log_type=log_type,
            log_id=log_id,
            message=f"LOGGED! 💪 {log_type.title()} saved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CoachAPI] ❌ Confirm log failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm log: {str(e)}"
        )


@router.post("/cancel-log", response_model=CancelLogResponse)
async def cancel_log(
    request: CancelLogRequest,
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Cancel a detected log.

    **When to use:**
    - AI misunderstood: "I asked WHAT TO eat, not logged what I ate"
    - Wrong data: "That's not accurate"
    - Testing: User just trying the system

    **Learning:**
    We track cancellation reasons to improve classification:
    - If many logs cancelled with "not accurate" → improve extraction
    - If cancelled with "I was asking" → improve classification
    """
    try:
        user_id = current_user["id"]

        logger.info(
            f"[CoachAPI] ❌ Cancelling log: {request.quick_entry_id[:8]}... "
            f"(reason: {request.reason or 'N/A'})"
        )

        # Get quick entry log
        qe_response = supabase.table("quick_entry_logs")\
            .select("*")\
            .eq("id", request.quick_entry_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()

        if not qe_response.data:
            raise HTTPException(status_code=404, detail="Quick entry log not found")

        qe = qe_response.data

        # Verify not already confirmed
        if qe["status"] == "confirmed":
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel confirmed log"
            )

        # Update status
        supabase.table("quick_entry_logs")\
            .update({
                "status": "cancelled",
                "cancelled_at": datetime.utcnow().isoformat(),
                "cancellation_reason": request.reason
            })\
            .eq("id", request.quick_entry_id)\
            .execute()

        logger.info(f"[CoachAPI] ✅ Log cancelled")

        return CancelLogResponse(
            success=True,
            message="Got it! Just tell me what you actually want 💪"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CoachAPI] ❌ Cancel log failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel log: {str(e)}"
        )


# ============================================================================
# CONVERSATION ENDPOINTS
# ============================================================================

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_archived: bool = Query(False, description="Include archived conversations"),
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    List user's conversations.

    **Sorting:**
    - Most recent first (by updated_at)

    **Pagination:**
    - Default: 20 conversations per page
    - Max: 100 per page

    **Archived:**
    - By default, only active conversations shown
    - Set include_archived=true to see all
    """
    try:
        user_id = current_user["id"]

        # Build query
        query = supabase.table("coach_conversations")\
            .select("id, title, is_archived, created_at, updated_at", count="exact")\
            .eq("user_id", user_id)\
            .order("updated_at", desc=True)

        # Filter archived
        if not include_archived:
            query = query.eq("is_archived", False)

        # Pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        # Execute
        response = query.execute()
        conversations_data = response.data
        total_count = response.count

        # Get message counts and previews
        conversations = []
        for conv in conversations_data:
            # Get message count
            msg_count_response = supabase.table("coach_messages")\
                .select("id", count="exact")\
                .eq("conversation_id", conv["id"])\
                .execute()

            message_count = msg_count_response.count or 0

            # Get last message preview
            last_msg_response = supabase.table("coach_messages")\
                .select("content")\
                .eq("conversation_id", conv["id"])\
                .eq("role", "assistant")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()

            last_message_preview = None
            if last_msg_response.data:
                preview = last_msg_response.data[0]["content"]
                last_message_preview = preview[:100] + "..." if len(preview) > 100 else preview

            conversations.append(ConversationSummary(
                id=conv["id"],
                title=conv["title"],
                last_message_preview=last_message_preview,
                message_count=message_count,
                is_archived=conv["is_archived"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"]
            ))

        return ConversationListResponse(
            conversations=conversations,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"[CoachAPI] ❌ List conversations failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200, description="Number of messages to fetch"),
    before_message_id: Optional[str] = Query(None, description="Fetch messages before this ID (pagination)"),
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Get messages in a conversation.

    **Pagination:**
    - Fetch most recent 50 messages by default
    - Use before_message_id for infinite scroll
    - Max 200 messages per request

    **Message Types:**
    - User messages: role="user"
    - Coach messages: role="assistant"

    **Metadata:**
    - Tool calls: What tools AI used to generate response
    - Quick entry: Detected log linked to message
    - Costs: How much the response cost
    """
    try:
        user_id = current_user["id"]

        # Verify conversation belongs to user
        conv_response = supabase.table("coach_conversations")\
            .select("id")\
            .eq("id", conversation_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()

        if not conv_response.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Build query
        query = supabase.table("coach_messages")\
            .select("*")\
            .eq("conversation_id", conversation_id)\
            .order("created_at", desc=True)\
            .limit(limit)

        # Pagination (fetch messages before a specific message)
        if before_message_id:
            # Get timestamp of before_message_id
            before_msg = supabase.table("coach_messages")\
                .select("created_at")\
                .eq("id", before_message_id)\
                .single()\
                .execute()

            if before_msg.data:
                query = query.lt("created_at", before_msg.data["created_at"])

        # Execute
        response = query.execute()
        messages_data = response.data

        # Reverse to chronological order
        messages_data = list(reversed(messages_data))

        # Build message objects
        messages = []
        for msg in messages_data:
            # Parse tool calls (stored as JSONB)
            tool_calls = []
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    tool_calls.append(ToolCall(
                        tool_name=tc["tool_name"],
                        tool_input=tc.get("tool_input", {}),
                        tool_output=tc.get("tool_output", {})
                    ))

            messages.append(Message(
                id=msg["id"],
                role=msg["role"],
                content=msg["content"],
                created_at=msg["created_at"],
                has_image=msg.get("has_image", False),
                quick_entry_id=msg.get("quick_entry_id"),
                tool_calls=tool_calls,
                cost_usd=msg.get("cost_usd")
            ))

        # Check if there are more messages
        has_more = len(messages_data) == limit

        return MessageListResponse(
            conversation_id=conversation_id,
            messages=messages,
            total_count=len(messages),
            has_more=has_more
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CoachAPI] ❌ Get messages failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.patch("/conversations/{conversation_id}/archive", response_model=ArchiveConversationResponse)
async def archive_conversation(
    conversation_id: str,
    request: ArchiveConversationRequest,
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Archive or unarchive a conversation.

    **Archived conversations:**
    - Not shown in default conversation list
    - Can be viewed via include_archived=true
    - Boosts embedding importance scores (archived = important)
    - Can be unarchived later
    """
    try:
        user_id = current_user["id"]

        # Verify conversation belongs to user
        conv_response = supabase.table("coach_conversations")\
            .select("id, is_archived")\
            .eq("id", conversation_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()

        if not conv_response.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Update archive status
        supabase.table("coach_conversations")\
            .update({"is_archived": request.is_archived})\
            .eq("id", conversation_id)\
            .execute()

        logger.info(
            f"[CoachAPI] ✅ Conversation {conversation_id[:8]}... "
            f"{'archived' if request.is_archived else 'unarchived'}"
        )

        return ArchiveConversationResponse(
            success=True,
            conversation_id=conversation_id,
            is_archived=request.is_archived
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CoachAPI] ❌ Archive conversation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to archive conversation: {str(e)}"
        )
