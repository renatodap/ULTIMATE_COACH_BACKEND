"""
Time-Aware Progress Calculation

Calculates whether user is on track with their nutrition/fitness goals
based on TIME OF DAY, not just absolute numbers.

Example: 500 cal at 6 AM = AHEAD of schedule (great start!)
         500 cal at 2 PM = BEHIND schedule (need to eat more!)

This prevents coach from nagging users who started their day well.
"""

import structlog
from datetime import datetime, time
from typing import Dict, Any, Optional
import pytz

logger = structlog.get_logger()


def calculate_time_aware_progress(
    user_id: str,
    current_time_utc: datetime,
    actual_calories: float,
    goal_calories: float,
    user_timezone: str = "UTC",
    eating_start_hour: int = 6,
    eating_end_hour: int = 22,
) -> Dict[str, Any]:
    """
    Calculate time-aware progress for nutrition goals.

    Args:
        user_id: User UUID
        current_time_utc: Current time in UTC
        actual_calories: Calories consumed today
        goal_calories: Daily calorie goal
        user_timezone: User's timezone (e.g., "America/Sao_Paulo", "America/New_York")
        eating_start_hour: Start of typical eating window (default: 6 AM)
        eating_end_hour: End of typical eating window (default: 10 PM)

    Returns:
        {
            "actual_calories": 500,
            "goal_calories": 3000,
            "actual_progress": 0.167,  # 16.7%
            "expected_progress": 0.0,  # 0% expected at 6 AM
            "deviation": +0.167,  # Ahead of schedule!
            "time_context": "early_morning",
            "user_local_time": "2025-10-18T06:00:00-03:00",
            "interpretation": "ahead_of_schedule",
            "message_suggestion": "You're crushing it! Great start to the day!"
        }
    """
    try:
        # Convert to user's local time
        user_tz = pytz.timezone(user_timezone)
        user_local_time = current_time_utc.astimezone(user_tz)

        # Calculate progress through eating window
        current_hour = user_local_time.hour
        current_minute = user_local_time.minute
        hours_into_day = current_hour + (current_minute / 60)

        # Determine time context
        if current_hour < eating_start_hour:
            time_context = "early_morning"
            expected_progress = 0.0  # Haven't started eating yet
        elif current_hour >= eating_end_hour:
            time_context = "late_night"
            expected_progress = 1.0  # Should have finished eating
        else:
            time_context = "active_eating_period"
            # Linear progress through eating window
            eating_window_hours = eating_end_hour - eating_start_hour  # 16 hours (6am-10pm)
            hours_into_eating = hours_into_day - eating_start_hour
            expected_progress = hours_into_eating / eating_window_hours

        # Calculate actual progress
        actual_progress = actual_calories / goal_calories if goal_calories > 0 else 0

        # Calculate deviation
        deviation = actual_progress - expected_progress

        # Interpret progress
        interpretation = interpret_progress(
            deviation=deviation,
            time_context=time_context,
            actual_progress=actual_progress
        )

        # Generate message suggestion
        message_suggestion = generate_message_suggestion(
            interpretation=interpretation,
            actual_calories=actual_calories,
            goal_calories=goal_calories,
            deviation=deviation,
            time_context=time_context
        )

        logger.info(
            "time_aware_progress_calculated",
            user_id=user_id[:8],
            actual_progress=f"{actual_progress:.2%}",
            expected_progress=f"{expected_progress:.2%}",
            deviation=f"{deviation:+.2%}",
            interpretation=interpretation,
            time_context=time_context
        )

        return {
            "actual_calories": round(actual_calories),
            "goal_calories": round(goal_calories),
            "actual_progress": round(actual_progress, 3),
            "expected_progress": round(expected_progress, 3),
            "deviation": round(deviation, 3),
            "time_context": time_context,
            "user_local_time": user_local_time.isoformat(),
            "interpretation": interpretation,
            "message_suggestion": message_suggestion,
            "hours_into_eating_window": round(hours_into_day - eating_start_hour, 1) if time_context == "active_eating_period" else None,
            "hours_remaining_in_window": round(eating_end_hour - hours_into_day, 1) if time_context == "active_eating_period" else None
        }

    except Exception as e:
        logger.error("time_aware_progress_failed", error=str(e), exc_info=True)
        # Fallback to simple progress
        return {
            "actual_calories": round(actual_calories),
            "goal_calories": round(goal_calories),
            "actual_progress": round(actual_calories / goal_calories if goal_calories > 0 else 0, 3),
            "expected_progress": 0.5,  # Assume midday
            "deviation": 0,
            "time_context": "unknown",
            "interpretation": "calculation_error",
            "message_suggestion": f"{round(actual_calories)} / {round(goal_calories)} cal logged today"
        }


def interpret_progress(
    deviation: float,
    time_context: str,
    actual_progress: float
) -> str:
    """
    Interpret progress deviation into human-readable status.

    Args:
        deviation: Difference between actual and expected progress (-1.0 to +1.0)
        time_context: "early_morning", "active_eating_period", "late_night"
        actual_progress: Actual progress as fraction (0.0 to 1.0+)

    Returns:
        Status string for coach to use in response
    """
    if time_context == "early_morning":
        if deviation > 0:
            return "ahead_of_schedule"  # Already eating before typical window
        else:
            return "on_track"  # Nothing logged yet - normal

    elif time_context == "active_eating_period":
        if deviation > 0.15:
            return "significantly_ahead"  # Way ahead of expected
        elif deviation > 0:
            return "slightly_ahead"  # A bit ahead
        elif deviation > -0.15:
            return "slightly_behind"  # A bit behind but not concerning
        else:
            return "significantly_behind"  # Need to catch up

    elif time_context == "late_night":
        if actual_progress >= 0.95:
            return "goal_achieved"  # Hit the goal!
        elif actual_progress >= 0.8:
            return "close_to_goal"  # Close enough
        elif actual_progress >= 0.6:
            return "moderate_progress"  # Decent day
        else:
            return "missed_goal"  # Significantly short

    return "unknown"


