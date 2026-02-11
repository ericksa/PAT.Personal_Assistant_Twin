from typing import List, Optional
from datetime import datetime
from repositories.base import BaseRepository
from models.email import (
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
                user_id, apple_id, thread_id, subject, from_address,
                from_name, to_addresses, cc_addresses, bcc_addresses,
                body_preview, body_text, body_html, received_at, sent_at,
                is_read, is_flagged, folder, apple_message_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            RETURNING *
        """
        return await self.fetchrow(
            query,
            email.user_id,
            email.apple_id,
            email.thread_id,
            email.subject,
            email.from_address,
            email.from_name,
            email.to_addresses,
            email.cc_addresses,
            email.bcc_addresses,
            email.body_preview,
            email.body_text,
            email.body_html,
            email.received_at,
            email.sent_at,
            email.is_read,
            email.is_flagged,
            email.folder,
            email.apple_message_id,
        )

    async def get_email(self, email_id: str) -> Optional[dict]:
        """Get an email by ID"""
        query = "SELECT * FROM emails WHERE id = $1"
        return await self.fetchrow(query, email_id)

    async def get_email_by_apple_id(
        self, apple_id: str, user_id: str
    ) -> Optional[dict]:
        """Get an email by Apple Mail ID"""
        query = "SELECT * FROM emails WHERE apple_id = $1 AND user_id = $2"
        return await self.fetchrow(query, apple_id, user_id)

    async def list_emails(
        self,
        user_id: str,
        folder: Optional[str] = None,
        thread_id: Optional[str] = None,
        is_unread_only: bool = False,
        is_flagged_only: bool = False,
        classification: Optional[str] = None,
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
            conditions.append(f"is_read = ${param_idx}")
            params.append("false")
            param_idx += 1

        if is_flagged_only:
            conditions.append(f"is_flagged = ${param_idx}")
            params.append("true")
            param_idx += 1

        if classification:
            conditions.append(f"classification = ${param_idx}")
            params.append(classification)
            param_idx += 1

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT * FROM emails
            WHERE {where_clause}
            ORDER BY received_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([str(limit), str(offset)])

        return await self.fetch(query, *params)

    async def update_email(self, email_id: str, email: EmailUpdate) -> Optional[dict]:
        """Update an email"""
        updates = []
        params = []
        param_idx = 1

        if email.subject is not None:
            updates.append(f"subject = ${param_idx}")
            params.append(email.subject)
            param_idx += 1

        if email.body_preview is not None:
            updates.append(f"body_preview = ${param_idx}")
            params.append(email.body_preview)
            param_idx += 1

        if email.body_text is not None:
            updates.append(f"body_text = ${param_idx}")
            params.append(email.body_text)
            param_idx += 1

        if email.body_html is not None:
            updates.append(f"body_html = ${param_idx}")
            params.append(email.body_html)
            param_idx += 1

        if email.is_read is not None:
            updates.append(f"is_read = ${param_idx}")
            params.append(email.is_read)
            param_idx += 1

        if email.is_flagged is not None:
            updates.append(f"is_flagged = ${param_idx}")
            params.append(email.is_flagged)
            param_idx += 1

        if email.folder is not None:
            updates.append(f"folder = ${param_idx}")
            params.append(email.folder)
            param_idx += 1

        if email.classification is not None:
            updates.append(f"classification = ${param_idx}")
            params.append(email.classification)
            param_idx += 1

        if email.summary is not None:
            updates.append(f"summary = ${param_idx}")
            params.append(email.summary)
            param_idx += 1

        if not updates:
            return await self.get_email(email_id)

        updates.append(f"updated_at = NOW()")
        params.append(email_id)

        query = f"""
            UPDATE emails
            SET {", ".join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        """

        return await self.fetchrow(query, *params)

    async def delete_email(self, email_id: str) -> bool:
        """Delete an email"""
        query = "DELETE FROM emails WHERE id = $1"
        result = await self.execute(query, email_id)
        return result == "DELETE 1"

    async def create_thread(self, thread: EmailThreadCreate) -> dict:
        """Create a new email thread"""
        query = """
            INSERT INTO email_threads (
                user_id, apple_thread_id, subject, participant_count,
                message_count, is_unread, last_message_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """
        return await self.fetchrow(
            query,
            thread.user_id,
            thread.apple_thread_id,
            thread.subject,
            thread.participant_count,
            thread.message_count,
            thread.is_unread,
            thread.last_message_at,
        )

    async def get_thread(self, thread_id: str) -> Optional[dict]:
        """Get a thread by ID"""
        query = "SELECT * FROM email_threads WHERE id = $1"
        return await self.fetchrow(query, thread_id)

    async def get_thread_by_apple_id(
        self, apple_thread_id: str, user_id: str
    ) -> Optional[dict]:
        """Get a thread by Apple Mail thread ID"""
        query = (
            "SELECT * FROM email_threads WHERE apple_thread_id = $1 AND user_id = $2"
        )
        return await self.fetchrow(query, apple_thread_id, user_id)

    async def list_threads(
        self,
        user_id: str,
        is_unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """List email threads"""
        conditions = ["user_id = $1"]
        params = [user_id]
        param_idx = 2

        if is_unread_only:
            conditions.append(f"is_unread = ${param_idx}")
            params.append("true")
            param_idx += 1

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT * FROM email_threads
            WHERE {where_clause}
            ORDER BY last_message_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([str(limit), str(offset)])

        return await self.fetch(query, *params)

    async def update_thread(
        self, thread_id: str, thread: EmailThreadUpdate
    ) -> Optional[dict]:
        """Update a thread"""
        updates = []
        params = []
        param_idx = 1

        if thread.subject is not None:
            updates.append(f"subject = ${param_idx}")
            params.append(thread.subject)
            param_idx += 1

        if thread.participant_count is not None:
            updates.append(f"participant_count = ${param_idx}")
            params.append(thread.participant_count)
            param_idx += 1

        if thread.message_count is not None:
            updates.append(f"message_count = ${param_idx}")
            params.append(thread.message_count)
            param_idx += 1

        if thread.is_unread is not None:
            updates.append(f"is_unread = ${param_idx}")
            params.append(thread.is_unread)
            param_idx += 1

        if thread.last_message_at is not None:
            updates.append(f"last_message_at = ${param_idx}")
            params.append(thread.last_message_at)
            param_idx += 1

        if not updates:
            return await self.get_thread(thread_id)

        updates.append(f"updated_at = NOW()")
        params.append(thread_id)

        query = f"""
            UPDATE email_threads
            SET {", ".join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        """

        return await self.fetchrow(query, *params)
