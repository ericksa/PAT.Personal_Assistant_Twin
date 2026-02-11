from typing import List, Optional
from datetime import datetime, date, timedelta
from repositories.base import BaseRepository
from models.calendar import CalendarEventCreate, Conflict
import logging

logger = logging.getLogger(__name__)


class CalendarRepository(BaseRepository):
    """Repository for calendar operations in PostgreSQL"""

    async def create_event(self, event: CalendarEventCreate) -> dict:
        """Create a new calendar event"""
        query = """
            INSERT INTO calendar_events (
                user_id, title, description, start_date, start_time,
                end_date, end_time, location, event_type, is_all_day,
                is_recurring, recurrence, source, notes, apple_event_id, calendar_name
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            RETURNING *
        """
        return await self.fetchrow(
            query,
            event.user_id or "00000000-0000-0000-0000-000000000001",
            event.title,
            event.description,
            event.start_date,
            event.start_time,
            event.end_date,
            event.end_time,
            event.location,
            event.event_type or "meeting",
            event.is_all_day,
            event.is_recurring,
            event.recurrence,
            event.source or "manual",
            event.notes,
            event.apple_event_id,
            event.calendar_name or "Adam",
        )

    async def get_event(self, event_id: str) -> Optional[dict]:
        """Get an event by ID"""
        query = "SELECT * FROM calendar_events WHERE id = $1"
        return await self.fetchrow(query, event_id)

    async def get_event_by_apple_id(
        self, apple_id: str, user_id: str
    ) -> Optional[dict]:
        """Get an event by Apple Calendar ID"""
        query = (
            "SELECT * FROM calendar_events WHERE apple_event_id = $1 AND user_id = $2"
        )
        return await self.fetchrow(query, apple_id, user_id)

    async def list_events(
        self,
        user_id: str = "00000000-0000-0000-0000-000000000001",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """List events with optional filters"""
        conditions = ["user_id = $1"]
        params = [user_id]
        param_idx = 2

        if start_date:
            conditions.append(f"start_date >= ${param_idx}")
            params.append(str(start_date))
            param_idx += 1

        if end_date:
            conditions.append(f"start_date <= ${param_idx}")
            params.append(str(end_date))
            param_idx += 1

        if event_type:
            conditions.append(f"event_type = ${param_idx}")
            params.append(event_type)
            param_idx += 1

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT * FROM calendar_events
            WHERE {where_clause}
            ORDER BY start_date, start_time
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([str(limit), str(offset)])

        return await self.fetch(query, *params)

    async def update_event(self, event_id: str, event_data: dict) -> Optional[dict]:
        """Update a calendar event"""
        updates = []
        params = []
        param_idx = 1

        for key, value in event_data.items():
            if value is not None:
                updates.append(f"{key} = ${param_idx}")
                params.append(value)
                param_idx += 1

        if not updates:
            return await self.get_event(event_id)

        updates.append("updated_at = NOW()")
        params.append(event_id)

        query = f"""
            UPDATE calendar_events
            SET {", ".join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        """

        return await self.fetchrow(query, *params)

    async def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        query = "DELETE FROM calendar_events WHERE id = $1"
        result = await self.execute(query, event_id)
        return result == "DELETE 1"

    async def create_conflicts(self, conflicts: List[Conflict]):
        """Create conflict records"""
        for conflict in conflicts:
            query = """
                INSERT INTO calendar_conflicts (
                    event_id, conflict_event_id, conflict_type,
                    severity, overlap_minutes, message
                )
                VALUES ($1, $2, $3, $4, $5, $6)
            """
            await self.execute(
                query,
                conflict.event_id,
                conflict.conflict_event_id,
                conflict.conflict_type.value,
                conflict.severity.value,
                conflict.overlap_minutes,
                conflict.message,
            )

    async def get_conflicts(self, event_id: str) -> List[dict]:
        """Get conflicts for an event"""
        query = """
            SELECT * FROM calendar_conflicts
            WHERE event_id = $1 OR conflict_event_id = $1
            ORDER BY severity
        """
        return await self.fetch(query, event_id)

    async def update_schedule_preferences(
        self, user_id: str, preferences: dict
    ) -> dict:
        """Update user schedule preferences"""
        query = """
            INSERT INTO schedule_preferences (
                user_id, work_start_time, work_end_time, buffer_minutes,
                max_back_to_back, break_min_duration, max_daily_meetings,
                timezone, prefer_morning, prefer_afternoon, avoid_friday_afternoon
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (user_id) DO UPDATE SET
                work_start_time = EXCLUDED.work_start_time,
                work_end_time = EXCLUDED.work_end_time,
                buffer_minutes = EXCLUDED.buffer_minutes,
                max_back_to_back = EXCLUDED.max_back_to_back,
                break_min_duration = EXCLUDED.break_min_duration,
                max_daily_meetings = EXCLUDED.max_daily_meetings,
                timezone = EXCLUDED.timezone,
                prefer_morning = EXCLUDED.prefer_morning,
                prefer_afternoon = EXCLUDED.prefer_afternoon,
                avoid_friday_afternoon = EXCLUDED.avoid_friday_afternoon,
                updated_at = NOW()
            RETURNING *
        """
        return await self.fetchrow(
            query,
            user_id,
            preferences.get("work_start_time", "09:00"),
            preferences.get("work_end_time", "17:00"),
            preferences.get("buffer_minutes", 15),
            preferences.get("max_back_to_back", 3),
            preferences.get("break_min_duration", 15),
            preferences.get("max_daily_meetings", 8),
            preferences.get("timezone", "America/New_York"),
            preferences.get("prefer_morning", False),
            preferences.get("prefer_afternoon", False),
            preferences.get("avoid_friday_afternoon", True),
        )
