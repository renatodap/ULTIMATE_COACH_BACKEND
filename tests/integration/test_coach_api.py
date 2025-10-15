"""
Integration tests for Coach API endpoints.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.api.dependencies import get_current_user
from app.api.v1.coach import get_supabase

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {"id": "test_user_id"}

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    return Mock()

@pytest.fixture
def auth_client(mock_user, mock_supabase_client):
    """FastAPI test client with mocked authentication and Supabase."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_supabase] = lambda: mock_supabase_client
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

class TestConfirmLog:
    """Test POST /api/v1/coach/confirm-log endpoint."""

    @patch('app.api.v1.coach.nutrition_service', new_callable=AsyncMock)
    def test_confirm_log_with_edits_updates_structured_data(self, mock_nutrition_service, auth_client, mock_supabase_client):
        """Should update structured_data in the database when edits are provided."""
        quick_entry_id = str(uuid4())
        user_id = "test_user_id"

        # Mock the initial quick_entry_log data
        initial_log_data = {
            "id": quick_entry_id,
            "user_id": user_id,
            "status": "pending",
            "log_type": "meal",
            "structured_data": {"food": "pancakes", "quantity": 2},
        }

        # Mock Supabase SELECT
        mock_select_response = Mock()
        mock_select_response.data = initial_log_data
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_select_response

        # Mock Supabase UPDATE
        mock_update_response = Mock()
        mock_update_response.data = [{"id": quick_entry_id}]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        # Mock nutrition_service.create_meal
        mock_meal = Mock()
        mock_meal.id = uuid4()
        mock_nutrition_service.create_meal.return_value = mock_meal

        # Define edits
        edits = {"quantity": 3, "notes": "with syrup"}

        # Call the endpoint
        response = auth_client.post(
            "/api/v1/coach/confirm-log",
            json={"quick_entry_id": quick_entry_id, "edits": edits},
        )

        # Assert response
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Assert that the update method was called with the correct data
        mock_supabase_client.table.return_value.update.assert_called_once()
        update_call_args = mock_supabase_client.table.return_value.update.call_args
        updated_data = update_call_args[0][0]

        # Check that structured_data includes the edits
        assert updated_data["structured_data"]["food"] == "pancakes"
        assert updated_data["structured_data"]["quantity"] == 3
        assert updated_data["structured_data"]["notes"] == "with syrup"
