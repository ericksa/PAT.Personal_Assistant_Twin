from typing import List, Optional
from datetime import datetime
from src.repositories.task_repo import TaskRepository
from src.repositories.calendar_repo import CalendarRepository
from src.models.task import TaskCreate, TaskUpdate
from src.models.calendar import CalendarEventCreate
from src.services.llm_service import LLMService
from src.utils.applescript.base_manager import AppleScriptManager


class TaskService:
    """Service for task operations with AI processing"""

    def __init__(
        self,
        task_repo: TaskRepository,
        calendar_repo: CalendarRepository,
        llm_service: LLMService,
        applescript_manager: AppleScriptManager,
    ):
        self.task_repo = task_repo
        self.calendar_repo = calendar_repo
        self.llm_service = llm_service
        self.applescript = applescript_manager

    async def sync_from_reminders(self, user_id: str, limit: int = 100) -> dict:
        """Sync tasks from Apple Reminders to database"""
        result = {"synced": 0, "errors": 0, "message": "Sync not yet implemented"}

        try:
            script = """
            tell application "Reminders"
                set allLists to name of every list
                set idList to {}
                repeat with currentList in allLists
                    try
                        set listRef to list currentList
                        set allReminders to every reminder of listRef
                        repeat with currentReminder in allReminders
                            set id of currentReminder to id of currentReminder
                            set end of idList to id of currentReminder
                        end repeat
                    end try
                end repeat
                return idList
            end tell
            """

            apple_ids = await self.applescript.run_applescript(script, limit)

            for apple_id in (apple_ids or [])[:limit]:
                if await self.task_repo.get_task_by_apple_id(str(apple_id), user_id):
                    continue

                await self.sync_single_reminder(user_id, str(apple_id))
                result["synced"] += 1

            result["message"] = (
                f"Synced {result['synced']} new reminders from Reminders"
            )

        except Exception as e:
            result["errors"] += 1
            result["message"] = f"Sync error: {str(e)}"

        return result

    async def sync_single_reminder(self, user_id: str, apple_id: str):
        """Sync a single reminder from Apple Reminders"""
        script = f"""
        tell application "Reminders"
            set reminderRef to first reminder whose id is "{apple_id}"
            set reminderName to name of reminderRef
            set reminderNotes to notes of reminderRef
            set reminderDue to due date of reminderRef
            set reminderCompleted to completed of reminderRef as string
            set reminderPriority to priority of reminderRef as integer
            set reminderFlagged to flagged of reminderRef as string
            
            return {{"name": reminderName, "notes": reminderNotes, "due": reminderDue, "completed": reminderCompleted, "priority": reminderPriority, "flagged": reminderFlagged}}
        end tell
        """

        reminder_data = await self.applescript.run_applescript(script)

        if reminder_data:
            priority_map = {0: "low", 1: "medium", 5: "high", 9: "urgent"}
            priority = priority_map.get(reminder_data.get("priority", 1), "medium")

            task_create = TaskCreate(
                user_id=user_id,
                apple_id=apple_id,
                title=reminder_data.get("name", ""),
                description="",
                notes=reminder_data.get("notes"),
                status="completed"
                if reminder_data.get("completed") == "true"
                else "pending",
                priority=priority,
                is_flagged=reminder_data.get("flagged") == "true",
                due_date=reminder_data.get("due"),
                tags=["reminders"],
            )

            await self.task_repo.create_task(task_create)

    async def suggest_priorities(self, user_id: str) -> dict:
        """AI-based task priority suggestions"""
        tasks = await self.task_repo.list_tasks(
            user_id=user_id, status="pending", limit=50
        )

        suggestions = {
            "reordered_tasks": [],
            "urgent_tasks": [],
            "high_priority": [],
            "can_defer": [],
        }

        for task in tasks:
            title = task.get("title", "")
            description = task.get("description", "")
            due_date = task.get("due_date")

            suggestion = await self.llm_service.suggest_task_priority(
                title, description, due_date
            )

            if suggestion["priority"] != task.get("priority"):
                suggestions["reordered_tasks"].append(
                    {
                        "task_id": task["id"],
                        "title": title,
                        "current_priority": task.get("priority"),
                        "suggested_priority": suggestion["priority"],
                        "reason": suggestion["reason"],
                    }
                )

            await self.task_repo.update_task(
                task["id"], TaskUpdate(user_id=user_id, priority=suggestion["priority"])
            )

            if suggestion["priority"] in ["urgent", "high"]:
                key = (
                    "urgent_tasks"
                    if suggestion["priority"] == "urgent"
                    else "high_priority"
                )
                suggestions[key].append(
                    {"task_id": task["id"], "title": title, "due_date": due_date}
                )

        return suggestions

    async def suggest_schedule_time(self, task_id: str, user_id: str) -> dict:
        """Suggest optimal time for task execution based on calendar"""
        task = await self.task_repo.get_task(task_id)
        if not task:
            return {"error": "Task not found"}

        title = task.get("title", "")
        description = task.get("description", "")
        estimated_duration = task.get("estimated_duration", 30)

        schedule = await self.llm_service.optimize_schedule(
            [], title, description, estimated_duration
        )

        if schedule["suggested_times"]:
            suggested_time = schedule["suggested_times"][0]

            from src.models.calendar import CalendarEventCreate

            event_create = CalendarEventCreate(
                user_id=user_id,
                title=f"Task: {title}",
                description=description,
                start_date=suggested_time["date"],
                start_time=suggested_time["time"],
                end_date=suggested_time["date"],
                event_type="task",
                source="ai_suggestion",
                notes=f"AI-suggested time for task execution",
            )

            event = await self.calendar_repo.create_event(event_create)

            return {
                "task_id": task_id,
                "suggested_time": suggested_time,
                "reason": schedule.get("reason", ""),
                "calendar_event": event,
            }

        return {"error": "No suitable time found"}

    async def batch_create_tasks(
        self, user_id: str, task_descriptions: List[str]
    ) -> List[dict]:
        """Batch create tasks from descriptions with AI parsing"""
        created_tasks = []

        for description in task_descriptions:
            parsed = await self.llm_service.parse_task_from_text(description)

            task_create = TaskCreate(
                user_id=user_id,
                title=parsed["title"],
                description=parsed.get("description", ""),
                priority=parsed.get("priority", "medium"),
                tags=parsed.get("tags", []),
                notes=f"Parsed from: {description}",
            )

            if parsed.get("due_date"):
                from datetime import datetime

                try:
                    task_create.due_date = datetime.fromisoformat(parsed["due_date"])
                except:
                    pass

            task = await self.task_repo.create_task(task_create)
            created_tasks.append(task)

        return created_tasks

    async def get_focus_tasks(self, user_id: str, limit: int = 5) -> List[dict]:
        """Get top focus tasks for current session"""
        overdue = await self.task_repo.get_overdue_tasks(user_id)
        today = await self.task_repo.get_today_tasks(user_id)

        priority_order = {"urgent": 1, "high": 2, "medium": 3, "low": 4}

        focus_tasks = []
        for task in overdue[:2]:
            task.setdefault("priority_score", 0)
            focus_tasks.append(task)

        for task in today:
            if len(focus_tasks) >= limit:
                break
            if task.get("title") in [t.get("title") for t in focus_tasks]:
                continue
            focus_tasks.append(task)

        focus_tasks.sort(
            key=lambda t: (
                priority_order.get(t.get("priority", "medium"), 5),
                t.get("due_date") or datetime.max,
            )
        )

        return focus_tasks[:limit]

    async def complete_task(
        self, task_id: str, user_id: str, notes: Optional[str] = None
    ) -> dict:
        """Mark a task as completed"""
        task = await self.task_repo.get_task(task_id)
        if not task:
            return {"error": "Task not found"}

        updated = await self.task_repo.update_task(
            task_id,
            TaskUpdate(
                user_id=user_id, status="completed", notes=notes or task.get("notes")
            ),
        )

        return {"task_id": task_id, "status": "completed", "task": updated}

    async def smart_task_completion_suggestions(self, user_id: str) -> dict:
        """AI-based suggestions for task completion strategies"""
        pending_tasks = await self.task_repo.list_tasks(
            user_id=user_id, status="pending", limit=20
        )

        suggestions = {
            "quick_wins": [],
            "blocking_tasks": [],
            "related_tasks": {},
            "suggested_order": [],
        }

        for task in pending_tasks:
            estimated_duration = task.get("estimated_duration", 30)

            if estimated_duration <= 15:
                suggestions["quick_wins"].append(
                    {
                        "task_id": task["id"],
                        "title": task.get("title"),
                        "duration": estimated_duration,
                    }
                )

        suggestions["suggested_order"] = (
            suggestions["quick_wins"]
            + [
                {
                    "task_id": t["id"],
                    "title": t.get("title"),
                    "priority": t.get("priority"),
                }
                for t in pending_tasks
                if t.get("estimated_duration", 30) > 15
            ][:5]
        )

        return suggestions
