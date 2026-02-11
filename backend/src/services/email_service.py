import json
from typing import List, Optional
from datetime import datetime
from src.repositories.email_repo import EmailRepository
from src.repositories.task_repo import TaskRepository
from src.repositories.calendar_repo import CalendarRepository
from src.models.email import EmailCreate, EmailUpdate
from src.models.task import TaskCreate
from src.services.llm_service import LLMService
from src.utils.applescript.base_manager import AppleScriptManager


class EmailService:
    """Service for email operations with AI processing"""

    def __init__(
        self,
        email_repo: EmailRepository,
        task_repo: TaskRepository,
        calendar_repo: CalendarRepository,
        llm_service: LLMService,
        applescript_manager: AppleScriptManager,
    ):
        self.email_repo = email_repo
        self.task_repo = task_repo
        self.calendar_repo = calendar_repo
        self.llm_service = llm_service
        self.applescript = applescript_manager

    async def sync_from_mailbox(self, user_id: str, limit: int = 100) -> dict:
        """Sync emails from Apple Mail to database"""
        result = {"synced": 0, "errors": 0, "message": "Sync not yet implemented"}

        try:
            script = """
            tell application "Mail"
                set messageIdList to {}
                set emailList to messages of inbox
                set i to 1
                repeat with currentEmail in (get emailList)
                    if i > {limit} then exit repeat
                    set end of messageIdList to message id of currentEmail
                    set i to i + 1
                end repeat
                return messageIdList
            end tell
            """

            apple_ids = await self.applescript.run_applescript(script, limit)
            if not apple_ids:
                return {**result, "message": "No emails found in Mail inbox"}

            for apple_id in apple_ids[:limit]:
                if await self.email_repo.get_email_by_apple_id(apple_id, user_id):
                    continue

                await self.sync_single_email(user_id, apple_id)
                result["synced"] += 1

            result["message"] = f"Synced {result['synced']} new emails from Mail"

        except Exception as e:
            result["errors"] += 1
            result["message"] = f"Sync error: {str(e)}"

        return result

    async def sync_single_email(self, user_id: str, apple_id: str):
        """Sync a single email from Apple Mail"""
        script = f"""
        tell application "Mail"
            set currentEmail to first message whose id is "{apple_id}"
            set emailSubject to subject of currentEmail
            set emailFrom to sender of currentEmail
            set emailDate to date received of currentEmail
            set emailBody to content of currentEmail
            set emailRead to read status of currentEmail as string
            set emailFlagged to flagged status of currentEmail as string
            set messageId to message id of currentEmail

            return {{"subject": emailSubject, "from": emailFrom, "date": emailDate, "body": emailBody, "read": emailRead, "flagged": emailFlagged}}
        end tell
        """

        email_data = await self.applescript.run_applescript(script)

        if email_data:
            from_address = email_data.get("from", "").lower()
            from_name = ""
            if "<" in from_address:
                from_name, from_address = from_address.split("<", 1)
                from_name = from_name.strip()
                from_address = from_address.rstrip(">")

            email_create = EmailCreate(
                user_id=user_id,
                apple_id=apple_id,
                subject=email_data.get("subject", ""),
                thread_id="manual-sync",
                from_address=from_address,
                from_name=from_name or None,
                to_addresses=[],
                cc_addresses=[],
                bcc_addresses=[],
                body_preview=email_data.get("body", "")[:200],
                body_text=email_data.get("body", ""),
                body_html=None,
                received_at=datetime.now(),
                sent_at=email_data.get("date", datetime.now()),
                is_read=email_data.get("read", "yes") == "yes",
                is_flagged=email_data.get("flagged", "no") == "yes",
                folder="INBOX",
                apple_message_id=email_data.get("messageId"),
            )

            await self.email_repo.create_email(email_create)

    async def classify_email(self, email_id: str, user_id: str) -> dict:
        """Classify an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return {"error": "Email not found"}

        classification = await self.llm_service.classify_email(
            subject=email["subject"],
            body=email["body_preview"] or email["body_text"] or "",
        )

        await self.email_repo.update_email(
            email_id,
            EmailUpdate(
                classification=classification["category"],
                sub_classification=classification.get("subcategory"),
            ),
        )

        return classification

    async def summarize_email(self, email_id: str, user_id: str) -> dict:
        """Summarize an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return {"error": "Email not found"}

        summary = await self.llm_service.summarize_email(
            subject=email["subject"],
            body=email["body_preview"] or email["body_text"] or "",
        )

        await self.email_repo.update_email(
            email_id, EmailUpdate(summary=summary["summary"])
        )

        return summary

    async def draft_reply(
        self, email_id: str, user_id: str, tone: str = "professional"
    ) -> dict:
        """Draft a reply to an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return {"error": "Email not found"}

        reply = await self.llm_service.draft_email_reply(
            subject=email["subject"],
            body=email["body_preview"] or email["body_text"] or "",
            tone=tone,
        )

        return reply

    async def extract_tasks(self, email_id: str, user_id: str) -> List[dict]:
        """Extract tasks from an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return []

        tasks = await self.llm_service.extract_tasks_from_email(
            subject=email["subject"],
            body=email["body_preview"] or email["body_text"] or "",
        )

        created_tasks = []
        for task_data in tasks:
            task_create = TaskCreate(
                user_id=user_id,
                title=task_data["title"],
                description=task_data.get("description", ""),
                status="pending",
                priority=task_data.get("priority", "medium"),
                tags=["email", "extracted"] + task_data.get("tags", []),
                notes=f"Extracted from email: {email['subject']}",
            )

            task = await self.task_repo.create_task(task_create)
            created_tasks.append(task)

        return created_tasks

    async def extract_meetings(self, email_id: str, user_id: str) -> List[dict]:
        """Extract meeting requests from an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return []

        meetings = await self.llm_service.extract_meetings_from_email(
            subject=email["subject"],
            body=email["body_preview"] or email["body_text"] or "",
        )

        created_events = []
        for meeting in meetings:
            from src.models.calendar import CalendarEventCreate

            event_create = CalendarEventCreate(
                user_id=user_id,
                title=meeting["title"],
                description=meeting.get("description", ""),
                start_date=meeting["start_date"],
                start_time=meeting.get("start_time"),
                end_date=meeting["end_date"],
                end_time=meeting.get("end_time"),
                location=meeting.get("location"),
                event_type="meeting",
                source="email",
                notes=f"Extracted from email: {email['subject']}",
            )

            event = await self.calendar_repo.create_event(event_create)
            created_events.append(event)

        return created_events

    async def batch_classify_recent(self, user_id: str, limit: int = 20) -> dict:
        """Batch classify recent unclassified emails"""
        emails = await self.email_repo.list_emails(
            user_id=user_id, classification=None, limit=limit
        )

        results = {"processed": 0, "errors": 0, "classifications": {}}

        for email in emails:
            try:
                classification = await self.classify_email(email["id"], user_id)
                results["classifications"][email["id"]] = classification["category"]
                results["processed"] += 1
            except Exception as e:
                results["errors"] += 1

        return results
