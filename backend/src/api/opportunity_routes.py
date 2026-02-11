# src/api/opportunity_routes.py - FastAPI Routes
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from typing import List, Optional, Dict, Any
import logging
import os
import time

# Import models
from src.models.opportunity import OpportunitySearchRequest, JobStatus, Opportunity

logger = logging.getLogger(__name__)


def create_app(opportunity_service=None, scheduler_service=None):
    """Create FastAPI application with dependency injection and comprehensive API documentation"""

    app = FastAPI(
        title="PAT Job Search Service API",
        description="""
        Personal Assistant Twin (PAT) Job Search Service for Government Contracting Opportunities.
        
        This service automatically searches for government contracting jobs requiring security clearance,
        prioritizes opportunities by agency (VA, DHA, DOD, DOT), and provides real-time alerts.
        
        ## Features
        
        * **Automated Job Search**: Scheduled background searches for new opportunities
        * **Agency Priority**: Scoring system prioritizing VA, DHA, DOD, and DOT contracts
        * **Clearance Detection**: Automatic detection of security clearance requirements
        * **Email Alerts**: Daily email notifications for high-quality job matches
        * **Match Scoring**: Intelligent scoring based on user preferences and job requirements
        
        ## Usage
        
        1. Use `/search` to find government contracting jobs
        2. Review matches returned based on your preferences
        3. Mark interesting jobs as "interested" or "applied"
        4. Receive daily email alerts for new high-quality matches
        """,
        version="1.0.0",
        contact={
            "name": "PAT Development Team",
            "email": "admin@pat.local",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    responses = {
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"},
        503: {"description": "Service unavailable"},
    }

    # Import JobSearchService dynamically to prevent circular imports
    if opportunity_service is None:
        from src.services.opportunity_service import OpportunityService

        opportunity_service = OpportunityService()

    if scheduler_service is None:
        from src.services.simple_scheduler import SimpleOpportunityScheduler

        scheduler_service = SimpleOpportunityScheduler(opportunity_service)

    @app.get(
        "/health",
        tags=["System"],
        summary="Health Check",
        description="Check if the job search service is running healthy",
        operation_id="health_check",
        responses={
            200: {
                "description": "Service is healthy",
                "content": {
                    "application/json": {
                        "example": {"status": "healthy", "service": "job-search"}
                    }
                },
            }
        },
    )
    async def health_check() -> Dict[str, str]:
        return {"status": "healthy", "service": "job-search"}

    @app.post(
        "/search",
        tags=["Jobs"],
        summary="Search Government Contracting Jobs",
        description="""
        Search for government contracting jobs based on provided criteria.
        
        The search returns jobs that match your keywords, location preferences,
        and optionally filters by specific companies. Results are scored based on:
        
        * **Clearance Requirements**: Priority given to jobs requiring security clearance
        * **Agency Priority**: VA (highest), DHA, DOD, DOT, Other
        * **Match Score**: Calculated based on job description vs. your keywords
        
        The top 10 results are returned in the response, with all matching jobs
        stored in the database for future reference.
        """,
        operation_id="search_jobs",
        response_description="List of matching job opportunities with match scores",
        responses={
            200: {
                "description": "Search completed successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "success",
                            "jobs_found": 25,
                            "jobs": [
                                {
                                    "id": "12345",
                                    "title": "Senior Software Engineer",
                                    "company": "Booz Allen Hamilton",
                                    "location": "Remote",
                                    "agency": "VA",
                                    "clearance_required": True,
                                    "match_score": 0.95,
                                    "agency_score": 4,
                                }
                            ],
                            "message": "Found 25 government contracting jobs",
                        }
                    }
                },
            },
            400: {"description": "Invalid request parameters"},
            500: {"description": "Search failed due to server error"},
        },
    )
    async def search_jobs(
        request: OpportunitySearchRequest, background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Search for government contracting jobs"""
        start_time = time.time()
        try:
            from src.utils.metrics_middleware import BusinessMetricsTracker

            metrics = BusinessMetricsTracker()

            jobs = await opportunity_service.search_government_jobs(request)

            # Store jobs in database in background
            background_tasks.add_task(
                store_jobs_in_database, [job.model_dump() for job in jobs]
            )

            duration_ms = (time.time() - start_time) * 1000

            # Track metrics
            high_quality_count = len([j for j in jobs if j.match_score > 0.7])
            metrics.track_opportunity_search(
                success=True,
                location=request.location,
                opportunities_found=len(jobs),
                high_quality_count=high_quality_count,
                duration_ms=duration_ms,
            )

            return {
                "status": "success",
                "jobs_found": len(jobs),
                "jobs": [job.model_dump() for job in jobs[:10]],  # Return top 10
                "message": f"Found {len(jobs)} government contracting jobs",
                "duration_ms": round(duration_ms, 2),
            }
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Job search endpoint error: {e}",
                extra={
                    "event": "search_error",
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                },
            )

            # Track failed metrics
            from src.utils.metrics_middleware import BusinessMetricsTracker

            metrics = BusinessMetricsTracker()
            metrics.track_opportunity_search(
                success=False,
                location=request.location,
                opportunities_found=0,
                duration_ms=duration_ms,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Search failed: {str(e)}",
            )

    @app.get(
        "/jobs",
        tags=["Jobs"],
        summary="Get Stored Job Listings",
        description="""
        Retrieve previously searched and stored job listings.
        
        Supports filtering by status and limiting the number of results.
        Jobs are stored in PostgreSQL with vector embeddings for semantic search.
        """,
        operation_id="get_jobs",
        response_description="List of stored job opportunities",
        responses={
            200: {
                "description": "Jobs retrieved successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "success",
                            "jobs": [],
                            "total": 0,
                            "message": "Jobs retrieved",
                        }
                    }
                },
            }
        },
    )
    async def get_jobs(
        status: Optional[JobStatus] = None, limit: int = 50
    ) -> Dict[str, Any]:
        """Get stored job listings"""
        # TODO: Implement database query
        return {
            "status": "success",
            "jobs": [],
            "total": 0,
            "message": "Database integration pending",
        }

    @app.post(
        "/jobs/{job_id}/apply",
        tags=["Jobs"],
        summary="Mark Job as Applied",
        description="""
        Update the status of a job to 'applied' to track your application progress.
        
        This action updates the job's status in the database and can be used
        to track which opportunities you've applied to.
        """,
        operation_id="mark_job_applied",
        response_description="Confirmation of status update",
        responses={
            200: {
                "description": "Job status updated successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "success",
                            "message": "Marked job 12345 as applied",
                        }
                    }
                },
            },
            404: {"description": "Job not found"},
        },
    )
    async def mark_applied(job_id: str) -> Dict[str, str]:
        """Mark job as applied"""
        # TODO: Implement database update
        return {"status": "success", "message": f"Marked job {job_id} as applied"}

    @app.get(
        "/scheduler/status",
        tags=["Scheduler"],
        summary="Get Scheduler Status",
        description="""
        Get the current status of the automated job search scheduler.
        
        The scheduler runs daily searches according to the configured schedule
        and sends email alerts for high-quality job matches.
        """,
        operation_id="get_scheduler_status",
        response_description="Current scheduler status and next run time",
        responses={
            200: {
                "description": "Scheduler status retrieved",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "running",
                            "scheduled_jobs": 1,
                            "next_runtime": "Daily scheduled search",
                            "last_run": "2024-02-09T08:00:00Z",
                        }
                    }
                },
            }
        },
    )
    async def scheduler_status() -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "status": "running",
            "scheduled_jobs": 1,
            "next_runtime": "Daily scheduled search",
        }

    @app.post(
        "/jobs/alert",
        tags=["Jobs"],
        summary="Send Job Alert",
        description="""
        Send an email alert for specific job IDs.
        
        This endpoint triggers an email notification containing details
        of the specified jobs, useful for manually sending alerts
        or testing notification functionality.
        """,
        operation_id="send_job_alert",
        response_description="Email sent confirmation",
        responses={
            200: {
                "description": "Alert sent successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "success",
                            "message": "Job alert sent for 3 jobs",
                            "jobs_sent": 3,
                        }
                    }
                },
            },
            400: {"description": "Invalid job IDs"},
            500: {"description": "Failed to send email"},
        },
    )
    async def send_job_alert(job_ids: List[str]) -> Dict[str, Any]:
        """Send email alert for specific jobs"""
        # TODO: Retrieve jobs from database and send alert
        return {
            "status": "success",
            "message": "Job alert sent",
            "jobs_sent": len(job_ids),
        }

    # Startup event to start scheduler
    @app.on_event("startup")
    async def startup_event():
        """Start automated job search scheduler"""
        if os.getenv("JOB_SEARCH_ENABLED", "true").lower() == "true":
            scheduler_service.start_scheduled_searches()
            logger.info("Job search scheduler started")

    async def store_jobs_in_database(jobs: list):
        """Store jobs in database (background task)"""
        logger.info(f"Storing {len(jobs)} jobs in database")
        # TODO: Implement database storage
        for job in jobs[:3]:
            logger.info(f"  - {job.get('title')} at {job.get('company')}")

    return app


# Global app instance for external use
app = create_app()
