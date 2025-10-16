"""
Activity test data factory

Generates realistic activity data for testing activity tracking workflows.
Follows 2025 modern testing standards.
"""

import factory
from faker import Faker
from uuid import uuid4
from datetime import datetime, timedelta
import random

fake = Faker()


class ActivityFactory(factory.Factory):
    """Factory for generating test activity data"""

    class Meta:
        model = dict

    # Core fields
    id = factory.LazyFunction(lambda: str(uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid4()))

    # Activity details
    category = factory.Faker("random_element", elements=[
        "cardio_steady_state",
        "cardio_interval",
        "strength_training",
        "sports",
        "flexibility",
        "other"
    ])

    activity_name = factory.LazyAttribute(
        lambda obj: fake.random_element(elements={
            "cardio_steady_state": ["Morning Run", "Treadmill", "Cycling", "Swimming"],
            "cardio_interval": ["HIIT Workout", "Sprint Training", "Tabata", "Intervals"],
            "strength_training": ["Upper Body", "Lower Body", "Full Body", "Push Day", "Pull Day"],
            "sports": ["Basketball", "Tennis", "Soccer", "Volleyball"],
            "flexibility": ["Yoga", "Stretching", "Pilates", "Mobility Work"],
            "other": ["Walking", "Hiking", "Dancing", "Recreational"]
        }.get(obj.category, ["Workout"]))
    )

    # Timing
    start_time = factory.LazyFunction(
        lambda: datetime.now() - timedelta(hours=random.randint(1, 48))
    )
    end_time = factory.LazyAttribute(
        lambda obj: obj.start_time + timedelta(minutes=obj.duration_minutes)
    )
    duration_minutes = factory.Faker("random_int", min=15, max=120)

    # Performance metrics
    calories_burned = factory.LazyAttribute(
        lambda obj: _calculate_calories(obj.category, obj.duration_minutes, obj.intensity_mets)
    )

    intensity_mets = factory.LazyAttribute(
        lambda obj: fake.pyfloat(
            min_value=_get_mets_range(obj.category)[0],
            max_value=_get_mets_range(obj.category)[1],
            right_digits=1
        )
    )

    # Category-specific metrics
    metrics = factory.LazyAttribute(lambda obj: _generate_metrics(obj.category))

    notes = factory.Faker("sentence", nb_words=8)

    # Metadata
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)
    deleted_at = None


class CardioActivityFactory(ActivityFactory):
    """Factory for cardio activities with specific metrics"""

    category = "cardio_steady_state"

    metrics = factory.LazyAttribute(lambda _: {
        "distance_km": fake.pyfloat(min_value=2.0, max_value=20.0, right_digits=2),
        "avg_heart_rate": fake.random_int(min=120, max=180),
        "max_heart_rate": fake.random_int(min=160, max=200),
        "avg_pace": f"{fake.random_int(min=4, max=8)}:{fake.random_int(min=0, max=59):02d}/km",
        "elevation_gain_m": fake.random_int(min=0, max=500)
    })


class StrengthActivityFactory(ActivityFactory):
    """Factory for strength training with exercise sets"""

    category = "strength_training"

    metrics = factory.LazyAttribute(lambda _: {
        "exercises": [
            {
                "name": fake.random_element(elements=[
                    "Bench Press", "Squat", "Deadlift", "Overhead Press",
                    "Pull-ups", "Rows", "Lunges", "Leg Press"
                ]),
                "sets": fake.random_int(min=3, max=5),
                "reps": fake.random_int(min=5, max=12),
                "weight_kg": fake.random_int(min=20, max=150),
                "rpe": fake.random_int(min=6, max=10)
            }
            for _ in range(fake.random_int(min=3, max=6))
        ],
        "total_volume_kg": fake.random_int(min=1000, max=10000)
    })


