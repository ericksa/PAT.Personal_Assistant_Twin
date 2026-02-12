"""API routes for service management"""

from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import logging

from models import Service, ServiceAction, ServiceActionResponse, SystemHealth, LogEntry
from config import PYTHON_SERVICES, DOCKER_SERVICES, ALL_SERVICES, START_ORDER
from service_manager import PythonProcessManager
from docker_manager import DockerManager

router = APIRouter(prefix="/api", tags=["services"])
logger = logging.getLogger(__name__)

# Will be initialized in app.py
python_manager: PythonProcessManager = None
docker_manager: DockerManager = None

# Active WebSocket connections
active_websockets: Dict[str, List[WebSocket]] = {}


def set_managers(py_manager: PythonProcessManager, dkr_manager: DockerManager):
    """Set the managers for the routes module"""
    global python_manager, docker_manager
    python_manager = py_manager
    docker_manager = dkr_manager


@router.get("/services", response_model=List[Service])
async def get_services():
    """Get all services with current status"""
    services = []

    # Get status of Python services
    for service_id, config in PYTHON_SERVICES.items():
        running, pid = python_manager.get_status(service_id)

        # Enhanced detection: Check Health URL if script pgrep failed
        if not running and config.get("health_url"):
            try:
                import httpx

                # Fast sync check
                resp = httpx.get(config["health_url"], timeout=0.2)
                if resp.status_code < 400:
                    running = True
            except:
                pass

        service = Service(
            id=service_id,
            name=config["name"],
            description=config["description"],
            type="python",
            status="running" if running else "stopped",
            port=config.get("port"),
            health_url=config.get("health_url"),
            pid=pid if running else None,
            dependencies=config.get("depends_on", []),
        )
        services.append(service)

    # Get status of Docker services
    for service_id, config in DOCKER_SERVICES.items():
        status, container_id = docker_manager.get_container_status(
            config["container_name"]
        )
        service = Service(
            id=service_id,
            name=config["name"],
            description=config["description"],
            type="docker",
            status=status if status == "running" else "stopped",
            port=config.get("port"),
            container_id=container_id,
            dependencies=config.get("depends_on", []) if "depends_on" in config else [],
        )
        services.append(service)

    return services


@router.post("/services/{service_id}/start", response_model=ServiceActionResponse)
async def start_service(service_id: str):
    """Start a service (Python or Docker)"""
    logger.info(f"Request to start service: {service_id}")

    if service_id in PYTHON_SERVICES:
        config = PYTHON_SERVICES[service_id]
        success, message, pid = python_manager.start_service(
            service_id=service_id, script=config["script"], env_vars={}
        )
        return ServiceActionResponse(
            success=success, message=message, service_id=service_id
        )
    elif service_id in DOCKER_SERVICES:
        config = DOCKER_SERVICES[service_id]
        success, message = docker_manager.start_container(
            container_name=config["container_name"]
        )
        return ServiceActionResponse(
            success=success, message=message, service_id=service_id
        )
    else:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")


@router.post("/services/{service_id}/stop", response_model=ServiceActionResponse)
async def stop_service(service_id: str):
    """Stop a service (Python or Docker)"""
    logger.info(f"Request to stop service: {service_id}")

    if service_id in PYTHON_SERVICES:
        success, message = python_manager.stop_service(service_id)
        return ServiceActionResponse(
            success=success, message=message, service_id=service_id
        )
    elif service_id in DOCKER_SERVICES:
        config = DOCKER_SERVICES[service_id]
        success, message = docker_manager.stop_container(
            container_name=config["container_name"]
        )
        return ServiceActionResponse(
            success=success, message=message, service_id=service_id
        )
    else:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")


