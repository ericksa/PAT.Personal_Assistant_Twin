"""
Comprehensive async tests for health check endpoints
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import status

from app.main import create_app
from app.models.health import HealthStatus, ComponentStatus


class TestHealthEndpoints:
    """Test suite for all health check endpoints"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing"""
        return create_app()

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    def test_basic_health_check_success(self, client):
        """Test basic health check endpoint returns 200 on success"""
        response = client.get("/api/v1/health/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert "message" in data
        
        # Check status values
        assert data["status"] in [status.value for status in HealthStatus]
        assert data["service"] == "PAT Backend API"
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0

    def test_detailed_health_check_success(self, client):
        """Test detailed health check endpoint returns comprehensive information"""
        response = client.get("/api/v1/health/detailed")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check basic fields
        assert "overall_status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert "components" in data
        assert "system_info" in data
        assert "message" in data
        
        # Check components structure
        components = data["components"]
        assert isinstance(components, dict)
        expected_components = ["python_runtime", "memory", "disk", "cpu"]
        for component in expected_components:
            assert component in components
            assert components[component] in [status.value for status in ComponentStatus]

    def test_system_metrics_endpoint(self, client):
        """Test system metrics endpoint returns performance data"""
        response = client.get("/api/v1/health/metrics")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check required metrics fields
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "memory_available_mb" in data
        assert "disk_usage_percent" in data
        assert "load_average" in data
        assert "process_count" in data
        
        # Check data types and ranges
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
        assert all(isinstance(x, (int, float)) for x in data["load_average"])
        assert isinstance(data["process_count"], int)
        assert data["process_count"] >= 0

    def test_liveness_probe_endpoint(self, client):
        """Test liveness probe endpoint returns basic alive status"""
        response = client.get("/api/v1/health/live")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        
        # Check values
        assert data["status"] == "alive"
        assert data["service"] == "PAT Backend API"
        
        # Verify timestamp format
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        assert isinstance(timestamp, datetime)

    def test_readiness_probe_endpoint(self, client):
        """Test readiness probe endpoint returns ready status when healthy"""
        response = client.get("/api/v1/health/ready")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        
        # Check values
        assert data["status"] == "ready"
        assert data["service"] == "PAT Backend API"

    @pytest.mark.asyncio
    async def test_health_check_response_time(self, client):
        """Test that health check endpoints respond quickly"""
        import time
        
        # Test basic health check response time
        start_time = time.time()
        response = client.get("/api/v1/health/")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
        
        # Test detailed health check response time (can be slightly slower)
        start_time = time.time()
        response = client.get("/api/v1/health/detailed")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds

    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.cpu_percent')
    def test_detailed_health_with_mocked_system_data(self, mock_cpu, mock_disk, mock_memory, client):
        """Test detailed health check with mocked system data"""
        # Mock system metrics
        mock_memory.return_value = MagicMock(percent=45.5, available=8 * 1024**3)
        mock_disk.return_value = MagicMock(percent=67.2)
        mock_cpu.return_value = 23.1
        
        response = client.get("/api/v1/health/detailed")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify components are properly checked
        components = data["components"]
        assert "memory" in components
        assert "disk" in components
        assert "cpu" in components
        assert "python_runtime" in components

    @patch('psutil.virtual_memory')
    def test_health_check_with_high_memory_usage(self, mock_memory, client):
        """Test health check behavior with high memory usage"""
        # Mock high memory usage (95%)
        mock_memory.return_value = MagicMock(percent=95.0, available=512 * 1024**3)
        
        response = client.get("/api/v1/health/detailed")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # With 95% memory usage, the memory component should be DOWN
        components = data["components"]
        assert components["memory"] == ComponentStatus.DOWN.value
        
        # Overall status should reflect the degraded state
        assert data["overall_status"] in [HealthStatus.DEGRADED.value, HealthStatus.UNHEALTHY.value]

    @patch('psutil.disk_usage')
    def test_health_check_with_high_disk_usage(self, mock_disk, client):
        """Test health check behavior with high disk usage"""
        # Mock high disk usage (92%)
        mock_disk.return_value = MagicMock(percent=92.0)
        
        response = client.get("/api/v1/health/detailed")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # With 92% disk usage, the disk component should be DEGRADED
        components = data["components"]
        assert components["disk"] == ComponentStatus.DEGRADED.value

    @patch('psutil.cpu_percent')
    def test_health_check_with_high_cpu_usage(self, mock_cpu, client):
        """Test health check behavior with high CPU usage"""
        # Mock high CPU usage (97%)
        mock_cpu.return_value = 97.0
        
        response = client.get("/api/v1/health/detailed")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # With 97% CPU usage, the cpu component should be DOWN
        components = data["components"]
        assert components["cpu"] == ComponentStatus.DOWN.value

    def test_health_check_consistency(self, client):
        """Test that multiple health checks return consistent service info"""
        # Make multiple requests
        response1 = client.get("/api/v1/health/")
        response2 = client.get("/api/v1/health/")
        
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Service information should be consistent
        assert data1["service"] == data2["service"]
        assert data1["version"] == data2["version"]
        assert data1["environment"] == data2["environment"]
        
        # Uptime should increase or stay the same
        assert data2["uptime_seconds"] >= data1["uptime_seconds"]

    def test_health_check_error_handling(self, client):
        """Test health check endpoints handle errors gracefully"""
        # These endpoints should never return 500 errors
        # They should always return 200 with appropriate status
        
        endpoints = [
            "/api/v1/health/",
            "/api/v1/health/detailed",
            "/api/v1/health/metrics",
            "/api/v1/health/live",
            "/api/v1/health/ready"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK
            
            # Verify response has expected structure
            data = response.json()
            assert isinstance(data, dict)
            assert len(data) > 0

    def test_health_check_schema_validation(self, client):
        """Test that health check responses match expected schemas"""
        # Test basic health check schema
        response = client.get("/api/v1/health/")
        data = response.json()
        
        # Verify all expected fields are present and have correct types
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["service"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["environment"], str)
        assert isinstance(data["uptime_seconds"], (int, float))
        assert isinstance(data["message"], str)

    def test_uptime_calculation(self, client):
        """Test that uptime calculations are reasonable"""
        response = client.get("/api/v1/health/")
        data = response.json()
        
        uptime = data["uptime_seconds"]
        
        # Uptime should be positive
        assert uptime > 0
        
        # Uptime should be reasonable for a test (not days)
        assert uptime < 3600  # Less than 1 hour

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, client):
        """Test multiple concurrent health check requests"""
        import asyncio
        import aiohttp
        
        # Make multiple concurrent requests
        tasks = []
        for _ in range(5):
            task = asyncio.create_task(
                asyncio.to_thread(client.get, "/api/v1/health/")
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "status" in data
            assert data["status"] in [status.value for status in HealthStatus]

    def test_health_check_environment_variables(self, client):
        """Test that health check returns correct environment information"""
        response = client.get("/api/v1/health/")
        data = response.json()
        
        # Verify environment-specific information
        assert data["service"] == "PAT Backend API"
        assert isinstance(data["version"], str)
        assert data["environment"] in ["development", "testing", "staging", "production"]


class TestHealthModels:
    """Test health check data models"""

    def test_health_status_enum(self):
        """Test HealthStatus enum values"""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.UNKNOWN == "unknown"

    def test_component_status_enum(self):
        """Test ComponentStatus enum values"""
        assert ComponentStatus.UP == "up"
        assert ComponentStatus.DOWN == "down"
        assert ComponentStatus.DEGRADED == "degraded"
        assert ComponentStatus.UNKNOWN == "unknown"


if __name__ == "__main__":
    pytest.main([__file__])