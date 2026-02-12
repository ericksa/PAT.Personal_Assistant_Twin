"""MCP Handlers Package"""

from .rag_handlers import search_documents, upload_document, list_documents
from .react_handlers import reason_step, create_plan, execute_plan_step
from .memory_handlers import store_memory, retrieve_memory, search_memory
from .action_handlers import (
    query_agent,
    process_interview,
    broadcast_teleprompter,
    web_search,
)
from .pat_core_handlers import (
    list_calendar_events,
    create_calendar_event,
    sync_calendar,
    list_tasks,
    create_task,
    process_email,
)

__all__ = [
    # RAG handlers
    "search_documents",
    "upload_document",
    "list_documents",
    # ReAct handlers
    "reason_step",
    "create_plan",
    "execute_plan_step",
    # Memory handlers
    "store_memory",
    "retrieve_memory",
    "search_memory",
    # Action handlers
    "query_agent",
    "process_interview",
    "broadcast_teleprompter",
    "web_search",
    # PAT Core handlers
    "list_calendar_events",
    "create_calendar_event",
    "sync_calendar",
    "list_tasks",
    "create_task",
    "process_email",
]