def generate_message_suggestion(
    interpretation: str,
    actual_calories: float,
    goal_calories: float,
    deviation: float,
    time_context: str
) -> str:
    """
    Generate a message suggestion for the coach based on progress interpretation.

    Args:
        interpretation: Progress interpretation status
        actual_calories: Calories consumed
        goal_calories: Daily calorie goal
        deviation: Progress deviation
        time_context: Time of day context

    Returns:
        Suggested message for coach to use
    """
    remaining = round(goal_calories - actual_calories)

    if interpretation == "ahead_of_schedule":
        return f"You're crushing it! 💪 {round(actual_calories)} cal logged already - great start to the day!"

    elif interpretation == "significantly_ahead":
        percent_ahead = abs(deviation) * 100
        return f"BEAST MODE! 🔥 You're {percent_ahead:.0f}% ahead of schedule. {remaining} cal to go!"

    elif interpretation == "slightly_ahead":
        return f"Right on track! 💪 {round(actual_calories)} / {round(goal_calories)} cal. Keep it up!"

    elif interpretation == "slightly_behind":
        return f"You've got {remaining} cal left to hit your goal. Plenty of time! 💪"

    elif interpretation == "significantly_behind":
        if time_context == "late_night":
            return f"A bit short today - {round(actual_calories)} / {round(goal_calories)} cal. Let's crush tomorrow! 🔥"
        else:
            return f"Time to fuel up! 💪 You need {remaining} more calories to hit your goal today."

    elif interpretation == "goal_achieved":
        return f"NAILED IT! 🎯 {round(actual_calories)} / {round(goal_calories)} cal. Perfect day of eating!"

    elif interpretation == "close_to_goal":
        return f"Solid day! 💪 You hit {round(actual_calories)} / {round(goal_calories)} cal ({actual_calories/goal_calories*100:.0f}%). Great work!"

    elif interpretation == "moderate_progress":
        return f"Decent day - {round(actual_calories)} / {round(goal_calories)} cal logged. Let's aim higher tomorrow! 💪"

    elif interpretation == "missed_goal":
        return f"Fell short today - {round(actual_calories)} / {round(goal_calories)} cal. Tomorrow's a new day! 🔥"

    elif interpretation == "on_track":
        return "Nothing logged yet - ready to start the day strong? 💪"

    else:
        return f"{round(actual_calories)} / {round(goal_calories)} cal logged today"


def get_time_of_day_category(hour: int) -> str:
    """
    Categorize time of day for coaching context.

    Args:
        hour: Hour of day (0-23)

    Returns:
        Category: "early_morning", "morning", "midday", "afternoon", "evening", "late_night"
    """
    if hour < 6:
        return "early_morning"
    elif hour < 11:
        return "morning"
    elif hour < 14:
        return "midday"
    elif hour < 18:
        return "afternoon"
    elif hour < 22:
        return "evening"
    else:
        return "late_night"


def get_time_of_day_prompt(hour: int, user_goal: str) -> str:
    """
    Get coaching prompt based on time of day and user goal.

    Args:
        hour: Hour of day (0-23)
        user_goal: User's primary goal (e.g., "muscle_gain", "fat_loss")

    Returns:
        Coaching context prompt for LLM
    """
    category = get_time_of_day_category(hour)

    prompts = {
        "early_morning": {
            "default": "It's very early. User may be logging pre-workout meal or planning ahead.",
            "muscle_gain": "It's early - if they're eating now, praise the dedication! Suggest protein-rich breakfast.",
            "fat_loss": "It's early - be supportive. Encourage hydration and mindful eating when they start."
        },
        "morning": {
            "default": "It's morning. Focus on energizing, protein-rich breakfast suggestions.",
            "muscle_gain": "Morning time - emphasize protein and carbs for muscle fuel. Suggest eggs, oats, protein.",
            "fat_loss": "Morning time - emphasize protein for satiety. Suggest high-protein, moderate-carb breakfast."
        },
        "midday": {
            "default": "It's lunchtime. Focus on balanced, satisfying meals.",
            "muscle_gain": "Lunch time - recommend substantial meals with protein, carbs, and healthy fats.",
            "fat_loss": "Lunch time - emphasize volume with veggies, lean protein, controlled portions."
        },
        "afternoon": {
            "default": "It's afternoon. User may want snacks or pre-workout fuel.",
            "muscle_gain": "Afternoon - great time for pre-workout carbs or a snack. Suggest fruit, rice cakes, protein.",
            "fat_loss": "Afternoon - watch for mindless snacking. If hungry, suggest protein-rich snacks."
        },
        "evening": {
            "default": "It's dinner time. Focus on satisfying, balanced meals to end the day.",
            "muscle_gain": "Dinner time - recommend substantial post-workout meals if they trained today.",
            "fat_loss": "Dinner time - focus on protein and veggies. Lighter on carbs unless post-workout."
        },
        "late_night": {
            "default": "It's late at night. Be mindful of late eating habits.",
            "muscle_gain": "Late night - if they're eating, acknowledge it. Suggest casein protein if pre-bed.",
            "fat_loss": "Late night - gently mention timing if logging food. Don't nag, but be aware."
        }
    }

    return prompts.get(category, {}).get(user_goal, prompts.get(category, {}).get("default", ""))
