# services/jobs/core/job_service.py - Job Search Service Logic
from typing import List, Dict, Optional
import logging
import os
import re
from datetime import datetime, timedelta
from enum import Enum

# Import models
from models.job_listing import JobListing, JobSearchRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
AGENCY_PRIORITY_SCORES = {"VA": 4, "DHA": 3, "DOD": 2, "DOT": 1}

# Clearance requirement patterns
CLEARANCE_PATTERNS = [
    r"(secret|top secret|TS/SCI|confidential)[\\s-]*clearance",
    r"clearance[\\s-]*level[\\s:]*(secret|top secret|TS/SCI)",
    r"(DOD|department of defense)[\\s-]*clearance",
    r"security clearance required",
    r"must have (security )?clearance",
]


class LinkedInClient:
    """LinkedIn Jobs API client"""

    def __init__(self):
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
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
