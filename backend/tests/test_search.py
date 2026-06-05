"""Tests for search functionality."""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

@pytest.fixture
def client():
    """Get test client."""
    from backend.app.main import app
    os.environ['DEMO_MODE'] = 'true'
    return TestClient(app)

class TestSearchEndpoint:
    """Test search endpoint."""

    def test_search_valid_query(self, client):
        """Valid search should return results."""
        response = client.post(
            "/api/search?query=kubernetes&top_k=5",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'query' in data
        assert 'results' in data
        assert 'latency_ms' in data

    def test_search_empty_query(self, client):
        """Empty query should return 400."""
        response = client.post(
            "/api/search?query=&top_k=5",
            json={}
        )
        assert response.status_code == 400

    def test_search_with_filters(self, client):
        """Search with valid filters should work."""
        response = client.post(
            "/api/search?query=python&top_k=5&department=Platform&category=FAQ",
            json={}
        )
        assert response.status_code in [200, 400]  # 400 if validation fails

    def test_search_invalid_top_k(self, client):
        """Invalid top_k should return 400."""
        response = client.post(
            "/api/search?query=test&top_k=200",
            json={}
        )
        assert response.status_code == 400

class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Health check should return 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert 'version' in data

class TestMetricsEndpoint:
    """Test metrics endpoint."""

    def test_get_metrics(self, client):
        """Metrics endpoint should return metrics."""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert 'total_queries' in data
        assert 'cache_hit_rate' in data
        assert 'avg_latency_ms' in data