@router.post("/services/{service_id}/restart", response_model=ServiceActionResponse)
async def restart_service(service_id: str):
    """Restart a service"""
    # First stop the service if running
    if service_id in PYTHON_SERVICES:
        python_manager.stop_service(service_id)
        await asyncio.sleep(1)  # Brief pause
        success, message, pid = python_manager.start_service(
            service_id=service_id,
            script=PYTHON_SERVICES[service_id]["script"],
        )
    elif service_id in DOCKER_SERVICES:
        config = DOCKER_SERVICES[service_id]
        success, message = docker_manager.restart_container(
            container_name=config["container_name"]
        )
    else:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")

    return ServiceActionResponse(
        success=success, message=message, service_id=service_id
    )


@router.post("/services/start-all")
async def start_all_services():
    """Start all services in dependency order"""
    logger.info("Request to start all services")
    results = []

    for service_id in START_ORDER:
        if service_id in ALL_SERVICES:
            try:
                response = await start_service(service_id)
                results.append(
                    {
                        "service_id": service_id,
                        "success": response.success,
                        "message": response.message,
                    }
                )
            except Exception as e:
                results.append(
                    {"service_id": service_id, "success": False, "message": str(e)}
                )

            if service_id != "listening":
                await asyncio.sleep(2)  # Brief pause between starts

    return {"results": results}


@router.post("/services/stop-all")
async def stop_all_services():
    """Stop all services"""
    logger.info("Request to stop all services")
    results = []

    # First stop all Python services
    python_results = python_manager.stop_all_services()
    results.extend(
        [
            {"service_id": sid, "success": r["success"], "message": r["message"]}
            for sid, r in python_results.items()
        ]
    )

    # Then stop Docker containers
    docker_results = docker_manager.stop_all_containers()
    results.extend(
        [
            {"service_id": sid, "success": r["success"], "message": r["message"]}
            for sid, r in docker_results.items()
        ]
    )

    return {"results": results}


@router.get("/services/{service_id}/logs")
async def get_service_logs(service_id: str, tail: int = 100):
    """Get service logs"""
    logger.info(f"Getting logs for service: {service_id}")

    if service_id in PYTHON_SERVICES:
        logs = python_manager.get_logs(service_id, tail)
    elif service_id in DOCKER_SERVICES:
        logs = docker_manager.get_container_logs(
            container_name=DOCKER_SERVICES[service_id]["container_name"], tail=tail
        )
    else:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")

    return {"service_id": service_id, "logs": logs}


@router.websocket("/ws/logs/{service_id}")
async def websocket_logs(websocket: WebSocket, service_id: str):
    """WebSocket for real-time log streaming"""
    await websocket.accept()

    if service_id not in active_websockets:
        active_websockets[service_id] = []
    active_websockets[service_id].append(websocket)

    logger.info(f"New WebSocket connection for logs: {service_id}")

    try:
        if service_id in PYTHON_SERVICES:
            # Stream from Python process
            async for log in python_manager.stream_logs(service_id):
                await websocket.send_text(log)
        elif service_id in DOCKER_SERVICES:
            # Stream from Docker container
            config = DOCKER_SERVICES[service_id]
            async for log in docker_manager.stream_container_logs(
                config["container_name"]
            ):
                await websocket.send_text(log)
    except Exception as e:
        logger.error(f"WebSocket error for {service_id}: {str(e)}")
    finally:
        active_websockets[service_id].remove(websocket)
        logger.info(f"WebSocket closed for {service_id}")


@router.get("/health", response_model=SystemHealth)
async def get_health():
    """Get overall system health"""
    # Get all services status
    services = await get_services()

    # Count statuses
    running = sum(1 for s in services if s.status == "running")
    stopped = sum(1 for s in services if s.status == "stopped")
    errored = sum(1 for s in services if s.status == "error")
    total = len(services)

    # Determine overall status
    if errored > 0:
        overall_status = "unhealthy"
    elif stopped > total // 3:  # More than 1/3 stopped
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return SystemHealth(
        overall_status=overall_status,
        total_services=total,
        running=running,
        stopped=stopped,
        errored=errored,
        python_version="3.13.1",  # Hardcoded, could be dynamic
        docker_running=any(s.container_id is not None for s in services),
    )
