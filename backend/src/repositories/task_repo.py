from typing import List, Optional, Dict, Any
from datetime import datetime, date
from src.repositories.base import BaseRepository
from src.models.task import TaskCreate, TaskUpdate


class TaskRepository(BaseRepository):
    """Repository for task operations in PostgreSQL"""

    async def create_task(self, task: TaskCreate) -> dict:
        """Create a new task"""
        query = """
            INSERT INTO tasks (
                user_id, title, description, due_date, due_time,
                priority, status, reminder_date, source,
                list_name, estimated_duration_minutes, tags
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
        """
        # Note: task might be a Pydantic model or a dict
        if hasattr(task, "model_dump"):
            data = task.model_dump()
        else:
            data = task

        return await self.fetchrow(
            query,
            data.get("user_id", "00000000-0000-0000-0000-000000000001"),
            data.get("title"),
            data.get("description"),
            data.get("due_date"),
            data.get("due_time"),
            data.get("priority", 0),
            data.get("status", "pending"),
            data.get("reminder_date"),
            data.get("source", "pat"),
            data.get("list_name", "Reminders"),
            data.get("estimated_duration_minutes"),
            data.get("tags", []),
        )

    async def get_task(self, task_id: str) -> Optional[dict]:
        """Get a task by ID"""
        query = "SELECT * FROM tasks WHERE id = $1"
        return await self.fetchrow(query, task_id)

    async def get_task_by_external_id(
        self, external_id: str, user_id: str
    ) -> Optional[dict]:
        """Get a task by Apple Reminders ID"""
        query = "SELECT * FROM tasks WHERE external_task_id = $1 AND user_id = $2"
        return await self.fetchrow(query, external_id, user_id)

    async def list_tasks(
        self,
        user_id: str,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        tag: Optional[str] = None,
        is_due_soon: bool = False,
        is_overdue: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """List tasks with optional filters"""
        conditions = ["user_id = $1"]
        params = [user_id]
        param_idx = 2

        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        if priority is not None:
            conditions.append(f"priority = ${param_idx}")
            params.append(priority)
            param_idx += 1

        if tag:
            conditions.append(f"${param_idx} = ANY(tags)")
            params.append(tag)
            param_idx += 1

        if is_due_soon:
            conditions.append(
                f"due_date >= CURRENT_DATE AND due_date <= CURRENT_DATE + INTERVAL '3 days'"
            )
            conditions.append(f"status != 'completed'")

        if is_overdue:
            conditions.append(f"due_date < CURRENT_DATE")
            conditions.append(f"status != 'completed'")

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT * FROM tasks
            WHERE {where_clause}
            ORDER BY priority DESC, due_date ASC NULLS LAST, created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])

        return await self.fetch(query, *params)

    async def update_task(self, task_id: str, task: TaskUpdate) -> Optional[dict]:
        """Update a task"""
        updates = []
        params = []
        param_idx = 1

        data = task.model_dump(exclude_unset=True)

        for key, value in data.items():
            if key in [
                "title",
                "description",
                "status",
                "priority",
                "due_date",
                "due_time",
                "reminder_date",
                "completion_notes",
                "tags",
            ]:
                updates.append(f"{key} = ${param_idx}")
                params.append(value)
                param_idx += 1

                if key == "status" and value == "completed":
                    updates.append(f"completed_at = NOW()")

        if not updates:
            return await self.get_task(task_id)

        updates.append("updated_at = NOW()")
        params.append(task_id)

        query = f"""
            UPDATE tasks
            SET {", ".join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        """

        return await self.fetchrow(query, *params)

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        query = "DELETE FROM tasks WHERE id = $1"
        result = await self.execute(query, task_id)
        return result == "DELETE 1"

    async def get_overdue_tasks(self, user_id: str) -> List[dict]:
        """Get all overdue tasks"""
        query = """
            SELECT * FROM tasks
            WHERE user_id = $1
              AND due_date < CURRENT_DATE
              AND status != 'completed'
            ORDER BY due_date ASC
        """
        return await self.fetch(query, user_id)

    async def get_today_tasks(self, user_id: str) -> List[dict]:
        """Get tasks due today"""
        query = """
            SELECT * FROM tasks
            WHERE user_id = $1
              AND due_date = CURRENT_DATE
              AND status != 'completed'
            ORDER BY priority DESC, due_time ASC NULLS LAST
        """
        return await self.fetch(query, user_id)
