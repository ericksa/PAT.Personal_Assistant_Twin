# src/models/opportunity.py - Data Models
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Status of a job/opportunity in the pipeline"""

    NEW = "new"
    REVIEWED = "reviewed"
    INTERESTED = "interested"
    APPLIED = "applied"


class ApplicationStatus(str, Enum):
    """Status of job application process"""

    INTERESTED = "interested"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    OFFER = "offer"


class OpportunitySearchRequest(BaseModel):
    """Request model for searching job opportunities

    Attributes:
        keywords: Search keywords for job matching
        location: Geographic location preference
        company_filter: Optional list of companies to filter by
        days_back: Number of past days to search for new postings
    """

    keywords: str = Field(
        default="government secret clearance senior software engineer",
        description="Keywords to search for in job listings",
        examples=[
            "government secret clearance senior software engineer",
            "java backend developer remote",
        ],
    )
    location: str = Field(
        default="remote",
        description="Job location preference",
        examples=["remote", "Washington, DC", "Arlington, VA"],
    )
    company_filter: Optional[List[str]] = Field(
        default=None,
        description="Optional list of companies to include in search",
        examples=[["Booz Allen Hamilton", "Leidos", "General Dynamics"]],
    )
    days_back: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Number of days to look back for new job postings (1-30)",
        examples=[7, 14, 30],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "keywords": "government secret clearance senior software engineer",
                    "location": "remote",
                    "company_filter": ["Booz Allen Hamilton", "Leidos"],
                    "days_back": 7,
                }
            ]
        }
    }


class Opportunity(BaseModel):
    """Model representing a job opportunity

    Attributes:
        id: Unique identifier for the opportunity
        title: Job title
        company: Company name
        location: Job location
        agency: Government agency (if applicable)
        clearance_required: Whether security clearance is required
        salary_range: Salary range if available
        description: Full job description
        requirements: Specific requirements for the role
        url: URL to apply for the job
        match_score: Calculated match score (0.0-1.0)
        agency_score: Priority score based on agency (0-4)
        posted_date: When the job was posted
        source: Source where the job was found
        status: Current status in the pipeline
    """

    id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the opportunity",
        examples=["12345", "67890"],
    )
    title: str = Field(
        description="Job title",
        examples=["Senior Software Engineer", "Backend Developer", "DevOps Engineer"],
    )
    company: str = Field(
        description="Company name",
        examples=["Booz Allen Hamilton", "Leidos", "General Dynamics IT"],
    )
    location: str = Field(
        description="Job location",
        examples=["Remote", "Washington, DC / Remote", "Arlington, VA"],
    )
    agency: Optional[str] = Field(
        default=None,
        description="Government agency if applicable (VA, DHA, DOD, DOT)",
        examples=["VA", "DHA", "DOD"],
    )
    clearance_required: bool = Field(
        default=False, description="Whether security clearance is required"
    )
    salary_range: Optional[str] = Field(
        default=None,
        description="Salary range if available",
        examples=["$120,000 - $160,000", "$150,000 - $200,000"],
    )
    description: str = Field(description="Full job description")
    requirements: Optional[str] = Field(
        default=None, description="Specific requirements for the role"
    )
    url: str = Field(
        description="URL to apply for the job",
        examples=["https://linkedin.com/jobs/view/12345"],
    )
    match_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Calculated match score based on user preferences (0.0-1.0)",
    )
    agency_score: int = Field(
        default=0,
        ge=0,
        le=4,
        description="Priority score based on agency (VA=4, DHA=3, DOD=2, DOT=1, Other=0)",
    )
    posted_date: Optional[datetime] = Field(
        default=None, description="When the job was posted"
    )
    source: str = Field(
        default="linkedin",
        description="Source where the job was found",
        examples=["linkedin", "indeed", "monster"],
    )
    status: JobStatus = Field(
        default=JobStatus.NEW,
        description="Current status in the job application pipeline",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "12345",
                    "title": "Senior Software Engineer - Government Contracts",
                    "company": "General Dynamics IT",
                    "location": "Remote",
                    "agency": "DOD",
                    "clearance_required": True,
                    "salary_range": "$120,000 - $160,000",
                    "description": "Senior software engineer needed for government contracts requiring secret clearance.",
                    "requirements": "Java Spring Boot, AWS experience required",
                    "url": "https://linkedin.com/jobs/view/12345",
                    "match_score": 0.95,
                    "agency_score": 2,
                    "posted_date": "2024-02-08T10:00:00Z",
                    "source": "linkedin",
                    "status": "new",
                }
            ]
        }
    }
