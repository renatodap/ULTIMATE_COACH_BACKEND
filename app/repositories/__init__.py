"""
Repository Package

Provides clean database access layer using Repository Pattern.

Benefits:
- Easy to mock for testing
- Database changes isolated
- Consistent error handling
- Clear data access patterns
- Retry logic built-in

Architecture:
- BaseRepository: Abstract base with common operations
- Domain repositories: One per domain (User, Meal, Activity, etc.)
- Services use repositories (not direct Supabase)

Usage:
    from app.repositories import UserRepository, MealRepository

    user_repo = UserRepository(supabase)
    profile = await user_repo.get_profile(user_id)

    meal_repo = MealRepository(supabase)
    meals = await meal_repo.get_recent_meals(user_id)
"""

from app.repositories.base_repository import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.meal_repository import MealRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.body_metrics_repository import BodyMetricsRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "MealRepository",
    "ActivityRepository",
    "BodyMetricsRepository",
]
