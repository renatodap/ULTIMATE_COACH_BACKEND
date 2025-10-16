"""
Unit tests for NutritionService.

Tests business logic for foods, servings, meals, and nutrition calculations.
Uses mocked Supabase client to isolate service layer.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from app.services.nutrition_service import nutrition_service
from app.models.nutrition import Food, FoodServing, Meal, MealItemBase
from app.models.errors import (
    SearchQueryTooShortError,
    FoodNotFoundError,
    InvalidServingError,
    ServingMismatchError,
    MealEmptyError,
    InvalidGramsPerServingError,
)


# =====================================================
# Test Data Fixtures
# =====================================================

@pytest.fixture
def sample_food_data():
    """Sample food database row."""
    return {
        "id": str(uuid4()),
        "name": "Grilled Chicken Breast",
        "brand_name": None,
        "calories_per_100g": Decimal("165.0"),
        "protein_g_per_100g": Decimal("31.0"),
        "carbs_g_per_100g": Decimal("0.0"),
        "fat_g_per_100g": Decimal("3.6"),
        "fiber_g_per_100g": Decimal("0.0"),
        "sugar_g_per_100g": None,
        "sodium_mg_per_100g": None,
        "food_type": "ingredient",
        "dietary_flags": None,
        "is_public": True,
        "verified": True,
        "usage_count": 100,
        "created_by": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_serving_data(sample_food_data):
    """Sample serving database row."""
    return {
        "id": str(uuid4()),
        "food_id": sample_food_data["id"],
        "serving_size": 1.0,
        "serving_unit": "medium breast",
        "serving_label": "1 medium breast (174g)",
        "grams_per_serving": 174.0,
        "is_default": True,
        "display_order": 0,
        "created_at": datetime.now().isoformat(),
    }


@pytest.fixture
def mock_supabase_response(sample_food_data, sample_serving_data):
    """Mock Supabase query response."""
    mock_response = Mock()
    mock_response.data = [{
        **sample_food_data,
        "food_servings": [sample_serving_data]
    }]
    return mock_response


# =====================================================
# Search Foods Tests
# =====================================================

class TestSearchFoods:
    """Test food search functionality."""

    @pytest.mark.asyncio
    async def test_search_query_too_short_raises_error(self):
        """Should raise SearchQueryTooShortError for queries < 2 chars."""
        with pytest.raises(SearchQueryTooShortError) as exc_info:
            await nutrition_service.search_foods(query="a", limit=20)

        assert exc_info.value.code == "NUTRITION_001"
        assert "2 characters" in exc_info.value.message

    @pytest.mark.asyncio
    @patch('app.services.nutrition_service.supabase_service')
    async def test_search_foods_returns_public_foods(self, mock_supabase, mock_supabase_response):
        """Should return public foods from text search."""
        (
            mock_supabase.client.table.return_value.select.return_value.eq.return_value.ilike.return_value.order.return_value.order.return_value.limit.return_value.execute
        ).return_value = mock_supabase_response

        result = await nutrition_service.search_foods(query="chicken", limit=20)

        assert len(result) == 1
        assert result[0].name == "Grilled Chicken Breast"
        assert len(result[0].servings) == 1

    @pytest.mark.asyncio
    @patch('app.services.nutrition_service.supabase_service')
    async def test_search_includes_user_custom_foods(self, mock_supabase, sample_food_data, sample_serving_data):
        """Should include user's custom foods in search results."""
        user_id = uuid4()

        # Mock public foods (empty)
        empty_public = Mock()
        empty_public.data = []

        # Mock custom foods
        custom_food_data = {**sample_food_data, "name": "My Custom Recipe", "created_by": str(user_id)}
        custom_response = Mock()
        custom_response.data = [{**custom_food_data, "food_servings": [sample_serving_data]}]

        mock_supabase.client.table.return_value.select.return_value\
            .eq.return_value.text_search.return_value.order.return_value\
            .order.return_value.limit.return_value.execute.return_value = empty_public

        mock_supabase.client.table.return_value.select.return_value\
            .eq.return_value.ilike.return_value.limit.return_value.execute.return_value = custom_response

        result = await nutrition_service.search_foods(query="recipe", limit=20, user_id=user_id)

        assert len(result) == 1
        assert result[0].name == "My Custom Recipe"


# =====================================================
# Create Custom Food Tests
# =====================================================

