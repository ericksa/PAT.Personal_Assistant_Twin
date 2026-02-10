# services/jobs/app.py - Job Search and Resume Customization Service
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import os
import asyncio
import httpx
import json
import re
from datetime import datetime, timedelta
from enum import Enum

from .notification_service import NotificationService, MockNotificationService
from .scheduler import scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PAT Job Search Service")

# Configuration
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
PAT_NOTIFICATION_EMAIL = os.getenv("PAT_NOTIFICATION_EMAIL")
AGENCY_PRIORITY = os.getenv("GOVERNMENT_AGENCY_PRIORITY", "VA,DHA,DOD,DOT").split(",")

# Agency priority mapping (VA highest priority, DOT lowest)
AGENCY_PRIORITY_SCORES = {"VA": 4, "DHA": 3, "DOD": 2, "DOT": 1}

# Clearance requirement patterns
CLEARANCE_PATTERNS = [
    r"(secret|top secret|TS/SCI|confidential)[\\s-]*clearance",
    r"clearance[\\s-]*level[\\s:]*(secret|top secret|TS/SCI)",
    r"(DOD|department of defense)[\\s-]*clearance",
    r"security clearance required",
    r"must have (security )?clearance",
]


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


class LinkedInClient:
    """LinkedIn Jobs API client"""

    def __init__(self):
        self.client_id = LINKEDIN_CLIENT_ID
        self.client_secret = LINKEDIN_CLIENT_SECRET
        self.access_token = None
        self.token_expires = None

    async def authenticate(self):
        """Authenticate with LinkedIn API"""
        if (
            self.access_token
            and self.token_expires
            and self.token_expires > datetime.now()
        ):
            return True

        try:
            # Implement LinkedIn OAuth2 authentication
            # This is a placeholder - real implementation would use proper LinkedIn SDK
            logger.info("Authenticating with LinkedIn API")
            # Simulate authentication
            self.access_token = "linkedin_simulated_token"
            self.token_expires = datetime.now() + timedelta(days=60)
            return True
        except Exception as e:
            logger.error(f"LinkedIn authentication failed: {e}")
            return False

    async def search_jobs(
        self, keywords: str, location: str = "remote", days_back: int = 7
    ) -> List[JobListing]:
        """Search for jobs matching criteria"""
        if not await self.authenticate():
            return []

        try:
            # Simulate job search - in real implementation, call LinkedIn Jobs API
            logger.info(f"Searching LinkedIn jobs: {keywords} in {location}")

            # Mock job data for development
            mock_jobs = [
                JobListing(
                    title="Senior Software Engineer - Government Contracts",
                    company="General Dynamics IT",
                    location="Remote",
                    agency="DOD",
                    clearance_required=True,
                    description="Senior software engineer needed for government contracts requiring secret clearance. Java Spring Boot, AWS experience required.",
                    url="https://linkedin.com/jobs/view/12345",
                    match_score=0.95,
                    agency_score=AGENCY_PRIORITY_SCORES.get("DOD", 0),
                    posted_date=datetime.now() - timedelta(days=2),
                ),
                JobListing(
                    title="Backend Developer - Veterans Affairs",
                    company="Booz Allen Hamilton",
                    location="Washington, DC / Remote",
                    agency="VA",
                    clearance_required=True,
                    description="Backend developer for VA contracts. Spring Boot, API development, government experience.",
                    url="https://linkedin.com/jobs/view/67890",
                    match_score=0.88,
                    agency_score=AGENCY_PRIORITY_SCORES.get("VA", 0),
                    posted_date=datetime.now() - timedelta(days=1),
                ),
                JobListing(
                    title="DevOps Engineer - Defense Health Agency",
                    company="Leidos",
                    location="Remote",
                    agency="DHA",
                    clearance_required=False,
                    description="DevOps engineer for DHA healthcare systems. AWS, Kubernetes, CI/CD experience.",
                    url="https://linkedin.com/jobs/view/54321",
                    match_score=0.82,
                    agency_score=AGENCY_PRIORITY_SCORES.get("DHA", 0),
                    posted_date=datetime.now() - timedelta(days=3),
                ),
            ]

            return mock_jobs

        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return []


