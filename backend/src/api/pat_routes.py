# src/api/pat_routes.py - PAT Calendar/Email/Task Management API
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
import logging

from models.calendar import (
    CalendarEventCreate,
    CalendarEvent,
    Conflict,
    SyncResult,
    ConflictType,
    ConflictSeverity,
)
from models.email import EmailCreate, EmailUpdate
from models.task import TaskCreate, TaskUpdate
from services.calendar_service import CalendarService
from services.email_service import EmailService
from services.task_service import TaskService
from services.llm_service import LlamaLLMService
from repositories.email_repo import EmailRepository
from repositories.task_repo import TaskRepository
from repositories.calendar_repo import CalendarRepository
from utils.applescript.base_manager import AppleScriptManager
from repositories.sql_helper import SQLHelper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pat", tags=["PAT Assistant"])


@router.on_event("startup")
async def startup():
    """Initialize PAT services"""
    logger.info("PAT Assistant routes initialized")


# ===== CALENDAR ENDPOINTS =====


@router.post("/calendar/events", response_model=Dict[str, Any])
async def create_calendar_event(
    event: CalendarEventCreate,
    background_tasks: BackgroundTasks,
    check_conflicts: bool = True,
):
    """Create a new calendar event with conflict detection"""
    service = CalendarService()

    try:
        result = await service.create_event(event.model_dump(), check_conflicts)
        return {"status": "success", "event": result}
    except Exception as e:
        logger.error(f"Failed to create calendar event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}",
        )


@router.get("/calendar/events")
async def list_calendar_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_status: Optional[str] = None,
):
    """List calendar events with optional filtering"""
    service = CalendarService()

    try:
        events = await service.get_events(start_date, end_date, event_status)
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.error(f"Failed to list calendar events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list events: {str(e)}",
        )


@router.get("/calendar/events/{event_id}")
async def get_calendar_event(event_id: UUID):
    """Get a specific calendar event"""
    service = CalendarService()
    event = await service.calendar_repo.get_event(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    return event


@router.put("/calendar/events/{event_id}")
async def update_calendar_event(
    event_id: UUID, updates: Dict[str, Any], check_conflicts: bool = True
):
    """Update a calendar event"""
    service = CalendarService()

    try:
        result = await service.update_event(event_id, updates, check_conflicts)
        return {"status": "success", "event": result}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event: {str(e)}",
        )


@router.delete("/calendar/events/{event_id}")
async def delete_calendar_event(event_id: UUID):
    """Delete a calendar event"""
    service = CalendarService()

    try:
        success = await service.delete_event(event_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
            )
        return {"status": "success", "event_id": str(event_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {str(e)}",
        )


@router.post("/calendar/events/{event_id}/reschedule")
async def reschedule_event(event_id: UUID, reason: str, suggest_times: int = 3):
    """Suggest optimal rescheduling times using AI"""
    service = CalendarService()

    try:
        suggestions = await service.reschedule_event(event_id, reason, suggest_times)
        return {"status": "success", "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Failed to reschedule event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reschedule: {str(e)}",
        )


@router.get("/calendar/conflicts")
async def list_conflicts(start_time: datetime, end_time: datetime):
    """Detect conflicts within a time range"""
    service = CalendarService()

    try:
        conflicts = await service.detect_conflicts(start_time, end_time)
        return {"conflicts": conflicts, "count": len(conflicts)}
    except Exception as e:
        logger.error(f"Failed to detect conflicts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect conflicts: {str(e)}",
        )


@router.get("/calendar/free-slots")
async def get_free_slots(
    start_date: datetime, end_date: datetime, duration_minutes: int
):
    """Get available time slots"""
    service = CalendarService()

    try:
        slots = await service.get_free_slots(start_date, end_date, duration_minutes)
        return {"slots": slots, "count": len(slots)}
    except Exception as e:
        logger.error(f"Failed to get free slots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get free slots: {str(e)}",
        )


@router.post("/calendar/optimization")
async def optimize_schedule(target_date: Optional[date] = None):
    """Get AI-powered schedule optimization suggestions"""
    service = CalendarService()

    try:
        optimization = await service.optimize_schedule(target_date)
        return optimization.model_dump()
    except Exception as e:
        logger.error(f"Failed to optimize schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize schedule: {str(e)}",
        )


@router.post("/calendar/sync/apple")
async def sync_from_apple_calendar(calendar_name: str = "Adam", hours_back: int = 24):
    """Sync events from Apple Calendar"""
    service = CalendarService()

    try:
        result = await service.sync_from_apple(calendar_name, hours_back)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Failed to sync from Apple Calendar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync: {str(e)}",
        )


