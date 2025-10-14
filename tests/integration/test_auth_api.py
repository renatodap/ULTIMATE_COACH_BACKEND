"""
Integration tests for Authentication API endpoints.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app

# Use a non-authenticated client for signup/login tests
client = TestClient(app)


class TestSignup:
    """Test POST /api/v1/auth/signup endpoint."""

    @patch("app.services.auth_service.auth_service.signup", new_callable=AsyncMock)
    def test_signup_success(self, mock_signup):
        """Should return 201 on successful signup."""
        # Arrange
        mock_signup.return_value = {
            "user": {
                "id": "a-fake-uuid",
                "email": "test@example.com",
                "full_name": "Test User",
            },
            "session": {
                "access_token": "fake-access-token",
                "refresh_token": "fake-refresh-token",
            },
        }

        request_data = {
            "email": "test@example.com",
            "password": "ValidPassword123!",
            "full_name": "Test User",
        }

        # Act
        response = client.post("/api/v1/auth/signup", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["full_name"] == "Test User"
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

        mock_signup.assert_awaited_once_with(
            email="test@example.com",
            password="ValidPassword123!",
            full_name="Test User",
        )

    def test_signup_missing_fields(self):
        """Should return 422 for missing required fields."""
        request_data = {"email": "test@example.com"}  # Missing password
        response = client.post("/api/v1/auth/signup", json=request_data)
        assert response.status_code == 422

    @patch("app.services.auth_service.auth_service.signup", new_callable=AsyncMock)
    def test_signup_service_value_error(self, mock_signup):
        """Should return 400 if auth service raises ValueError (e.g., weak password)."""
        # Arrange
        mock_signup.side_effect = ValueError("Password is too weak.")
        request_data = {
            "email": "test@example.com",
            "password": "weakpassword",
            "full_name": "Test User",
        }

        # Act
        response = client.post("/api/v1/auth/signup", json=request_data)

        # Assert
        assert response.status_code == 400
        assert "Password is too weak" in response.json()["detail"]

    @patch("app.services.auth_service.auth_service.signup", new_callable=AsyncMock)
    def test_signup_service_generic_exception(self, mock_signup):
        """Should return 500 if a generic exception occurs."""
        # Arrange
        mock_signup.side_effect = Exception("Something went wrong with Supabase.")
        request_data = {
            "email": "test@example.com",
            "password": "ValidPassword123!",
            "full_name": "Test User",
        }

        # Act
        response = client.post("/api/v1/auth/signup", json=request_data)

        # Assert
        assert response.status_code == 500
        assert "Failed to create account" in response.json()["detail"]
