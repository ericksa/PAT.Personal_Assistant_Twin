# services/jobs/api/endpoints.py - FastAPI Routes
from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import List, Optional
import logging
import os

# Import models
from models.job_listing import JobSearchRequest, JobStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(job_service=None, scheduler_service=None):
    """Create FastAPI application with dependency injection"""
    app = FastAPI(title="PAT Job Search Service")

    # Import JobSearchService dynamically to prevent circular imports
    if job_service is None:
        from core.job_service import JobSearchService

        job_service = JobSearchService()

    if scheduler_service is None:
        from core.scheduler import JobSearchScheduler

        scheduler_service = JobSearchScheduler(job_service)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "job-search"}

    @app.post("/search")
    async def search_jobs(request: JobSearchRequest, background_tasks: BackgroundTasks):
        """Search for government contracting jobs"""
        try:
            jobs = await job_service.search_government_jobs(request)

            # Store jobs in database in background
            background_tasks.add_task(
                store_jobs_in_database, [job.dict() for job in jobs]
            )

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
        return {
            "status": "success",
            "jobs": [],
            "message": "Database integration pending",
        }

    @app.post("/jobs/{job_id}/apply")
    async def mark_applied(job_id: str):
        """Mark job as applied"""
        # TODO: Implement database update
        return {"status": "success", "message": f"Marked job {job_id} as applied"}

    @app.get("/scheduler/status")
    async def scheduler_status():
        """Get scheduler status"""
        jobs = scheduler_service.scheduler.get_jobs()
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
