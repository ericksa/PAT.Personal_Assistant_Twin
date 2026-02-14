from fastapi import FastAPI
from .health import router as health_router

app = FastAPI(
    title="PAT Backend",
    description="Production-ready PAT Application Backend",
    version="0.1.0",
    openapi_url="/openapi.json",
)

# Register routes
app.include_router(health_router, prefix="/api/v1/health", tags=["health"])


@app.get("/")
def read_root():
    return {"message": "Welcome to PAT Backend Service"}