class TestCreateCustomFood:
    """Test custom food creation with grams_per_serving."""

    @pytest.mark.asyncio
    async def test_invalid_grams_per_serving_raises_error(self):
        """Should raise InvalidGramsPerServingError for grams <= 0."""
        with pytest.raises(InvalidGramsPerServingError) as exc_info:
            await nutrition_service.create_custom_food(
                user_id=uuid4(),
                name="Test Food",
                brand_name=None,
                serving_size=Decimal("1"),
                serving_unit="cookie",
                grams_per_serving=Decimal("0"),  # Invalid!
                calories=Decimal("100"),
                protein_g=Decimal("5"),
                carbs_g=Decimal("10"),
                fat_g=Decimal("2"),
            )

        assert exc_info.value.code == "NUTRITION_301"

    @pytest.mark.asyncio
    @patch('app.services.nutrition_service.supabase_service')
    async def test_create_custom_food_converts_to_per_100g(self, mock_supabase):
        """Should correctly convert nutrition from per-serving to per-100g."""
        # Mock food insert
        food_id = str(uuid4())
        mock_food_response = Mock()
        mock_food_response.data = [{
            "id": food_id,
            "name": "Test Cookie",
            "brand_name": None,
            "calories_per_100g": 480.0,  # 120 * (100/25)
            "protein_g_per_100g": 32.0,   # 8 * 4
            "carbs_g_per_100g": 48.0,     # 12 * 4
            "fat_g_per_100g": 16.0,       # 4 * 4
            "fiber_g_per_100g": None,
            "food_type": "dish",
            "is_public": False,
            "created_by": str(uuid4()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }]

        # Mock serving insert
        mock_serving_response = Mock()
        mock_serving_response.data = [{
            "id": str(uuid4()),
            "food_id": food_id,
            "serving_size": 1.0,
            "serving_unit": "cookie",
            "grams_per_serving": 25.0,
            "is_default": True,
            "display_order": 0,
            "created_at": datetime.now().isoformat(),
        }]

        mock_supabase.client.table.return_value.insert.return_value.execute.side_effect = [
            mock_food_response,
            mock_serving_response,
        ]

        result = await nutrition_service.create_custom_food(
            user_id=uuid4(),
            name="Test Cookie",
            brand_name=None,
            serving_size=Decimal("1"),
            serving_unit="cookie",
            grams_per_serving=Decimal("25"),  # 1 cookie = 25g
            calories=Decimal("120"),  # 120 cal per cookie
            protein_g=Decimal("8"),
            carbs_g=Decimal("12"),
            fat_g=Decimal("4"),
        )

        assert result.name == "Test Cookie"
        assert result.calories_per_100g == 480.0  # Correct conversion
        assert result.protein_g_per_100g == 32.0
        assert len(result.servings) == 1


# =====================================================
# Create Meal Tests (with N+1 fix)
# =====================================================

class TestCreateMeal:
    """Test meal creation with batched food fetching."""

    @pytest.mark.asyncio
    async def test_empty_meal_raises_error(self):
        """Should raise MealEmptyError for meals with no items."""
        with pytest.raises(MealEmptyError) as exc_info:
            await nutrition_service.create_meal(
                user_id=uuid4(),
                name="Test Meal",
                meal_type="lunch",
                logged_at=None,
                notes=None,
                items=[],  # Empty!
            )

        assert exc_info.value.code == "NUTRITION_202"

    @pytest.mark.asyncio
    @patch('app.services.nutrition_service.supabase_service')
    async def test_create_meal_batches_food_queries(self, mock_supabase, sample_food_data, sample_serving_data):
        """Should fetch all foods in single query (fix N+1 issue)."""
        food_id = uuid4()
        serving_id = uuid4()

        # Mock batch food fetch
        mock_foods_response = Mock()
        mock_foods_response.data = [{
            **sample_food_data,
            "id": str(food_id),
            "food_servings": [{**sample_serving_data, "id": str(serving_id), "food_id": str(food_id)}]
        }]

        # Mock meal creation
        meal_id = str(uuid4())
        mock_meal_response = Mock()
        mock_meal_response.data = [{
            "id": meal_id,
            "user_id": str(uuid4()),
            "name": "Test Meal",
            "meal_type": "lunch",
            "logged_at": datetime.now().isoformat(),
            "notes": None,
            "total_calories": 287.1,  # 165 * 1.74
            "total_protein_g": 53.94,
            "total_carbs_g": 0.0,
            "total_fat_g": 6.264,
            "source": "manual",
            "ai_confidence": None,
            "ai_cost_usd": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }]

        # Mock meal items creation
        mock_items_response = Mock()
        mock_items_response.data = [{
            "id": str(uuid4()),
            "meal_id": meal_id,
            "food_id": str(food_id),
            "quantity": 1.0,
            "serving_id": str(serving_id),
            "grams": 174.0,
            "calories": 287.1,
            "protein_g": 53.94,
            "carbs_g": 0.0,
            "fat_g": 6.264,
            "display_unit": "medium breast",
            "display_label": "1 medium breast (174g)",
            "display_order": 0,
            "created_at": datetime.now().isoformat(),
        }]

        # Set up mock chain
        mock_supabase.client.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_foods_response
        mock_supabase.client.table.return_value.insert.return_value.execute.side_effect = [
            mock_meal_response,
            mock_items_response,
        ]

        result = await nutrition_service.create_meal(
            user_id=uuid4(),
            name="Test Meal",
            meal_type="lunch",
            logged_at=None,
            notes=None,
            items=[MealItemBase(food_id=food_id, quantity=Decimal("1"), serving_id=serving_id)],
        )

        assert result.name == "Test Meal"
        assert len(result.items) == 1
        # Verify batch fetch was called (not individual get_food calls)
        mock_supabase.client.table.return_value.select.return_value.in_.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.nutrition_service.supabase_service')
    async def test_serving_mismatch_raises_error(self, mock_supabase, sample_food_data, sample_serving_data):
        """Should raise ServingMismatchError if serving doesn't belong to food."""
        food_id = uuid4()
        wrong_food_id = uuid4()
        serving_id = uuid4()

        # Mock food with serving that belongs to DIFFERENT food
        mock_foods_response = Mock()
        mock_foods_response.data = [{
            **sample_food_data,
            "id": str(food_id),
            "food_servings": [{
                **sample_serving_data,
                "id": str(serving_id),
                "food_id": str(wrong_food_id)  # Mismatch!
            }]
        }]

        mock_supabase.client.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_foods_response

        with pytest.raises(ServingMismatchError) as exc_info:
            await nutrition_service.create_meal(
                user_id=uuid4(),
                name="Test Meal",
                meal_type="lunch",
                logged_at=None,
                notes=None,
                items=[MealItemBase(food_id=food_id, quantity=Decimal("1"), serving_id=serving_id)],
            )

        assert exc_info.value.code == "NUTRITION_104"
        assert str(food_id) in exc_info.value.message
