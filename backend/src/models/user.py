# src/models/user.py - User model
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class User(BaseModel):
    """User model for PAT personal assistant"""

    id: Optional[UUID] = None
    full_name: str = Field(default="Local User")
    email: Optional[str] = None
    timezone: str = Field(default="America/New_York")
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    """User update model"""

    full_name: Optional[str] = None
    email: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
