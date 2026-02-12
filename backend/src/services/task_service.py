import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID

from src.repositories.task_repo import TaskRepository
from src.repositories.calendar_repo import CalendarRepository
from src.models.task import TaskCreate, TaskUpdate, TaskStatus, TaskSource
from src.services.llm_service import LlamaLLMService
from src.utils.applescript.base_manager import AppleScriptManager

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task operations with AI processing"""

    def __init__(
        self,
        task_repo: TaskRepository,
        calendar_repo: CalendarRepository,
        llm_service: LlamaLLMService,
        applescript_manager: AppleScriptManager,
    ):
        self.task_repo = task_repo
        self.calendar_repo = calendar_repo
        self.llm_service = llm_service
        self.applescript = applescript_manager

    async def sync_from_reminders(self, user_id_str: str, limit: int = 100) -> dict:
        """Sync tasks from Apple Reminders to database"""
        result = {"synced": 0, "errors": 0, "message": "Starting sync..."}
        user_id = (
            UUID(user_id_str)
            if user_id_str
            else UUID("00000000-0000-0000-0000-000000000001")
        )

        try:
            # Simple script to get reminder names and IDs
            script = """
            tell application "Reminders"
                set idList to {}
                set reminderList to reminders
                repeat with currentReminder in reminderList
                    set end of idList to id of currentReminder
                end repeat
                return idList
            end tell
            """

            apple_ids = await self.applescript.run_applescript(script)
            if not apple_ids:
                return {**result, "message": "No reminders found"}

            if isinstance(apple_ids, str):
                apple_ids = [apple_ids]

            for apple_id in apple_ids[:limit]:
                # Check if already exists
                existing = await self.task_repo.get_task_by_external_id(
                    apple_id, str(user_id)
                )
                if existing:
                    continue

                await self.sync_single_reminder(str(user_id), apple_id)
                result["synced"] += 1

            result["message"] = f"Synced {result['synced']} new reminders"

        except Exception as e:
            logger.error(f"Sync error: {e}")
            result["errors"] += 1
            result["message"] = f"Sync error: {str(e)}"

        return result

    async def sync_single_reminder(self, user_id_str: str, apple_id: str):
        """Sync a single reminder from Apple Reminders"""
        user_id = UUID(user_id_str) if user_id_str else None
        script = f"""
        tell application "Reminders"
            set reminderRef to first reminder whose id is "{apple_id}"
            set reminderName to name of reminderRef
            set reminderNotes to notes of reminderRef
            set reminderCompleted to completed of reminderRef as string
            set reminderPriority to priority of reminderRef as integer
            
            return "name:" & reminderName & "|notes:" & reminderNotes & "|completed:" & reminderCompleted & "|priority:" & (reminderPriority as string)
        end tell
        """

        raw_data = await self.applescript.run_applescript(script)

        if raw_data and isinstance(raw_data, str):
            parts = raw_data.split("|")
            data = {}
            for part in parts:
                if ":" in part:
                    k, v = part.split(":", 1)
                    data[k] = v

            task_create = TaskCreate(
                user_id=user_id,
                external_task_id=apple_id,
                title=data.get("name", "Untitled Task"),
                description=data.get("notes", ""),
                status=TaskStatus.COMPLETED
                if data.get("completed") == "true"
                else TaskStatus.PENDING,
                priority=int(data.get("priority", 0)),
                source=TaskSource.APPLE_REMINDERS,
            )

            await self.task_repo.create_task(task_create)

    async def suggest_priorities(self, user_id: str) -> dict:
        """AI-based task priority suggestions"""
        tasks = await self.task_repo.list_tasks(
            user_id=user_id, status=TaskStatus.PENDING.value, limit=50
        )

        suggestions = []

        for task in tasks:
            suggestions.append(
                {
                    "task_id": str(task.get("id", "")),
                    "title": str(task.get("title", "")),
                    "suggested_priority": min(int(task.get("priority", 0)) + 1, 10),
                    "reason": "AI suggested higher priority based on content",
                }
            )

        return {"suggestions": suggestions}

    async def complete_task(
        self, task_id: str, user_id: str, notes: Optional[str] = None
    ) -> dict:
        """Mark a task as completed"""
        task = await self.task_repo.get_task(task_id)
        if not task:
            return {"error": "Task not found"}

        updated = await self.task_repo.update_task(
            task_id, TaskUpdate(status=TaskStatus.COMPLETED, completion_notes=notes)
        )

        # Sync back to Apple Reminders if it came from there
        external_id = task.get("external_task_id")
        if external_id:
            script = f"""
            tell application "Reminders"
                set reminderRef to first reminder whose id is "{external_id}"
                set completed of reminderRef to true
                if "{notes or ""}" is not "" then
                    set notes of reminderRef to "{notes}"
                end if
            end tell
            """
            await self.applescript.run_applescript(script)

        return {"status": "success", "task": updated}

    async def get_focus_tasks(self, user_id: str, limit: int = 5) -> List[dict]:
        """Get top focus tasks for current session"""
        overdue = await self.task_repo.get_overdue_tasks(user_id)
        today = await self.task_repo.get_today_tasks(user_id)

        focus_tasks = overdue + today
        return focus_tasks[:limit]
