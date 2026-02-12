from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime


class ServiceType(str, Enum):
    python = "python"
    docker = "docker"


class ServiceStatus(str, Enum):
    stopped = "stopped"
    starting = "starting"
    running = "running"
    stopping = "stopping"
    error = "error"


class Service(BaseModel):
    id: str
    name: str
    description: str
    type: ServiceType
    status: ServiceStatus = ServiceStatus.stopped
    port: Optional[int] = None
    health_url: Optional[str] = None
    pid: Optional[int] = None
    uptime: Optional[float] = None  # Seconds
    start_time: Optional[datetime] = None
    container_id: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    dependencies: List[str] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)


class ServiceAction(BaseModel):
    action: str = Field(..., pattern="^(start|stop|restart)$")


class ServiceActionResponse(BaseModel):
    success: bool
    message: str
    service_id: str


class LogEntry(BaseModel):
    timestamp: datetime
    level: str = Field(..., pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    message: str
    source: str  # Service ID


class SystemHealth(BaseModel):
    overall_status: str = Field(..., pattern=r"^(healthy|degraded|unhealthy)$")
    total_services: int
    running: int
    stopped: int
    errored: int
    python_version: str
    docker_running: bool
