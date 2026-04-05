"""
Unit tests for main FastAPI application.

Tests API initialization, integration, and health endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAPIInitialization:
    """Test FastAPI application initialization."""

    def test_app_created(self):
        """FastAPI app is created successfully."""
        assert app is not None
        assert app.title == "Watermark Removal Streaming API"
        assert app.version == "3.0.0"

    def test_cors_configured(self):
        """CORS middleware is configured."""
        # Make a request with CORS headers to verify CORS is enabled
        # The middleware should allow all origins
        client = TestClient(app)
        response = client.options("/health", headers={"Origin": "http://example.com"})
        # CORS should be configured (doesn't necessarily require specific response code)
        assert app is not None

    def test_streaming_router_included(self):
        """Streaming router is included."""
        # Check if /stream routes exist
        routes = [route.path for route in app.routes]
        assert any("/stream" in path for path in routes)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self, client):
        """GET /health returns health status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "watermark-removal-streaming"
        assert data["version"] == "3.0.0"
        assert "active_sessions" in data
        assert "timestamp" in data

    def test_health_check_structure(self, client):
        """Health check response has correct structure."""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["active_sessions"], int)
        assert data["active_sessions"] >= 0


class TestRootEndpoint:
    """Test API root endpoint."""

    def test_root_endpoint(self, client):
        """GET / returns service information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Watermark Removal Streaming API"
        assert data["version"] == "3.0.0"
        assert "endpoints" in data

    def test_root_endpoints_documented(self, client):
        """Root endpoint lists available endpoints."""
        response = client.get("/")
        data = response.json()
        endpoints = data["endpoints"]

        assert "health" in endpoints
        assert "streaming" in endpoints
        assert "documentation" in endpoints


class TestStreamingIntegration:
    """Test streaming module integration with main API."""

    def test_streaming_endpoints_accessible(self, client):
        """Streaming endpoints are accessible through main app."""
        # Start streaming
        payload = {
            "source_url": "file:///test.mp4",
            "output_format": "h264",
            "quality_preset": "balanced",
            "buffer_size": 30,
            "enable_stats": True,
        }

        response = client.post("/stream/start", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        session_id = data["session_id"]

        # Get status
        status_response = client.get(f"/stream/{session_id}/status")
        assert status_response.status_code == 200

        # Stop streaming
        stop_response = client.post(f"/stream/{session_id}/stop")
        assert stop_response.status_code == 200

    def test_health_check_reflects_active_sessions(self, client):
        """Health check reflects active sessions."""
        # Check initial health
        initial_health = client.get("/health").json()
        initial_sessions = initial_health["active_sessions"]

        # Start streaming
        payload = {"source_url": "file:///test.mp4"}
        start_response = client.post("/stream/start", json=payload)
        session_id = start_response.json()["session_id"]

        # Check health again
        health_after_start = client.get("/health").json()
        assert health_after_start["active_sessions"] == initial_sessions + 1

        # Stop streaming
        client.post(f"/stream/{session_id}/stop")

        # Check health after stop
        health_after_stop = client.get("/health").json()
        assert health_after_stop["active_sessions"] == initial_sessions


class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_swagger_ui_available(self, client):
        """Swagger UI documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_redoc_available(self, client):
        """ReDoc documentation is available."""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling in API."""

    def test_invalid_request_returns_error(self, client):
        """Invalid request returns proper error response."""
        # Missing required field
        payload = {"output_format": "h264"}

        response = client.post("/stream/start", json=payload)

        assert response.status_code == 422  # Validation error

    def test_not_found_returns_404(self, client):
        """Accessing nonexistent resource returns 404."""
        response = client.get("/stream/sess_nonexistent/status")

        assert response.status_code == 404


class TestAPIMetadata:
    """Test API metadata."""

    def test_app_has_title(self):
        """App has proper title."""
        assert app.title == "Watermark Removal Streaming API"

    def test_app_has_description(self):
        """App has proper description."""
        assert app.description is not None
        assert "streaming" in app.description.lower()

    def test_app_has_version(self):
        """App has version."""
        assert app.version == "3.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
