"""
Integration Tests for Adaptive Program System

Drop-in file for: ULTIMATE_COACH_BACKEND/tests/integration/test_programs.py

Tests complete workflow:
1. Generate program from consultation
2. Get today's plan
3. Log meals and workouts
4. Trigger reassessment
5. Verify adjustments

Run with: pytest test_integration.py -v
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, date
import json
import os
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, os.getenv("ULTIMATE_AI_CONSULTATION_PATH", "../ultimate_ai_consultation"))

# Import FastAPI app (adjust import based on your structure)
# from app.main import app

# For demo, we'll create a mock client
# In production, replace with: client = TestClient(app)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def test_user_id():
    """Test user UUID"""
    return "test-user-123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def consultation_data():
    """Sample consultation data"""
    return {
        "goal": "muscle_gain",
        "age": 28,
        "biological_sex": "male",
        "height_cm": 180,
        "weight_kg": 82,
        "activity_level": "moderately_active",
        "training_experience": "intermediate",
        "workouts_per_week": 5,
        "workout_duration_minutes": 60,
        "equipment_access": ["full_gym"],
        "dietary_preferences": ["none"],
        "medical_conditions": [],
        "injuries": [],
    }


# =============================================================================
# Test: Program Generation
# =============================================================================

def test_generate_program(client, test_user_id, consultation_data):
    """Test generating initial program from consultation data"""

    response = client.post(
        "/api/v1/programs/generate",
        json={
            "user_id": test_user_id,
            "consultation_data": consultation_data,
        }
    )

    assert response.status_code == 200, f"Failed to generate program: {response.text}"

    data = response.json()

    # Verify response structure
    assert "plan_id" in data
    assert "user_id" in data
    assert data["user_id"] == test_user_id
    assert "version" in data
    assert data["version"] == 1  # First version

    # Verify plan details
    assert "macro_targets" in data
    assert "workouts_per_week" in data
    assert data["workouts_per_week"] == 5

    # Verify macro targets
    macros = data["macro_targets"]
    assert macros["calories"] > 2000
    assert macros["protein_g"] > 100

    print("✅ Program generation successful")
    print(f"   Plan ID: {data['plan_id']}")
    print(f"   Calories: {macros['calories']} kcal/day")
    print(f"   Protein: {macros['protein_g']} g/day")

    return data["plan_id"]


# =============================================================================
# Test: Get Active Plan
# =============================================================================

def test_get_active_plan(client, test_user_id):
    """Test fetching user's active plan"""

    response = client.get(f"/api/v1/programs/{test_user_id}/active")

    assert response.status_code == 200, f"Failed to get active plan: {response.text}"

    data = response.json()

    # Verify plan structure
    assert "plan_id" in data
    assert "workouts" in data
    assert "meal_plans" in data
    assert "grocery_list" in data

    # Verify workouts
    assert len(data["workouts"]) > 0
    first_workout = data["workouts"][0]
    assert "exercises" in first_workout
    assert len(first_workout["exercises"]) > 0

    # Verify meal plans
    assert len(data["meal_plans"]) == 14  # 14-day meal plan

    print("✅ Active plan retrieved successfully")
    print(f"   Workouts: {len(data['workouts'])}")
    print(f"   Meal plan days: {len(data['meal_plans'])}")

    return data


# =============================================================================
# Test: Get Today's Plan
# =============================================================================

def test_get_today_plan(client, test_user_id):
    """Test getting today's specific workout and meals"""

    response = client.get(f"/api/v1/programs/{test_user_id}/today")

    assert response.status_code == 200, f"Failed to get today's plan: {response.text}"

    data = response.json()

    # Verify structure
    assert "plan_id" in data
    assert "cycle_day" in data
    assert "is_training_day" in data
    assert "meals" in data
    assert "macro_targets" in data

    # If training day, should have workout
    if data["is_training_day"]:
        assert "workout" in data
        assert data["workout"] is not None
        print("✅ Today is a training day")
        print(f"   Workout: {data['workout']['day_name']}")
    else:
        print("✅ Today is a rest day")

    # Should always have meals
    assert len(data["meals"]) > 0
    print(f"   Meals: {len(data['meals'])}")

    return data


