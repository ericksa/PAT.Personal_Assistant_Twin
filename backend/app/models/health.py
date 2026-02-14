"""
Health Check API Models
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentStatus(str, Enum):
    """Component status enumeration"""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class HealthCheckResponse(BaseModel):
    """Standard health check response"""
    status: HealthStatus
    timestamp: datetime
    service: str
    version: str
    environment: str
    uptime_seconds: float
    message: str = "Service is healthy"


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with component status"""
    overall_status: HealthStatus
    timestamp: datetime
    service: str
    version: str
    environment: str
    uptime_seconds: float
    components: Dict[str, ComponentStatus]
    system_info: Dict[str, Any]
    message: str = "Service health check completed"


class ComponentHealth(BaseModel):
    """Individual component health status"""
    name: str
    status: ComponentStatus
    message: Optional[str] = None
    last_check: datetime
    response_time_ms: Optional[float] = None


class SystemMetrics(BaseModel):
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    load_average: list[float]
    process_count: int