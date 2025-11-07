"""
Training Volume Analysis Tool

Analyzes workout volume over time for strength training.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from app.services.tools.base_tool import BaseTool


class TrainingVolumeTool(BaseTool):
    """Analyze training volume for strength workouts."""

    def get_definition(self) -> Dict[str, Any]:
        """Return tool definition for LLM."""
        return {
            "name": "analyze_training_volume",
            "description": "Analyze training volume (sets × reps × weight) for strength training over time. Shows total volume, average per workout, and volume trends.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze",
                        "default": 30
                    },
                    "exercise": {
                        "type": "string",
                        "description": "Specific exercise to analyze (optional)"
                    }
                },
                "required": []
            }
        }

    async def execute(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze training volume."""
        self.log_execution("analyze_training_volume", params)

        try:
            days = params.get("days", 30)
            specific_exercise = params.get("exercise")

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get strength training activities
            result = self.supabase.table("activities")\
                .select("id, activity_name, start_time, metrics")\
                .eq("user_id", user_id)\
                .eq("category", "strength_training")\
                .gte("start_time", cutoff_date)\
                .order("start_time", desc=False)\
                .execute()

            if not result.data:
                return {
                    "days_analyzed": days,
                    "workout_count": 0,
                    "total_volume_kg": 0,
                    "message": f"No strength training activities in past {days} days"
                }

            # Calculate volume from metrics
            total_volume = 0
            workout_count = len(result.data)
            exercise_volumes = {}

            for activity in result.data:
                metrics = activity.get("metrics", {})
                exercises = metrics.get("exercises", [])

                for exercise in exercises:
                    exercise_name = exercise.get("name", "").lower()

                    # Filter by specific exercise if provided
                    if specific_exercise and specific_exercise.lower() not in exercise_name:
                        continue

                    sets = exercise.get("sets", 0)
                    reps = exercise.get("reps", 0)
                    weight = exercise.get("weight_kg", 0)

                    volume = sets * reps * weight
                    total_volume += volume

                    if exercise_name not in exercise_volumes:
                        exercise_volumes[exercise_name] = 0
                    exercise_volumes[exercise_name] += volume

            avg_volume_per_workout = total_volume / workout_count if workout_count > 0 else 0

            response = {
                "days_analyzed": days,
                "workout_count": workout_count,
                "total_volume_kg": round(total_volume, 1),
                "avg_volume_per_workout_kg": round(avg_volume_per_workout, 1),
            }

            if specific_exercise:
                response["exercise"] = specific_exercise
                response["exercise_volume_kg"] = round(exercise_volumes.get(specific_exercise.lower(), 0), 1)
            else:
                # Top 5 exercises by volume
                top_exercises = sorted(
                    exercise_volumes.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                response["top_exercises"] = [
                    {"exercise": name, "volume_kg": round(vol, 1)}
                    for name, vol in top_exercises
                ]

            return response

        except Exception as e:
            self.log_error("analyze_training_volume", e, params)
            return {"error": str(e)}
