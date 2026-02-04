# services/tool_proxy/tool_proxy.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
import httpx

app = FastAPI()
AGENT_URL = os.getenv("AGENT_URL", "http://agent-service:8000")


# 🔧 CRITICAL: Add OpenAPI metadata for Open WebUI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Tool Proxy API",
        version="1.0.0",
        description="Proxy for agent-service tools",
        routes=app.routes,
    )

    # Add the GenerateResume endpoint schema that Open WebUI expects
    openapi_schema["paths"]["/tool/generate_resume"] = {
        "post": {
            "summary": "Generate Resume",
            "description": "Generate a tailored resume for a job description",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "job_description": {
                                    "type": "string",
                                    "description": "The job description to tailor the resume for"
                                }
                            },
                            "required": ["job_description"]
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            }
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Your existing endpoints
@app.post("/tool/generate_resume")
async def generate_resume(payload: dict):
    """Forward GenerateResume requests to agent-service"""
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
        raise HTTPException(status_code=502, detail=f"Agent error: {resp.text}")
    return resp.json()


# Add root endpoint for OpenAPI
@app.get("/")
async def root():
    return {"message": "Tool proxy is running"}


@app.get("/openapi.json")
async def get_openapi_schema():
    return app.openapi_schema


# Health endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tool-proxy"}


# Test that the agent-service is reachable
@app.get("/test-agent")
async def test_agent():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{AGENT_URL}/", timeout=5)
            return {"agent_reachable": resp.status_code == 200}
    except Exception as e:
        return {"agent_reachable": False, "error": str(e)}