# =============================================================================
# Test: Simulate User Activity (Log Meals & Workouts)
# =============================================================================

def test_log_user_activity(client, test_user_id, supabase_client):
    """Simulate user logging meals and workouts for 2 weeks"""

    print("Simulating 2 weeks of user activity...")

    # Simulate 14 days of data
    for day in range(14):
        day_date = (date.today() - timedelta(days=14 - day)).isoformat()

        # Log meals (12 out of 14 days)
        if day % 7 != 2:  # Skip 2 days
            meal_data = {
                "user_id": test_user_id,
                "logged_at": f"{day_date}T12:00:00Z",
                "meal_name": "lunch",
                "total_calories": 2500 + (day % 3) * 50,
                "total_protein_g": 180 + (day % 3) * 5,
                "total_carbs_g": 300,
                "total_fat_g": 70,
                "source": "test_simulation",
            }
            supabase_client.table("meals").insert(meal_data).execute()

        # Log workouts (6 out of 7 planned)
        if day % 2 == 0 and day < 12:  # 6 workouts
            workout_data = {
                "user_id": test_user_id,
                "created_at": f"{day_date}T18:00:00Z",
                "activity_type": "workout",
                "activity_name": f"Workout Day {day + 1}",
                "total_sets": 22 + (day % 2) * 2,
                "duration_minutes": 60,
                "source": "test_simulation",
            }
            supabase_client.table("activities").insert(workout_data).execute()

        # Log weight (5 weigh-ins)
        if day % 3 == 0:
            weight_data = {
                "user_id": test_user_id,
                "recorded_at": f"{day_date}T07:00:00Z",
                "weight_kg": 82.0 + (day * 0.15),  # Gaining 0.3 kg/week
            }
            supabase_client.table("body_metrics").insert(weight_data).execute()

    print("✅ Simulated 2 weeks of activity")
    print("   Meals logged: 12/14 days (86%)")
    print("   Workouts completed: 6 sessions")
    print("   Weight measurements: 5 weigh-ins")


# =============================================================================
# Test: Get Progress Metrics
# =============================================================================

def test_get_progress_metrics(client, test_user_id):
    """Test progress metrics calculation"""

    response = client.get(f"/api/v1/programs/{test_user_id}/progress?days=14")

    assert response.status_code == 200, f"Failed to get progress: {response.text}"

    data = response.json()

    # Verify structure
    assert "metrics" in data
    assert "trend_direction" in data

    metrics = data["metrics"]

    # Verify metrics calculated
    assert "start_weight_kg" in metrics
    assert "current_weight_kg" in metrics
    assert "weight_change_kg" in metrics
    assert "meal_logging_adherence" in metrics
    assert "training_adherence" in metrics

    print("✅ Progress metrics retrieved")
    print(f"   Weight change: {metrics['weight_change_kg']:.2f} kg")
    print(f"   Meal adherence: {metrics['meal_logging_adherence']:.1%}")
    print(f"   Training adherence: {metrics['training_adherence']:.1%}")
    print(f"   Trend: {data['trend_direction']}")

    return data


# =============================================================================
# Test: Trigger Reassessment
# =============================================================================

def test_trigger_reassessment(client, test_user_id):
    """Test triggering bi-weekly reassessment"""

    response = client.post(
        f"/api/v1/programs/{test_user_id}/reassess",
        json={"force": True}  # Force reassessment even if not due
    )

    assert response.status_code == 202, f"Failed to trigger reassessment: {response.text}"

    data = response.json()

    assert data["success"] is True
    assert "check_progress_url" in data

    print("✅ Reassessment triggered")
    print(f"   Status: Running in background")
    print(f"   Estimated completion: {data['estimated_completion_seconds']}s")

    # Wait for completion (in production, poll the check_progress_url)
    import time
    time.sleep(5)

    return data


# =============================================================================
# Test: Verify Adjustments Applied
# =============================================================================

