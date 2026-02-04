# services/tool_proxy/tool_proxy.py
# -------------------------------------------------
# Tiny HTTP wrapper that forwards the "GenerateResume" call
# to your existing agent‑service.
# -------------------------------------------------
import os
from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()
AGENT_URL = os.getenv("AGENT_URL", "http://agent-service:8000")
@app.get("/")
async def root():
    return {"message": "Tool proxy is running"}

@app.get("/health")
async def health_check():
    """Test connectivity to agent-service"""
    try:
        async with httpx.AsyncClient() as client:
            # Test if agent-service is reachable
            resp = await client.get(f"{AGENT_URL}/", timeout=5)
            return {
                "status": "healthy",
                "agent_service_reachable": resp.status_code == 200,
                "tool_proxy": "running"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "agent_service_reachable": False,
            "error": str(e)
        }
@app.post("/tool/generate_resume")
async def generate_resume(payload: dict):
    """
    Expected payload from Open‑WebUI:
        { "job_description": "string …" }
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{AGENT_URL}/generate-resume",
                json=payload,
                timeout=120,
            )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Network error: {exc}")

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Agent error {resp.status_code}: {resp.text}",
        )
    return resp.json()
