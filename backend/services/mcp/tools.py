"""
MCP Tool Registry for PAT Project
Defines all available tools for the MCP-ReAct-RAG Stack
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class ToolDefinition(BaseModel):
    """Definition of an MCP tool"""

    name: str = Field(description="Unique tool identifier")
    description: str = Field(description="Tool description and usage")
    input_schema: Dict[str, Any] = Field(description="JSON Schema for tool input")
    handler: str = Field(description="Python path to handler function")
    category: str = Field(description="Tool category: rag, react, memory, action")


# ============== RAG Tools ==============
class RAGSearchInput(BaseModel):
    """Input for RAG document search"""

    query: str = Field(description="Search query for document retrieval")
    top_k: int = Field(default=5, description="Number of results to return")
    threshold: float = Field(default=0.2, description="Similarity threshold")


class RAGUploadInput(BaseModel):
    """Input for uploading documents to RAG"""

    file_path: str = Field(description="Path to file to upload")
    chunk_size: int = Field(default=800, description="Text chunk size")
    chunk_overlap: int = Field(default=120, description="Text chunk overlap")


# ============== ReAct Reasoning Tools ==============
class ReasonInput(BaseModel):
    """Input for reasoning step"""

    question: str = Field(description="Current question or step to reason about")
    context: str = Field(default="", description="Available context")


class PlanStepInput(BaseModel):
    """Input for planning a step"""

    step_description: str = Field(description="Description of the planned step")
    dependencies: List[str] = Field(
        default_factory=list, description="Previous step IDs"
    )


# ============== Memory Tools ==============
class MemoryStoreInput(BaseModel):
    """Input for storing a memory"""

    key: str = Field(description="Memory key/identifier")
    value: str = Field(description="Memory value/content")
    ttl: Optional[int] = Field(default=None, description="Time to live in seconds")


class MemoryRetrieveInput(BaseModel):
    """Input for retrieving a memory"""

    key: str = Field(description="Memory key to retrieve")


# ============== Action Tools ==============
class AgentQueryInput(BaseModel):
    """Input for querying the agent service"""

    query: str = Field(description="Query to process")
    user_id: str = Field(default="default", description="User identifier")
    use_web_search: bool = Field(default=False, description="Enable web search")


class InterviewInput(BaseModel):
    """Input for interview question processing"""

    question: str = Field(description="Interview question to process")
    source: str = Field(default="interviewer", description="Question source")


class TeleprompterInput(BaseModel):
    """Input for teleprompter display"""

    message: str = Field(description="Message to display on teleprompter")


# ============== Tool Definitions ==============
TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    # RAG Tools
    "rag_search": ToolDefinition(
        name="rag_search",
        description="Search through uploaded documents (resume, technical docs) to find relevant information. Returns document chunks with similarity scores.",
        input_schema=RAGSearchInput.model_json_schema(),
        handler="mcp.handlers.rag_handlers.search_documents",
        category="rag",
    ),
    "rag_upload": ToolDefinition(
        name="rag_upload",
        description="Upload a new document to the RAG knowledge base. Supports PDF, TXT, DOCX formats.",
        input_schema=RAGUploadInput.model_json_schema(),
        handler="mcp.handlers.rag_handlers.upload_document",
        category="rag",
    ),
    "rag_list_docs": ToolDefinition(
        name="rag_list_docs",
        description="List all documents currently stored in the RAG system with metadata.",
        input_schema={"type": "object", "properties": {}},
        handler="mcp.handlers.rag_handlers.list_documents",
        category="rag",
    ),
    # ReAct Reasoning Tools
    "reason_step": ToolDefinition(
        name="reason_step",
        description="Perform a single reasoning step with the LLM. Useful for breaking down complex problems into smaller steps.",
        input_schema=ReasonInput.model_json_schema(),
        handler="mcp.handlers.react_handlers.reason_step",
        category="react",
    ),
    "create_plan": ToolDefinition(
        name="create_plan",
        description="Create a multi-step plan for complex tasks. Analyzes the goal and breaks it into achievable steps.",
        input_schema={
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "The goal to achieve"},
                "context": {
                    "type": "string",
                    "default": "",
                    "description": "Additional context",
                },
            },
        },
        handler="mcp.handlers.react_handlers.create_plan",
        category="react",
    ),
    "execute_plan_step": ToolDefinition(
        name="execute_plan_step",
        description="Execute a specific step in a multi-step plan. Handles dependencies between steps.",
        input_schema=PlanStepInput.model_json_schema(),
        handler="mcp.handlers.react_handlers.execute_plan_step",
        category="react",
    ),
    # Memory Tools
    "memory_store": ToolDefinition(
        name="memory_store",
        description="Store information in short-term memory (Redis) for later retrieval in the conversation.",
        input_schema=MemoryStoreInput.model_json_schema(),
        handler="mcp.handlers.memory_handlers.store_memory",
        category="memory",
    ),
    "memory_retrieve": ToolDefinition(
        name="memory_retrieve",
        description="Retrieve information from short-term memory. Useful for maintaining conversation state.",
        input_schema=MemoryRetrieveInput.model_json_schema(),
        handler="mcp.handlers.memory_handlers.retrieve_memory",
        category="memory",
    ),
    "memory_search": ToolDefinition(
        name="memory_search",
        description="Search through stored memories for relevant information to current context.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "Max results to return",
                },
            },
        },
        handler="mcp.handlers.memory_handlers.search_memory",
        category="memory",
    ),
    # Action Tools
    "agent_query": ToolDefinition(
        name="agent_query",
        description="Query the PAT agent service with RAG-enabled responses. Handles interview questions, technical queries, and general assistance.",
        input_schema=AgentQueryInput.model_json_schema(),
        handler="mcp.handlers.action_handlers.query_agent",
        category="action",
    ),
    "interview_process": ToolDefinition(
        name="interview_process",
        description="Process an interview question through the full pipeline: transcription, RAG retrieval, LLM generation, and teleprompter display.",
        input_schema=InterviewInput.model_json_schema(),
        handler="mcp.handlers.action_handlers.process_interview",
        category="action",
    ),
    "teleprompter_broadcast": ToolDefinition(
        name="teleprompter_broadcast",
        description="Send a message to the teleprompter service for on-screen display during interviews.",
        input_schema=TeleprompterInput.model_json_schema(),
        handler="mcp.handlers.action_handlers.broadcast_teleprompter",
        category="action",
    ),
    "web_search": ToolDefinition(
        name="web_search",
        description="Perform web search using DuckDuckGo for current information outside the knowledge base.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {
                    "type": "integer",
                    "default": 3,
                    "description": "Number of results",
                },
            },
        },
        handler="mcp.handlers.action_handlers.web_search",
        category="action",
    ),
}


def get_tool_definition(tool_name: str) -> Optional[ToolDefinition]:
    """Get a tool definition by name"""
    return TOOL_REGISTRY.get(tool_name)


def list_tools(category: Optional[str] = None) -> List[ToolDefinition]:
    """List all available tools, optionally filtered by category"""
    if category:
        return [tool for tool in TOOL_REGISTRY.values() if tool.category == category]
    return list(TOOL_REGISTRY.values())


def list_categories() -> List[str]:
    """Get all unique tool categories"""
    return list(set(tool.category for tool in TOOL_REGISTRY.values()))