@router.post("/calendar/events/{event_id}/auto-reschedule")
async def auto_reschedule_for_delayed_meeting(event_id: UUID, delay_minutes: int = 30):
    """Proactively reschedule subsequent items when a meeting runs long"""
    service = CalendarService()

    try:
        success = await service.auto_reschedule_for_delayed_meeting(
            event_id, delay_minutes
        )
        return {
            "status": "success"
            if success
            else "rescheduled_count: 0 if not success else success",
            "delay_minutes": delay_minutes,
        }
    except Exception as e:
        logger.error(f"Failed to auto-reschedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-reschedule: {str(e)}",
        )


# ===== LLM/CHAT ENDPOINTS =====


@router.post("/chat/completions")
async def chat_completion(
    messages: List[Dict[str, str]], temperature: Optional[float] = None
):
    """
    Get chat completion from Llama 3.2 3B.

    Generic chat endpoint for PAT conversations.
    """
    llm = LlamaLLMService()

    try:
        response = await llm.chat_completion(messages, temperature)
        return {"status": "success", "response": response}
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )


@router.post("/chat/test-connection")
async def test_llm_connection():
    """Test connection to Llama 3.2 3B"""
    llm = LlamaLLMService()

    try:
        success = await llm.test_connection()
        return {"status": "success" if success else "failed", "model": "llama3.2:3b"}
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection test failed: {str(e)}",
        )


# ===== EMAIL CRUD ENDPOINTS =====


