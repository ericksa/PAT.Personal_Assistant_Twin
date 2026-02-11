from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum


class ConflictType(str, Enum):
    """Types of calendar conflicts"""

    OVERLAP = "overlap"
    BACK_TO_BACK = "back_to_back"
    TRAVEL_TIME = "travel_time"
    RESOURCE = "resource"


class ConflictSeverity(str, Enum):
    """Severity levels for conflicts"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Conflict(BaseModel):
    """Represents a calendar conflict"""

    event_id: str
    conflict_event_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    overlap_minutes: Optional[int] = None
    message: str


class CalendarEventCreate(BaseModel):
    """Model for creating a calendar event"""

    user_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    start_date: date
    start_time: Optional[str] = None
    end_date: date
    end_time: Optional[str] = None
    location: Optional[str] = None
    event_type: Optional[str] = "meeting"
    is_all_day: bool = False
    is_recurring: bool = False
    recurrence: Optional[str] = None
    source: Optional[str] = "manual"
    notes: Optional[str] = None
    apple_event_id: Optional[str] = None
    calendar_name: Optional[str] = "Adam"

    # For backward compatibility with dicts
    class Config:
        from_attributes = True


class CalendarEventUpdate(BaseModel):
    """Model for updating a calendar event"""

    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    start_time: Optional[str] = None
    end_date: Optional[date] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    event_type: Optional[str] = None
    is_all_day: Optional[bool] = None
    notes: Optional[str] = None


class CalendarEvent(CalendarEventCreate):
    """Full calendar event model with database fields"""

    id: str
    created_at: datetime
    updated_at: datetime


class SyncResult(BaseModel):
    """Result of syncing from Apple Calendar"""

    synced: int
    updated: int
    errors: int
    message: str
    details: Optional[List[dict]] = None


class TimeSlot(BaseModel):
    """Represents an available time slot"""

    start_date: date
    start_time: str
    end_date: date
    end_time: str
    duration_minutes: int


class ScheduleOptimization(BaseModel):
    """Result of schedule optimization"""

    suggested_time: Optional[TimeSlot] = None
    conflicts: List[Conflict] = []
    reason: str
    alternatives: List[TimeSlot] = []


class SchedulePreferences(BaseModel):
    """User schedule preferences"""

    work_start_time: str = Field(
        default="09:00", description="Default work day start time"
    )
    work_end_time: str = Field(default="17:00", description="Default work day end time")
    buffer_minutes: int = Field(default=15, description="Buffer time between meetings")
    max_back_to_back: int = Field(
        default=3, description="Maximum consecutive meetings before break"
    )
    break_min_duration: int = Field(
        default=15, description="Minimum duration of breaks"
    )
    max_daily_meetings: int = Field(
        default=8, description="Maximum daily meeting count"
    )
    timezone: str = Field(default="America/New_York", description="User's timezone")
    prefer_morning: bool = Field(default=False, description="Prefer morning slots")
    prefer_afternoon: bool = Field(default=False, description="Prefer afternoon slots")
    avoid_friday_afternoon: bool = Field(
        default=True, description="Avoid scheduling on Friday afternoon"
    )
