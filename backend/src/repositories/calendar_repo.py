# src/repositories/calendar_repo.py - Calendar repository with AppleScript integration
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from uuid import UUID
import logging
import json

from src.repositories.sql_helper import sql_helper
from src.models.calendar import CalendarEvent, Conflict, SyncResult, TimeSlot
from src.utils.applescript.base_manager import list_calendars

logger = logging.getLogger(__name__)


class CalendarRepository:
    """Repository for calendar operations with Apple Calendar integration"""

    # Default user ID for single-user setup
    DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"

    # Default calendar name
    DEFAULT_CALENDAR = "PAT-cal"

    async def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new calendar event.
        """
        try:
            query = """
            INSERT INTO calendar_events (
                user_id, title, description, location, 
                start_time, end_time, all_day, recurrence_rule,
                timezone, calendar_name, event_type, status,
                priority, travel_time_minutes, requires_preparation,
                preparation_minutes, sync_status, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, NOW(), NOW())
            RETURNING id, external_event_id, created_at
            """

            values = (
                str(event_data.get("user_id", self.DEFAULT_USER_ID)),
                event_data.get("title"),
                event_data.get("description"),
                event_data.get("location"),
                event_data.get("start_time"),
                event_data.get("end_time"),
                event_data.get("all_day", False),
                event_data.get("recurrence_rule"),
                event_data.get("timezone"),
                event_data.get("calendar_name", self.DEFAULT_CALENDAR),
                event_data.get("event_type", "meeting"),
                event_data.get("status", "confirmed"),
                event_data.get("priority", 0),
                event_data.get("travel_time_minutes", 0),
                event_data.get("requires_preparation", False),
                event_data.get("preparation_minutes", 15),
                event_data.get("sync_status", "pending"),
            )

            result = await sql_helper.execute(query, *values, fetch="one")

            return {
                "id": str(result["id"]),
                "external_event_id": result.get("external_event_id"),
                "created_at": result["created_at"],
            }

        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise

    async def get_event(self, event_id: UUID) -> Optional[Dict[str, Any]]:
        """Get event by ID"""
        try:
            query = "SELECT * FROM calendar_events WHERE id = $1"
            result = await sql_helper.execute(query, str(event_id), fetch="one")
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"Failed to get event {event_id}: {e}")
            raise

    async def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        user_id: str = DEFAULT_USER_ID,
    ) -> List[Dict[str, Any]]:
        """Get events with optional filters"""
        try:
            query = "SELECT * FROM calendar_events WHERE user_id = $1"
            values: List[Any] = [user_id]

            if start_date:
                query += f" AND start_time >= ${len(values) + 1}"
                values.append(start_date)

            if end_date:
                query += f" AND end_time <= ${len(values) + 1}"
                values.append(end_date)

            if status:
                query += f" AND status = ${len(values) + 1}"
                values.append(status)

            query += " ORDER BY start_time ASC"

            results = await sql_helper.execute(query, *values, fetch="all")
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            raise

    async def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[str] = None,
        user_id: str = DEFAULT_USER_ID,
    ) -> List[Dict[str, Any]]:
        """Get events within date range"""
        return await self.get_events(start_date, end_date, status, user_id)

    async def update_event(
        self, event_id: UUID, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update event"""
        try:
            set_clauses = []
            values: List[Any] = []

            allowed_fields = [
                "title",
                "description",
                "location",
                "start_time",
                "end_time",
                "status",
                "priority",
                "sync_status",
                "ai_summary",
                "travel_time_minutes",
                "requires_preparation",
                "preparation_minutes",
            ]

            for field, value in updates.items():
                if field in allowed_fields:
                    set_clauses.append(f"{field} = ${len(values) + 1}")
                    values.append(value)

            if set_clauses:
                values.append(str(event_id))
                query = f"""
                UPDATE calendar_events
                SET {", ".join(set_clauses)}, updated_at = NOW()
                WHERE id = ${len(values)}
                RETURNING *
                """
                result = await sql_helper.execute(query, *values, fetch="one")
                return dict(result) if result else None
            return None
        except Exception as e:
            logger.error(f"Failed to update event {event_id}: {e}")
            raise

    async def delete_event(self, event_id: UUID) -> bool:
        """Delete event"""
        try:
            query = "DELETE FROM calendar_events WHERE id = $1"
            result = await sql_helper.execute(query, str(event_id))
            return "DELETE 1" in result
        except Exception as e:
            logger.error(f"Failed to delete event {event_id}: {e}")
            raise

    async def detect_conflicts(
        self,
        start_time: datetime,
        end_time: datetime,
        exclude_event_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Detect overlapping events"""
        try:
            query = """
            SELECT id, title, start_time, end_time, location
            FROM calendar_events
            WHERE status != 'cancelled'
            AND (
                (start_time < $1 AND end_time > $1) OR
                (start_time >= $1 AND start_time < $2)
            )
            """
            values: List[Any] = [start_time, end_time]

            if exclude_event_id:
                query += f" AND id != ${len(values) + 1}"
                values.append(str(exclude_event_id))

            results = await sql_helper.execute(query, *values, fetch="all")
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to detect conflicts: {e}")
            raise

    async def get_free_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        buffer_minutes: int = 15,
    ) -> List[TimeSlot]:
        """Find available time slots"""
        try:
            events = await self.get_events_by_date_range(start_date, end_date)
            free_slots = []
            current_start = start_date

            for event in sorted(events, key=lambda e: e["start_time"]):
                gap_end = event["start_time"] - timedelta(minutes=buffer_minutes)
                if (gap_end - current_start).total_seconds() >= duration_minutes * 60:
                    free_slots.append(
                        TimeSlot(
                            start_time=current_start,
                            end_time=gap_end,
                            duration_minutes=duration_minutes,
                            confidence=0.9,
                        )
                    )
                current_start = event["end_time"] + timedelta(minutes=buffer_minutes)

            if (end_date - current_start).total_seconds() >= duration_minutes * 60:
                free_slots.append(
                    TimeSlot(
                        start_time=current_start,
                        end_time=end_date,
                        duration_minutes=duration_minutes,
                        confidence=0.8,
                    )
                )
            return free_slots
        except Exception as e:
            logger.error(f"Failed to get free slots: {e}")
            raise

    async def sync_from_apple_calendar(
        self, calendar_name: str = DEFAULT_CALENDAR, hours_back: int = 24
    ) -> SyncResult:
        """Placeholder for Apple Calendar sync"""
        calendars = list_calendars()
        return SyncResult(
            synced=0,
            updated=0,
            errors=0,
            conflicts=0,
            details={"message": "Sync not implemented", "calendars": calendars},
        )
