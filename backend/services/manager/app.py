import os
import asyncio
import logging
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import our modules
from config import PYTHON_SERVICES, ALL_SERVICES
from service_manager import PythonProcessManager
from docker_manager import DockerManager
from routes import router as api_router
from chat_routes import router as chat_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instance of managers
python_manager: Optional[PythonProcessManager] = None
docker_manager: Optional[DockerManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI app"""
    global python_manager, docker_manager

    # Startup
    logger.info("Starting PAT Service Manager")

    # Initialize managers
    backend_path = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    python_path = "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
    compose_files = [
        os.path.join(backend_path, "docker-compose.yml"),
        os.path.join(backend_path, "docker-compose.enterprise.yml"),
    ]

    # Check which compose files exist
    existing_compose_files = [
        f for f in compose_files if os.path.exists(f) and os.path.isfile(f)
    ]

    if not existing_compose_files:
        logger.warning("No docker-compose files found in backend directory")

    try:
        python_manager = PythonProcessManager(
            backend_path=backend_path,
            python_path=python_path,
        )

        docker_manager = DockerManager(compose_files=existing_compose_files)

        # Inject managers into the routes module
        from routes import set_managers

        set_managers(python_manager, docker_manager)

        logger.info("PAT Service Manager ready")

        yield

    finally:
        # Shutdown cleanup
        logger.info("Shutting down PAT Service Manager")

        # Stop all Python services
        if python_manager:
            logger.info("Stopping all Python services")
            python_manager.stop_all_services()

        # Stop Docker services? (Optional - we'll leave Docker containers running)
        # docker_manager.stop_all_containers()

        logger.info("Cleanup complete")


app = FastAPI(
    title="PAT Service Manager",
    description="Web-based service manager for PAT",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include API routes
app.include_router(api_router)
app.include_router(chat_router)

# Serve static files for the Vue frontend in production
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    logger.info(f"Serving static files from {static_dir}")
else:

    @app.get("/")
    async def root():
        """Basic root endpoint if static files are not found"""
        return {
            "message": "PAT Service Manager API",
            "docs": "/docs",
            "status": "Use /api/services for service management",
        }


# Add handler for when we have a function to set the managers
def set_managers(py_manager: PythonProcessManager, dkr_manager: DockerManager):
    """Function to set the managers for routes"""
    global python_manager, docker_manager
    python_manager = py_manager
    docker_manager = dkr_manager


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
        access_log=True,
        log_level="info",
    )
