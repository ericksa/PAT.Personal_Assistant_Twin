from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class EmailCreate(BaseModel):
    """Model for creating an email record"""

    user_id: Optional[str] = None
    apple_id: Optional[str] = None
    thread_id: Optional[str] = None
    subject: str
    from_address: str
    from_name: Optional[str] = None
    to_addresses: List[str]
    cc_addresses: List[str] = []
    bcc_addresses: List[str] = []
    body_preview: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    received_at: datetime
    sent_at: Optional[datetime] = None
    is_read: bool = False
    is_flagged: bool = False
    folder: str = "INBOX"
    apple_message_id: Optional[str] = None
    classification: Optional[str] = None
    sub_classification: Optional[str] = None
    summary: Optional[str] = None
    reply_draft: Optional[str] = None

    class Config:
        from_attributes = True


class EmailUpdate(BaseModel):
    """Model for updating an email"""

    user_id: Optional[str] = None
    subject: Optional[str] = None
    body_preview: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    is_read: Optional[bool] = None
    is_flagged: Optional[bool] = None
    folder: Optional[str] = None
    classification: Optional[str] = None
    sub_classification: Optional[str] = None
    summary: Optional[str] = None
    reply_draft: Optional[str] = None


class EmailThreadCreate(BaseModel):
    """Model for creating an email thread"""

    user_id: str
    apple_thread_id: Optional[str] = None
    subject: str
    participant_count: int = 0
    message_count: int = 1
    is_unread: bool = False
    last_message_at: datetime

    class Config:
        from_attributes = True


class EmailThreadUpdate(BaseModel):
    """Model for updating an email thread"""

    subject: Optional[str] = None
    participant_count: Optional[int] = None
    message_count: Optional[int] = None
    is_unread: Optional[bool] = None
    last_message_at: Optional[datetime] = None
