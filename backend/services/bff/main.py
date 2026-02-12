"""
BFF (Backend for Frontend) Service
REST API Gateway for Mobile and Web Frontend
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket
import uvicorn
from pydantic import BaseModel
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BFF Service",
    description="Backend for Frontend - API Gateway",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
APAT_SERVICE_URL = os.getenv("APAT_SERVICE_URL", "http://apat-service:8010")
MCP_SERVICE_URL = os.getenv("MCP_SERVICE_URL", "http://mcp-server:8003")
RAG_SCORING_URL = os.getenv("RAG_SCORING_URL", "http://rag-scoring:8030")
NEXT_ERP_URL = os.getenv("NEXT_ERP_URL", "")

# JWT Secret for authentication
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


# Pydantic models for request/response
class OpportunityInput(BaseModel):
    name: str
    description: Optional[str] = None
    tam: Optional[float] = None
    growth_rate: Optional[float] = None
    competitor_count: Optional[int] = None
    market_trends: Optional[List[str]] = []
    risk_factors: Optional[List[str]] = []
    source_data: Optional[Dict[str, Any]] = {}


class BusinessPlanRequest(BaseModel):
    document_type: str
    template_name: str
    data: Dict[str, Any]
    output_format: str = "pdf"


class RAGUpdateRequest(BaseModel):
    id: str
    rag_status: str


# API Routes


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check connectivity to dependent services
    services_status = {}

    try:
        async with httpx.AsyncClient() as client:
            # Check APAT service
            try:
                response = await client.get(f"{APAT_SERVICE_URL}/health", timeout=5.0)
                services_status["apat"] = (
                    "connected" if response.status_code == 200 else "disconnected"
                )
            except:
                services_status["apat"] = "disconnected"

            # Check MCP service
            try:
                response = await client.get(f"{MCP_SERVICE_URL}/health", timeout=5.0)
                services_status["mcp"] = (
                    "connected" if response.status_code == 200 else "disconnected"
                )
            except:
                services_status["mcp"] = "disconnected"

            # Check RAG scoring service
            try:
                response = await client.get(f"{RAG_SCORING_URL}/health", timeout=5.0)
                services_status["rag_scoring"] = (
                    "connected" if response.status_code == 200 else "disconnected"
                )
            except:
                services_status["rag_scoring"] = "disconnected"

    except Exception as e:
        logger.error(f"Health check failed: {e}")

    return {
        "status": "healthy",
        "service": "bff",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": services_status,
    }


@app.get("/api/opportunities")
async def get_opportunities(
    rag_filter: Optional[str] = None, limit: int = 50, offset: int = 0
):
    """Get market opportunities with optional RAG filter"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{RAG_SCORING_URL}/opportunities",
                params={"rag_filter": rag_filter, "limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch opportunities")


@app.get("/api/opportunities/{id}")
async def get_opportunity(id: str):
    """Get single opportunity by ID"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RAG_SCORING_URL}/opportunities/{id}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch opportunity {id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch opportunity")


@app.post("/api/opportunities")
async def create_opportunity(opportunity: OpportunityInput):
    """Create new market opportunity"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RAG_SCORING_URL}/opportunities", json=opportunity.dict()
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to create opportunity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create opportunity")


@app.patch("/api/opportunities/{id}/rag")
async def update_opportunity_rag(id: str, rag_data: RAGUpdateRequest):
    """Update opportunity RAG status manually"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{RAG_SCORING_URL}/opportunities/{id}/rag",
                json={"rag_status": rag_data.rag_status},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to update RAG status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update RAG status")


@app.get("/api/rag/metrics")
async def get_rag_metrics():
    """Get RAG scoring metrics and overview"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RAG_SCORING_URL}/metrics")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch RAG metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch RAG metrics")


@app.post("/api/business-plans/generate")
async def generate_business_plan(
    request: BusinessPlanRequest, background_tasks: BackgroundTasks
):
    """Generate business plan document"""
    try:
        # Queue the job
        job_data = {
            "type": request.document_type,
            "template": request.template_name,
            "data": request.data,
            "output_format": request.output_format,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{APAT_SERVICE_URL}/jobs/generate", json=job_data
            )
            response.raise_for_status()
            return response.json()

    except Exception as e:
        logger.error(f"Failed to generate business plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate business plan")


@app.get("/api/documents")
async def get_documents(
    document_type: Optional[str] = None, limit: int = 50, offset: int = 0
):
    """Get documents (business plans, SOWs, RFPs)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MCP_SERVICE_URL}/documents",
                params={"type": document_type, "limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch documents")


@app.get("/api/documents/{id}")
async def get_document(id: str):
    """Get single document by ID"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MCP_SERVICE_URL}/documents/{id}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch document {id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch document")


@app.get("/api/business-plans")
async def get_business_plans(limit: int = 20, offset: int = 0):
    """Get business plans"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MCP_SERVICE_URL}/business_plans",
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch business plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch business plans")


@app.get("/api/market-insights")
async def get_market_insights(limit: int = 10, offset: int = 0):
    """Get market insights and trends"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MCP_SERVICE_URL}/market_insights",
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch market insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch market insights")


# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time RAG updates"""
    await websocket.accept()

    try:
        while True:
            # Send periodic RAG updates
            await websocket.send_json(
                {
                    "type": "rag_update",
                    "data": await get_latest_rag_data(),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            await asyncio.sleep(30)  # Send updates every 30 seconds

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        try:
            await websocket.close()
        except:
            pass


async def get_latest_rag_data() -> Dict[str, Any]:
    """Get latest RAG scoring data for WebSocket updates"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RAG_SCORING_URL}/metrics", timeout=10.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to get latest RAG data: {str(e)}")
        return {}


# Authentication middleware (placeholder)
@app.middleware("http")
async def auth_middleware(request, call_next):
    """Authentication middleware"""
    # Extract JWT token from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

        # Validate token (implement JWT validation here)
        # For now, just check if token exists
        if not token:
            return JSONResponse(
                status_code=401, content={"detail": "Invalid authentication token"}
            )

    # Continue with request
    response = await call_next(request)
    return response


# Rate limiting middleware (placeholder)
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    """Rate limiting middleware"""
    # Implement rate limiting logic here
    response = await call_next(request)
    return response


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8020, reload=True, log_level="info")
