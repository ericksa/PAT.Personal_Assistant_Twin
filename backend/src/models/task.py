from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    """Model for creating a task"""

    user_id: Optional[str] = None
    apple_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    due_date: Optional[datetime] = None
    due_time: Optional[str] = None
    estimated_duration: Optional[int] = None
    tags: List[str] = []
    reminder_minutes: Optional[int] = None
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence: Optional[str] = None
    is_flagged: bool = False
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None

    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    """Model for updating a task"""

    user_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    due_time: Optional[str] = None
    estimated_duration: Optional[int] = None
    tags: Optional[List[str]] = None
    reminder_minutes: Optional[int] = None
    location: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence: Optional[str] = None
    is_flagged: Optional[bool] = None
    notes: Optional[str] = None
