# services/jobs/main.py - Application Entry Point
import uvicorn
import os
import logging

# Import the app factory function
from api.endpoints import create_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting PAT Job Search Service")

    # Create the FastAPI application
    app = create_app()

    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8007")))
