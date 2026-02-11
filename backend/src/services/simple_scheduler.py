# src/services/simple_scheduler.py - Simple Scheduler
import asyncio
import logging
from datetime import datetime, timedelta
import os
from typing import List, Dict

# Import notification service
from src.services.notification_service import (
    NotificationService,
    MockNotificationService,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleOpportunityScheduler:
    """Simple async scheduler for opportunity searches"""

    def __init__(self, opportunity_service, notification_service=None):
        self.opportunity_service = opportunity_service
        self.running = False

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
        """Start automated opportunity searches"""
        self.running = True
        logger.info("Starting simple scheduler")

        # Create background task for scheduled searches
        asyncio.create_task(self._run_periodic_search())

    async def _run_periodic_search(self):
        """Run periodic opportunity searches"""
        while self.running:
            try:
                await self._run_daily_search()

                # Wait 24 hours (simulated cron)
                await asyncio.sleep(24 * 60 * 60)  # 24 hours

            except Exception as e:
                logger.error(f"Periodic search error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _run_daily_search(self):
        """Run daily opportunity search and send notifications"""
        try:
            logger.info("Starting daily government opportunity search...")

            # Import OpportunitySearchRequest dynamically
            from src.models.opportunity import OpportunitySearchRequest

            search_request = OpportunitySearchRequest(
                keywords="government secret clearance senior software engineer backend java spring boot aws",
                location="remote",
                days_back=7,  # Last week only
            )

            opportunities = (
                await self.opportunity_service.search_government_opportunities(
                    search_request
                )
            )

            # Filter for high-quality matches
            high_quality_opportunities = [
                opportunity
                for opportunity in opportunities
                if opportunity.match_score > 0.7  # 70%+ match
                and opportunity.clearance_required  # Require clearance
            ]

            if high_quality_opportunities:
                logger.info(
                    f"Found {len(high_quality_opportunities)} high-quality opportunities"
                )

                # Send email notification
                success = await self.notification_service.send_job_alert(
                    [opportunity.dict() for opportunity in high_quality_opportunities],
                    daily_summary=True,
                )

                if success:
                    logger.info("Sent daily opportunity alert email")
                else:
                    logger.warning("Failed to send opportunity alert email")

                # Store opportunities in database
                await self._store_opportunities_in_database(
                    [opportunity.dict() for opportunity in high_quality_opportunities]
                )

            else:
                logger.info("No high-quality opportunities found today")

        except Exception as e:
            logger.error(f"Daily opportunity search failed: {e}")

    async def _store_opportunities_in_database(self, opportunities: List[Dict]):
        """Store opportunities in database"""
        logger.info(f"Would store {len(opportunities)} opportunities in database")

        for opportunity in opportunities[:5]:  # Log first 5
            logger.info(
                f"  - {opportunity.get('title')} at {opportunity.get('company')} (Score: {opportunity.get('match_score', 0):.2f})"
            )

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Stopped opportunity search scheduler")