# Helper functions
def _get_mets_range(category: str) -> tuple[float, float]:
    """Get appropriate METs range for activity category"""
    mets_ranges = {
        "cardio_steady_state": (3.0, 15.0),
        "cardio_interval": (5.0, 18.0),
        "strength_training": (3.0, 8.0),
        "sports": (4.0, 12.0),
        "flexibility": (1.5, 4.0),
        "other": (2.0, 6.0)
    }
    return mets_ranges.get(category, (3.0, 10.0))


def _calculate_calories(category: str, duration: int, mets: float) -> int:
    """Estimate calories burned based on METs and duration"""
    # Simplified calculation: METs * 3.5 * weight(kg) * duration(hours)
    # Assuming average weight of 75kg
    weight_kg = 75
    duration_hours = duration / 60
    calories = mets * 3.5 * weight_kg * duration_hours / 200
    return int(calories)


def _generate_metrics(category: str) -> dict:
    """Generate category-specific metrics"""
    if category == "cardio_steady_state":
        return {
            "distance_km": fake.pyfloat(min_value=2.0, max_value=20.0, right_digits=2),
            "avg_heart_rate": fake.random_int(min=120, max=180),
            "avg_pace": f"{fake.random_int(min=4, max=8)}:{fake.random_int(min=0, max=59):02d}/km"
        }
    elif category == "cardio_interval":
        return {
            "intervals": fake.random_int(min=5, max=20),
            "work_seconds": fake.random_int(min=20, max=60),
            "rest_seconds": fake.random_int(min=10, max=60),
            "avg_heart_rate": fake.random_int(min=140, max=190)
        }
    elif category == "strength_training":
        return {
            "exercises": [
                {
                    "name": fake.random_element(elements=["Bench Press", "Squat", "Deadlift"]),
                    "sets": fake.random_int(min=3, max=5),
                    "reps": fake.random_int(min=5, max=12),
                    "weight_kg": fake.random_int(min=20, max=150)
                }
                for _ in range(3)
            ],
            "total_volume_kg": fake.random_int(min=1000, max=5000)
        }
    elif category == "sports":
        return {
            "sport_type": fake.random_element(elements=["tennis", "basketball", "soccer"]),
            "opponent": fake.name(),
            "score": f"{fake.random_int(min=0, max=10)}-{fake.random_int(min=0, max=10)}"
        }
    elif category == "flexibility":
        return {
            "type": fake.random_element(elements=["yoga", "stretching", "pilates"]),
            "difficulty": fake.random_element(elements=["beginner", "intermediate", "advanced"])
        }
    return {}


# Convenience builders
def create_test_activity(**kwargs):
    """Create a generic test activity"""
    return ActivityFactory.create(**kwargs)


def create_cardio_activity(**kwargs):
    """Create a cardio activity with realistic metrics"""
    return CardioActivityFactory.create(**kwargs)


def create_strength_activity(**kwargs):
    """Create a strength training activity"""
    return StrengthActivityFactory.create(**kwargs)


def create_activity_batch(count=10, **kwargs):
    """Create multiple test activities"""
    return ActivityFactory.create_batch(count, **kwargs)


def create_daily_activities(user_id: str, date: datetime, count: int = 3):
    """Create activities for a specific day"""
    activities = []
    for i in range(count):
        start_time = date.replace(
            hour=random.randint(6, 20),
            minute=random.randint(0, 59)
        )
        activity = ActivityFactory.create(
            user_id=user_id,
            start_time=start_time
        )
        activities.append(activity)
    return activities


# Example usage:
if __name__ == "__main__":
    # Create generic activity
    activity = create_test_activity()
    print("Generic Activity:", activity)

    # Create cardio activity
    cardio = create_cardio_activity()
    print("\nCardio Activity:", cardio)

    # Create strength activity
    strength = create_strength_activity()
    print("\nStrength Activity:", strength)

    # Create daily activities
    daily = create_daily_activities(
        user_id="test-user-123",
        date=datetime.now(),
        count=2
    )
    print(f"\nCreated {len(daily)} activities for today")
