"""
Pytest configuration and fixtures.

Shared test fixtures available to all tests.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """
    FastAPI test client fixture.

    Returns:
        TestClient: Test client for making requests
    """
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    """
    Mock Supabase client for testing.

    Returns:
        Mock: Mocked Supabase client
    """
    # TODO: Implement proper mocking
    pass
