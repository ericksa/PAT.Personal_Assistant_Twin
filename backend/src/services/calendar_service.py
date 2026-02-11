from typing import List, Optional
from datetime import datetime, date, timedelta
from repositories.calendar_repo import CalendarRepository
from models.calendar import (
    CalendarEventCreate,
    Conflict,
    ConflictType,
    ConflictSeverity,
    TimeSlot,
    ScheduleOptimization,
)
from services.llm_service import LLMService
from utils.applescript.base_manager import AppleScriptManager


class CalendarService:
    """Service for calendar operations with AI optimization"""

    def __init__(self):
        from repositories.sql_helper import SQLHelper

        self.calendar_repo = CalendarRepository(SQLHelper())
        self.llm_service = LLMService()
        self.applescript = AppleScriptManager()

    async def create_event(
        self, event_data: dict, check_conflicts: bool = True
    ) -> dict:
        """Create a new calendar event"""
        event_create = CalendarEventCreate(**event_data)

        conflicts = []
        if check_conflicts:
            conflicts = await self.detect_conflicts(event_create)

        event = await self.calendar_repo.create_event(event_create)

        if conflicts:
            await self.calendar_repo.create_conflicts(conflicts)

        return {**event, "conflicts": conflicts}

    async def detect_conflicts(self, event: CalendarEventCreate) -> List[Conflict]:
        """Detect conflicts for a new event"""
        try:
            start_dt = (
                datetime.combine(
                    event.start_date,
                    datetime.strptime(event.start_time, "%H:%M").time(),
                )
                if event.start_time
                else datetime.combine(event.start_date, datetime.min.time())
            )
            end_dt = (
                datetime.combine(
                    event.end_date, datetime.strptime(event.end_time, "%H:%M").time()
                )
                if event.end_time
                else datetime.combine(event.end_date, datetime.min.time())
            )

            existing_events = await self.calendar_repo.list_events(
                user_id=event.user_id or "00000000-0000-0000-0000-000000000001",
                start_date=event.start_date - timedelta(days=1),
                end_date=event.end_date + timedelta(days=1),
            )

            conflicts = []

            for existing in existing_events:
                ex_start = existing.get("start_date")
                ex_start_time = existing.get("start_time")

                if ex_start:
                    try:
                        ex_start_dt = (
                            datetime.combine(
                                ex_start,
                                datetime.strptime(ex_start_time, "%H:%M").time(),
                            )
                            if ex_start_time
                            else datetime.combine(ex_start, datetime.min.time())
                        )
                        ex_end = existing.get("end_date") or ex_start
                        ex_end_time = existing.get("end_time")
                        ex_end_dt = (
                            datetime.combine(
                                ex_end, datetime.strptime(ex_end_time, "%H:%M").time()
                            )
                            if ex_end_time
                            else datetime.combine(ex_end, datetime.min.time())
                        )

                        if self._has_overlap(start_dt, end_dt, ex_start_dt, ex_end_dt):
                            overlap = min(end_dt, ex_end_dt) - max(
                                start_dt, ex_start_dt
                            )
                            overlap_minutes = int(overlap.total_seconds() / 60)

                            severity = ConflictSeverity.LOW
                            if overlap_minutes > 30:
                                severity = ConflictSeverity.CRITICAL
                            elif overlap_minutes > 15:
                                severity = ConflictSeverity.HIGH
                            elif overlap_minutes > 5:
                                severity = ConflictSeverity.MEDIUM

                            conflicts.append(
                                Conflict(
                                    event_id=existing.get("id", ""),
                                    conflict_event_id="",
                                    conflict_type=ConflictType.OVERLAP,
                                    severity=severity,
                                    overlap_minutes=overlap_minutes,
                                    message=f"Overlaps with '{existing.get('title', 'Unknown')}' for {overlap_minutes} minutes",
                                )
                            )
                    except Exception:
                        pass

            return conflicts

        except Exception as e:
            return []

    def _has_overlap(
        self, start1: datetime, end1: datetime, start2: datetime, end2: datetime
    ) -> bool:
        """Check if two time ranges overlap"""
        return max(start1, start2) < min(end1, end2)

    async def smart_reschedule(
        self, event_id: str, user_id: str, preferences: Optional[dict] = None
    ) -> ScheduleOptimization:
        """Suggest optimal rescheduling for an event"""
        event = await self.calendar_repo.get_event(event_id)
        if not event:
            return ScheduleOptimization(reason="Event not found")

        conflicts = await self.detect_conflicts(event)

        if not conflicts:
            return ScheduleOptimization(reason="No conflicts detected", alternatives=[])

        existing_events = await self.calendar_repo.list_events(
            user_id=user_id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        duration = event.get("duration", 60)
        title = event.get("title", "Event")
        description = event.get("description", "")

        optimization = await self.llm_service.optimize_schedule(
            existing_events, title, description, duration
        )

        suggested_time = (
            optimization.get("suggested_times", [{}])[0]
            if optimization.get("suggested_times")
            else None
        )

        return ScheduleOptimization(
            suggested_time=TimeSlot(**suggested_time) if suggested_time else None,
            conflicts=conflicts,
            reason=optimization.get("reason", "Optimized schedule"),
            alternatives=[
                TimeSlot(**t) for t in optimization.get("suggested_times", [])
            ],
        )

    async def optimize_schedule(
        self, user_id: str, start_date: date, end_date: date
    ) -> List[dict]:
        """Optimize schedule for date range"""
        user_id = user_id or "00000000-0000-0000-0000-000000000001"

        events = await self.calendar_repo.list_events(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        optimization = await self.llm_service.optimize_schedule(
            events, "Schedule Optimization", "Optimize full day schedule", 480
        )

        return optimization.get("suggested_times", [])

    async def auto_reschedule_for_delayed_meeting(
        self, event_id: str, delay_minutes: int = 30
    ) -> bool:
        """Proactively reschedule subsequent items when a meeting runs long"""
        event = await self.calendar_repo.get_event(event_id)
        if not event:
            return False

        if not event.get("end_time"):
            return False

        end_dt = datetime.combine(
            event["end_date"], datetime.strptime(event["end_time"], "%H:%M").time()
        )
        new_end = end_dt + timedelta(minutes=delay_minutes)

        subsequent_events = await self.calendar_repo.list_events(
            user_id=event.get("user_id", "00000000-0000-0000-0000-000000000001"),
            start_date=event["end_date"],
            end_date=event["end_date"],
        )

        rescheduled_count = 0

        for sub_event in subsequent_events:
            if sub_event.get("id") == event_id:
                continue

            sub_start = sub_event.get("start_time")
            if sub_start:
                try:
                    sub_start_dt = datetime.combine(
                        sub_event["start_date"],
                        datetime.strptime(sub_start, "%H:%M").time(),
                    )

                    if sub_start_dt >= end_dt:
                        new_start = sub_start_dt + timedelta(minutes=delay_minutes)

                        from models.calendar import CalendarEventUpdate

                        await self.calendar_repo.update_event(
                            sub_event["id"],
                            CalendarEventUpdate(start_time=new_start.strftime("%H:%M")),
                        )
                        rescheduled_count += 1
                except Exception:
                    pass

        return rescheduled_count > 0

    async def get_available_slots(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        min_duration_minutes: int = 15,
    ) -> List[TimeSlot]:
        """Find available time slots"""
        events = await self.calendar_repo.list_events(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        slots = []
        current_date = start_date
        work_start = datetime.strptime("09:00", "%H:%M").time()
        work_end = datetime.strptime("17:00", "%H:%M").time()

        while current_date <= end_date:
            day_slots = self._find_slots_for_day(
                events, current_date, work_start, work_end, min_duration_minutes
            )
            slots.extend(day_slots)
            current_date += timedelta(days=1)

        return slots

    def _find_slots_for_day(
        self,
        events: List[dict],
        day: date,
        work_start,
        work_end,
        min_duration_minutes: int,
    ) -> List[TimeSlot]:
        """Find available slots for a single day"""
        day_events = [e for e in events if e.get("start_date") == day]

        day_events.sort(key=lambda x: x.get("start_time", "00:00"))

        slots = []
        current_time = datetime.combine(day, work_start)
        day_end = datetime.combine(day, work_end)
        min_duration = timedelta(minutes=min_duration_minutes)

        for event in day_events:
            event_start = datetime.combine(
                day, datetime.strptime(event.get("start_time", "09:00"), "%H:%M").time()
            )

            if event_start - current_time >= min_duration:
                slots.append(
                    TimeSlot(
                        start_date=day,
                        start_time=current_time.strftime("%H:%M"),
                        end_date=day,
                        end_time=event_start.strftime("%H:%M"),
                        duration_minutes=int(
                            (event_start - current_time).total_seconds() / 60
                        ),
                    )
                )

            event_end = event.get("end_time") or event.get("start_time", "09:00")
            current_time = max(
                current_time,
                datetime.combine(day, datetime.strptime(event_end, "%H:%M").time()),
            )

        if day_end - current_time >= min_duration:
            slots.append(
                TimeSlot(
                    start_date=day,
                    start_time=current_time.strftime("%H:%M"),
                    end_date=day,
                    end_time=day_end.strftime("%H:%M"),
                    duration_minutes=int((day_end - current_time).total_seconds() / 60),
                )
            )

        return slots

    async def sync_from_apple(
        self,
        calendar_name: str = "Adam",
        user_id: str = "00000000-0000-0000-0000-000000000001",
        hours_back: int = 72,
    ):
        """Sync events from Apple Calendar"""
        from models.calendar import SyncResult

        result = SyncResult(
            synced=0,
            updated=0,
            errors=0,
            message="Apple Calendar sync not yet fully implemented",
            details=[],
        )

        try:
            script = f"""
            tell application "Calendar"
                tell calendar "{calendar_name}"
                    set eventList to every event whose start date is greater than (current date) - ({hours_back} * hours)
                    set idList to {{}}
                    repeat with currentEvent in eventList
                        set end of idList to uid of currentEvent
                    end repeat
                    return idList
                end tell
            end tell
            """

            apple_ids = await self.applescript.run_applescript(script)

            for apple_id in apple_ids or []:
                existing = await self.calendar_repo.get_event_by_apple_id(
                    str(apple_id), user_id
                )

                if existing:
                    result.updated += 1
                else:
                    await self.sync_single_event(user_id, str(apple_id))
                    result.synced += 1

            result.message = (
                f"Synced {result.synced} new events, updated {result.updated}"
            )

        except Exception as e:
            result.errors += 1
            result.message = f"Sync error: {str(e)}"

        return result

    async def sync_single_event(self, user_id: str, apple_id: str):
        """Sync a single event from Apple Calendar"""
        script = f'''
        tell application "Calendar"
            set currentEvent to first event whose uid is "{apple_id}"
            set eventSummary to summary of currentEvent
            set eventStart to start date of currentEvent
            set eventEnd to end date of currentEvent
            set eventLocation to location of currentEvent if location of currentEvent is not missing else "N/A"
            set eventNotes to description of currentEvent if description of currentEvent is not missing else ""
            
            return {{"title": eventSummary, "start": eventStart, "end": eventEnd, "location": eventLocation, "notes": eventNotes}}
        end tell
        '''

        event_data = await self.applescript.run_applescript(script)

        if event_data:
            event_create = CalendarEventCreate(
                user_id=user_id,
                apple_id=apple_id,
                title=event_data.get("title", "Untitled"),
                start_date=event_data.get("start", date.today()),
                end_date=event_data.get("end", date.today()),
                location=event_data.get("location"),
                notes=event_data.get("notes"),
                source="apple_calendar",
            )

            await self.calendar_repo.create_event(event_create)
