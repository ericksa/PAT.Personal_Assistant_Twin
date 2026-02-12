"""
MCP Server - Main Application
Implements the MCP-ReAct-RAG Stack for the PAT project
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Configure logging first
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Try to import MCP library, but make it optional
try:
    from mcp.server import Server
    from mcp.server.sse import SseServerTransport
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        LoggingLevel,
    )

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP library not available. Running in HTTP-only mode.")

# Import tool registry and handlers
from tools import (
    TOOL_REGISTRY,
    ToolDefinition,
    get_tool_definition,
    list_tools,
    list_categories,
)
from handlers import (
    search_documents,
    upload_document,
    list_documents,
    reason_step,
    create_plan,
    execute_plan_step,
    store_memory,
    retrieve_memory,
    search_memory,
    query_agent,
    process_interview,
    broadcast_teleprompter,
    web_search,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# MCP Server instance (only if MCP is available)
mcp_server = None
if MCP_AVAILABLE:
    mcp_server = Server("pat-mcp-server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info("🚀 Starting MCP-ReAct-RAG Server for PAT...")
    yield
    logger.info("🛑 Shutting down MCP Server")


# FastAPI app
app = FastAPI(
    title="PAT MCP Server",
    description="Multi-Chain Planning + ReAct + RAG Stack for Personal Assistant Twin",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== MCP Server Handlers ====================


@mcp_server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available MCP tools"""
    tools = []

    for tool_def in TOOL_REGISTRY.values():
        tool = Tool(
            name=tool_def.name,
            description=tool_def.description,
            inputSchema=tool_def.input_schema,
        )
        tools.append(tool)

    logger.info(f"Provided {len(tools)} tools to MCP client")
    return tools


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls from MCP clients"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    # Get tool definition
    tool_def = get_tool_definition(name)
    if not tool_def:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": f"Tool not found: {name}",
                        "available_tools": list(TOOL_REGISTRY.keys()),
                    }
                ),
            )
        ]

    try:
        # Call the appropriate handler
        result = await invoke_handler(tool_def, arguments)

        # Format result as text content
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": str(e), "tool": name, "arguments": arguments}
                ),
            )
        ]


async def invoke_handler(
    tool_def: ToolDefinition, arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """Invoke the appropriate handler based on tool category"""

    # RAG Tools
    if tool_def.name == "rag_search":
        return await search_documents(
            query=arguments.get("query", ""),
            top_k=arguments.get("top_k", 5),
            threshold=arguments.get("threshold", 0.2),
        )

    elif tool_def.name == "rag_upload":
        return await upload_document(
            file_path=arguments.get("file_path", ""),
            chunk_size=arguments.get("chunk_size", 800),
            chunk_overlap=arguments.get("chunk_overlap", 120),
        )

    elif tool_def.name == "rag_list_docs":
        return await list_documents()

    # ReAct Tools
    elif tool_def.name == "reason_step":
        return await reason_step(
            question=arguments.get("question", ""), context=arguments.get("context", "")
        )

    elif tool_def.name == "create_plan":
        return await create_plan(
            goal=arguments.get("goal", ""), context=arguments.get("context", "")
        )

    elif tool_def.name == "execute_plan_step":
        return await execute_plan_step(
            plan_id=arguments.get("plan_id", ""),
            step_description=arguments.get("step_description"),
            step_number=arguments.get("step_number"),
        )

    # Memory Tools
    elif tool_def.name == "memory_store":
        return await store_memory(
            key=arguments.get("key", ""),
            value=arguments.get("value", ""),
            ttl=arguments.get("ttl"),
        )

    elif tool_def.name == "memory_retrieve":
        return await retrieve_memory(key=arguments.get("key", ""))

    elif tool_def.name == "memory_search":
        return await search_memory(
            query=arguments.get("query", ""), limit=arguments.get("limit", 5)
        )

    # Action Tools
    elif tool_def.name == "agent_query":
        return await query_agent(
            query=arguments.get("query", ""),
            user_id=arguments.get("user_id", "default"),
            use_web_search=arguments.get("use_web_search", False),
        )

    elif tool_def.name == "interview_process":
        return await process_interview(
            question=arguments.get("question", ""),
            source=arguments.get("source", "interviewer"),
        )

    elif tool_def.name == "teleprompter_broadcast":
        return await broadcast_teleprompter(message=arguments.get("message", ""))

    elif tool_def.name == "web_search":
        return await web_search(
            query=arguments.get("query", ""),
            num_results=arguments.get("num_results", 3),
        )

    else:
        return {
            "error": f"Unknown tool: {tool_def.name}",
            "available_tools": list(TOOL_REGISTRY.keys()),
        }


# ==================== HTTP Endpoints ====================


@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "name": "PAT MCP Server",
        "version": "1.0.0",
        "description": "Multi-Chain Planning + ReAct + RAG Stack",
        "tools_count": len(TOOL_REGISTRY),
        "categories": list_categories(),
    }


@app.get("/tools")
async def get_tools(category: Optional[str] = None):
    """List available tools"""
    tools = list_tools(category)
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
            }
            for tool in tools
        ],
        "category": category,
    }


@app.get("/categories")
async def get_categories():
    """List tool categories"""
    return {"categories": list_categories(), "count": len(list_categories())}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check Redis
    redis_healthy = False
    try:
        from handlers.memory_handlers import redis_client

        if redis_client:
            redis_client.ping()
            redis_healthy = True
    except:
        pass

    return {
        "status": "healthy",
        "services": {
            "redis": "healthy" if redis_healthy else "unhealthy",
            "mcp_server": "running",
        },
        "tools_available": len(TOOL_REGISTRY),
    }


@app.post("/execute")
async def execute_tool(tool_name: str, arguments: Dict[str, Any]):
    """Execute a tool via HTTP API"""
    tool_def = get_tool_definition(tool_name)
    if not tool_def:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    result = await invoke_handler(tool_def, arguments)
    return result


# ==================== Server Startup ====================


async def main():
    """Run the MCP server"""
    # Run using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream, write_stream, mcp_server.create_initialization_options()
        )


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting PAT MCP Server...")
    logger.info(f"📦 Tools available: {len(TOOL_REGISTRY)}")
    logger.info(f"📋 Categories: {', '.join(list_categories())}")

    uvicorn.run("app:app", host="0.0.0.0", port=8003, reload=True, log_level="info")
