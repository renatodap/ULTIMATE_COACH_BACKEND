"""
Coach API Schemas

Pydantic models for coach API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# MESSAGE ENDPOINTS
# ============================================================================

class MessageRequest(BaseModel):
    """
    Request to send a message to the coach.
    """
    message: str = Field(..., min_length=1, max_length=10000, description="User's message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (creates new if not provided)")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image (JPEG/PNG)")
    audio_base64: Optional[str] = Field(None, description="Base64-encoded audio (future support)")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "I ate 3 eggs and oatmeal for breakfast",
                "conversation_id": None,
                "image_base64": None
            }
        }


class ToolCall(BaseModel):
    """
    Tool call made by the AI during response generation.
    """
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Dict[str, Any]


class MessageResponse(BaseModel):
    """
    Response from the coach.
    """
    message_id: str = Field(..., description="ID of coach's response message")
    conversation_id: str = Field(..., description="ID of the conversation")
    content: str = Field(..., description="Coach's response text")

    # Classification & Routing
    classification: Dict[str, Any] = Field(..., description="Message classification result")
    complexity: Optional[Dict[str, Any]] = Field(None, description="Complexity analysis (if CHAT)")

    # Quick Entry Log (if detected)
    quick_entry_id: Optional[str] = Field(None, description="ID of detected log (if is_log=true)")
    should_show_preview: bool = Field(False, description="Whether to show log preview card")

    # Tool Calls (if agentic)
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tools called during generation")

    # Metadata
    model_used: str = Field(..., description="Model used: canned, groq, or claude")
    response_time_ms: int = Field(..., description="Response generation time")
    cost_usd: float = Field(..., description="Cost in USD")
    tokens_used: Optional[int] = Field(None, description="Tokens used (if applicable)")

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg-123",
                "conversation_id": "conv-456",
                "content": "HELL YEAH! 💪 That's a solid breakfast - 18g protein from those eggs...",
                "classification": {
                    "is_log": True,
                    "log_type": "meal",
                    "confidence": 0.95
                },
                "quick_entry_id": "qe-789",
                "should_show_preview": True,
                "model_used": "claude",
                "response_time_ms": 1850,
                "cost_usd": 0.12,
                "tokens_used": 1200
            }
        }


# ============================================================================
# QUICK ENTRY LOG ENDPOINTS
# ============================================================================

class ConfirmLogRequest(BaseModel):
    """
    Confirm a detected log and save to database.
    """
    quick_entry_id: str = Field(..., description="ID of the quick entry log")
    edits: Optional[Dict[str, Any]] = Field(None, description="User edits to structured data")

    class Config:
        json_schema_extra = {
            "example": {
                "quick_entry_id": "qe-789",
                "edits": {
                    "foods": [
                        {"name": "eggs", "quantity": 4}  # Changed from 3 to 4
                    ]
                }
            }
        }


class ConfirmLogResponse(BaseModel):
    """
    Response after confirming a log.
    """
    success: bool
    log_type: str  # "meal", "activity", "measurement"
    log_id: str  # ID of created meal/activity/measurement
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "log_type": "meal",
                "log_id": "meal-123",
                "message": "LOGGED! 💪 3 eggs + oatmeal = 350 cal, 25g protein"
            }
        }


class CancelLogRequest(BaseModel):
    """
    Cancel a detected log.
    """
    quick_entry_id: str = Field(..., description="ID of the quick entry log")
    reason: Optional[str] = Field(None, description="Why user cancelled (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "quick_entry_id": "qe-789",
                "reason": "Not accurate - I had 4 eggs, not 3"
            }
        }


class CancelLogResponse(BaseModel):
    """
    Response after cancelling a log.
    """
    success: bool
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Log cancelled. Just tell me what you actually ate!"
            }
        }


# ============================================================================
# CONVERSATION ENDPOINTS
# ============================================================================

class ConversationSummary(BaseModel):
    """
    Summary of a conversation.
    """
    id: str
    title: str
    last_message_preview: Optional[str] = None
    message_count: int = 0
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """
    List of user's conversations.
    """
    conversations: List[ConversationSummary]
    total_count: int
    page: int = 1
    page_size: int = 20

    class Config:
        json_schema_extra = {
            "example": {
                "conversations": [
                    {
                        "id": "conv-123",
                        "title": "Meal planning discussion",
                        "last_message_preview": "CRUSH IT! Here's your meal plan...",
                        "message_count": 15,
                        "is_archived": False,
                        "created_at": "2025-01-15T10:00:00Z",
                        "updated_at": "2025-01-15T11:30:00Z"
                    }
                ],
                "total_count": 5,
                "page": 1,
                "page_size": 20
            }
        }


class Message(BaseModel):
    """
    A single message in a conversation.
    """
    id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime

    # Optional metadata
    has_image: bool = False
    quick_entry_id: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    cost_usd: Optional[float] = None


class MessageListResponse(BaseModel):
    """
    List of messages in a conversation.
    """
    conversation_id: str
    messages: List[Message]
    total_count: int
    has_more: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv-123",
                "messages": [
                    {
                        "id": "msg-1",
                        "role": "user",
                        "content": "What should I eat for breakfast?",
                        "created_at": "2025-01-15T10:00:00Z"
                    },
                    {
                        "id": "msg-2",
                        "role": "assistant",
                        "content": "BEAST MODE breakfast incoming! 💪...",
                        "created_at": "2025-01-15T10:00:02Z",
                        "tool_calls": [
                            {
                                "tool_name": "get_user_profile",
                                "tool_input": {},
                                "tool_output": {"daily_protein_goal": 150}
                            }
                        ]
                    }
                ],
                "total_count": 2,
                "has_more": False
            }
        }


class ArchiveConversationRequest(BaseModel):
    """
    Archive a conversation.
    """
    is_archived: bool = Field(True, description="Set to true to archive, false to unarchive")


class ArchiveConversationResponse(BaseModel):
    """
    Response after archiving a conversation.
    """
    success: bool
    conversation_id: str
    is_archived: bool

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "conversation_id": "conv-123",
                "is_archived": True
            }
        }
