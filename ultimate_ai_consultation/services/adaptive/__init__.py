"""
Adaptive Loop Module

Implements bi-weekly reassessment and automatic plan adjustments based on:
- Meal and training adherence
- Body weight progression
- Coach conversation sentiment
- PID controller adjustments

Main entry point: ReassessmentOrchestrator.run_reassessment()
"""

from .data_aggregator import (
    DataAggregator,
    AggregatedData,
    MealAdherence,
    TrainingAdherence,
    BodyMetricsTrend,
    TrendDirection,
    DataQuality,
)

from .controllers import (
    AdaptiveController,
    CaloriePIDController,
    VolumePIDController,
    CalorieAdjustment,
    VolumeAdjustment,
    AdjustmentType,
    PIDParameters,
    generate_adjustment_summary,
)

from .reassessment import (
    ReassessmentOrchestrator,
    ReassessmentResult,
)

from .sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentAnalysis,
    ExtractedSignal,
    SentimentSignal,
    analyze_coach_conversations,
)

__all__ = [
    # Data Aggregator
    "DataAggregator",
    "AggregatedData",
    "MealAdherence",
    "TrainingAdherence",
    "BodyMetricsTrend",
    "TrendDirection",
    "DataQuality",
    # Controllers
    "AdaptiveController",
    "CaloriePIDController",
    "VolumePIDController",
    "CalorieAdjustment",
    "VolumeAdjustment",
    "AdjustmentType",
    "PIDParameters",
    "generate_adjustment_summary",
    # Reassessment
    "ReassessmentOrchestrator",
    "ReassessmentResult",
    # Sentiment Analysis
    "SentimentAnalyzer",
    "SentimentAnalysis",
    "ExtractedSignal",
    "SentimentSignal",
    "analyze_coach_conversations",
]
