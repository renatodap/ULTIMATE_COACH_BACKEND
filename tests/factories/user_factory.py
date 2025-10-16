"""
User test data factory

Uses factory-boy pattern for generating test users with realistic data.
Follows 2025 modern testing standards - minimal mocking, real data generation.
"""

import factory
from faker import Faker
from uuid import uuid4
from datetime import datetime

fake = Faker()


class UserFactory(factory.Factory):
    """Factory for generating test user data"""

    class Meta:
        model = dict

    # Core user fields
    id = factory.LazyFunction(lambda: str(uuid4()))
    email = factory.LazyAttribute(lambda _: f"test{uuid4().hex[:8]}@gmail.com")
    full_name = factory.Faker("name")
    created_at = factory.LazyFunction(datetime.now)

    # Onboarding status
    onboarding_completed = True

    # Profile fields (if onboarding completed)
    primary_goal = factory.Faker("random_element", elements=[
        "lose_weight",
        "gain_muscle",
        "maintain_weight",
        "improve_fitness",
        "gain_strength"
    ])

    experience_level = factory.Faker("random_element", elements=[
        "beginner",
        "intermediate",
        "advanced"
    ])

    workout_frequency = factory.Faker("random_int", min=2, max=7)

    # Biometrics
    age = factory.Faker("random_int", min=18, max=75)
    biological_sex = factory.Faker("random_element", elements=["male", "female"])
    height_cm = factory.LazyAttribute(
        lambda obj: fake.random_int(min=150, max=190) if obj.biological_sex == "male"
        else fake.random_int(min=145, max=180)
    )
    current_weight_kg = factory.LazyAttribute(
        lambda obj: fake.random_int(min=60, max=110) if obj.biological_sex == "male"
        else fake.random_int(min=45, max=90)
    )
    goal_weight_kg = factory.LazyAttribute(
        lambda obj: obj.current_weight_kg + fake.random_int(min=-15, max=10)
    )

    # Activity & nutrition
    activity_level = factory.Faker("random_element", elements=[
        "sedentary",
        "lightly_active",
        "moderately_active",
        "very_active",
        "extremely_active"
    ])

    dietary_preference = factory.Faker("random_element", elements=[
        "none",
        "vegetarian",
        "vegan",
        "pescatarian",
        "paleo"
    ])

    meals_per_day = factory.Faker("random_int", min=2, max=6)
    sleep_hours = factory.Faker("pyfloat", min_value=5.0, max_value=10.0, right_digits=1)
    stress_level = factory.Faker("random_element", elements=["low", "medium", "high"])
    cooks_regularly = factory.Faker("boolean", chance_of_getting_true=70)

    # Preferences
    unit_system = "metric"
    timezone = "America/New_York"


class MinimalUserFactory(factory.Factory):
    """Factory for minimal user (signup only, no onboarding)"""

    class Meta:
        model = dict

    id = factory.LazyFunction(lambda: str(uuid4()))
    email = factory.LazyAttribute(lambda _: f"test{uuid4().hex[:8]}@gmail.com")
    full_name = factory.Faker("name")
    onboarding_completed = False
    created_at = factory.LazyFunction(datetime.now)


# Convenience builders
def create_test_user(**kwargs):
    """Create a complete test user with all fields"""
    return UserFactory.create(**kwargs)


def create_minimal_user(**kwargs):
    """Create a minimal test user (signup only)"""
    return MinimalUserFactory.create(**kwargs)


def create_user_batch(count=10, **kwargs):
    """Create multiple test users"""
    return UserFactory.create_batch(count, **kwargs)


# Example usage:
if __name__ == "__main__":
    # Create single user
    user = create_test_user()
    print("Complete User:", user)

    # Create minimal user
    minimal = create_minimal_user()
    print("\nMinimal User:", minimal)

    # Create user with overrides
    custom = create_test_user(
        email="custom@example.com",
        primary_goal="lose_weight",
        age=30
    )
    print("\nCustom User:", custom)

    # Create batch
    users = create_user_batch(5, biological_sex="male")
    print(f"\nCreated {len(users)} male users")
