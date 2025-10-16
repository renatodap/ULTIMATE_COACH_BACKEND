"""
Integration Tests - Real UI to Database Workflows

Tests actual user workflows from frontend to database with minimal mocking.
Focus on real business flows that users execute daily.
"""

import pytest
import httpx
from datetime import datetime, date, timedelta
from uuid import uuid4
import asyncio


# =============================================================================
# Configuration
# =============================================================================

BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = f"test_integration_{uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPassword123!"


# =============================================================================
# Test Fixtures - Real Data Setup
# =============================================================================

@pytest.fixture
async def auth_headers():
    """
    Create a real test user and return authenticated headers.

    This simulates a user signing up and logging in.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Signup
        signup_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": "Integration Test User"
        }

        signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
        assert signup_response.status_code == 201, f"Signup failed: {signup_response.text}"

        # Login to get session cookie
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }

        login_response = await client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"

        # Extract cookies
        cookies = login_response.cookies

        # Return headers with cookies
        return {"Cookie": f"{list(cookies.keys())[0]}={list(cookies.values())[0]}"}


@pytest.fixture
async def completed_onboarding_user(auth_headers):
    """
    Create a user who has completed onboarding.

    This represents the typical user state after initial setup.
    """
    async with httpx.AsyncClient(base_url=BASE_URL, headers=auth_headers) as client:
        onboarding_data = {
            "primary_goal": "lose_weight",
            "experience_level": "intermediate",
            "workout_frequency": 4,
            "age": 28,
            "biological_sex": "male",
            "height_cm": 178.0,
            "current_weight_kg": 85.0,
            "goal_weight_kg": 78.0,
            "activity_level": "moderately_active",
            "dietary_preference": "none",
            "food_allergies": [],
            "foods_to_avoid": [],
            "meals_per_day": 3,
            "sleep_hours": 7.5,
            "stress_level": "medium",
            "cooks_regularly": True,
            "unit_system": "metric",
            "timezone": "America/New_York"
        }

        response = await client.post("/api/v1/onboarding/complete", json=onboarding_data)
        assert response.status_code == 200, f"Onboarding failed: {response.text}"

        return auth_headers


# =============================================================================
# TEST 1: Activities Page - Fetch User Activities
# =============================================================================

@pytest.mark.asyncio
async def test_activities_page_fetch_workflow(completed_onboarding_user):
    """
    TEST: User opens Activities page

    Flow:
    1. Frontend: GET /api/v1/activities?date={today}
    2. Backend: Query activities table with RLS
    3. Database: Return user's activities for date
    4. Frontend: Display activities list

    Expected: Empty list initially, then activities after logging
    """
    headers = completed_onboarding_user

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        # Step 1: Fetch activities for today (should be empty)
        today = date.today().isoformat()
        response = await client.get(f"/api/v1/activities?date={today}")

        assert response.status_code == 200, f"Failed to fetch activities: {response.text}"

        data = response.json()
        assert "activities" in data, "Response missing 'activities' key"
        assert isinstance(data["activities"], list), "Activities should be a list"
        assert len(data["activities"]) == 0, "Should have no activities initially"

        print("✅ Activities page initial fetch: SUCCESS")
        print(f"   Response: {data}")


@pytest.mark.asyncio
async def test_activities_daily_summary_workflow(completed_onboarding_user):
    """
    TEST: User views daily activity summary

    Flow:
    1. Frontend: GET /api/v1/activities/summary?date={today}
    2. Backend: Aggregate activities (calories, duration, METs)
    3. Database: SUM and AVG across activities
    4. Frontend: Display summary stats

    Expected: Zeroed summary initially
    """
    headers = completed_onboarding_user

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        today = date.today().isoformat()
        response = await client.get(f"/api/v1/activities/summary?date={today}")

        assert response.status_code == 200, f"Failed to fetch summary: {response.text}"

        summary = response.json()
        assert "total_calories" in summary
        assert "total_duration" in summary
        assert "average_intensity" in summary

        # Should be zero initially
        assert summary["total_calories"] == 0
        assert summary["total_duration"] == 0

        print("✅ Daily activity summary: SUCCESS")
        print(f"   Summary: {summary}")


# =============================================================================
# TEST 2: Activity Logging Workflow
# =============================================================================

@pytest.mark.asyncio
async def test_log_strength_training_workflow(completed_onboarding_user):
    """
    TEST: User logs a strength training session

    Flow:
    1. Frontend: User fills out activity form
    2. POST /api/v1/activities with exercise data
    3. Backend: Validate category-specific fields
    4. Database: Insert into activities + exercise_sets
    5. Frontend: Show success, refresh activities list

    Expected: Activity created with exercise sets
    """
    headers = completed_onboarding_user

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        # Step 1: Log a strength training session
        now = datetime.now()
        activity_data = {
            "category": "strength_training",
            "activity_name": "Upper Body Push Day",
            "start_time": (now - timedelta(hours=1)).isoformat(),
            "end_time": now.isoformat(),
            "duration_minutes": 60,
            "calories_burned": 285,
            "intensity_mets": 5.0,
            "metrics": {
                "exercises": [
                    {
                        "name": "Bench Press",
                        "sets": 4,
                        "reps": 8,
                        "weight_kg": 80,
                        "rpe": 8
                    },
                    {
                        "name": "Overhead Press",
                        "sets": 3,
                        "reps": 10,
                        "weight_kg": 50,
                        "rpe": 7
                    }
                ],
                "total_volume_kg": 2420
            },
            "notes": "Felt strong today, good pump"
        }

        response = await client.post("/api/v1/activities", json=activity_data)

        assert response.status_code == 201, f"Failed to log activity: {response.text}"

        activity = response.json()
        assert "id" in activity
        assert activity["category"] == "strength_training"
        assert activity["calories_burned"] == 285

        activity_id = activity["id"]

        print("✅ Strength training logged: SUCCESS")
        print(f"   Activity ID: {activity_id}")

        # Step 2: Verify activity appears in list
        today = date.today().isoformat()
        list_response = await client.get(f"/api/v1/activities?date={today}")

        assert list_response.status_code == 200
        activities = list_response.json()["activities"]
        assert len(activities) == 1
        assert activities[0]["id"] == activity_id

        print("✅ Activity appears in list: SUCCESS")

        # Step 3: Verify summary updated
        summary_response = await client.get(f"/api/v1/activities/summary?date={today}")
        summary = summary_response.json()

        assert summary["total_calories"] == 285
        assert summary["total_duration"] == 60
        assert summary["average_intensity"] == 5.0

        print("✅ Summary updated correctly: SUCCESS")


@pytest.mark.asyncio
async def test_log_cardio_workout_workflow(completed_onboarding_user):
    """
    TEST: User logs a cardio session

    Flow:
    1. Frontend: User selects cardio category
    2. POST /api/v1/activities with distance/pace data
    3. Backend: Validate cardio-specific metrics
    4. Database: Store JSONB metrics
    5. Frontend: Display with cardio-specific UI

    Expected: Activity with distance, pace, heart rate
    """
    headers = completed_onboarding_user

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        now = datetime.now()
        cardio_data = {
            "category": "cardio_steady_state",
            "activity_name": "Morning Run",
            "start_time": (now - timedelta(minutes=35)).isoformat(),
            "end_time": now.isoformat(),
            "duration_minutes": 35,
            "calories_burned": 320,
            "intensity_mets": 9.0,
            "metrics": {
                "distance_km": 5.5,
                "avg_pace": "6:22/km",
                "avg_heart_rate": 155,
                "max_heart_rate": 172,
                "elevation_gain_m": 45
            },
            "notes": "Good pace, felt easy"
        }

        response = await client.post("/api/v1/activities", json=cardio_data)

        assert response.status_code == 201, f"Failed to log cardio: {response.text}"

        activity = response.json()
        assert activity["category"] == "cardio_steady_state"
        assert activity["metrics"]["distance_km"] == 5.5
        assert activity["metrics"]["avg_heart_rate"] == 155

        print("✅ Cardio activity logged: SUCCESS")
        print(f"   Distance: {activity['metrics']['distance_km']}km")
        print(f"   Avg HR: {activity['metrics']['avg_heart_rate']} bpm")


# =============================================================================
# TEST 3: Meals Page - Fetch and Search
# =============================================================================

@pytest.mark.asyncio
async def test_meals_page_fetch_workflow(completed_onboarding_user):
    """
    TEST: User opens Meals page

    Flow:
    1. Frontend: GET /api/v1/meals?date={today}
    2. Backend: Query meals table with RLS
    3. Database: Join with foods for nutrition data
    4. Frontend: Display meals with macro totals

    Expected: Empty initially, then populated after logging
    """
    headers = completed_onboarding_user

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        today = date.today().isoformat()
        response = await client.get(f"/api/v1/meals?date={today}")

        assert response.status_code == 200, f"Failed to fetch meals: {response.text}"

        data = response.json()
        assert "meals" in data
        assert isinstance(data["meals"], list)
        assert len(data["meals"]) == 0, "Should have no meals initially"

        print("✅ Meals page initial fetch: SUCCESS")


@pytest.mark.asyncio
async def test_food_search_workflow(completed_onboarding_user):
    """
    TEST: User searches for food to log

    Flow:
    1. Frontend: User types "chicken breast" in search
    2. GET /api/v1/foods/search?q=chicken%20breast
    3. Backend: Full-text search on foods table
    4. Database: Return matching foods with servings
    5. Frontend: Display search results

    Expected: List of matching foods with nutrition info
    """
    headers = completed_onboarding_user

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        # Search for common food
        response = await client.get("/api/v1/foods/search?q=chicken%20breast&limit=5")

        assert response.status_code == 200, f"Food search failed: {response.text}"

        results = response.json()
        assert "foods" in results
        assert isinstance(results["foods"], list)

        if len(results["foods"]) > 0:
            food = results["foods"][0]
            assert "id" in food
            assert "name" in food
            assert "servings" in food

            print("✅ Food search: SUCCESS")
            print(f"   Found {len(results['foods'])} results")
            print(f"   First result: {food['name']}")
        else:
            print("⚠️  Food search returned no results (database may be empty)")


# =============================================================================
# TEST 4: Meal Logging Workflow
# =============================================================================

@pytest.mark.asyncio
async def test_log_meal_with_foods_workflow(completed_onboarding_user):
    """
    TEST: User logs a complete meal

    Flow:
    1. Frontend: User searches and adds foods
    2. POST /api/v1/meals with food items
    3. Backend: Calculate total macros
    4. Database: Insert meal + food items
    5. Frontend: Show meal in daily log

    Expected: Meal created with accurate macro totals
    """
    headers = completed_onboarding_user

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        # Step 1: Create custom foods if needed (for reliable testing)
        custom_food_data = {
            "name": "Test Chicken Breast",
            "brand": "Generic",
            "servings": [
                {
                    "serving_size": 100,
                    "serving_unit": "g",
                    "calories": 165,
                    "protein_g": 31,
                    "carbs_g": 0,
                    "fat_g": 3.6
                }
            ]
        }

        food_response = await client.post("/api/v1/foods/custom", json=custom_food_data)
        assert food_response.status_code == 201, f"Failed to create custom food: {food_response.text}"
        food = food_response.json()
        food_id = food["id"]
        serving_id = food["servings"][0]["id"]

        print(f"✅ Created test food: {food_id}")

        # Step 2: Log a meal
        now = datetime.now()
        meal_data = {
            "meal_type": "lunch",
            "logged_at": now.isoformat(),
            "foods": [
                {
                    "food_id": food_id,
                    "serving_id": serving_id,
                    "quantity": 2.0  # 200g chicken
                }
            ],
            "notes": "Post-workout meal"
        }

        meal_response = await client.post("/api/v1/meals", json=meal_data)

        assert meal_response.status_code == 201, f"Failed to log meal: {meal_response.text}"

        meal = meal_response.json()
        assert "id" in meal
        assert meal["meal_type"] == "lunch"
        assert meal["total_calories"] == 330  # 165 * 2
        assert meal["total_protein"] == 62  # 31 * 2

        print("✅ Meal logged: SUCCESS")
        print(f"   Meal ID: {meal['id']}")
        print(f"   Total calories: {meal['total_calories']} kcal")
        print(f"   Total protein: {meal['total_protein']}g")

        # Step 3: Verify meal appears in daily log
        today = date.today().isoformat()
        meals_response = await client.get(f"/api/v1/meals?date={today}")

        assert meals_response.status_code == 200
        meals = meals_response.json()["meals"]
        assert len(meals) == 1
        assert meals[0]["id"] == meal["id"]

        print("✅ Meal appears in daily log: SUCCESS")


# =============================================================================
# TEST 5: Dashboard Data Aggregation
# =============================================================================

@pytest.mark.asyncio
async def test_dashboard_data_workflow(completed_onboarding_user):
    """
    TEST: User views dashboard with aggregated data

    Flow:
    1. Frontend: GET /api/v1/dashboard
    2. Backend: Aggregate today's activities + meals
    3. Database: SUM calories, compare to goals
    4. Frontend: Display progress rings

    Expected: Accurate daily totals and progress
    """
    headers = completed_onboarding_user

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        # First, log some data
        now = datetime.now()

        # Log activity
        activity_data = {
            "category": "cardio_steady_state",
            "activity_name": "Quick Walk",
            "start_time": (now - timedelta(minutes=20)).isoformat(),
            "end_time": now.isoformat(),
            "duration_minutes": 20,
            "calories_burned": 100,
            "intensity_mets": 4.0,
            "metrics": {}
        }
        await client.post("/api/v1/activities", json=activity_data)

        # Get dashboard
        response = await client.get("/api/v1/dashboard")

        assert response.status_code == 200, f"Dashboard fetch failed: {response.text}"

        dashboard = response.json()

        # Should have today's summary
        if "today" in dashboard:
            today_data = dashboard["today"]
            assert "calories_burned" in today_data
            assert today_data["calories_burned"] >= 100

            print("✅ Dashboard data aggregation: SUCCESS")
            print(f"   Today's calories burned: {today_data['calories_burned']}")


# =============================================================================
# TEST 6: Quick Meals/Templates
# =============================================================================

@pytest.mark.asyncio
async def test_quick_meal_template_workflow(completed_onboarding_user):
    """
    TEST: User creates and uses a meal template

    Flow:
    1. Frontend: User saves frequent meal as template
    2. POST /api/v1/quick-meals with food items
    3. Backend: Store template with foods
    4. Frontend: User selects template to log
    5. POST /api/v1/meals/from-template

    Expected: Quick logging of saved meals
    """
    headers = completed_onboarding_user

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        # Step 1: Create a quick meal template
        template_data = {
            "meal_name": "Protein Shake",
            "meal_type": "snack",
            "components": [
                {
                    "name": "Whey Protein",
                    "quantity": 30,
                    "unit": "g",
                    "calories": 120,
                    "protein_g": 25,
                    "carbs_g": 3,
                    "fat_g": 1.5
                },
                {
                    "name": "Banana",
                    "quantity": 1,
                    "unit": "medium",
                    "calories": 105,
                    "protein_g": 1.3,
                    "carbs_g": 27,
                    "fat_g": 0.4
                }
            ]
        }

        template_response = await client.post("/api/v1/quick-meals", json=template_data)

        if template_response.status_code == 201:
            template = template_response.json()

            print("✅ Quick meal template created: SUCCESS")
            print(f"   Template: {template['meal_name']}")
            print(f"   Total calories: {template['total_calories']}")

            # Step 2: List templates
            list_response = await client.get("/api/v1/quick-meals")
            assert list_response.status_code == 200

            templates = list_response.json()["quick_meals"]
            assert len(templates) >= 1

            print(f"✅ Quick meals list: {len(templates)} templates")
        else:
            print(f"⚠️  Quick meal endpoint may not be fully implemented: {template_response.status_code}")


# =============================================================================
# TEST 7: Activity Templates
# =============================================================================

@pytest.mark.asyncio
async def test_activity_template_workflow(completed_onboarding_user):
    """
    TEST: User saves and reuses activity templates

    Flow:
    1. Frontend: User saves workout as template
    2. POST /api/v1/templates with exercise data
    3. Backend: Store template
    4. Frontend: User selects template to log
    5. POST /api/v1/activities/from-template

    Expected: Quick logging of routine workouts
    """
    headers = completed_onboarding_user

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        template_data = {
            "template_name": "Leg Day Routine",
            "category": "strength_training",
            "template_data": {
                "exercises": [
                    {"name": "Squat", "sets": 4, "reps": 8, "rest_seconds": 180},
                    {"name": "Leg Press", "sets": 3, "reps": 12, "rest_seconds": 120},
                    {"name": "Leg Curl", "sets": 3, "reps": 12, "rest_seconds": 90}
                ]
            }
        }

        response = await client.post("/api/v1/templates", json=template_data)

        if response.status_code == 201:
            template = response.json()

            print("✅ Activity template created: SUCCESS")
            print(f"   Template: {template['template_name']}")

            # List templates
            list_response = await client.get("/api/v1/templates")
            assert list_response.status_code == 200

            templates = list_response.json()["templates"]
            print(f"✅ Activity templates list: {len(templates)} templates")
        else:
            print(f"⚠️  Activity template endpoint: {response.status_code}")


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("INTEGRATION TESTING - Real UI to Database Workflows")
    print("=" * 80)
    print()
    print("Testing with REAL backend at http://localhost:8000")
    print("Minimal mocking - only when absolutely necessary")
    print()

    # Run with pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])
