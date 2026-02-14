"""
Health Check API Endpoints
"""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime, UTC
import time
import psutil
import logging
from typing import Dict, Any

from app.models.health import (
    HealthCheckResponse, 
    DetailedHealthResponse, 
    HealthStatus, 
    ComponentStatus,
    SystemMetrics
)
from app.core.config import settings

# Global startup time for uptime calculation
START_TIME = time.time()

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic Health Check",
    description="Simple health check endpoint that returns basic service status"
)
async def basic_health_check() -> HealthCheckResponse:
    """
    Basic health check endpoint.
    
    Returns basic service status and uptime information.
    This endpoint should respond quickly and not depend on external services.
    """
    try:
        uptime_seconds = time.time() - START_TIME
        
        return HealthCheckResponse(
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(UTC),
            service=settings.APP_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            uptime_seconds=uptime_seconds,
            message="Service is healthy and responding"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        
        return HealthCheckResponse(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.now(UTC),
            service=settings.APP_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            uptime_seconds=time.time() - START_TIME,
            message=f"Service health check failed: {str(e)}"
        )


@router.get(
    "/detailed",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed Health Check",
    description="Comprehensive health check with system metrics and component status"
)
async def detailed_health_check() -> DetailedHealthResponse:
    """
    Detailed health check endpoint with system metrics.
    
    Checks various components and returns comprehensive health information
    including system performance metrics and component status.
    """
    try:
        uptime_seconds = time.time() - START_TIME
        
        # Check system components
        components_status = await _check_system_components()
        
        # Get system metrics
        system_metrics = _get_system_metrics()
        
        # Determine overall health status
        overall_status = _determine_overall_status(components_status)
        
        system_info = {
            "platform": system_metrics.model_dump(),
            "python_version": _get_python_version(),
            "dependencies": _check_dependencies(),
            "components": {k: v.value for k, v in components_status.items()}
        }
        
        return DetailedHealthResponse(
            overall_status=overall_status,
            timestamp=datetime.now(UTC),
            service=settings.APP_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            uptime_seconds=uptime_seconds,
            components=components_status,
            system_info=system_info,
            message="Detailed health check completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        
        # Return degraded status with error information
        return DetailedHealthResponse(
            overall_status=HealthStatus.UNHEALTHY,
            timestamp=datetime.now(UTC),
            service=settings.APP_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            uptime_seconds=time.time() - START_TIME,
            components={"error": ComponentStatus.UNKNOWN},
            system_info={"error": str(e)},
            message=f"Health check failed: {str(e)}"
        )


@router.get(
    "/metrics",
    response_model=SystemMetrics,
    status_code=status.HTTP_200_OK,
    summary="System Metrics",
    description="Get current system performance metrics"
)
async def system_metrics() -> SystemMetrics:
    """Get current system performance metrics"""
    return _get_system_metrics()


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Kubernetes-style liveness probe endpoint"
)
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes-style liveness probe.
    Returns 200 if the service is alive and responding.
    This endpoint should not depend on external services.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": settings.APP_NAME
    }


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Kubernetes-style readiness probe endpoint"
)
async def readiness_probe() -> Dict[str, str]:
    """
    Kubernetes-style readiness probe.
    Returns 200 if the service is ready to receive traffic.
    This endpoint can check dependencies if needed.
    """
    # Check if service dependencies are ready
    try:
        # Add dependency checks here when available
        # For now, just return ready if basic health check passes
        await basic_health_check()
        
        return {
            "status": "ready",
            "timestamp": datetime.now(UTC).isoformat(),
            "service": settings.APP_NAME
        }
    except Exception as e:
        logger.warning(f"Readiness check failed: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "service": settings.APP_NAME,
                "error": str(e)
            }
        )


async def _check_system_components() -> Dict[str, ComponentStatus]:
    """Check status of system components"""
    components = {}
    
    # Check Python runtime
    components["python_runtime"] = ComponentStatus.UP
    
    # Check memory availability
    try:
        memory = psutil.virtual_memory()
        if memory.percent > 95:
            components["memory"] = ComponentStatus.DOWN
        elif memory.percent > 90:
            components["memory"] = ComponentStatus.DEGRADED
        else:
            components["memory"] = ComponentStatus.UP
    except Exception:
        components["memory"] = ComponentStatus.UNKNOWN
    
    # Check disk space
    try:
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            components["disk"] = ComponentStatus.DEGRADED
        elif disk.percent > 95:
            components["disk"] = ComponentStatus.DOWN
        else:
            components["disk"] = ComponentStatus.UP
    except Exception:
        components["disk"] = ComponentStatus.UNKNOWN
    
    # Check CPU load
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 95:
            components["cpu"] = ComponentStatus.DOWN
        elif cpu_percent > 80:
            components["cpu"] = ComponentStatus.DEGRADED
        else:
            components["cpu"] = ComponentStatus.UP
    except Exception:
        components["cpu"] = ComponentStatus.UNKNOWN
    
    return components


def _get_system_metrics() -> SystemMetrics:
    """Get current system performance metrics"""
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        
        # Get load average (Unix systems)
        try:
            load_avg = list(psutil.getloadavg())
        except AttributeError:
            load_avg = [0.0, 0.0, 0.0]  # Windows fallback
        
        # Get process count
        process_count = len(psutil.pids())
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_available_mb=memory.available / (1024 * 1024),
            disk_usage_percent=disk.percent,
            load_average=load_avg,
            process_count=process_count
        )
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}")
        
        # Return default values on error
        return SystemMetrics(
            cpu_percent=0.0,
            memory_percent=0.0,
            memory_available_mb=0.0,
            disk_usage_percent=0.0,
            load_average=[0.0, 0.0, 0.0],
            process_count=0
        )


def _determine_overall_status(components_status: Dict[str, ComponentStatus]) -> HealthStatus:
    """Determine overall health status based on component status"""
    
    if not components_status:
        return HealthStatus.UNKNOWN
    
    # Count component statuses
    up_count = sum(1 for status in components_status.values() if status == ComponentStatus.UP)
    degraded_count = sum(1 for status in components_status.values() if status == ComponentStatus.DEGRADED)
    down_count = sum(1 for status in components_status.values() if status == ComponentStatus.DOWN)
    unknown_count = sum(1 for status in components_status.values() if status == ComponentStatus.UNKNOWN)
    
    total_count = len(components_status)
    
    # Determine overall status
    if down_count > 0:
        return HealthStatus.UNHEALTHY
    elif degraded_count > total_count * 0.5:  # More than half degraded
        return HealthStatus.DEGRADED
    elif unknown_count > total_count * 0.5:  # More than half unknown
        return HealthStatus.UNKNOWN
    else:
        return HealthStatus.HEALTHY


def _get_python_version() -> str:
    """Get Python version information"""
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _check_dependencies() -> Dict[str, bool]:
    """Check if key dependencies are available"""
    dependencies = {}
    
    # Check FastAPI
    try:
        import fastapi
        dependencies["fastapi"] = True
    except ImportError:
        dependencies["fastapi"] = False
    
    # Check pydantic
    try:
        import pydantic
        dependencies["pydantic"] = True
    except ImportError:
        dependencies["pydantic"] = False
    
    # Check psutil
    try:
        import psutil
        dependencies["psutil"] = True
    except ImportError:
        dependencies["psutil"] = False
    
    return dependencies