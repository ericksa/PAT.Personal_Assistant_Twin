# services/jobs/core/scheduler.py - Scheduler Logic
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import os
from typing import List, Dict

# Import notification service
from notification_service import NotificationService, MockNotificationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobSearchScheduler:
    """Automated job search scheduler"""

    def __init__(self, job_service, notification_service=None):
        self.job_service = job_service
        self.scheduler = AsyncIOScheduler()

        # Use provided notification service or create mock
        self.notification_service = (
            notification_service
            if notification_service
            else (
                NotificationService()
                if os.getenv("SMTP_PASSWORD")
                else MockNotificationService()
            )
        )

    def start_scheduled_searches(self):
        """Start automated job searches"""
        schedule = os.getenv("JOB_SEARCH_SCHEDULE", "0 8 * * *")

        try:
            self.scheduler.add_job(
                self._run_daily_search,
                CronTrigger.from_crontab(schedule),
                id="daily_job_search",
                name="Daily Government Job Search",
            )

            self.scheduler.start()
            logger.info(f"Started job search scheduler with schedule: {schedule}")

        except Exception as e:
            logger.error(f"Failed to schedule job searches: {e}")

    async def _run_daily_search(self):
        """Run daily job search and send notifications"""
        try:
            logger.info("Starting daily government job search...")

            # Import JobSearchRequest dynamically
            from models.job_listing import JobSearchRequest

            search_request = JobSearchRequest(
                keywords="government secret clearance senior software engineer backend java spring boot aws",
                location="remote",
                days_back=7,  # Last week only
            )

            jobs = await self.job_service.search_government_jobs(search_request)

            # Filter for high-quality matches
            high_quality_jobs = [
                job
                for job in jobs
                if job.match_score > 0.7  # 70%+ match
                and job.clearance_required  # Require clearance
            ]

            if high_quality_jobs:
                logger.info(f"Found {len(high_quality_jobs)} high-quality jobs")

                # Send email notification
                success = await self.notification_service.send_job_alert(
                    [job.dict() for job in high_quality_jobs], daily_summary=True
                )

                if success:
                    logger.info("Sent daily job alert email")
                else:
                    logger.warning("Failed to send job alert email")

                # Store jobs in database
                await self._store_jobs_in_database(
                    [job.dict() for job in high_quality_jobs]
                )

            else:
                logger.info("No high-quality jobs found today")

        except Exception as e:
            logger.error(f"Daily job search failed: {e}")

    async def _store_jobs_in_database(self, jobs: List[Dict]):
        """Store jobs in database"""
        # This would connect to PostgreSQL and store the jobs
        # For now, just log the intent
        logger.info(f"Would store {len(jobs)} jobs in database")

        for job in jobs[:5]:  # Log first 5
            logger.info(
                f"  - {job.get('title')} at {job.get('company')} (Score: {job.get('match_score', 0):.2f})"
            )

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Stopped job search scheduler")