def test_verify_adjustments(client, test_user_id):
    """Verify that plan was adjusted after reassessment"""

    # Get active plan (should be version 2 now)
    response = client.get(f"/api/v1/programs/{test_user_id}/active")
    assert response.status_code == 200

    data = response.json()

    # Should be version 2
    assert data["version"] == 2, "Plan should be updated to version 2"

    # Get plan history
    history_response = client.get(f"/api/v1/programs/{test_user_id}/plan-history")
    assert history_response.status_code == 200

    history = history_response.json()

    # Should have 2 versions
    assert len(history["versions"]) == 2
    assert history["total_adjustments"] >= 1

    # Get most recent adjustment
    if len(history["adjustments"]) > 0:
        adjustment = history["adjustments"][0]
        print("✅ Plan adjusted successfully")
        print(f"   Old version: v{adjustment['from_version']}")
        print(f"   New version: v{adjustment['to_version']}")
        print(f"   Reason: {adjustment['adjustment_reason']}")
        print(f"   Rationale: {adjustment['rationale']}")

    return history


# =============================================================================
# Test: Get Grocery List
# =============================================================================

def test_get_grocery_list(client, test_user_id):
    """Test grocery list generation"""

    response = client.get(f"/api/v1/programs/{test_user_id}/grocery-list")

    assert response.status_code == 200, f"Failed to get grocery list: {response.text}"

    data = response.json()

    # Verify structure
    assert "items_by_category" in data
    assert "total_items" in data

    # Should have multiple categories
    categories = data["items_by_category"]
    assert len(categories) > 0

    print("✅ Grocery list generated")
    print(f"   Total items: {data['total_items']}")
    print(f"   Categories: {', '.join(categories.keys())}")

    return data


# =============================================================================
# Integration Test Suite
# =============================================================================

@pytest.mark.integration
def test_complete_workflow(client, test_user_id, consultation_data, supabase_client):
    """
    Complete end-to-end integration test.

    Workflow:
    1. Generate initial program
    2. Get today's plan
    3. Simulate 2 weeks of user activity
    4. Check progress metrics
    5. Trigger reassessment
    6. Verify adjustments
    7. Get grocery list
    """

    print("\n" + "=" * 80)
    print("COMPLETE WORKFLOW INTEGRATION TEST")
    print("=" * 80 + "\n")

    # Step 1: Generate program
    print("Step 1: Generate Initial Program")
    print("-" * 80)
    plan_id = test_generate_program(client, test_user_id, consultation_data)
    print()

    # Step 2: Get active plan
    print("Step 2: Get Active Plan")
    print("-" * 80)
    active_plan = test_get_active_plan(client, test_user_id)
    print()

    # Step 3: Get today's plan
    print("Step 3: Get Today's Plan")
    print("-" * 80)
    today_plan = test_get_today_plan(client, test_user_id)
    print()

    # Step 4: Simulate user activity
    print("Step 4: Simulate 2 Weeks of User Activity")
    print("-" * 80)
    test_log_user_activity(client, test_user_id, supabase_client)
    print()

    # Step 5: Get progress metrics
    print("Step 5: Get Progress Metrics")
    print("-" * 80)
    progress = test_get_progress_metrics(client, test_user_id)
    print()

    # Step 6: Trigger reassessment
    print("Step 6: Trigger Bi-Weekly Reassessment")
    print("-" * 80)
    reassessment = test_trigger_reassessment(client, test_user_id)
    print()

    # Step 7: Verify adjustments
    print("Step 7: Verify Adjustments Applied")
    print("-" * 80)
    history = test_verify_adjustments(client, test_user_id)
    print()

    # Step 8: Get grocery list
    print("Step 8: Get Grocery List")
    print("-" * 80)
    grocery_list = test_get_grocery_list(client, test_user_id)
    print()

    print("=" * 80)
    print("✅ COMPLETE WORKFLOW TEST PASSED")
    print("=" * 80)
    print("\nAll integration tests completed successfully!")
    print("The adaptive program system is fully functional.")


# =============================================================================
# Helper: Create Test Client (Mock for Demo)
# =============================================================================

@pytest.fixture
def client():
    """
    Create FastAPI test client.

    In production, replace with actual app import:
    from app.main import app
    return TestClient(app)
    """
    # Mock client for demonstration
    # Replace with: TestClient(app)
    print("WARNING: Using mock client. Replace with TestClient(app) in production.")
    return None


@pytest.fixture
def supabase_client():
    """
    Create Supabase client for database operations.

    In production:
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)
    """
    print("WARNING: Using mock Supabase client. Replace with actual client in production.")
    return None


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
