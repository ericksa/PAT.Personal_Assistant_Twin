import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.repositories.email_repo import EmailRepository
from src.repositories.task_repo import TaskRepository
from src.repositories.calendar_repo import CalendarRepository
from src.models.email import EmailCreate, EmailUpdate
from src.models.task import TaskCreate
from src.services.llm_service import LlamaLLMService
from src.utils.applescript.base_manager import AppleScriptManager

logger = logging.getLogger(__name__)


class EmailService:
    """Service for email operations with AI processing"""

    def __init__(
        self,
        email_repo: EmailRepository,
        task_repo: TaskRepository,
        calendar_repo: CalendarRepository,
        llm_service: LlamaLLMService,
        applescript_manager: AppleScriptManager,
    ):
        self.email_repo = email_repo
        self.task_repo = task_repo
        self.calendar_repo = calendar_repo
        self.llm_service = llm_service
        self.applescript = applescript_manager

    async def sync_from_mailbox(self, user_id: str, limit: int = 100) -> dict:
        """Sync emails from Apple Mail to database"""
        result = {"synced": 0, "errors": 0, "message": "Starting sync..."}

        try:
            # Get message IDs from Apple Mail
            script = f"""
            tell application "Mail"
                set messageIdList to {{}}
                set emailList to messages of inbox
                set countLimit to {limit}
                set i to 1
                repeat with currentEmail in emailList
                    if i > countLimit then exit repeat
                    set end of messageIdList to message id of currentEmail
                    set i to i + 1
                end repeat
                return messageIdList
            end tell
            """

            apple_ids = await self.applescript.run_applescript(script)
            if not apple_ids:
                return {**result, "message": "No emails found in Mail inbox"}

            if isinstance(apple_ids, str):
                apple_ids = [apple_ids]

            for apple_id in apple_ids:
                # Check if already exists
                existing = await self.email_repo.get_email_by_external_id(
                    apple_id, user_id
                )
                if existing:
                    continue

                await self.sync_single_email(user_id, apple_id)
                result["synced"] += 1

            result["message"] = f"Synced {result['synced']} new emails from Mail"

        except Exception as e:
            logger.error(f"Sync error: {e}")
            result["errors"] += 1
            result["message"] = f"Sync error: {str(e)}"

        return result

    async def sync_single_email(self, user_id: str, apple_id: str):
        """Sync a single email from Apple Mail"""
        script = f"""
        tell application "Mail"
            set currentEmail to first message of inbox whose message id is "{apple_id}"
            set emailSubject to subject of currentEmail
            set emailFrom to sender of currentEmail
            set emailDate to date received of currentEmail
            set emailBody to content of currentEmail
            set emailRead to read status of currentEmail as string
            set emailFlagged to flagged status of currentEmail as string
            
            return "subject:" & emailSubject & "|from:" & emailFrom & "|date:" & (emailDate as string) & "|read:" & emailRead & "|flagged:" & emailFlagged & "|body:" & emailBody
        end tell
        """

        raw_data = await self.applescript.run_applescript(script)

        # Simple parsing (improvement needed for robust parsing)
        if raw_data and isinstance(raw_data, str):
            parts = raw_data.split("|", 5)
            data = {}
            for part in parts:
                if ":" in part:
                    k, v = part.split(":", 1)
                    data[k] = v

            sender = data.get("from", "")
            sender_name = ""
            sender_email = sender
            if "<" in sender:
                sender_name, sender_email = sender.split("<", 1)
                sender_name = sender_name.strip()
                sender_email = sender_email.rstrip(">").strip()

            email_create = EmailCreate(
                user_id=user_id,
                external_message_id=apple_id,
                subject=data.get("subject", "No Subject"),
                sender_email=sender_email,
                sender_name=sender_name or None,
                body_text=data.get("body", ""),
                received_at=datetime.now(),  # Should parse from data['date']
                read=data.get("read") == "true",
                flagged=data.get("flagged") == "true",
                folder="INBOX",
            )

            await self.email_repo.create_email(email_create)

    async def classify_email(self, email_id: str, user_id: str) -> dict:
        """Classify an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return {"error": "Email not found"}

        classification = await self.llm_service.classify_email(
            subject=email["subject"],
            sender=email["sender_email"],
            body=email["body_text"] or "",
        )

        await self.email_repo.update_email(
            email_id,
            EmailUpdate(
                category=classification.get("category", "personal"),
                priority=classification.get("priority", 0),
            ),
        )

        return classification

    async def summarize_email(self, email_id: str, user_id: str) -> dict:
        """Summarize an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return {"error": "Email not found"}

        summary_text = await self.llm_service.summarize_email(
            subject=email["subject"],
            body=email["body_text"] or "",
        )

        await self.email_repo.update_email(email_id, EmailUpdate(summary=summary_text))

        return {"summary": summary_text}

    async def draft_reply(
        self, email_id: str, user_id: str, tone: str = "professional"
    ) -> dict:
        """Draft a reply to an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return {"error": "Email not found"}

        reply = await self.llm_service.draft_email_reply(
            subject=email["subject"],
            sender=email["sender_email"],
            body=email["body_text"] or "",
            tone=tone,
        )

        return {"draft": reply}

    async def extract_tasks(self, email_id: str, user_id: str) -> List[dict]:
        """Extract tasks from an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return []

        tasks_data = await self.llm_service.extract_tasks(email["body_text"] or "")

        created_tasks = []
        for task_item in tasks_data:
            task_create = TaskCreate(
                user_id=user_id,
                title=task_item["title"],
                description=task_item.get("description", ""),
                status="pending",
                priority=task_item.get("priority", 5),
                source="email",
                related_email_id=email["id"],
                tags=["email-extracted"],
            )

            task = await self.task_repo.create_task(task_create)
            created_tasks.append(task)

        return created_tasks

    async def extract_meetings(self, email_id: str, user_id: str) -> List[dict]:
        """Extract meeting requests from an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return []

        meeting_details = await self.llm_service.extract_meeting_details(
            email["body_text"] or ""
        )

        if not meeting_details or "error" in meeting_details:
            return []

        # Convert meeting_details to calendar event
        from src.models.calendar import CalendarEventCreate

        event_create = CalendarEventCreate(
            user_id=user_id,
            title=meeting_details.get("title", f"Meeting from: {email['subject']}"),
            description=meeting_details.get("description", ""),
            start_time=datetime.now(),  # Placeholder, should parse from meeting_details
            end_time=datetime.now(),  # Placeholder
            location=meeting_details.get("location"),
            event_type="meeting",
        )

        event = await self.calendar_repo.create_event(event_create.model_dump())
        return [event]

    async def batch_classify_recent(self, user_id: str, limit: int = 20) -> dict:
        """Batch classify recent unclassified emails"""
        emails = await self.email_repo.list_emails(
            user_id=user_id, category=None, limit=limit
        )

        results = {"processed": 0, "errors": 0, "classifications": {}}

        for email in emails:
            try:
                classification = await self.classify_email(email["id"], user_id)
                results["classifications"][email["id"]] = classification.get("category")
                results["processed"] += 1
            except Exception as e:
                logger.error(f"Error classifying email {email['id']}: {e}")
                results["errors"] += 1

        return results
