"""
Pytest configuration and fixtures.

Shared test fixtures available to all tests.
"""

import os
from datetime import datetime, date
from typing import Generator, Dict, Any
from decimal import Decimal
from unittest.mock import Mock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


# ============================================================================
# FIXTURES - TEST CLIENT
# ============================================================================

@pytest.fixture
def client() -> TestClient:
    """
    FastAPI test client fixture.

    Returns:
        TestClient: Test client for making requests
    """
    return TestClient(app)


# ============================================================================
# FIXTURES - MOCK SUPABASE
# ============================================================================

@pytest.fixture
def mock_supabase() -> Mock:
    """
    Mock Supabase client for testing without database.

    Returns:
        Mock: Mocked Supabase client with common methods
    """
    mock = MagicMock()

    # Mock table() chain
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.insert.return_value = mock
    mock.update.return_value = mock
    mock.delete.return_value = mock
    mock.eq.return_value = mock
    mock.neq.return_value = mock
    mock.gte.return_value = mock
    mock.lte.return_value = mock
    mock.order.return_value = mock
    mock.limit.return_value = mock
    mock.single.return_value = mock
    mock.execute.return_value = Mock(data=[], count=0)

    return mock


@pytest.fixture
def mock_supabase_user() -> Dict[str, Any]:
    """Mock authenticated user data."""
    return {
        'id': 'test-user-id-123',
        'email': 'test@example.com',
        'age': 30,
        'sex': 'male',
        'height_cm': 180,
        'weight_kg': 80,
        'primary_goal': 'build_muscle',
        'activity_level': 'moderately_active',
        'onboarding_completed': True,
        'daily_calorie_goal': 2500,
        'daily_protein_g': 160,
        'daily_carbs_g': 250,
        'daily_fat_g': 80,
    }


# ============================================================================
# FIXTURES - TEST DATA
# ============================================================================

@pytest.fixture
def sample_food_simple() -> Dict[str, Any]:
    """Sample simple food (chicken breast)."""
    return {
        'id': 'food-simple-001',
        'name': 'Chicken Breast',
        'composition_type': 'simple',
        'calories_per_100g': 165,
        'protein_g_per_100g': 31,
        'carbs_g_per_100g': 0,
        'fat_g_per_100g': 3.6,
        'is_public': True,
        'verified': True,
    }


@pytest.fixture
def sample_food_branded() -> Dict[str, Any]:
    """Sample branded food (Quest Bar)."""
    return {
        'id': 'food-branded-001',
        'name': 'Quest Bar - Chocolate Chip Cookie Dough',
        'composition_type': 'branded',
        'calories_per_100g': 360,
        'protein_g_per_100g': 36,
        'carbs_g_per_100g': 40,
        'fat_g_per_100g': 12,
        'is_public': True,
        'verified': True,
    }


@pytest.fixture
def sample_food_composed() -> Dict[str, Any]:
    """Sample composed food (protein shake recipe)."""
    return {
        'id': 'food-composed-001',
        'name': 'Protein Shake',
        'composition_type': 'composed',
        'calories_per_100g': 0,  # Ignored for composed
        'protein_g_per_100g': 0,
        'carbs_g_per_100g': 0,
        'fat_g_per_100g': 0,
        'recipe_items': [
            {'food_id': 'whey-protein-id', 'grams': 30},
            {'food_id': 'banana-id', 'grams': 120},
            {'food_id': 'milk-id', 'grams': 250},
        ],
        'servings_count': 1,
        'composed_total_grams': 400,
        'is_public': True,
        'verified': False,
    }


@pytest.fixture
def sample_serving() -> Dict[str, Any]:
    """Sample food serving (1 scoop)."""
    return {
        'id': 'serving-001',
        'food_id': 'food-simple-001',
        'serving_unit': 'scoop',
        'serving_label': 'large',
        'grams_per_serving': 30,
    }


@pytest.fixture
def sample_activity() -> Dict[str, Any]:
    """Sample activity (morning run)."""
    return {
        'id': 'activity-001',
        'user_id': 'test-user-id-123',
        'category': 'cardio_steady_state',
        'activity_name': 'Morning Run',
        'start_time': datetime(2025, 10, 16, 6, 0, 0),
        'end_time': datetime(2025, 10, 16, 6, 45, 0),
        'duration_minutes': 45,
        'calories_burned': 400,
        'intensity_mets': 8.0,
        'metrics': {
            'distance_km': 6.5,
            'avg_heart_rate': 145,
            'max_heart_rate': 165,
        },
        'notes': 'Felt great today!',
        'created_at': datetime(2025, 10, 16, 6, 45, 0),
        'updated_at': datetime(2025, 10, 16, 6, 45, 0),
        'deleted_at': None,
    }


@pytest.fixture
def sample_meal() -> Dict[str, Any]:
    """Sample meal (breakfast)."""
    return {
        'id': 'meal-001',
        'user_id': 'test-user-id-123',
        'meal_type': 'breakfast',
        'logged_at': datetime(2025, 10, 16, 8, 0, 0),
        'total_calories': 650,
        'total_protein_g': 45,
        'total_carbs_g': 60,
        'total_fat_g': 20,
        'source': 'manual',
        'created_at': datetime(2025, 10, 16, 8, 0, 0),
    }


@pytest.fixture
def sample_body_metric() -> Dict[str, Any]:
    """Sample body weight measurement."""
    return {
        'id': 'metric-001',
        'user_id': 'test-user-id-123',
        'recorded_at': datetime(2025, 10, 16, 7, 0, 0),
        'weight_kg': 79.5,
        'body_fat_percentage': 15.5,
    }


# ============================================================================
# FIXTURES - ENVIRONMENT
# ============================================================================

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Auto-mock environment variables for all tests."""
    env_vars = {
        'SUPABASE_URL': 'https://test-project.supabase.co',
        'SUPABASE_KEY': 'test-anon-key',
        'SUPABASE_SERVICE_KEY': 'test-service-key',
        'SUPABASE_JWT_SECRET': 'test-jwt-secret',
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'ENVIRONMENT': 'test',
        'LOG_LEVEL': 'ERROR',  # Suppress logs during tests
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)


# ============================================================================
# FIXTURES - DATES & TIMES
# ============================================================================

@pytest.fixture
def today() -> date:
    """Current date for testing."""
    return date(2025, 10, 16)


@pytest.fixture
def yesterday() -> date:
    """Yesterday's date for testing."""
    return date(2025, 10, 15)


@pytest.fixture
def test_datetime() -> datetime:
    """Fixed datetime for testing."""
    return datetime(2025, 10, 16, 12, 0, 0)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def assert_decimal_equal(actual: Decimal, expected: Decimal, tolerance: Decimal = Decimal('0.1')):
    """Assert two decimals are equal within tolerance."""
    diff = abs(actual - expected)
    assert diff <= tolerance, f"Expected {expected}, got {actual} (diff: {diff})"


def assert_nutrition_equal(
    actual: Dict[str, Any],
    expected: Dict[str, Any],
    tolerance: float = 1.0
):
    """Assert nutrition values are equal within tolerance."""
    assert abs(actual['calories'] - expected['calories']) <= tolerance
    assert abs(actual['protein_g'] - expected['protein_g']) <= tolerance
    assert abs(actual['carbs_g'] - expected['carbs_g']) <= tolerance
    assert abs(actual['fat_g'] - expected['fat_g']) <= tolerance
