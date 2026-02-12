# src/services/calendar_service.py - Calendar service with AI integration
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from uuid import UUID
import logging

from src.repositories.calendar_repo import CalendarRepository
from src.services.llm_service import LlamaLLMService
from src.models.calendar import (
    CalendarEventCreate,
    CalendarEvent,
    SchedulePreferences,
    OptimizationSuggestion,
    SyncResult,
)
from src.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class CalendarService:
    """Calendar service with Apple Calendar integration and AI-powered features"""

    DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
    DEFAULT_CALENDAR = "PAT-cal"

    def __init__(
        self,
        calendar_repo: CalendarRepository,
        llm_service: LlamaLLMService,
        ws_manager: Optional[WebSocketManager] = None,
    ):
        self.calendar_repo = calendar_repo
        self.llm_service = llm_service
        self.ws_manager = ws_manager

    async def create_event(
        self, event_data: Dict[str, Any], check_conflicts: bool = True
    ) -> Dict[str, Any]:
        """
        Create new calendar event with optional conflict detection.
        """
        try:
            start_time = event_data.get("start_time")
            end_time = event_data.get("end_time")

            if check_conflicts and start_time and end_time:
                # Detect conflicts
                conflicts = await self.calendar_repo.detect_conflicts(
                    start_time=start_time, end_time=end_time
                )

                if conflicts:
                    logger.warning(f"Found {len(conflicts)} conflicts for new event")
                    event_data["status"] = "tentative"

            # Create event in database
            created = await self.calendar_repo.create_event(event_data)

            # Broadcast update
            if self.ws_manager:
                await self.ws_manager.broadcast_calendar_event(
                    {"type": "created", "event": created}
                )

            return created

        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise

    async def update_event(
        self, event_id: UUID, updates: Dict[str, Any], check_conflicts: bool = True
    ) -> Dict[str, Any]:
        """
        Update existing event with conflict checking.
        """
        try:
            if "start_time" in updates or "end_time" in updates and check_conflicts:
                event = await self.calendar_repo.get_event(event_id)
                if event:
                    new_start = updates.get("start_time", event.get("start_time"))
                    new_end = updates.get("end_time", event.get("end_time"))

                    if new_start and new_end:
                        conflicts = await self.calendar_repo.detect_conflicts(
                            start_time=new_start,
                            end_time=new_end,
                            exclude_event_id=event_id,
                        )
                        if conflicts:
                            logger.info(f"Update causes {len(conflicts)} conflicts")

            # Update in database
            updated = await self.calendar_repo.update_event(event_id, updates)

            if updated and self.ws_manager:
                await self.ws_manager.broadcast_calendar_event(
                    {"type": "updated", "event": updated}
                )

            return updated if updated else {}

        except Exception as e:
            logger.error(f"Failed to update event {event_id}: {e}")
            raise

    async def delete_event(self, event_id: UUID) -> bool:
        """Delete event"""
        try:
            success = await self.calendar_repo.delete_event(event_id)
            if success and self.ws_manager:
                await self.ws_manager.broadcast_calendar_event(
                    {"type": "deleted", "event_id": str(event_id)}
                )
            return success
        except Exception as e:
            logger.error(f"Failed to delete event {event_id}: {e}")
            raise

    async def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        user_id: str = DEFAULT_USER_ID,
    ) -> List[Dict[str, Any]]:
        """Get events"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=1)
        if not end_date:
            end_date = start_date + timedelta(days=30)

        return await self.calendar_repo.get_events_by_date_range(
            start_date, end_date, status, user_id
        )

    async def detect_conflicts(
        self, start_time: datetime, end_time: datetime, check_travel_time: bool = True
    ) -> List[Dict[str, Any]]:
        """Detect conflicts"""
        return await self.calendar_repo.detect_conflicts(start_time, end_time)

    async def reschedule_event(
        self, event_id: UUID, reason: str, suggest_times: int = 3
    ) -> List[Dict[str, Any]]:
        """Suggest optimal times for rescheduling using AI"""
        try:
            event = await self.calendar_repo.get_event(event_id)
            if not event:
                raise ValueError(f"Event {event_id} not found")

            duration_minutes = int(
                (event["end_time"] - event["start_time"]).total_seconds() / 60
            )

            # Get existing events for the week
            start_of_week = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_of_week = start_of_week + timedelta(days=7)
            existing_events = await self.calendar_repo.get_events_by_date_range(
                start_of_week, end_of_week
            )

            events_for_ai = [
                {
                    "title": e["title"],
                    "start": str(e["start_time"]),
                    "end": str(e["end_time"]),
                    "location": e.get("location"),
                }
                for e in existing_events
                if e.get("status") != "cancelled" and str(e["id"]) != str(event_id)
            ]

            preferences = {
                "work_start_time": "09:00",
                "work_end_time": "17:00",
                "break_start_time": "12:00",
                "break_end_time": "13:00",
                "preferred_meeting_days": [1, 2, 3, 4, 5],
                "peak_productivity_hours": [9, 10, 11, 14, 15, 16, 17],
                "min_time_between_meetings_minutes": 15,
            }

            suggestion = await self.llm_service.suggest_optimal_time(
                duration_minutes=duration_minutes,
                date=datetime.now().date().isoformat(),
                existing_events=events_for_ai,
                preferences=preferences,
            )

            suggested_time = suggestion.get("suggested_time")
            if not suggested_time:
                return []

            return [
                {
                    "start_time": suggested_time,
                    "end_time": self._add_minutes(suggested_time, duration_minutes),
                    "confidence": suggestion.get("confidence", 0.7),
                    "reasoning": suggestion.get("reasoning", ""),
                }
            ]

        except Exception as e:
            logger.error(f"Failed to reschedule event {event_id}: {e}")
            raise

    async def get_free_slots(
        self, start_date: datetime, end_date: datetime, duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """Get available time slots for meetings"""
        slots = await self.calendar_repo.get_free_slots(
            start_date=start_date, end_date=end_date, duration_minutes=duration_minutes
        )

        return [
            {
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "duration_minutes": slot.duration_minutes,
                "confidence": slot.confidence,
                "reason": getattr(slot, "reason", None),
            }
            for slot in slots
        ]

    async def optimize_schedule(
        self,
        target_date: Optional[date] = None,
        user_id: str = DEFAULT_USER_ID,
    ) -> OptimizationSuggestion:
        """AI-powered daily schedule optimization"""
        if not target_date:
            target_date = date.today() + timedelta(days=1)

        try:
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())

            current_events = await self.get_events(
                start_of_day, end_of_day, user_id=user_id
            )

            events_for_ai = [
                {
                    "title": e["title"],
                    "start": str(e["start_time"]),
                    "end": str(e["end_time"]),
                    "location": e.get("location"),
                    "priority": e.get("priority", 0),
                }
                for e in current_events
            ]

            preferences = SchedulePreferences()

            optimization = await self.llm_service.optimize_daily_schedule(
                date=target_date.isoformat(),
                current_schedule=events_for_ai,
                preferences=preferences.model_dump(),
            )

            suggestion = OptimizationSuggestion(
                date=target_date,
                current_events=[CalendarEvent(**e) for e in current_events],
                suggested_changes=optimization.get("suggested_changes", []),
                reasoning=optimization.get("reasoning", ""),
                confidence=optimization.get("confidence", 0.0),
                potential_conflicts_resolved=0,
            )

            if self.ws_manager:
                await self.ws_manager.broadcast_calendar_event(
                    {"type": "optimization_suggestion", "data": suggestion.model_dump()}
                )

            return suggestion

        except Exception as e:
            logger.error(f"Failed to optimize schedule: {e}")
            raise

    async def sync_from_apple(
        self, calendar_name: str = DEFAULT_CALENDAR, hours_back: int = 24
    ) -> SyncResult:
        """Sync events from Apple Calendar"""
        return await self.calendar_repo.sync_from_apple_calendar(
            calendar_name, hours_back
        )

    async def auto_reschedule_for_delayed_meeting(
        self, original_event_id: UUID, delay_minutes: int
    ) -> bool:
        """Proactively reschedule subsequent items when a meeting runs long"""
        try:
            event = await self.calendar_repo.get_event(original_event_id)
            if not event:
                return False

            original_end = event["end_time"]
            start_of_day = datetime.combine(original_end.date(), datetime.min.time())
            end_of_day = datetime.combine(
                original_end.date() + timedelta(days=1), datetime.max.time()
            )

            subsequent = await self.calendar_repo.get_events_by_date_range(
                start_of_day, end_of_day
            )

            affected_events = [
                e
                for e in subsequent
                if e["start_time"] > original_end and e.get("status") != "cancelled"
            ]

            rescheduled_count = 0
            for event_to_move in affected_events:
                new_start = event_to_move["start_time"] + timedelta(
                    minutes=delay_minutes
                )
                new_end = event_to_move["end_time"] + timedelta(minutes=delay_minutes)

                try:
                    await self.calendar_repo.update_event(
                        UUID(str(event_to_move["id"])),
                        {"start_time": new_start, "end_time": new_end},
                    )
                    rescheduled_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to reschedule event {event_to_move['id']}: {e}"
                    )

            logger.info(
                f"Auto-rescheduled {rescheduled_count} events due to {delay_minutes} minute delay"
            )
            return rescheduled_count > 0

        except Exception as e:
            logger.error(f"Failed to auto-reschedule: {e}")
            return False

    def _add_minutes(self, time_str: str, minutes: int) -> datetime:
        """Helper to add minutes to time string"""
        try:
            dt = datetime.fromisoformat(time_str)
            return dt + timedelta(minutes=minutes)
        except:
            return datetime.now()
