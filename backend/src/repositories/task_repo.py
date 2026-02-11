from typing import List, Optional
from datetime import datetime
from repositories.base import BaseRepository
from models.task import TaskCreate, TaskUpdate


class TaskRepository(BaseRepository):
    """Repository for task operations in PostgreSQL"""

    async def create_task(self, task: TaskCreate) -> dict:
        """Create a new task"""
        query = """
            INSERT INTO tasks (
                user_id, title, description, status, priority,
                due_date, due_time, estimated_duration, tags,
                reminder_minutes, location, is_recurring, recurrence,
                notes, completed_at, completed_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            RETURNING *
        """
        return await self.fetchrow(
            query,
            task.user_id,
            task.title,
            task.description,
            task.status,
            task.priority,
            task.due_date,
            task.due_time,
            task.estimated_duration,
            task.tags,
            task.reminder_minutes,
            task.location,
            task.is_recurring,
            task.recurrence,
            task.notes,
            task.completed_at,
            task.completed_by,
        )

    async def get_task(self, task_id: str) -> Optional[dict]:
        """Get a task by ID"""
        query = "SELECT * FROM tasks WHERE id = $1"
        return await self.fetchrow(query, task_id)

    async def get_task_by_apple_id(self, apple_id: str, user_id: str) -> Optional[dict]:
        """Get a task by Apple Reminders ID"""
        query = "SELECT * FROM tasks WHERE apple_id = $1 AND user_id = $2"
        return await self.fetchrow(query, apple_id, user_id)

    async def list_tasks(
        self,
        user_id: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
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

        if priority:
            conditions.append(f"priority = ${param_idx}")
            params.append(priority)
            param_idx += 1

        if tag:
            conditions.append(f"$${param_idx} = ANY(tags)")
            params.append(tag)
            param_idx += 1

        if is_due_soon:
            conditions.append(
                f"due_date >= NOW() AND due_date <= NOW() + INTERVAL '3 days'"
            )
            conditions.append(f"status != 'completed'")

        if is_overdue:
            conditions.append(f"due_date < NOW()")
            conditions.append(f"status != 'completed'")

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT * FROM tasks
            WHERE {where_clause}
            ORDER BY
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END ASC,
                due_date ASC NULLS LAST,
                created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([str(limit), str(offset)])

        return await self.fetch(query, *params)

    async def update_task(self, task_id: str, task: TaskUpdate) -> Optional[dict]:
        """Update a task"""
        updates = []
        params = []
        param_idx = 1

        if task.title is not None:
            updates.append(f"title = ${param_idx}")
            params.append(task.title)
            param_idx += 1

        if task.description is not None:
            updates.append(f"description = ${param_idx}")
            params.append(task.description)
            param_idx += 1

        if task.status is not None:
            updates.append(f"status = ${param_idx}")
            params.append(task.status)
            param_idx += 1

            if task.status == "completed":
                updates.append(f"completed_at = NOW()")
                updates.append(f"completed_by = ${param_idx}")
                params.append(task.user_id)
                param_idx += 1

        if task.priority is not None:
            updates.append(f"priority = ${param_idx}")
            params.append(task.priority)
            param_idx += 1

        if task.due_date is not None:
            updates.append(f"due_date = ${param_idx}")
            params.append(task.due_date)
            param_idx += 1

        if task.due_time is not None:
            updates.append(f"due_time = ${param_idx}")
            params.append(task.due_time)
            param_idx += 1

        if task.estimated_duration is not None:
            updates.append(f"estimated_duration = ${param_idx}")
            params.append(task.estimated_duration)
            param_idx += 1

        if task.tags is not None:
            updates.append(f"tags = ${param_idx}")
            params.append(task.tags)
            param_idx += 1

        if task.reminder_minutes is not None:
            updates.append(f"reminder_minutes = ${param_idx}")
            params.append(task.reminder_minutes)
            param_idx += 1

        if task.location is not None:
            updates.append(f"location = ${param_idx}")
            params.append(task.location)
            param_idx += 1

        if task.notes is not None:
            updates.append(f"notes = ${param_idx}")
            params.append(task.notes)
            param_idx += 1

        if not updates:
            return await self.get_task(task_id)

        updates.append(f"updated_at = NOW()")
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
              AND due_date < NOW()
              AND status != 'completed'
            ORDER BY due_date ASC
        """
        return await self.fetch(query, user_id)

    async def get_tasks_due_soon(self, user_id: str, days: int = 3) -> List[dict]:
        """Get tasks due within the specified number of days"""
        query = f"""
            SELECT * FROM tasks
            WHERE user_id = $1
              AND due_date >= NOW()
              AND due_date <= NOW() + INTERVAL '{days} days'
              AND status != 'completed'
            ORDER BY due_date ASC
        """
        return await self.fetch(query, user_id)

    async def get_today_tasks(self, user_id: str) -> List[dict]:
        """Get tasks due today"""
        query = """
            SELECT * FROM tasks
            WHERE user_id = $1
              AND due_date::date = CURRENT_DATE
              AND status != 'completed'
            ORDER BY
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END ASC,
                due_time ASC NULLS LAST
        """
        return await self.fetch(query, user_id)

    async def search_tasks(self, user_id: str, search_term: str) -> List[dict]:
        """Search tasks by title or description"""
        query = """
            SELECT * FROM tasks
            WHERE user_id = $1
              AND (title ILIKE $2 OR description ILIKE $2 OR notes ILIKE $2)
            ORDER BY created_at DESC
            LIMIT 50
        """
        return await self.fetch(query, user_id, f"%{search_term}%")
