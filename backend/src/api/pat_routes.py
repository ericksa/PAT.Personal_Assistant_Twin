# src/api/pat_routes.py - PAT Calendar/Email/Task Management API
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
import logging

from src.models.calendar import (
    CalendarEventCreate,
    CalendarEvent,
    Conflict,
    SyncResult,
    ConflictType,
    ConflictSeverity,
)
from src.services.calendar_service import CalendarService
from src.services.llm_service import LlamaLLMService

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


# ===== AI-POWERED EMAIL ENDPOINTS =====


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
