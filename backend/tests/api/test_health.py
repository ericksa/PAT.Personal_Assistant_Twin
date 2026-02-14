"""
Tests for Health Check API Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import create_app


@pytest.fixture
def client():
    """Create test client for the FastAPI app"""
    app = create_app()
    return TestClient(app)


def test_basic_health_check(client):
    """Test basic health check endpoint"""
    response = client.get("/api/v1/health/")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    assert "message" in data
    
    assert data["status"] == "healthy"
    assert data["service"] == "PAT Backend API"
    assert isinstance(data["uptime_seconds"], (int, float))
    assert data["uptime_seconds"] >= 0


def test_detailed_health_check(client):
    """Test detailed health check endpoint"""
    response = client.get("/api/v1/health/detailed")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "overall_status" in data
    assert "timestamp" in data
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    assert "components" in data
    assert "system_info" in data
    assert "message" in data
    
    # Check that components are present
    assert "components" in data
    assert isinstance(data["components"], dict)
    
    # Check that system_info contains platform data
    assert "platform" in data["system_info"]
    assert "python_version" in data["system_info"]
    assert "dependencies" in data["system_info"]


def test_system_metrics(client):
    """Test system metrics endpoint"""
    response = client.get("/api/v1/health/metrics")
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Check required metrics fields
    required_fields = [
        "cpu_percent", "memory_percent", "memory_available_mb",
        "disk_usage_percent", "load_average", "process_count"
    ]
    
    for field in required_fields:
        assert field in data
    
    # Validate data types
    assert isinstance(data["cpu_percent"], (int, float))
    assert 0 <= data["cpu_percent"] <= 100
    
    assert isinstance(data["memory_percent"], (int, float))
    assert 0 <= data["memory_percent"] <= 100
    
    assert isinstance(data["memory_available_mb"], (int, float))
    assert data["memory_available_mb"] >= 0
    
    assert isinstance(data["disk_usage_percent"], (int, float))
    assert 0 <= data["disk_usage_percent"] <= 100
    
    assert isinstance(data["load_average"], list)
    assert len(data["load_average"]) == 3
    
    assert isinstance(data["process_count"], int)
    assert data["process_count"] >= 0


def test_liveness_probe(client):
    """Test liveness probe endpoint"""
    response = client.get("/api/v1/health/live")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert data["service"] == "PAT Backend API"


def test_readiness_probe(client):
    """Test readiness probe endpoint"""
    response = client.get("/api/v1/health/ready")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ready"
    assert "timestamp" in data
    assert data["service"] == "PAT Backend API"


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "environment" in data
    assert "status" in data
    assert "timestamp" in data
    assert "docs" in data
    
    assert data["name"] == "PAT Backend API"
    assert data["status"] == "running"
    assert data["environment"] == "development"


def test_health_status_enum():
    """Test health status enum values"""
    from app.models.health import HealthStatus
    
    assert HealthStatus.HEALTHY == "healthy"
    assert HealthStatus.DEGRADED == "degraded"
    assert HealthStatus.UNHEALTHY == "unhealthy"
    assert HealthStatus.UNKNOWN == "unknown"


def test_component_status_enum():
    """Test component status enum values"""
    from app.models.health import ComponentStatus
    
    assert ComponentStatus.UP == "up"
    assert ComponentStatus.DOWN == "down"
    assert ComponentStatus.DEGRADED == "degraded"
    assert ComponentStatus.UNKNOWN == "unknown"


@pytest.mark.parametrize("endpoint", [
    "/api/v1/health/",
    "/api/v1/health/detailed",
    "/api/v1/health/metrics",
    "/api/v1/health/live",
    "/api/v1/health/ready"
])
def test_all_health_endpoints_respond(client, endpoint):
    """Test that all health endpoints are accessible"""
    response = client.get(endpoint)
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])