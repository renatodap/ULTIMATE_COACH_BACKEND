"""
Pydantic models for context tracking and informal activities.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ContextLog(BaseModel):
    """Life context entry (stress, travel, energy, etc.)"""
    id: UUID
    user_id: UUID
    context_type: str = Field(..., description="stress, energy, travel, injury, illness, motivation, life_event, informal_activity")
    severity: Optional[str] = Field(None, description="low, moderate, high")
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    description: str
    original_message: Optional[str]
    affects_training: bool = False
    affects_nutrition: bool = False
    suggested_adaptation: Optional[str]
    extracted_from_message_id: Optional[UUID]
    extraction_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    extraction_model: Optional[str]
    activity_created_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class ContextSummary(BaseModel):
    """Aggregated context summary for a period"""
    context_type: str
    count: int
    avg_severity: Optional[float]
    avg_sentiment: Optional[float]


class InformalActivityExtraction(BaseModel):
    """Response from informal activity extraction"""
    activity_id: Optional[UUID]
    activity_type: str
    duration_minutes: int
    confidence: float


class LifeContextExtraction(BaseModel):
    """Response from life context extraction"""
    context_id: Optional[UUID]
    context_type: str
    severity: Optional[str]
    sentiment_score: Optional[float]
    confidence: float


class MessageContextResult(BaseModel):
    """Complete result from processing a message for context"""
    informal_activity: Optional[InformalActivityExtraction]
    life_context: Optional[LifeContextExtraction]
    sentiment_score: float


class PersonaProfile(BaseModel):
    """User persona with adaptations"""
    persona_type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    adaptations: List[str]


class ContextTimelineResponse(BaseModel):
    """Timeline of context events"""
    context_logs: List[ContextLog]
    period_summary: Dict[str, ContextSummary]
    total_events: int
