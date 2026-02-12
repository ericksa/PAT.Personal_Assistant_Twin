"""
Job Repository
Database operations for job listings and applications
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class JobRepository(BaseRepository):
    """Repository for job-related database operations"""

    def __init__(self, db_helper):
        super().__init__(db_helper)
        self.table_name = "job_listings"

    async def create_job_listing(
        self, job_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a new job listing"""
        try:
            # Ensure required fields are present
            required_fields = ["title", "company", "url"]
            for field in required_fields:
                if field not in job_data or not job_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Set default values
            job_data.setdefault("status", "new")
            job_data.setdefault("source", "linkedin")
            job_data.setdefault("found_date", datetime.utcnow())

            # Check if job already exists
            existing = await self.get_by_url(job_data["url"])
            if existing:
                logger.info(f"Job already exists: {job_data['url']}")
                return existing

            # Create job listing
            result = await self.create(self.table_name, job_data)
            if result:
                logger.info(
                    f"Created job listing: {result['title']} at {result['company']}"
                )

            return result

        except Exception as e:
            logger.error(f"Error creating job listing: {e}")
            raise

    async def get_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get job listing by URL (to avoid duplicates)"""
        query = "SELECT * FROM job_listings WHERE url = $1"
        return await self.fetchrow(query, url)

    async def search_jobs(
        self,
        keywords: Optional[str] = None,
        agency: Optional[str] = None,
        clearance_required: Optional[bool] = None,
        status: Optional[str] = None,
        days_back: int = 7,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search job listings with filters"""
        try:
            conditions = []
            params = []
            param_count = 0

            # Date filter
            if days_back > 0:
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                param_count += 1
                conditions.append(f"found_date >= ${param_count}")
                params.append(cutoff_date)

            # Keyword search
            if keywords:
                param_count += 1
                conditions.append(
                    f"(title ILIKE ${param_count} OR company ILIKE ${param_count} OR description ILIKE ${param_count})"
                )
                params.append(f"%{keywords}%")

            # Agency filter
            if agency:
                param_count += 1
                conditions.append(f"agency = ${param_count}")
                params.append(agency)

            # Clearance requirement
            if clearance_required is not None:
                param_count += 1
                conditions.append(f"clearance_required = ${param_count}")
                params.append(clearance_required)

            # Status filter
            if status:
                param_count += 1
                conditions.append(f"status = ${param_count}")
                params.append(status)

            # Build query
            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT *, 
                       (match_score + agency_score::decimal / 10) as total_score
                FROM job_listings
                WHERE {where_clause}
                ORDER BY total_score DESC, found_date DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])

            results = await self.fetch(query, *params)
            return [dict(result) for result in results]

        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            raise

    async def get_jobs_by_status(
        self, status: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get jobs by status"""
        query = """
            SELECT * FROM job_listings
            WHERE status = $1
            ORDER BY found_date DESC
            LIMIT $2 OFFSET $3
        """
        results = await self.fetch(query, status, limit, offset)
        return [dict(result) for result in results]

    async def update_job_status(
        self, job_id: str, status: str
    ) -> Optional[Dict[str, Any]]:
        """Update job status"""
        return await self.update(self.table_name, job_id, {"status": status})

    async def get_job_statistics(self) -> Dict[str, Any]:
        """Get job statistics"""
        try:
            # Total jobs
            total_query = "SELECT COUNT(*) as total FROM job_listings"
            total_result = await self.fetchrow(total_query)
            total_jobs = total_result["total"] if total_result else 0

            # Status breakdown
            status_query = (
                "SELECT status, COUNT(*) as count FROM job_listings GROUP BY status"
            )
            status_results = await self.fetch(status_query)
            status_counts = {row["status"]: row["count"] for row in status_results}

            # Recent jobs (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_query = (
                "SELECT COUNT(*) as recent FROM job_listings WHERE found_date >= $1"
            )
            recent_result = await self.fetchrow(recent_cutoff)
            recent_jobs = recent_result["recent"] if recent_result else 0

            # Agency breakdown
            agency_query = """
                SELECT agency, COUNT(*) as count 
                FROM job_listings 
                WHERE agency IS NOT NULL 
                GROUP BY agency 
                ORDER BY count DESC
            """
            agency_results = await self.fetch(agency_query)
            agency_counts = {row["agency"]: row["count"] for row in agency_results}

            # Average match score
            score_query = "SELECT AVG(match_score) as avg_score FROM job_listings"
            score_result = await self.fetchrow(score_query)
            avg_score = (
                score_result["avg_score"]
                if score_result and score_result["avg_score"]
                else 0.0
            )

            return {
                "total_jobs": total_jobs,
                "recent_jobs_7_days": recent_jobs,
                "status_breakdown": status_counts,
                "agency_breakdown": agency_counts,
                "average_match_score": round(avg_score, 2),
            }

        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            raise

    async def mark_job_applied(
        self, job_id: str, application_data: Dict[str, Any] = None
    ) -> bool:
        """Mark job as applied and create application record"""
        try:
            # Update job status
            await self.update_job_status(job_id, "applied")

            # Create application record
            if application_data:
                app_data = {
                    "job_listing_id": job_id,
                    "applied_date": datetime.utcnow(),
                    "status": "applied",
                    **application_data,
                }

                app_repo = JobApplicationRepository(self.db)
                await app_repo.create_application(app_data)

            logger.info(f"Marked job {job_id} as applied")
            return True

        except Exception as e:
            logger.error(f"Error marking job as applied: {e}")
            return False

    async def get_high_priority_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get high priority jobs (high scores, recent, relevant agencies)"""
        query = """
            SELECT *,
                   (match_score + agency_score::decimal / 10) as priority_score
            FROM job_listings
            WHERE status IN ('new', 'reviewed') 
              AND (match_score > 0.7 OR agency_score > 3)
              AND found_date >= $1
            ORDER BY priority_score DESC, found_date DESC
            LIMIT $2
        """
        cutoff_date = datetime.utcnow() - timedelta(days=3)
        results = await self.fetch(query, cutoff_date, limit)
        return [dict(result) for result in results]

    async def cleanup_old_jobs(self, days_to_keep: int = 90) -> int:
        """Clean up old jobs that haven't been updated"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            query = """
                DELETE FROM job_listings 
                WHERE status = 'new' 
                  AND found_date < $1
                  AND created_at < $1
            """
            result = await self.execute(query, cutoff_date)

            # Extract count from DELETE result
            deleted_count = 0
            if "DELETE" in result:
                try:
                    deleted_count = int(result.split()[1])
                except (IndexError, ValueError):
                    pass

            logger.info(f"Cleaned up {deleted_count} old job listings")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {e}")
            return 0


class JobApplicationRepository(BaseRepository):
    """Repository for job applications tracking"""

    def __init__(self, db_helper):
        super().__init__(db_helper)
        self.table_name = "job_applications"

    async def create_application(
        self, app_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a new job application record"""
        try:
            # Ensure required fields
            required_fields = ["job_listing_id"]
            for field in required_fields:
                if field not in app_data or not app_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Set defaults
            app_data.setdefault("status", "interested")
            app_data.setdefault("applied_date", datetime.utcnow())

            result = await self.create(self.table_name, app_data)
            if result:
                logger.info(
                    f"Created application record for job {app_data['job_listing_id']}"
                )

            return result

        except Exception as e:
            logger.error(f"Error creating application: {e}")
            raise

    async def get_applications_by_status(
        self, status: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get applications by status"""
        query = """
            SELECT ja.*, jl.title, jl.company, jl.agency
            FROM job_applications ja
            JOIN job_listings jl ON ja.job_listing_id = jl.id
            WHERE ja.status = $1
            ORDER BY ja.applied_date DESC
            LIMIT $2
        """
        results = await self.fetch(query, status, limit)
        return [dict(result) for result in results]

    async def update_application_status(
        self, application_id: str, status: str, notes: str = None
    ) -> Optional[Dict[str, Any]]:
        """Update application status"""
        update_data = {"status": status}
        if notes:
            update_data["notes"] = notes

        return await self.update(self.table_name, application_id, update_data)

    async def get_follow_up_tasks(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get applications that need follow-up"""
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        query = """
            SELECT ja.*, jl.title, jl.company, jl.agency
            FROM job_applications ja
            JOIN job_listings jl ON ja.job_listing_id = jl.id
            WHERE ja.follow_up_date <= $1
              AND ja.status IN ('applied', 'interview')
            ORDER BY ja.follow_up_date ASC
        """
        results = await self.fetch(query, cutoff_date)
        return [dict(result) for result in results]


class ResumeRepository(BaseRepository):
    """Repository for resume versions tracking"""

    def __init__(self, db_helper):
        super().__init__(db_helper)
        self.table_name = "resume_versions"

    async def create_resume_version(
        self, resume_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a new resume version"""
        try:
            required_fields = ["job_listing_id"]
            for field in required_fields:
                if field not in resume_data or not resume_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            resume_data.setdefault("generated_date", datetime.utcnow())
            resume_data.setdefault("revisions", 1)

            result = await self.create(self.table_name, resume_data)
            if result:
                logger.info(
                    f"Created resume version for job {resume_data['job_listing_id']}"
                )

            return result

        except Exception as e:
            logger.error(f"Error creating resume version: {e}")
            raise

    async def get_resumes_for_job(self, job_listing_id: str) -> List[Dict[str, Any]]:
        """Get all resume versions for a specific job"""
        query = """
            SELECT rv.*, jl.title, jl.company
            FROM resume_versions rv
            JOIN job_listings jl ON rv.job_listing_id = jl.id
            WHERE rv.job_listing_id = $1
            ORDER BY rv.generated_date DESC
        """
        results = await self.fetch(query, job_listing_id)
        return [dict(result) for result in results]

    async def get_latest_resume_for_job(
        self, job_listing_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent resume version for a job"""
        query = """
            SELECT rv.*, jl.title, jl.company
            FROM resume_versions rv
            JOIN job_listings jl ON rv.job_listing_id = jl.id
            WHERE rv.job_listing_id = $1
            ORDER BY rv.generated_date DESC
            LIMIT 1
        """
        result = await self.fetchrow(query, job_listing_id)
        return dict(result) if result else None
