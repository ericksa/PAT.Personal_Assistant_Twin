# src/repositories/calendar_repo.py - Calendar repository with AppleScript integration
from typing import List, Dict, Any, Optional
from datetime import datetime, date
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

        Args:
            event_data: Event data dictionary

        Returns:
            Created event with ID
        """
        try:
            # Insert into database
            query = """
            INSERT INTO calendar_events (
                user_id, title, description, location, 
                start_time, end_time, all_day, recurrence_rule,
                timezone, calendar_name, event_type, status,
                priority, travel_time_minutes, requires_preparation,
                preparation_minutes, sync_status, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, NOW(), NOW())
            RETURNING id, external_event_id, created_at
            """

            values = (
                event_data.get("user_id", self.DEFAULT_USER_ID),
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
            query = """
            SELECT * FROM calendar_events 
            WHERE id = $1
            """

            result = await sql_helper.execute(query, str(event_id), fetch="one")

            if result:
                return self._row_to_dict(result)
            return None

        except Exception as e:
            logger.error(f"Failed to get event {event_id}: {e}")
            raise

    async def get_events_by_date_range(
        self, start_date: datetime, end_date: datetime, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get events within date range.

        Args:
            start_date: Start of range
            end_date: End of range
            status: Optional status filter

        Returns:
            List of events
        """
        try:
            query = """
            SELECT * FROM calendar_events
            WHERE start_time >= $1 AND start_time <= $2
            """
            values = [start_date, end_date]

            if status:
                query += " AND status = $3"
                values.append(status)

            query += " ORDER BY start_time ASC"

            results = await sql_helper.execute(query, *values, fetch="all")
            return [self._row_to_dict(row) for row in results]

        except Exception as e:
            logger.error(f"Failed to get events by date range: {e}")
            raise

    async def update_event(
        self, event_id: UUID, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update event"""
        try:
            # Build SET clause and values
            set_clauses = []
            values = []

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
                    set_clauses.append(f"{field} = ${len(set_clauses) + 1}")
                    values.append(value)

            if set_clauses:
                set_clauses.append("updated_at = NOW()")
                values.append(event_id)

                query = f"""
                UPDATE calendar_events
                SET {", ".join(set_clauses)}
                WHERE id = ${len(values)}
                RETURNING *
                """

                result = await sql_helper.execute(query, *values, fetch="one")
                return self._row_to_dict(result) if result else None

            return None

        except Exception as e:
            logger.error(f"Failed to update event {event_id}: {e}")
            raise

    async def delete_event(self, event_id: UUID) -> bool:
        """Delete event"""
        try:
            query = "DELETE FROM calendar_events WHERE id = $1"
            result = await sql_helper.execute(query, str(event_id))
            return f"DELETE 1" in result
        except Exception as e:
            logger.error(f"Failed to delete event {event_id}: {e}")
            raise

    async def detect_conflicts(
        self, start_time: datetime, end_time: datetime, exclude_event_id: UUID = None
    ) -> List[Dict[str, Any]]:
        """
        Detect overlapping events.

        Args:
            start_time: Start time to check
            end_time: End time to check
            exclude_event_id: Event ID to exclude from conflict check

        Returns:
            List of conflicting events
        """
        try:
            query = """
            SELECT id, title, start_time, end_time, location
            FROM calendar_events
            WHERE status != 'cancelled'
            AND (
                (start_time < $1 AND end_time > $2) OR
                (start_time >= $2 AND start_time < $3)
            )
            """
            values = [start_time, end_time, end_time]

            if exclude_event_id:
                query += " AND id != $4"
                values.append(str(exclude_event_id))

            results = await sql_helper.execute(query, *values, fetch="all")
            return [self._row_to_dict(row) for row in results]

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
        """
        Find available time slots.

        Args:
            start_date: Start search date/time
            end_date: End search date/time
            duration_minutes: Required duration
            buffer_minutes: Buffer between events

        Returns:
            List of available time slots
        """
        try:
            # Get all events in range
            events = await self.get_events_by_date_range(start_date, end_date)

            # Calculate gaps
            free_slots = []
            current_start = start_date

            for event in sorted(events, key=lambda e: e["start_time"]):
                # Check if there's a gap before this event
                gap_end = datetime.fromisoformat(event["start_time"]) - buffer_minutes

                if (gap_end - current_start).total_seconds() >= duration_minutes * 60:
                    free_slots.append(
                        TimeSlot(
                            start_time=current_start,
                            end_time=gap_end,
                            duration_minutes=duration_minutes,
                            confidence=0.9,  # High confidence from actual events
                        )
                    )

                # Move to after this event
                current_start = (
                    datetime.fromisoformat(event["end_time"]) + buffer_minutes
                )

            # Check if there's a gap after last event
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

    async def create_conflict(
        self,
        event1_id: UUID,
        event2_id: UUID,
        conflict_type: str,
        severity: str,
        ai_suggested_resolution: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create conflict record"""
        try:
            query = """
            INSERT INTO calendar_conflicts (
                event1_id, event2_id, conflict_type, severity,
                ai_suggested_resolution, detected_at, resolved
            ) VALUES ($1, $2, $3, $4, $5, NOW(), false)
            RETURNING id
            """

            result = await sql_helper.execute(
                query,
                str(event1_id),
                str(event2_id),
                conflict_type,
                severity,
                ai_suggested_resolution,
                fetch="one",
            )

            return {"conflict_id": result["id"]}

        except Exception as e:
            logger.error(f"Failed to create conflict: {e}")
            raise

    async def sync_from_apple_calendar(
        self, calendar_name: str = DEFAULT_CALENDAR, hours_back: int = 24
    ) -> SyncResult:
        """
        Sync events from Apple Calendar.

        This is a placeholder for now since AppleScript event reading is complex.
        In production, this would:
        1. Execute AppleScript to get events from Apple Calendar
        2. Parse results and convert to internal format
        3. Upsert into database
        4. Return sync results

        Returns:
            SyncResult with counts
        """
        calendars = list_calendars()
        logger.info(f"Apple Calendar sync from: {calendar_name}")
        logger.info(f"Available calendars: {calendars}")

        # TODO: Implement actual AppleScript event reading
        # For now, return success with no changes
        return SyncResult(
            synced=0,
            updated=0,
            errors=0,
            conflicts=0,
            details={
                "message": "AppleScript sync not yet implemented",
                "calendars_found": len(calendars),
            },
        )

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dict"""
        return dict(row) if row else {}