@router.get("/emails")
async def list_emails(
    user_id: str = "00000000-0000-0000-0000-000000000001",
    folder: Optional[str] = None,
    thread_id: Optional[str] = None,
    is_unread_only: bool = False,
    is_flagged_only: bool = False,
    classification: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List emails from the database with optional filters"""
    db = SQLHelper()
    repo = EmailRepository(db)

    try:
        emails = await repo.list_emails(
            user_id,
            folder,
            thread_id,
            is_unread_only,
            is_flagged_only,
            classification,
            limit,
            offset,
        )
        return {"status": "success", "emails": emails, "count": len(emails)}
    except Exception as e:
        logger.error(f"Failed to list emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list emails: {str(e)}",
        )


@router.get("/emails/{email_id}")
async def get_email(email_id: str):
    """Get a single email by ID"""
    db = SQLHelper()
    repo = EmailRepository(db)

    try:
        email = await repo.get_email(email_id)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found",
            )
        return {"status": "success", "email": email}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email: {str(e)}",
        )


@router.put("/emails/{email_id}")
async def update_email(email_id: str, email: EmailUpdate):
    """Update an email"""
    db = SQLHelper()
    repo = EmailRepository(db)

    try:
        updated = await repo.update_email(email_id, email)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found",
            )
        return {"status": "success", "email": updated}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update email: {str(e)}",
        )


@router.delete("/emails/{email_id}")
async def delete_email(email_id: str):
    """Delete an email"""
    db = SQLHelper()
    repo = EmailRepository(db)

    try:
        deleted = await repo.delete_email(email_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found",
            )
        return {"status": "success", "message": "Email deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete email: {str(e)}",
        )


@router.post("/emails/sync")
async def sync_emails_from_mailbox(
    request_user_id: str = "00000000-0000-0000-0000-000000000001",
    limit: int = 100,
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Sync emails from Apple Mail to the database"""
    db = SQLHelper()
    email_repo = EmailRepository(db)
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = EmailService(email_repo, task_repo, calendar_repo, llm, applescript)

    try:
        result = await service.sync_from_mailbox(request_user_id, limit)
        return result
    except Exception as e:
        logger.error(f"Failed to sync emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync emails: {str(e)}",
        )


@router.post("/emails/{email_id}/classify")
async def classify_email_db(
    email_id: str,
    user_id: str = "00000000-0000-0000-0000-000000000001",
):
    """Classify an email from the database using AI"""
    db = SQLHelper()
    email_repo = EmailRepository(db)
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = EmailService(email_repo, task_repo, calendar_repo, llm, applescript)

    try:
        classification = await service.classify_email(email_id, user_id)
        return {"status": "success", "classification": classification}
    except Exception as e:
        logger.error(f"Failed to classify email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify email: {str(e)}",
        )


@router.post("/emails/{email_id}/summarize")
async def summarize_email_db(
    email_id: str,
    user_id: str = "00000000-0000-0000-0000-000000000001",
):
    """Summarize an email from the database using AI"""
    db = SQLHelper()
    email_repo = EmailRepository(db)
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = EmailService(email_repo, task_repo, calendar_repo, llm, applescript)

    try:
        summary = await service.summarize_email(email_id, user_id)
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error(f"Failed to summarize email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize email: {str(e)}",
        )


@router.post("/emails/{email_id}/draft-reply")
async def draft_reply_db(
    email_id: str,
    user_id: str = "00000000-0000-0000-0000-000000000001",
    tone: str = "professional",
):
    """Draft a reply to an email from the database using AI"""
    db = SQLHelper()
    email_repo = EmailRepository(db)
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = EmailService(email_repo, task_repo, calendar_repo, llm, applescript)

    try:
        reply = await service.draft_reply(email_id, user_id, tone)
        return {"status": "success", "draft": reply}
    except Exception as e:
        logger.error(f"Failed to draft reply: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to draft reply: {str(e)}",
        )


@router.post("/emails/{email_id}/extract-tasks")
async def extract_tasks_db(
    email_id: str,
    user_id: str = "00000000-0000-0000-0000-000000000001",
):
    """Extract tasks from an email in the database using AI"""
    db = SQLHelper()
    email_repo = EmailRepository(db)
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = EmailService(email_repo, task_repo, calendar_repo, llm, applescript)

    try:
        tasks = await service.extract_tasks(email_id, user_id)
        return {"status": "success", "tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"Failed to extract tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract tasks: {str(e)}",
        )


@router.post("/emails/{email_id}/extract-meetings")
async def extract_meetings_db(
    email_id: str,
    user_id: str = "00000000-0000-0000-0000-000000000001",
):
    """Extract meetings from an email in the database using AI"""
    db = SQLHelper()
    email_repo = EmailRepository(db)
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = EmailService(email_repo, task_repo, calendar_repo, llm, applescript)

    try:
        meetings = await service.extract_meetings(email_id, user_id)
        return {"status": "success", "meetings": meetings, "count": len(meetings)}
    except Exception as e:
        logger.error(f"Failed to extract meetings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract meetings: {str(e)}",
        )


@router.post("/emails/batch-classify")
async def batch_classify_emails(
    user_id: str = "00000000-0000-0000-0000-000000000001",
    limit: int = 20,
):
    """Batch classify recent unclassified emails"""
    db = SQLHelper()
    email_repo = EmailRepository(db)
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = EmailService(email_repo, task_repo, calendar_repo, llm, applescript)

    try:
        results = await service.batch_classify_recent(user_id, limit)
        return {"status": "success", **results}
    except Exception as e:
        logger.error(f"Batch classify failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch classify failed: {str(e)}",
        )


# ===== AI-POWERED EMAIL ENDPOINTS (Text-based) =====


@router.post("/emails/classify")
async def classify_email(subject: str, sender: str, body: str):
    """
    Classify email using Llama 3.2.

    Returns category, priority, requires_action, and reasoning.
    """
    llm = LlamaLLMService()

    try:
        classification = await llm.classify_email(subject, sender, body)
        return {"status": "success", "classification": classification}
    except Exception as e:
        logger.error(f"Email classification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}",
        )


@router.post("/emails/summarize")
async def summarize_email(subject: str, body: str):
    """
    Generate email summary using Llama 3.2.
    """
    llm = LlamaLLMService()

    try:
        summary = await llm.summarize_email(subject, body)
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error(f"Email summarization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}",
        )


@router.post("/emails/draft-reply")
async def draft_email_reply(
    subject: str,
    sender: str,
    body: str,
    tone: str = "professional",
    context: Optional[str] = None,
):
    """
    Draft email reply using Llama 3.2.
    """
    llm = LlamaLLMService()

    try:
        reply = await llm.draft_email_reply(subject, sender, body, tone, context)
        return {"status": "success", "draft": reply}
    except Exception as e:
        logger.error(f"Reply drafter failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Draft failed: {str(e)}",
        )


@router.post("/emails/extract-tasks")
async def extract_tasks_from_text(text: str):
    """
    Extract action items from text using Llama 3.2.

    Parse emails, meeting notes, etc. and extract actionable tasks.
    """
    llm = LlamaLLMService()

    try:
        tasks = await llm.extract_tasks(text)
        return {"status": "success", "tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"Task extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task extraction failed: {str(e)}",
        )


@router.post("/emails/extract-meeting")
async def extract_meeting_details(text: str):
    """
    Extract meeting details from text using Llama 3.2.

    Parse email or notes to find meeting info and create events.
    """
    llm = LlamaLLMService()

    try:
        details = await llm.extract_meeting_details(text)
        return {"status": "success", "meeting": details}
    except Exception as e:
        logger.error(f"Meeting extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Meeting extraction failed: {str(e)}",
        )


# ===== TASK CRUD ENDPOINTS =====


@router.get("/tasks")
async def list_tasks(
    user_id: str = "00000000-0000-0000-0000-000000000001",
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tag: Optional[str] = None,
    is_due_soon: bool = False,
    is_overdue: bool = False,
    limit: int = 50,
    offset: int = 0,
):
    """List tasks from the database with optional filters"""
    db = SQLHelper()
    repo = TaskRepository(db)

    try:
        tasks = await repo.list_tasks(
            user_id, status, priority, tag, is_due_soon, is_overdue, limit, offset
        )
        return {"status": "success", "tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}",
        )


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a single task by ID"""
    db = SQLHelper()
    repo = TaskRepository(db)

    try:
        task = await repo.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return {"status": "success", "task": task}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}",
        )


@router.post("/tasks")
async def create_task(
    task: TaskCreate,
    user_id: str = "00000000-0000-0000-0000-000000000001",
):
    """Create a new task"""
    db = SQLHelper()
    repo = TaskRepository(db)

    task.user_id = task.user_id or user_id

    try:
        created = await repo.create_task(task)
        return {"status": "success", "task": created}
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}",
        )


@router.put("/tasks/{task_id}")
async def update_task(task_id: str, task: TaskUpdate):
    """Update a task"""
    db = SQLHelper()
    repo = TaskRepository(db)

    try:
        updated = await repo.update_task(task_id, task)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return {"status": "success", "task": updated}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}",
        )


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    db = SQLHelper()
    repo = TaskRepository(db)

    try:
        deleted = await repo.delete_task(task_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return {"status": "success", "message": "Task deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}",
        )


@router.post("/tasks/sync")
async def sync_tasks_from_reminders(
    request_user_id: str = "00000000-0000-0000-0000-000000000001",
    limit: int = 100,
):
    """Sync tasks from Apple Reminders to the database"""
    db = SQLHelper()
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = TaskService(task_repo, calendar_repo, llm, applescript)

    try:
        result = await service.sync_from_reminders(request_user_id, limit)
        return result
    except Exception as e:
        logger.error(f"Failed to sync tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync tasks: {str(e)}",
        )


@router.post("/tasks/suggest-priorities")
async def suggest_task_priorities(
    user_id: str = "00000000-0000-0000-0000-000000000001",
):
    """AI-based task priority suggestions"""
    db = SQLHelper()
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = TaskService(task_repo, calendar_repo, llm, applescript)

    try:
        suggestions = await service.suggest_priorities(user_id)
        return {"status": "success", "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Failed to suggest priorities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest priorities: {str(e)}",
        )


@router.post("/tasks/{task_id}/suggest-time")
async def suggest_task_time(
    task_id: str,
    user_id: str = "00000000-0000-0000-0000-000000000001",
):
    """Suggest optimal schedule time for a task"""
    db = SQLHelper()
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = TaskService(task_repo, calendar_repo, llm, applescript)

    try:
        suggestion = await service.suggest_schedule_time(task_id, user_id)
        return {"status": "success", "suggestion": suggestion}
    except Exception as e:
        logger.error(f"Failed to suggest time: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest time: {str(e)}",
        )


@router.get("/tasks/focus")
async def get_focus_tasks(
    user_id: str = "00000000-0000-0000-0000-000000000001",
    limit: int = 5,
):
    """Get top focus tasks for current session"""
    db = SQLHelper()
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = TaskService(task_repo, calendar_repo, llm, applescript)

    try:
        tasks = await service.get_focus_tasks(user_id, limit)
        return {"status": "success", "tasks": tasks}
    except Exception as e:
        logger.error(f"Failed to get focus tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get focus tasks: {str(e)}",
        )


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    notes: Optional[str] = None,
    user_id: str = "00000000-0000-0000-0000-000000000001",
):
    """Mark a task as completed"""
    db = SQLHelper()
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = TaskService(task_repo, calendar_repo, llm, applescript)

    try:
        result = await service.complete_task(task_id, user_id, notes)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Failed to complete task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete task: {str(e)}",
        )


@router.get("/tasks/completion-suggestions")
async def task_completion_suggestions(
    user_id: str = "00000000-0000-0000-0000-000000000001",
):
    """AI-based suggestions for task completion strategies"""
    db = SQLHelper()
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = TaskService(task_repo, calendar_repo, llm, applescript)

    try:
        suggestions = await service.smart_task_completion_suggestions(user_id)
        return {"status": "success", "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Failed to get completion suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get completion suggestions: {str(e)}",
        )


@router.post("/tasks/batch-create")
async def batch_create_tasks(
    task_descriptions: List[str],
    user_id: str = "00000000-0000-0000-0000-000000000001",
):
    """Batch create tasks from descriptions with AI parsing"""
    db = SQLHelper()
    task_repo = TaskRepository(db)
    calendar_repo = CalendarRepository(db)
    llm = LlamaLLMService()
    applescript = AppleScriptManager()

    service = TaskService(task_repo, calendar_repo, llm, applescript)

    try:
        tasks = await service.batch_create_tasks(user_id, task_descriptions)
        return {"status": "success", "tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"Batch create tasks failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch create tasks failed: {str(e)}",
        )


# ===== SYSTEM ENDPOINTS =====


@router.get("/health")
async def health_check():
    """Health check for PAT Core API"""
    return {
        "status": "healthy",
        "service": "pat-core",
        "model": "llama3.2:3b",
        "features": {"calendar": True, "ai_llm": True, "applescript": True},
    }


@router.get("/info")
async def pat_info():
    """Get PAT system information"""
    return {
        "name": "PAT - Personal Assistant Twin",
        "version": "1.0.0",
        "features": [
            "Calendar Management",
            "Email AI Processing",
            "Task Management",
            "LLaMA 3.2 3B Integration",
            "Apple Calendar Integration",
            "Apple Mail Integration",
            "Apple Reminders Integration",
        ],
        "integrations": {
            "ollama": "llama3.2:3b",
            "apple_calendar": "local (via AppleScript)",
            "apple_mail": "local (via AppleScript)",
            "apple_reminders": "local (via AppleScript)",
        },
    }
