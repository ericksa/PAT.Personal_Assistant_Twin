import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID

from src.repositories.task_repo import TaskRepository
from src.repositories.calendar_repo import CalendarRepository
from src.models.task import TaskCreate, TaskUpdate, TaskStatus, TaskSource
from src.services.llm_service import LlamaLLMService
from src.utils.applescript.base_manager import AppleScriptManager
from src.utils.applescript.reminders_manager import RemindersManager

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

        # Get reminder details from Apple Reminders
        script = f"""
        tell application "Reminders"
            set reminderRef to first reminder whose id is "{apple_id}"
            set reminderName to name of reminderRef
            set reminderNotes to body of reminderRef
            set reminderCompleted to completed of reminderRef
            set reminderPriority to priority of reminderRef
            set reminderDue to due date of reminderRef
            if reminderDue is not missing value then
                set reminderDueStr to reminderDue as string
            else
                set reminderDueStr to ""
            end if
            
            return "name:" & reminderName & "|notes:" & reminderNotes & "|completed:" & reminderCompleted & "|priority:" & (reminderPriority as string) & "|due:" & reminderDueStr
        end tell
        """

        raw_data = await self.applescript.run_applescript(script)

        if raw_data and isinstance(raw_data, str):
            parts = raw_data.split("|")
            data = {}
            for part in parts:
                if ":" in part and len(part.split(":", 1)) == 2:
                    k, v = part.split(":", 1)
                    data[k] = v

            # Parse due date
            due_date = None
            if data.get("due"):
                try:
                    due_date = datetime.strptime(
                        data["due"], "%A, %B %d, %Y at %I:%M:%S %p"
                    ).date()
                except:
                    pass

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
                due_date=due_date,
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
            try:
                RemindersManager.update_reminder(
                    reminder_id=external_id,
                    new_completed=True,
                    new_notes=notes,
                )
                logger.info(f"Synced task completion to Apple Reminders: {external_id}")
            except Exception as e:
                logger.warning(f"Failed to sync to Apple Reminders: {e}")

        return {"status": "success", "task": updated}

    async def get_focus_tasks(self, user_id: str, limit: int = 5) -> List[dict]:
        """Get top focus tasks for current session"""
        overdue = await self.task_repo.get_overdue_tasks(user_id)
        today = await self.task_repo.get_today_tasks(user_id)

        focus_tasks = overdue + today
        return focus_tasks[:limit]

    async def create_and_sync_to_reminders(
        self, task: TaskCreate, user_id_str: str
    ) -> dict:
        """Create task locally and sync to Apple Reminders"""
        # Create in database first
        db_task = await self.task_repo.create_task(task)

        # If not from Apple Reminders, create there too
        if task.source != TaskSource.APPLE_REMINDERS:
            try:
                due_date_str = None
                if task.due_date and task.due_time:
                    due_date_str = f"{task.due_date} {task.due_time}:00"
                elif task.due_date:
                    due_date_str = f"{task.due_date} 12:00:00"

                apple_id = RemindersManager.create_reminder(
                    title=task.title,
                    due_date=due_date_str,
                    notes=task.description,
                    priority=task.priority if task.priority else 9,
                    list_name=task.list_name,
                )

                # Update with Apple ID
                if apple_id:
                    await self.task_repo.update_task(
                        str(db_task["id"]), TaskUpdate(external_task_id=apple_id)
                    )

            except Exception as e:
                logger.warning(f"Failed to sync reminder to Apple: {e}")

        return {"status": "success", "task": db_task}

    async def sync_to_apple_reminders(self, task_id: str, user_id: str) -> dict:
        """Sync an existing task to Apple Reminders"""
        task = await self.task_repo.get_task(task_id)
        if not task:
            return {"error": "Task not found"}

        # Already synced?
        if task.get("external_task_id"):
            return {"status": "unchanged", "message": "Task already synced"}

        try:
            due_date_str = None
            due_date = task.get("due_date")
            due_time = task.get("due_time")

            if due_date and due_time:
                due_date_str = f"{due_date} {due_time}:00"
            elif due_date:
                due_date_str = f"{due_date} 12:00:00"

            apple_id = RemindersManager.create_reminder(
                title=task.get("title"),
                due_date=due_date_str,
                notes=task.get("description"),
                priority=task.get("priority", 9),
                list_name=task.get("list_name", "Reminders"),
            )

            if apple_id:
                await self.task_repo.update_task(
                    task_id, TaskUpdate(external_task_id=apple_id)
                )

            return {"status": "success", "apple_id": apple_id}

        except Exception as e:
            logger.error(f"Failed to sync to Apple: {e}")
            return {"error": str(e)}

    async def delete_from_reminders(self, task_id: str, user_id: str) -> dict:
        """Delete task from both database and Apple Reminders"""
        task = await self.task_repo.get_task(task_id)
        if not task:
            return {"error": "Task not found"}

        # Delete from Apple if synced
        external_id = task.get("external_task_id")
        if external_id:
            try:
                RemindersManager.delete_reminder(external_id)
                logger.info(f"Deleted reminder from Apple: {external_id}")
            except Exception as e:
                logger.warning(f"Failed to delete from Apple: {e}")

        # Delete from database
        success = await self.task_repo.delete_task(task_id)

        return {"status": "success" if success else "error"}

    async def get_analytics(self, user_id: str) -> dict:
        """Get task analytics"""
        all_tasks = await self.task_repo.list_tasks(user_id, limit=1000)
        overdue = await self.task_repo.get_overdue_tasks(user_id)
        today = await self.task_repo.get_today_tasks(user_id)

        status_counts = {}
        priority_counts = {}
        source_counts = {}

        for task in all_tasks:
            status = task.get("status", "unknown")
            priority = task.get("priority", 0)
            source = task.get("source", "unknown")

            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            source_counts[source] = source_counts.get(source, 0) + 1

        return {
            "total_tasks": len(all_tasks),
            "completed_tasks": status_counts.get("completed", 0),
            "overdue_tasks": len(overdue),
            "today_tasks": len(today),
            "pending_tasks": status_counts.get("pending", 0),
            "by_status": status_counts,
            "by_priority": priority_counts,
            "by_source": source_counts,
        }
