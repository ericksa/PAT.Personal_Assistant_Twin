from typing import List, Optional, Dict, Any
from datetime import datetime
from src.repositories.base import BaseRepository
from src.models.email import (
    EmailCreate,
    EmailUpdate,
    EmailThreadCreate,
    EmailThreadUpdate,
)


class EmailRepository(BaseRepository):
    """Repository for email operations in PostgreSQL"""

    async def create_email(self, email: EmailCreate) -> dict:
        """Create a new email"""
        query = """
            INSERT INTO emails (
                user_id, external_message_id, thread_id, subject, sender_email,
                sender_name, recipient_emails, cc_emails, bcc_emails,
                body_text, body_html, received_at, sent_at,
                read, flagged, folder, category, priority, summary
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
            RETURNING *
        """
        # Ensure user_id is UUID or string
        user_id = (
            str(email.user_id)
            if email.user_id
            else "00000000-0000-0000-0000-000000000001"
        )

        result = await self.fetchrow(
            query,
            user_id,
            email.external_message_id,
            email.thread_id,
            email.subject,
            email.sender_email,
            email.sender_name,
            email.recipient_emails,
            email.cc_emails,
            email.bcc_emails,
            email.body_text,
            email.body_html,
            email.received_at,
            email.sent_at,
            email.read,
            email.flagged,
            email.folder,
            email.category,
            email.priority,
            email.summary,
        )
        return dict(result) if result else {}

    async def get_email(self, email_id: str) -> Optional[dict]:
        """Get an email by ID"""
        query = "SELECT * FROM emails WHERE id = $1"
        result = await self.fetchrow(query, email_id)
        return dict(result) if result else None

    async def get_email_by_external_id(
        self, external_id: str, user_id: str
    ) -> Optional[dict]:
        """Get an email by External Message ID"""
        query = "SELECT * FROM emails WHERE external_message_id = $1 AND user_id = $2"
        result = await self.fetchrow(query, external_id, user_id)
        return dict(result) if result else None

    async def list_emails(
        self,
        user_id: str,
        folder: Optional[str] = None,
        thread_id: Optional[str] = None,
        is_unread_only: bool = False,
        is_flagged_only: bool = False,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """List emails with optional filters"""
        conditions = ["user_id = $1"]
        params = [user_id]
        param_idx = 2

        if folder:
            conditions.append(f"folder = ${param_idx}")
            params.append(folder)
            param_idx += 1

        if thread_id:
            conditions.append(f"thread_id = ${param_idx}")
            params.append(thread_id)
            param_idx += 1

        if is_unread_only:
            conditions.append(f"read = ${param_idx}")
            params.append(False)
            param_idx += 1

        if is_flagged_only:
            conditions.append(f"flagged = ${param_idx}")
            params.append(True)
            param_idx += 1

        if category:
            conditions.append(f"category = ${param_idx}")
            params.append(category)
            param_idx += 1

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT * FROM emails
            WHERE {where_clause}
            ORDER BY received_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])

        results = await self.fetch(query, *params)
        return [dict(r) for r in results]

    async def update_email(self, email_id: str, email: EmailUpdate) -> Optional[dict]:
        """Update an email"""
        updates = []
        params = []
        param_idx = 1

        # Use model_dump to get values
        data = email.model_dump(exclude_unset=True)

        for key, value in data.items():
            if key in [
                "subject",
                "body_text",
                "body_html",
                "read",
                "flagged",
                "folder",
                "category",
                "priority",
                "summary",
            ]:
                updates.append(f"{key} = ${param_idx}")
                params.append(value)
                param_idx += 1

        if not updates:
            return await self.get_email(email_id)

        params.append(email_id)
        query = f"""
            UPDATE emails
            SET {", ".join(updates)}, updated_at = NOW()
            WHERE id = ${param_idx}
            RETURNING *
        """

        result = await self.fetchrow(query, *params)
        return dict(result) if result else None

    async def delete_email(self, email_id: str) -> bool:
        """Delete an email"""
        query = "DELETE FROM emails WHERE id = $1"
        result = await self.execute(query, email_id)
        return "DELETE 1" in result
