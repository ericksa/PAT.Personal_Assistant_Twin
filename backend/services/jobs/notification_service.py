# services/jobs/notification_service.py - Email Notification Service
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import logging
import os
from typing import List, Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationService:
    """Email notification service for job alerts"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.recipient_email = os.getenv("PAT_NOTIFICATION_EMAIL")

    async def send_job_alert(
        self, jobs: List[Dict], daily_summary: bool = False
    ) -> bool:
        """Send job alert email"""
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured")
            return False

        try:
            subject = self._format_subject(jobs, daily_summary)
            body = self._format_email_body(jobs, daily_summary)

            await self._send_email(subject, body)
            logger.info(f"Sent job alert email with {len(jobs)} jobs")
            return True

        except Exception as e:
            logger.error(f"Failed to send job alert email: {e}")
            return False

    def _format_subject(self, jobs: List[Dict], daily_summary: bool) -> str:
        """Format email subject"""
        if daily_summary:
            return f"PAT Job Alert: {len(jobs)} New Government Contract Positions"

        # Count by agency
        agency_counts = {}
        for job in jobs:
            agency = job.get("agency", "Unknown")
            agency_counts[agency] = agency_counts.get(agency, 0) + 1

        agency_summary = ", ".join([f"{k}: {v}" for k, v in agency_counts.items()])
        return f"PAT Job Alert: {len(jobs)} New Positions ({agency_summary})"

    def _format_email_body(self, jobs: List[Dict], daily_summary: bool) -> str:
        """Format email body with job details"""
        body_parts = []

        if daily_summary:
            body_parts.append(
                f"<h2>Daily Government Job Summary - {datetime.now().strftime('%Y-%m-%d')}</h2>"
            )
        else:
            body_parts.append(f"<h2>New Government Contract Job Alerts</h2>")

        body_parts.append(
            f"<p><strong>Found {len(jobs)} matching positions</strong></p>"
        )

        # Group by agency priority
        agencies = {"VA": [], "DHA": [], "DOD": [], "DOT": [], "Other": []}

        for job in jobs:
            agency = job.get("agency", "Other")
            if agency not in agencies:
                agency = "Other"
            agencies[agency].append(job)

        # Display by priority order
        for agency in ["VA", "DHA", "DOD", "DOT", "Other"]:
            agency_jobs = agencies[agency]
            if agency_jobs:
                body_parts.append(f"<h3>{agency} Positions ({len(agency_jobs)})</h3>")

                for job in agency_jobs:
                    clearance_badge = " 🛡️" if job.get("clearance_required") else ""
                    match_badge = (
                        f" ⭐{job.get('match_score', 0) * 100:.0f}%"
                        if job.get("match_score", 0) > 0.7
                        else ""
                    )

                    body_parts.append(
                        f"""
                    <div style="border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 5px;">
                        <h4>{job.get("title", "N/A")}{clearance_badge}{match_badge}</h4>
                        <p><strong>Company:</strong> {job.get("company", "N/A")}</p>
                        <p><strong>Location:</strong> {job.get("location", "Remote")}</p>
                        <p><strong>Match Score:</strong> {job.get("match_score", 0) * 100:.0f}%</p>
                        <p><strong>Description:</strong> {job.get("description", "")[:200]}...</p>
                        <p><a href="{job.get("url", "#")}" target="_blank">View Job & Apply</a></p>
                    </div>
                    """.format(**job)
                    )

        body_parts.append("""
        <hr>
        <p><small>
            You're receiving this email because you've enabled automated job searching 
            in your PAT (Personal Assistant Twin) system. To modify your search criteria, 
            visit your PAT dashboard.
        </small></p>
        """)

        return "\n".join(body_parts)

    async def _send_email(self, subject: str, body: str) -> None:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MimeMultipart()
            msg["From"] = self.smtp_username
            msg["To"] = self.recipient_email
            msg["Subject"] = subject

            # Add HTML body
            msg.attach(MimeText(body, "html"))

            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise


# Simple fallback for testing
class MockNotificationService:
    """Mock notification service for development"""

    async def send_job_alert(
        self, jobs: List[Dict], daily_summary: bool = False
    ) -> bool:
        """Log job alerts instead of sending emails"""
        logger.info(f"Mock job alert: {len(jobs)} jobs (daily_summary={daily_summary})")
        for job in jobs[:3]:  # Log first 3 jobs
            logger.info(f"  - {job.get('title')} at {job.get('company')}")
        return True
