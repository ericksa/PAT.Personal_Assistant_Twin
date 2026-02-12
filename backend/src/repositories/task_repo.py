from typing import List, Optional, Dict, Any
from datetime import datetime, date
from src.repositories.base import BaseRepository
from src.models.task import TaskCreate, TaskUpdate


class TaskRepository(BaseRepository):
    """Repository for task operations in PostgreSQL"""

    async def create_task(self, task: TaskCreate) -> Optional[Dict[str, Any]]:
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
        # Access attributes directly from Pydantic model
        user_id = (
            str(task.user_id)
            if task.user_id
            else "00000000-0000-0000-0000-000000000001"
        )

        result = await self.fetchrow(
            query,
            user_id,
            task.title,
            task.description,
            task.due_date,
            task.due_time,
            task.priority,
            str(task.status.value)
            if hasattr(task.status, "value")
            else str(task.status),
            task.reminder_date,
            str(task.source.value)
            if hasattr(task.source, "value")
            else str(task.source),
            task.list_name,
            task.estimated_duration_minutes,
            task.tags,
        )
        return dict(result) if result else None

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID"""
        query = "SELECT * FROM tasks WHERE id = $1"
        result = await self.fetchrow(query, task_id)
        return dict(result) if result else None

    async def get_task_by_external_id(
        self, external_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a task by Apple Reminders ID"""
        query = "SELECT * FROM tasks WHERE external_task_id = $1 AND user_id = $2"
        result = await self.fetchrow(query, external_id, user_id)
        return dict(result) if result else None

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
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filters"""
        conditions = ["user_id = $1"]
        params: List[Any] = [user_id]
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

        results = await self.fetch(query, *params)
        return [dict(r) for r in results]

    async def update_task(
        self, task_id: str, task: TaskUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update a task"""
        updates = []
        params: List[Any] = []
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
                # Handle Enum
                if key in ["status", "priority"] and value and hasattr(value, "value"):
                    params.append(value.value)
                else:
                    params.append(value)
                param_idx += 1

                if key == "status" and value == "completed":
                    updates.append("completed_at = NOW()")

        if not updates:
            return await self.get_task(task_id)

        params.append(task_id)
        query = f"""
            UPDATE tasks
            SET {", ".join(updates)}, updated_at = NOW()
            WHERE id = ${param_idx}
            RETURNING *
        """

        result = await self.fetchrow(query, *params)
        return dict(result) if result else None

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        query = "DELETE FROM tasks WHERE id = $1"
        result = await self.execute(query, task_id)
        return "DELETE 1" in result

    async def get_overdue_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all overdue tasks"""
        query = """
            SELECT * FROM tasks
            WHERE user_id = $1
              AND due_date < CURRENT_DATE
              AND status != 'completed'
            ORDER BY due_date ASC
        """
        results = await self.fetch(query, user_id)
        return [dict(r) for r in results]

    async def get_today_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get tasks due today"""
        query = """
            SELECT * FROM tasks
            WHERE user_id = $1
              AND due_date = CURRENT_DATE
              AND status != 'completed'
            ORDER BY priority DESC, due_time ASC NULLS LAST
        """
        results = await self.fetch(query, user_id)
        return [dict(r) for r in results]
