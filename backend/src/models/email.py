# src/models/email.py - Email models
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


class EmailCategory(str, Enum):
    """Email categories from AI classification"""

    WORK = "work"
    PERSONAL = "personal"
    URGENT = "urgent"
    NEWSLETTER = "newsletter"
    SPAM = "spam"
    NOTIFICATION = "notification"
    MARKETING = "marketing"
    SOCIAL = "social"
    FINANCIAL = "financial"
    TRAVEL = "travel"


class SyncStatusEmail(str, Enum):
    """Email sync status"""

    SYNCED = "synced"
    PENDING = "pending"
    ERROR = "error"
    ARCHIVED = "archived"


class EmailCreate(BaseModel):
    """Model for creating a new email record"""

    external_message_id: Optional[str] = Field(
        None, description="Apple Mail Message-ID"
    )
    subject: str
    sender_email: str = Field(..., description="Sender email address")
    sender_name: Optional[str] = Field(None, description="Sender name")
    recipient_emails: List[str] = Field(
        default_factory=list, description="To recipients"
    )
    cc_emails: List[str] = Field(default_factory=list, description="CC recipients")
    bcc_emails: List[str] = Field(default_factory=list, description="BCC recipients")
    received_at: datetime
    sent_at: Optional[datetime] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    account_name: str = Field(default="Apple Mail")
    folder: str = Field(default="INBOX")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subject": "Meeting Tomorrow",
                    "sender_email": "client@example.com",
                    "sender_name": "John Smith",
                    "received_at": "2024-02-12T10:00:00Z",
                }
            ]
        }
    }


class Email(BaseModel):
    """Full email model"""

    id: Optional[UUID] = None
    external_message_id: Optional[str] = None
    subject: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    recipient_emails: List[str] = Field(default_factory=list)
    cc_emails: List[str] = Field(default_factory=list)
    bcc_emails: List[str] = Field(default_factory=list)
    received_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    account_name: str = "Apple Mail"
    folder: str = "INBOX"
    read: bool = False
    flagged: bool = False
    important: bool = False
    category: Optional[EmailCategory] = None
    priority: int = 0
    summary: Optional[str] = None
    requires_action: bool = False
    related_event_id: Optional[UUID] = None
    related_task_ids: List[UUID] = Field(default_factory=list)
    thread_id: Optional[UUID] = None
    ai_processed: bool = False
    ai_classified_at: Optional[datetime] = None
    ai_suggested_reply: Optional[str] = None
    sync_status: SyncStatusEmail = SyncStatusEmail.SYNCED
    last_synced_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmailThreadCreate(BaseModel):
    """Model for creating an email thread"""

    thread_id: str = Field(..., description="Apple Mail thread identifier")
    subject: str = Field(..., description="Thread subject")
    participants: List[str] = Field(
        default_factory=list, description="Email addresses in conversation"
    )


class EmailThread(BaseModel):
    """Email thread model"""

    id: Optional[UUID] = None
    thread_id: str
    subject: Optional[str] = None
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    participants: List[str] = Field(default_factory=list)
    ai_summary: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EmailClassification(BaseModel):
    """AI email classification result"""

    category: EmailCategory
    priority: int = Field(..., ge=0, le=10, description="Priority score (0-10)")
    requires_action: bool
    reasoning: str = Field(..., description="AI's reasoning for classification")


class EmailSummary(BaseModel):
    """AI-generated email summary"""

    summary: str = Field(..., description="Concise summary (~200 chars)")


class EmailReplyDraft(BaseModel):
    """AI-generated email reply draft"""

    subject: Optional[str] = None
    body: str = Field(..., description="Draft email body")
    tone: str = Field(default="professional")


class EmailFilters(BaseModel):
    """Filters for querying emails"""

    folder: Optional[str] = None
    category: Optional[EmailCategory] = None
    read: Optional[bool] = None
    flagged: Optional[bool] = None
    requires_action: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sender_email: Optional[str] = None
    priority_min: Optional[int] = None


class EmailAnalytics(BaseModel):
    """Email analytics data"""

    total_emails: int = 0
    unread_count: int = 0
    flagged_count: int = 0
    categories: Dict[str, int] = Field(default_factory=dict)
    average_response_time_hours: Optional[float] = None
    emails_per_day_last_week: float = 0.0
    urgent_count: int = 0
