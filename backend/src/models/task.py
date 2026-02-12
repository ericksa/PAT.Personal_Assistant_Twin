# src/models/task.py - Task and reminder models
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from uuid import UUID


class TaskStatus(str, Enum):
    """Task status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


class TaskSource(str, Enum):
    """Task source"""

    PAT = "pat"
    APPLE_REMINDERS = "apple_reminders"
    EMAIL = "email"
    CALENDAR = "calendar"
    MANUAL = "manual"


class Task(BaseModel):
    """Task/Reminder model"""

    id: Optional[UUID] = None
    external_task_id: Optional[str] = Field(None, description="Apple Reminders ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    due_date: Optional[date] = Field(None, description="Due date")
    due_time: Optional[str] = Field(None, description="Due time (HH:MM)")
    priority: int = Field(default=0, ge=0, le=10, description="Priority level (0-10)")
    status: TaskStatus = TaskStatus.PENDING
    completed_at: Optional[datetime] = None
    reminder_date: Optional[datetime] = None
    reminder_sent: bool = False
    source: TaskSource = TaskSource.PAT
    related_email_id: Optional[UUID] = None
    related_event_id: Optional[UUID] = None
    list_name: str = Field(default="High")
    ai_generated: bool = False
    estimated_duration_minutes: Optional[int] = Field(
        None, description="Estimated time to complete"
    )
    tags: List[str] = Field(default_factory=list)
    completion_notes: Optional[str] = None
    ai_processed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Follow up with client",
                    "priority": 7,
                    "status": "pending",
                    "tags": ["work", "client"],
                }
            ]
        }
    }


class TaskCreate(BaseModel):
    """Model for creating a new task"""

    user_id: Optional[UUID] = None
    external_task_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[str] = None
    priority: int = 0
    status: TaskStatus = TaskStatus.PENDING
    reminder_date: Optional[datetime] = None
    list_name: str = "High"
    estimated_duration_minutes: Optional[int] = None
    tags: List[str] = []
    source: TaskSource = TaskSource.PAT


class TaskUpdate(BaseModel):
    """Model for updating a task"""

    status: Optional[TaskStatus] = None
    priority: Optional[int] = Field(None, ge=0, le=10)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    completion_notes: Optional[str] = None
    due_date: Optional[date] = None
    reminder_date: Optional[datetime] = None
    external_task_id: Optional[str] = None
    tags: Optional[List[str]] = None


class TaskFilters(BaseModel):
    """Filters for querying tasks"""

    status: Optional[TaskStatus] = None
    priority_min: Optional[int] = None
    list_name: Optional[str] = None
    source: Optional[TaskSource] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None
    search: Optional[str] = Field(None, description="Search in title and description")


class TaskAnalytics(BaseModel):
    """Task analytics"""

    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    overdue_tasks: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)
    by_source: Dict[str, int] = Field(default_factory=dict)
    average_completion_time_hours: Optional[float] = None
