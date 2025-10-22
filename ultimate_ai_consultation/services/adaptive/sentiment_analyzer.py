"""
Sentiment Analyzer for Coach Messages

Extracts adherence signals and patterns from coach conversation messages:
- Fatigue/soreness patterns
- Hunger/satiety signals
- Motivation levels
- Barriers and challenges
- Positive progress indicators

Uses keyword matching and pattern recognition for cost-free, deterministic analysis.
Can be enhanced with LLM analysis if needed in future.
"""

from typing import List, Dict, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re


class SentimentSignal(str, Enum):
    """Types of sentiment signals extracted"""

    FATIGUE = "fatigue"
    SORENESS = "soreness"
    INJURY_RISK = "injury_risk"
    HUNGER = "hunger"
    SATIETY = "satiety"
    MOTIVATION_HIGH = "motivation_high"
    MOTIVATION_LOW = "motivation_low"
    PROGRESS_POSITIVE = "progress_positive"
    PROGRESS_NEGATIVE = "progress_negative"
    BARRIER_TIME = "barrier_time"
    BARRIER_COST = "barrier_cost"
    BARRIER_SOCIAL = "barrier_social"


@dataclass
class ExtractedSignal:
    """A single extracted sentiment signal"""

    signal_type: SentimentSignal
    confidence: float  # 0.0-1.0
    message_text: str  # The text that triggered this signal
    timestamp: datetime


@dataclass
class SentimentAnalysis:
    """Complete sentiment analysis results"""

    analysis_period_days: int
    total_messages: int
    signals_detected: List[ExtractedSignal]
    summary: Dict[SentimentSignal, int]  # Count of each signal type
    overall_adherence_sentiment: str  # "positive", "neutral", "negative"
    key_barriers: List[str]
    recommendations: List[str]


# Keyword dictionaries for pattern matching
FATIGUE_KEYWORDS = {
    "exhausted",
    "tired",
    "worn out",
    "drained",
    "no energy",
    "can't recover",
    "burned out",
    "overtraining",
    "fatigued",
    "wiped out",
}

SORENESS_KEYWORDS = {
    "sore",
    "aching",
    "stiff",
    "tight",
    "painful",
    "hurts",
    "discomfort",
    "tender",
}

INJURY_KEYWORDS = {
    "injury",
    "injured",
    "hurt",
    "pain",
    "strain",
    "pulled",
    "tweaked",
    "can't move",
    "sharp pain",
}

HUNGER_KEYWORDS = {
    "hungry",
    "starving",
    "starved",
    "famished",
    "can't stop eating",
    "always hungry",
    "cravings",
    "craving",
}

SATIETY_KEYWORDS = {
    "full",
    "stuffed",
    "satisfied",
    "not hungry",
    "hard to eat",
    "can't finish",
    "too much food",
}

MOTIVATION_HIGH_KEYWORDS = {
    "motivated",
    "excited",
    "pumped",
    "feeling great",
    "crushing it",
    "love it",
    "enjoying",
    "can't wait",
}

MOTIVATION_LOW_KEYWORDS = {
    "not motivated",
    "don't want to",
    "struggling",
    "hate",
    "dreading",
    "boring",
    "sick of",
    "giving up",
}

PROGRESS_POSITIVE_KEYWORDS = {
    "stronger",
    "getting better",
    "improving",
    "PR",
    "personal record",
    "more reps",
    "heavier weight",
    "looking better",
    "feel amazing",
}

PROGRESS_NEGATIVE_KEYWORDS = {
    "weaker",
    "getting worse",
    "regressing",
    "lost strength",
    "can't lift",
    "not improving",
    "plateau",
    "stuck",
}

TIME_BARRIER_KEYWORDS = {
    "no time",
    "too busy",
    "work is crazy",
    "can't fit it in",
    "schedule",
    "rushed",
}

COST_BARRIER_KEYWORDS = {
    "too expensive",
    "can't afford",
    "broke",
    "budget",
    "money",
}

SOCIAL_BARRIER_KEYWORDS = {
    "family",
    "friends don't understand",
    "social pressure",
    "eating out",
    "parties",
    "temptation",
}


