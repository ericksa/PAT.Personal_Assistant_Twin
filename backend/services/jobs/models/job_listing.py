# services/jobs/models/job_listing.py - Data Models
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    INTERESTED = "interested"
    APPLIED = "applied"


class ApplicationStatus(str, Enum):
    INTERESTED = "interested"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    OFFER = "offer"


class JobSearchRequest(BaseModel):
    keywords: str = "government secret clearance senior software engineer"
    location: str = "remote"
    company_filter: Optional[List[str]] = None
    days_back: int = 7  # Search jobs posted in last N days


class JobListing(BaseModel):
    id: Optional[str] = None
    title: str
    company: str
    location: str
    agency: Optional[str] = None
    clearance_required: bool = False
    salary_range: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    url: str
    match_score: float = 0.0
    agency_score: int = 0
    posted_date: Optional[datetime] = None
    source: str = "linkedin"
    status: JobStatus = JobStatus.NEW
