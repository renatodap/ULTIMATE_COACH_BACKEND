"""
Coach Message Utilities

Helper functions for generating coach responses and confirmations.
Extracted from coach.py for reusability and testability.
"""

from typing import Dict, Any


def generate_log_confirmation_message(log_type: str, data: Dict[str, Any]) -> str:
    """
    Generate confirmation message for detected log.

    Args:
        log_type: Type of log ('meal', 'activity', 'measurement')
        data: Structured log data

    Returns:
        Formatted confirmation message
    """
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


def generate_chat_response(message: str) -> str:
    """
    Generate friendly chat response.

    Simple responses for now - can be enhanced with AI later.

    Args:
        message: User's message

    Returns:
        Appropriate chat response
    """
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
