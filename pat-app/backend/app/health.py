from fastapi import APIRouter
from pydantic import BaseModel
import time
import psutil
from typing import Optional

router = APIRouter()


class HealthStatus(BaseModel):
    status: str
    message: Optional[str] = None
    uptime: float
    version: str = "0.1.0"
    timestamp: float = time.time()


start_time = time.time()


@router.get("/", response_model=HealthStatus)
def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "uptime": time.time() - start_time}


@router.get("/detailed")
def detailed_health_check():
    """
    Detailed health check with system metrics
    Returns comprehensive system health information including CPU, memory, and disk usage
    """
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    load_1, load_5, load_15 = psutil.getloadavg()

    return {
        "status": "healthy",
        "system": {
            "memory": {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "percent": mem.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
            },
            "cpu": {
                "load_1m": load_1,
                "load_5m": load_5,
                "load_15m": load_15,
                "percent_per_core": psutil.cpu_percent(percpu=True),
            },
        },
        "uptime": time.time() - start_time,
        "timestamp": time.time(),
        "version": "0.1.0",
    }


@router.get("/liveness")
def liveness_probe():
    """Kubernetes liveness probe endpoint"""
    return {"status": "alive"}


@router.get("/readiness")
def readiness_probe():
    """Kubernetes readiness probe endpoint"""
    # Add any necessary readiness checks here (e.g., database connection)
    return {
        "status": "ready",
        "services": {
            "database": "ready"  # This should be dynamically checked
        },
    }