class ClearanceDetector:
    """Detect clearance requirements in job descriptions"""

    @staticmethod
    def has_clearance_requirement(text: str) -> bool:
        """Check if job description mentions clearance requirements"""
        if not text:
            return False

        text_lower = text.lower()
        for pattern in CLEARANCE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def detect_agency(text: str) -> Optional[str]:
        """Detect government agency from job description"""
        agency_patterns = {
            "VA": [r"veterans affairs", r"VA", r"veterans administration"],
            "DHA": [r"defense health agency", r"DHA", r"military health"],
            "DOD": [r"department of defense", r"DOD", r"defense department"],
            "DOT": [r"department of transportation", r"DOT"],
        }

        text_lower = text.lower()
        for agency, patterns in agency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return agency
        return None

    @staticmethod
    def calculate_match_score(job: JobListing) -> float:
        """Calculate how well job matches target criteria"""
        score = 0.0

        # Base score for clearance match
        if job.clearance_required:
            score += 0.4

        # Agency priority boost
        score += job.agency_score * 0.1

        # Keyword matching (simple implementation)
        target_keywords = ["java", "spring", "aws", "api", "backend", "senior"]
        description_lower = job.description.lower()

        for keyword in target_keywords:
            if keyword in description_lower:
                score += 0.05

        return min(score, 1.0)


class JobSearchService:
    """Main job search orchestration service"""

    def __init__(self):
        self.linkedin_client = LinkedInClient()
        self.clearance_detector = ClearanceDetector()

    async def search_government_jobs(
        self, request: JobSearchRequest
    ) -> List[JobListing]:
        """Search for government contracting jobs"""
        try:
            # Search LinkedIn for jobs
            jobs = await self.linkedin_client.search_jobs(
                keywords=request.keywords,
                location=request.location,
                days_back=request.days_back,
            )

            # Enhance job data with clearance detection and scoring
            enhanced_jobs = []
            for job in jobs:
                # Detect clearance requirements
                job.clearance_required = (
                    self.clearance_detector.has_clearance_requirement(
                        f"{job.description} {job.requirements or ''}"
                    )
                )

                # Detect agency if not already set
                if not job.agency:
                    job.agency = self.clearance_detector.detect_agency(
                        f"{job.description} {job.requirements or ''}"
                    )

                # Calculate match score
                job.match_score = self.clearance_detector.calculate_match_score(job)

                # Set agency score
                job.agency_score = AGENCY_PRIORITY_SCORES.get(job.agency or "", 0)

                enhanced_jobs.append(job)

            # Sort by match score (highest first)
            enhanced_jobs.sort(key=lambda x: x.match_score, reverse=True)

            logger.info(f"Found {len(enhanced_jobs)} government jobs")
            return enhanced_jobs

        except Exception as e:
            logger.error(f"Government job search failed: {e}")
            return []


# Global service instance
job_service = JobSearchService()

# Email service (use mock if no SMTP configured)
notification_service = (
    NotificationService() if os.getenv("SMTP_PASSWORD") else MockNotificationService()
)


# Startup event to start scheduler
@app.on_event("startup")
async def startup_event():
    """Start automated job search scheduler"""
    if os.getenv("JOB_SEARCH_ENABLED", "true").lower() == "true":
        scheduler.start_scheduled_searches()
        logger.info("Job search scheduler started")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "job-search"}


@app.get("/scheduler/status")
async def scheduler_status():
    """Get scheduler status"""
    jobs = scheduler.scheduler.get_jobs()
    return {
        "status": "running",
        "scheduled_jobs": len(jobs),
        "next_runtime": str(jobs[0].next_run_time) if jobs else "No scheduled jobs",
    }


@app.post("/jobs/alert")
async def send_job_alert(job_ids: List[str]):
    """Send email alert for specific jobs"""
    # TODO: Retrieve jobs from database and send alert
    return {"status": "success", "message": "Job alert sent"}


@app.post("/search")
async def search_jobs(request: JobSearchRequest, background_tasks: BackgroundTasks):
    """Search for government contracting jobs"""
    try:
        jobs = await job_service.search_government_jobs(request)

        # Store jobs in database in background
        background_tasks.add_task(store_jobs_in_database, jobs)

        return {
            "status": "success",
            "jobs_found": len(jobs),
            "jobs": [job.dict() for job in jobs[:10]],  # Return top 10
            "message": f"Found {len(jobs)} government contracting jobs",
        }
    except Exception as e:
        logger.error(f"Job search endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/jobs")
async def get_jobs(status: Optional[JobStatus] = None, limit: int = 50):
    """Get stored job listings"""
    # TODO: Implement database query
    return {"status": "success", "jobs": [], "message": "Database integration pending"}


@app.post("/jobs/{job_id}/apply")
async def mark_applied(job_id: str):
    """Mark job as applied"""
    # TODO: Implement database update
    return {"status": "success", "message": f"Marked job {job_id} as applied"}


async def store_jobs_in_database(jobs: List[JobListing]):
    """Store jobs in database (background task)"""
    # TODO: Implement database storage
    logger.info(f"Storing {len(jobs)} jobs in database")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8007)
