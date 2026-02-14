"""
Minimal FastAPI application for PAT backend.
"""
from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    status: str
    
    class Config:
        schema_extra = {
            "example": {
                "status": "ok"
            }
        }


# Create FastAPI application
app = FastAPI(
    title="PAT Backend API",
    description="Personal Assistant Toolkit Backend Service",
    version="0.1.0"
)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the health status of the service"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Health status of the service
    """
    return HealthResponse(status="ok")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )