"""
MCP Server - Simplified version without MCP dependencies
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PAT MCP Server",
    description="Multi-Chain Planning + ReAct + RAG Stack for Personal Assistant Twin",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Simple tool registry for demonstration
TOOLS = {
    "rag_search": {
        "name": "rag_search",
        "description": "Search through uploaded documents",
        "parameters": {
            "query": {"type": "string", "description": "Search query"},
            "top_k": {
                "type": "integer",
                "description": "Number of results",
                "default": 5,
            },
        },
    },
    "agent_query": {
        "name": "agent_query",
        "description": "Query the PAT agent",
        "parameters": {
            "query": {"type": "string", "description": "Question to ask"},
            "use_web_search": {
                "type": "boolean",
                "description": "Use web search",
                "default": False,
            },
        },
    },
    "interview_process": {
        "name": "interview_process",
        "description": "Process interview questions",
        "parameters": {
            "question": {"type": "string", "description": "Interview question"},
            "source": {
                "type": "string",
                "description": "Source of question",
                "default": "interviewer",
            },
        },
    },
}


@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "name": "PAT MCP Server",
        "version": "1.0.0",
        "description": "Simplified MCP Server for PAT",
        "tools_count": len(TOOLS),
    }


@app.get("/tools")
async def get_tools(category: Optional[str] = None):
    """List available tools"""
    tools = list(TOOLS.values())
    return {
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            }
            for tool in tools
        ],
        "category": category,
    }


@app.get("/categories")
async def get_categories():
    """List tool categories"""
    return {"categories": ["rag", "agent", "interview"], "count": 3}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "mcp_server": "running",
        },
        "tools_available": len(TOOLS),
    }


@app.post("/execute")
async def execute_tool(tool_name: str, arguments: Dict[str, Any]):
    """Execute a tool via HTTP API"""
    if tool_name not in TOOLS:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    tool = TOOLS[tool_name]

    # Simulate tool execution
    if tool_name == "rag_search":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        return {
            "result": f"Found {top_k} results for query: {query}",
            "tool": tool_name,
            "status": "success",
        }
    elif tool_name == "agent_query":
        query = arguments.get("query", "")
        return {
            "result": f"Agent response to: {query}",
            "tool": tool_name,
            "status": "success",
        }
    elif tool_name == "interview_process":
        question = arguments.get("question", "")
        return {
            "result": f"Processed interview question: {question}",
            "tool": tool_name,
            "status": "success",
        }

    return {
        "result": f"Executed {tool_name} with arguments: {arguments}",
        "tool": tool_name,
        "status": "success",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting PAT MCP Server...")
    logger.info(f"📦 Tools available: {len(TOOLS)}")

    uvicorn.run("app:app", host="0.0.0.0", port=8003, reload=True, log_level="info")
