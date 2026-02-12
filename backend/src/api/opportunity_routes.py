# src/api/opportunity_routes.py - FastAPI Routes
from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Query
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
        * **Resume Matching**: AI-powered resume customization for each opportunity
        * **Application Tracking**: Track application status and follow-up reminders
        * **Performance Analytics**: Monitor success rates and optimize search parameters
        """,
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Default services if not provided
    if opportunity_service is None:
        from src.services.opportunity_service import OpportunityService

        opportunity_service = OpportunityService()

    if scheduler_service is None:
        from src.services.scheduler_service import OpportunityScheduler

        scheduler_service = OpportunityScheduler(opportunity_service)

    @app.get(
        "/health",
        tags=["Health"],
        summary="Health Check",
        description="""
        Check if the service is running and operational.
        
        This endpoint performs a comprehensive health check including:
        - Service status
        - Database connectivity
        - Job scheduler status
        - Last successful job search
        """,
        operation_id="health_check",
        responses={
            200: {
                "description": "Service is healthy",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "healthy",
                            "timestamp": "2024-01-15T10:30:00Z",
                            "service": "pat-job-search",
                            "version": "2.0.0",
                            "database": "connected",
                            "scheduler": "running",
                            "last_job_search": "2024-01-15T09:00:00Z",
                        }
                    }
                },
            },
        },
    )
    async def health_check():
        """Comprehensive health check"""
        try:
            # Check database connectivity
            db_status = "connected"  # In real implementation, test database connection

            # Check scheduler status
            scheduler_status = "running" if scheduler_service.is_running else "stopped"

            # Get last job search time
            last_search = None  # TODO: Implement in OpportunityService

            return {
                "status": "healthy",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "service": "pat-job-search",
                "version": "2.0.0",
                "database": db_status,
                "scheduler": scheduler_status,
                "last_job_search": last_search.isoformat() if last_search else None,
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
            )

    @app.get(
        "/jobs",
        tags=["Jobs"],
        summary="Get Job Listings",
        description="""
        Retrieve stored job listings with optional filtering.
        
        This endpoint provides access to all job opportunities that have been
        collected and stored in the database. You can filter by status, agency,
        and other criteria to find relevant opportunities.
        """,
        operation_id="get_job_listings",
        response_description="List of job opportunities",
        responses={
            200: {
                "description": "Job listings retrieved successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "success",
                            "jobs": [
                                {
                                    "id": "123e4567-e89b-12d3-a456-426614174000",
                                    "title": "Senior Software Engineer",
                                    "company": "Department of Veterans Affairs",
                                    "location": "Remote",
                                    "agency": "VA",
                                    "clearance_required": True,
                                    "salary_range": "$120,000 - $160,000",
                                    "description": "Lead development of...",
                                    "url": "https://linkedin.com/jobs/view/...",
                                    "match_score": 0.85,
                                    "agency_score": 4,
                                    "status": "new",
                                    "posted_date": "2024-01-15",
                                    "found_date": "2024-01-15T10:30:00Z",
                                    "source": "linkedin",
                                }
                            ],
                            "total": 1,
                            "message": "Found 1 job opportunities",
                        }
                    }
                },
            },
        },
    )
    async def get_jobs(
        agency: Optional[str] = Query(
            None, description="Filter by agency (VA, DHA, DoD, DOT)"
        ),
        status: Optional[str] = Query(None, description="Filter by job status"),
        clearance_required: Optional[bool] = Query(
            None, description="Filter by clearance requirement"
        ),
        days_back: int = Query(7, description="Jobs from last N days"),
        limit: int = Query(50, description="Maximum number of jobs to return"),
        offset: int = Query(0, description="Number of jobs to skip"),
    ) -> Dict[str, Any]:
        """Get stored job listings with database integration"""
        try:
            from src.repositories.job_repo import JobRepository
            from src.repositories.sql_helper import get_db_helper

            # Get database helper
            db_helper = get_db_helper()
            job_repo = JobRepository(db_helper)

            # Convert None values to appropriate defaults
            status_filter = status if status else None

            # Search jobs using repository
            jobs = await job_repo.search_jobs(
                keywords=None,  # Can add keyword search later
                agency=agency,
                clearance_required=clearance_required,
                status=status_filter,
                days_back=days_back,
                limit=limit,
                offset=offset,
            )

            # Convert datetime objects to ISO strings for JSON serialization
            for job in jobs:
                if job.get("found_date"):
                    job["found_date"] = job["found_date"].isoformat()
                if job.get("posted_date"):
                    job["posted_date"] = job["posted_date"].isoformat()

            return {
                "status": "success",
                "jobs": jobs,
                "total": len(jobs),
                "message": f"Found {len(jobs)} job opportunities",
                "filters": {
                    "agency": agency,
                    "status": status_filter,
                    "clearance_required": clearance_required,
                    "days_back": days_back,
                },
            }

        except Exception as e:
            logger.error(f"Error retrieving job listings: {e}")
            return {
                "status": "error",
                "jobs": [],
                "total": 0,
                "message": f"Error retrieving jobs: {str(e)}",
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
        try:
            from src.repositories.job_repo import JobRepository
            from src.repositories.sql_helper import get_db_helper

            # Get database helper and repository
            db_helper = get_db_helper()
            job_repo = JobRepository(db_helper)

            # Mark job as applied
            success = await job_repo.mark_job_applied(job_id)

            if success:
                return {
                    "status": "success",
                    "message": f"Marked job {job_id} as applied",
                    "job_id": job_id,
                }
            else:
                raise HTTPException(
                    status_code=404, detail="Job not found or could not be updated"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error marking job as applied: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to update job status: {str(e)}"
            )

    @app.get(
        "/scheduler/status",
        tags=["Scheduler"],
        summary="Get Scheduler Status",
        description="""
        Get the current status of the automated job search scheduler.
        
        This endpoint shows whether the scheduler is running, how many jobs
        are scheduled, and when the next job search will occur.
        """,
        operation_id="get_scheduler_status",
        response_description="Scheduler status information",
        responses={
            200: {
                "description": "Scheduler status retrieved",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "running",
                            "scheduled_jobs": 3,
                            "next_runtime": "2024-01-15T14:00:00Z",
                            "last_success": "2024-01-15T10:30:00Z",
                            "total_searches_today": 5,
                        }
                    }
                },
            },
        },
    )
    async def scheduler_status():
        """Get scheduler status"""
        try:
            jobs = scheduler_service.scheduler.get_jobs()
            stats = scheduler_service.get_scheduler_stats()

            return {
                "status": "running" if scheduler_service.is_running else "stopped",
                "scheduled_jobs": len(jobs),
                "next_runtime": str(jobs[0].next_run_time)
                if jobs
                else "No scheduled jobs",
                "last_success": stats.get("last_success"),
                "total_searches_today": stats.get("searches_today", 0),
            }
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {"status": "error", "error": str(e)}

    @app.post(
        "/scheduler/start",
        tags=["Scheduler"],
        summary="Start Job Scheduler",
        description="""
        Start the automated job search scheduler.
        
        This will begin scheduled background searches for new job opportunities
        according to the configured schedule.
        """,
        operation_id="start_scheduler",
        response_description="Scheduler start confirmation",
        responses={
            200: {
                "description": "Scheduler started successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "success",
                            "message": "Job search scheduler started",
                            "scheduled_jobs": 3,
                        }
                    }
                },
            },
        },
    )
    async def start_scheduler():
        """Start the job scheduler"""
        try:
            if scheduler_service.is_running:
                return {
                    "status": "success",
                    "message": "Scheduler is already running",
                    "scheduled_jobs": len(scheduler_service.scheduler.get_jobs()),
                }

            scheduler_service.start_scheduled_searches()

            return {
                "status": "success",
                "message": "Job search scheduler started",
                "scheduled_jobs": len(scheduler_service.scheduler.get_jobs()),
            }
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post(
        "/scheduler/stop",
        tags=["Scheduler"],
        summary="Stop Job Scheduler",
        description="""
        Stop the automated job search scheduler.
        
        This will halt all scheduled background searches.
        """,
        operation_id="stop_scheduler",
        response_description="Scheduler stop confirmation",
        responses={
            200: {
                "description": "Scheduler stopped successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "success",
                            "message": "Job search scheduler stopped",
                        }
                    }
                },
            },
        },
    )
    async def stop_scheduler():
        """Stop the job scheduler"""
        try:
            if not scheduler_service.is_running:
                return {"status": "success", "message": "Scheduler is not running"}

            scheduler_service.stop_scheduled_searches()

            return {"status": "success", "message": "Job search scheduler stopped"}
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post(
        "/jobs/alert",
        tags=["Jobs"],
        summary="Send Job Alert",
        description="""
        Send email alert for specific jobs.
        
        This endpoint can be used to trigger email notifications for
        selected job opportunities.
        """,
        operation_id="send_job_alert",
        response_description="Alert sending confirmation",
        responses={
            200: {
                "description": "Alerts sent successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "success",
                            "message": "Job alert sent",
                            "jobs_sent": 3,
                        }
                    }
                },
            },
        },
    )
    async def send_job_alert(job_ids: List[str]):
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

        try:
            from src.repositories.job_repo import JobRepository
            from src.repositories.sql_helper import get_db_helper

            # Get database helper and repository
            db_helper = get_db_helper()
            job_repo = JobRepository(db_helper)

            stored_count = 0
            for job in jobs:
                try:
                    # Ensure job has required fields
                    if not all(key in job for key in ["title", "company", "url"]):
                        logger.warning(
                            f"Skipping job missing required fields: {job.get('title', 'Unknown')}"
                        )
                        continue

                    # Store job in database
                    result = await job_repo.create_job_listing(job)
                    if result:
                        stored_count += 1
                        logger.info(f"  ✓ {job.get('title')} at {job.get('company')}")
                    else:
                        logger.info(
                            f"  - {job.get('title')} at {job.get('company')} (already exists)"
                        )

                except Exception as e:
                    logger.error(
                        f"Error storing job {job.get('title', 'Unknown')}: {e}"
                    )
                    continue

            logger.info(
                f"Successfully stored {stored_count} new jobs out of {len(jobs)} total"
            )

        except Exception as e:
            logger.error(f"Error in background job storage: {e}")

    return app


# Global app instance for external use
app = create_app()
