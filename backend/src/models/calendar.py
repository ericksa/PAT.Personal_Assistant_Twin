# src/models/calendar.py - Calendar event models
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from uuid import UUID


class EventType(str, Enum):
    """Types of calendar events"""

    MEETING = "meeting"
    CALL = "call"
    TASK = "task"
    REMINDER = "reminder"
    PERSONAL = "personal"
    VACATION = "vacation"
    DEEP_WORK = "deep_work"


class EventStatus(str, Enum):
    """Calendar event status"""

    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"
    DECLINED = "declined"


class ConflictType(str, Enum):
    """Types of calendar conflicts"""

    OVERLAP = "overlap"
    TRAVEL_TIME = "travel_time"
    PREPARATION = "preparation"


class ConflictSeverity(str, Enum):
    """Severity of calendar conflicts"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SyncStatus(str, Enum):
    """Sync status with Apple Calendar"""

    SYNCED = "synced"
    PENDING = "pending"
    ERROR = "error"
    CONFLICTED = "conflicted"


class CalendarEventCreate(BaseModel):
    """Model for creating a new calendar event"""

    title: str = Field(
        ..., description="Event title", examples=["Team Standup", "Client Meeting"]
    )
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(
        None, description="Event location", examples=["Conference Room A", "Remote"]
    )
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    all_day: bool = Field(default=False, description="Is this an all-day event?")
    recurrence_rule: Optional[str] = Field(
        None, description="iCal RRULE format", examples=["FREQ=WEEKLY;BYDAY=MO,WE,FR"]
    )
    timezone: Optional[str] = Field(
        None, description="Event timezone", examples=["America/New_York"]
    )
    calendar_name: str = Field(default="Adam", description="Which Apple calendar")
    event_type: EventType = Field(
        default=EventType.MEETING, description="Type of event"
    )
    status: EventStatus = Field(
        default=EventStatus.CONFIRMED, description="Event status"
    )
    priority: int = Field(default=0, ge=0, le=10, description="Priority level (0-10)")
    travel_time_minutes: int = Field(
        default=0, ge=0, description="Travel time before event"
    )
    requires_preparation: bool = Field(
        default=False, description="Does event need preparation?"
    )
    preparation_minutes: int = Field(
        default=15, ge=0, description="Preparation time needed"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Team Standup",
                    "start_time": "2024-02-12T09:00:00",
                    "end_time": "2024-02-12T09:30:00",
                    "location": "Conference Room A",
                    "event_type": "meeting",
                    "priority": 5,
                }
            ]
        }
    }


class CalendarEvent(BaseModel):
    """Full calendar event model"""

    id: Optional[UUID] = Field(None, description="Event ID")
    external_event_id: Optional[str] = Field(None, description="Apple Calendar ID")
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    recurrence_rule: Optional[str] = None
    timezone: Optional[str] = None
    calendar_name: str = "Adam"
    event_type: EventType = EventType.MEETING
    status: EventStatus = EventStatus.CONFIRMED
    priority: int = 0
    travel_time_minutes: int = 0
    requires_preparation: bool = False
    preparation_minutes: int = 15
    sync_status: SyncStatus = SyncStatus.SYNCED
    last_synced_at: Optional[datetime] = None
    ai_processed: bool = False
    ai_summary: Optional[str] = None
    ai_suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConflictCreate(BaseModel):
    """Model for creating a conflict record"""

    event1_id: UUID = Field(..., description="First conflicting event ID")
    event2_id: UUID = Field(..., description="Second conflicting event ID")
    conflict_type: ConflictType = ConflictType.OVERLAP
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    ai_suggested_resolution: Optional[str] = Field(
        None, description="AI's suggested resolution"
    )


class Conflict(BaseModel):
    """Conflict model"""

    id: Optional[UUID] = None
    event1_id: UUID
    event2_id: UUID
    conflict_type: ConflictType
    severity: ConflictSeverity
    detected_at: Optional[datetime] = None
    resolved: bool = False
    resolved_action: Optional[str] = None
    resolved_at: Optional[datetime] = None
    ai_suggested_resolution: Optional[str] = None


class SchedulePreferences(BaseModel):
    """User schedule preferences"""

    user_id: Optional[UUID] = Field(None, description="User ID (default single user)")
    work_start_time: str = Field(default="09:00", description="Work day start time")
    work_end_time: str = Field(default="17:00", description="Work day end time")
    break_start_time: str = Field(default="12:00", description="Lunch break start time")
    break_end_time: str = Field(default="13:00", description="Lunch break end time")
    preferred_meeting_days: List[int] = Field(
        default=[1, 2, 3, 4, 5], description="Preferred meeting days (1-7)"
    )
    avoid_meetings_first_last_hours: bool = Field(
        default=True, description="Avoid meetings first/last hours"
    )
    travel_time_buffer_minutes: int = Field(
        default=15, description="Buffer for travel time"
    )
    preferred_meeting_length_minutes: int = Field(
        default=60, description="Preferred meeting duration"
    )
    min_time_between_meetings_minutes: int = Field(
        default=15, description="Minimum time between meetings"
    )
    max_meetings_per_day: int = Field(
        default=8, ge=1, description="Max meetings per day"
    )
    peak_productivity_hours: List[int] = Field(
        default=[9, 10, 11, 14, 15, 16, 17], description="Peak productivity hours"
    )
    deep_work_blocks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Protected focus time blocks"
    )
    meeting_free_afternoons: bool = Field(
        default=False, description="Reserve afternoons for deep work"
    )


class TimeSlot(BaseModel):
    """Available time slot"""

    start_time: datetime
    end_time: datetime
    duration_minutes: int
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: Optional[str] = None


class OptimizationSuggestion(BaseModel):
    """AI-powered schedule optimization suggestion"""

    date: date
    current_events: List[CalendarEvent] = Field(default_factory=list)
    suggested_changes: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    potential_conflicts_resolved: int = 0
    user_id: Optional[str] = Field(
        default=None, description="User ID for the optimization"
    )


class SyncResult(BaseModel):
    """Result of sync operation"""

    synced: int = 0
    updated: int = 0
    errors: int = 0
    conflicts: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)
