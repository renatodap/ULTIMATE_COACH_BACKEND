"""
Unit tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_check(client: TestClient):
    """Test detailed health check endpoint."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "timestamp" in data
    assert "environment" in data
    assert "version" in data
    assert "checks" in data
    assert data["version"] == "1.0.0"


@pytest.mark.unit
def test_liveness_probe(client: TestClient):
    """Test liveness probe endpoint."""
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "alive"


@pytest.mark.unit
def test_readiness_probe(client: TestClient):
    """Test readiness probe endpoint."""
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ready"


@pytest.mark.unit
def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "ULTIMATE COACH API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "operational"
    assert "environment" in data