class SentimentAnalyzer:
    """Analyzes coach conversation messages for adherence signals"""

    def __init__(self):
        self.keyword_map = {
            SentimentSignal.FATIGUE: FATIGUE_KEYWORDS,
            SentimentSignal.SORENESS: SORENESS_KEYWORDS,
            SentimentSignal.INJURY_RISK: INJURY_KEYWORDS,
            SentimentSignal.HUNGER: HUNGER_KEYWORDS,
            SentimentSignal.SATIETY: SATIETY_KEYWORDS,
            SentimentSignal.MOTIVATION_HIGH: MOTIVATION_HIGH_KEYWORDS,
            SentimentSignal.MOTIVATION_LOW: MOTIVATION_LOW_KEYWORDS,
            SentimentSignal.PROGRESS_POSITIVE: PROGRESS_POSITIVE_KEYWORDS,
            SentimentSignal.PROGRESS_NEGATIVE: PROGRESS_NEGATIVE_KEYWORDS,
            SentimentSignal.BARRIER_TIME: TIME_BARRIER_KEYWORDS,
            SentimentSignal.BARRIER_COST: COST_BARRIER_KEYWORDS,
            SentimentSignal.BARRIER_SOCIAL: SOCIAL_BARRIER_KEYWORDS,
        }

    def analyze_messages(
        self, messages: List[Dict], analysis_period_days: int
    ) -> SentimentAnalysis:
        """
        Analyze coach conversation messages for sentiment signals.

        Args:
            messages: List of message dicts with 'content', 'timestamp', 'role'
            analysis_period_days: Length of analysis period

        Returns:
            SentimentAnalysis with extracted signals and summary
        """
        # Filter to user messages only (not coach responses)
        user_messages = [m for m in messages if m.get("role", "") == "user"]

        # Extract signals from each message
        all_signals = []
        for message in user_messages:
            signals = self._extract_signals_from_message(message)
            all_signals.extend(signals)

        # Summarize signal counts
        summary = {}
        for signal_type in SentimentSignal:
            count = len([s for s in all_signals if s.signal_type == signal_type])
            if count > 0:
                summary[signal_type] = count

        # Determine overall sentiment
        overall_sentiment = self._calculate_overall_sentiment(summary)

        # Identify key barriers
        key_barriers = self._identify_key_barriers(summary)

        # Generate recommendations
        recommendations = self._generate_recommendations(summary, key_barriers)

        return SentimentAnalysis(
            analysis_period_days=analysis_period_days,
            total_messages=len(user_messages),
            signals_detected=all_signals,
            summary=summary,
            overall_adherence_sentiment=overall_sentiment,
            key_barriers=key_barriers,
            recommendations=recommendations,
        )

    def _extract_signals_from_message(self, message: Dict) -> List[ExtractedSignal]:
        """Extract sentiment signals from a single message"""
        content = message.get("content", "").lower()
        timestamp_str = message.get("timestamp", datetime.now().isoformat())
        timestamp = datetime.fromisoformat(timestamp_str) if isinstance(timestamp_str, str) else timestamp_str

        signals = []

        # Check each signal type
        for signal_type, keywords in self.keyword_map.items():
            for keyword in keywords:
                if keyword in content:
                    # Calculate confidence based on keyword specificity
                    confidence = self._calculate_confidence(keyword, content)

                    # Extract surrounding context (±50 chars)
                    match_pos = content.index(keyword)
                    start = max(0, match_pos - 50)
                    end = min(len(content), match_pos + len(keyword) + 50)
                    context = content[start:end].strip()

                    signals.append(
                        ExtractedSignal(
                            signal_type=signal_type,
                            confidence=confidence,
                            message_text=context,
                            timestamp=timestamp,
                        )
                    )
                    break  # Only match once per signal type per message

        return signals

    def _calculate_confidence(self, keyword: str, full_text: str) -> float:
        """Calculate confidence score for keyword match"""
        # Base confidence
        confidence = 0.7

        # Increase for longer, more specific keywords
        if len(keyword) > 10:
            confidence += 0.15

        # Increase if keyword appears multiple times
        count = full_text.count(keyword)
        if count > 1:
            confidence += 0.1

        # Cap at 0.95
        return min(confidence, 0.95)

    def _calculate_overall_sentiment(self, summary: Dict[SentimentSignal, int]) -> str:
        """Determine overall adherence sentiment"""
        # Count positive vs negative signals
        positive_signals = (
            summary.get(SentimentSignal.MOTIVATION_HIGH, 0)
            + summary.get(SentimentSignal.PROGRESS_POSITIVE, 0)
            + summary.get(SentimentSignal.SATIETY, 0)
        )

        negative_signals = (
            summary.get(SentimentSignal.MOTIVATION_LOW, 0)
            + summary.get(SentimentSignal.PROGRESS_NEGATIVE, 0)
            + summary.get(SentimentSignal.FATIGUE, 0)
            + summary.get(SentimentSignal.INJURY_RISK, 0)
            + summary.get(SentimentSignal.HUNGER, 0)
            + summary.get(SentimentSignal.BARRIER_TIME, 0)
            + summary.get(SentimentSignal.BARRIER_COST, 0)
            + summary.get(SentimentSignal.BARRIER_SOCIAL, 0)
        )

        if positive_signals > negative_signals * 1.5:
            return "positive"
        elif negative_signals > positive_signals * 1.5:
            return "negative"
        else:
            return "neutral"

    def _identify_key_barriers(self, summary: Dict[SentimentSignal, int]) -> List[str]:
        """Identify most common barriers"""
        barriers = []

        if summary.get(SentimentSignal.BARRIER_TIME, 0) >= 2:
            barriers.append("Time constraints (busy schedule, work demands)")

        if summary.get(SentimentSignal.BARRIER_COST, 0) >= 2:
            barriers.append("Cost/budget concerns")

        if summary.get(SentimentSignal.BARRIER_SOCIAL, 0) >= 2:
            barriers.append("Social pressures (family, friends, eating out)")

        if summary.get(SentimentSignal.FATIGUE, 0) >= 3:
            barriers.append("Excessive fatigue (possible overtraining)")

        if summary.get(SentimentSignal.HUNGER, 0) >= 3:
            barriers.append("Persistent hunger (calories may be too low)")

        if summary.get(SentimentSignal.MOTIVATION_LOW, 0) >= 3:
            barriers.append("Low motivation (plan may be too aggressive)")

        return barriers

    def _generate_recommendations(
        self, summary: Dict[SentimentSignal, int], barriers: List[str]
    ) -> List[str]:
        """Generate recommendations based on sentiment analysis"""
        recommendations = []

        # Fatigue recommendations
        if summary.get(SentimentSignal.FATIGUE, 0) >= 3:
            recommendations.append(
                "Consider early deload or reducing training frequency due to high fatigue reports."
            )

        # Hunger recommendations
        if summary.get(SentimentSignal.HUNGER, 0) >= 3:
            recommendations.append(
                "Increase calories slightly (5-10%) or adjust meal timing to address persistent hunger."
            )

        # Injury risk recommendations
        if summary.get(SentimentSignal.INJURY_RISK, 0) >= 1:
            recommendations.append(
                "URGENT: User reporting pain/injury. Recommend medical clearance before continuing."
            )

        # Time barrier recommendations
        if summary.get(SentimentSignal.BARRIER_TIME, 0) >= 2:
            recommendations.append(
                "Reduce session duration or frequency to fit schedule constraints better."
            )

        # Motivation recommendations
        if summary.get(SentimentSignal.MOTIVATION_LOW, 0) >= 3:
            recommendations.append(
                "Plan may be too aggressive. Consider simplifying meal plan or reducing training volume."
            )

        # Positive progress reinforcement
        if summary.get(SentimentSignal.PROGRESS_POSITIVE, 0) >= 2:
            recommendations.append(
                "User reporting positive progress. Maintain current approach and celebrate wins."
            )

        # Default if no strong signals
        if not recommendations:
            recommendations.append(
                "No major concerns detected. Continue monitoring adherence and progress."
            )

        return recommendations


# Example usage function
def analyze_coach_conversations(
    supabase_client, user_id: str, start_date: datetime, end_date: datetime
) -> SentimentAnalysis:
    """
    Fetch and analyze coach conversation messages from database.

    Args:
        supabase_client: Supabase client instance
        user_id: User UUID
        start_date: Start of analysis period
        end_date: End of analysis period

    Returns:
        SentimentAnalysis with results
    """
    # Fetch messages from database
    response = (
        supabase_client.table("coach_conversations")
        .select("*")
        .eq("user_id", user_id)
        .gte("created_at", start_date.isoformat())
        .lte("created_at", end_date.isoformat())
        .order("created_at", desc=False)
        .execute()
    )

    messages = response.data
    analysis_period_days = (end_date - start_date).days

    analyzer = SentimentAnalyzer()
    return analyzer.analyze_messages(messages, analysis_period_days)
