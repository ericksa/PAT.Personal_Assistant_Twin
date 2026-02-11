from typing import Optional
from datetime import datetime
import re


def validate_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return re.match(pattern, url) is not None


def sanitize_input(input_string: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not input_string:
        return ""
    return input_string.strip()


def validate_date_range(
    start_date: Optional[datetime], end_date: Optional[datetime]
) -> bool:
    """Validate that end_date is after start_date"""
    if not start_date or not end_date:
        return True
    return end_date >= start_date
