import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from src.repositories.email_repo import EmailRepository
from src.repositories.task_repo import TaskRepository
from src.repositories.calendar_repo import CalendarRepository
from src.models.email import EmailCreate, EmailUpdate, EmailCategory
from src.models.task import TaskCreate, TaskSource, TaskStatus
from src.models.calendar import CalendarEventCreate
from src.services.llm_service import LlamaLLMService
from src.utils.applescript.mail_manager import MailManager

logger = logging.getLogger(__name__)


class EmailService:
    """Service for email operations with AI processing"""

    def __init__(
        self,
        email_repo: EmailRepository,
        task_repo: TaskRepository,
        calendar_repo: CalendarRepository,
        llm_service: LlamaLLMService,
        mail_manager: MailManager,
    ):
        self.email_repo = email_repo
        self.task_repo = task_repo
        self.calendar_repo = calendar_repo
        self.llm_service = llm_service
        self.mail_manager = mail_manager

    async def sync_from_mailbox(self, user_id_str: str, limit: int = 100) -> dict:
        """Sync emails from Apple Mail to database"""
        result = {"synced": 0, "errors": 0, "message": "Starting sync..."}
        user_id = (
            UUID(user_id_str)
            if user_id_str
            else UUID("00000000-0000-0000-0000-000000000001")
        )

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

            apple_ids = await self.mail_manager.run_applescript(script)
            if not apple_ids:
                return {**result, "message": "No emails found in Mail inbox"}

            if isinstance(apple_ids, str):
                apple_ids = [apple_ids]

            for apple_id in apple_ids:
                # Check if already exists
                existing = await self.email_repo.get_email_by_external_id(
                    apple_id, str(user_id)
                )
                if existing:
                    continue

                await self.sync_single_email(str(user_id), apple_id)
                result["synced"] += 1

            result["message"] = f"Synced {result['synced']} new emails from Mail"

        except Exception as e:
            logger.error(f"Sync error: {e}")
            result["errors"] += 1
            result["message"] = f"Sync error: {str(e)}"

        return result

    async def sync_single_email(self, user_id_str: str, apple_id: str):
        """Sync a single email from Apple Mail"""
        user_id = UUID(user_id_str) if user_id_str else None

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

        raw_data = await self.mail_manager.run_applescript(script)

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
                received_at=datetime.now(),
                read=data.get("read") == "true",
                flagged=data.get("flagged") == "true",
                folder="INBOX",
            )

            await self.email_repo.create_email(email_create)

    async def send_email(
        self, recipient: str, subject: str, body: str, cc: Optional[List[str]] = None
    ) -> bool:
        """Send a new email"""
        return await self.mail_manager.send_email(recipient, subject, body, cc)

    async def reply_to(self, email_id: str, body: str, reply_all: bool = False) -> bool:
        """Reply to an existing email"""
        email = await self.email_repo.get_email(email_id)
        if not email or not email.get("external_message_id"):
            return False

        success = await self.mail_manager.reply_to_email(
            email["external_message_id"], body, reply_all
        )

        if success:
            # Mark as read in DB
            await self.email_repo.update_email(email_id, EmailUpdate(read=True))

        return success

    async def archive(self, email_id: str) -> bool:
        """Archive an email"""
        email = await self.email_repo.get_email(email_id)
        if not email or not email.get("external_message_id"):
            return False

        success = await self.mail_manager.archive_email(email["external_message_id"])

        if success:
            await self.email_repo.update_email(email_id, EmailUpdate(folder="Archive"))

        return success

    async def mark_read(self, email_id: str) -> bool:
        """Mark email as read"""
        email = await self.email_repo.get_email(email_id)
        if not email or not email.get("external_message_id"):
            return False

        success = await self.mail_manager.mark_as_read(email["external_message_id"])

        if success:
            await self.email_repo.update_email(email_id, EmailUpdate(read=True))

        return success

    async def classify_email(self, email_id: str, user_id: str) -> dict:
        """Classify an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return {"error": "Email not found"}

        classification = await self.llm_service.classify_email(
            subject=email.get("subject", ""),
            sender=email.get("sender_email", ""),
            body=email.get("body_text") or "",
        )

        await self.email_repo.update_email(
            email_id,
            EmailUpdate(
                category=EmailCategory(classification.get("category", "personal")),
                priority=int(classification.get("priority", 0)),
            ),
        )

        return classification

    async def summarize_email(self, email_id: str, user_id: str) -> dict:
        """Summarize an email using AI"""
        email = await self.email_repo.get_email(email_id)
        if not email:
            return {"error": "Email not found"}

        summary_text = await self.llm_service.summarize_email(
            subject=email.get("subject", ""),
            body=email.get("body_text") or "",
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
            subject=email.get("subject", ""),
            sender=email.get("sender_email", ""),
            body=email.get("body_text") or "",
            tone=tone,
        )

        return {"draft": reply}

    async def extract_tasks(self, email_id: str, user_id_str: str) -> List[dict]:
        """Extract tasks from an email using AI"""
        user_id = UUID(user_id_str) if user_id_str else None
        email = await self.email_repo.get_email(email_id)
        if not email:
            return []

        tasks_data = await self.llm_service.extract_tasks(email.get("body_text") or "")

        created_tasks = []
        for task_item in tasks_data:
            task_create = TaskCreate(
                user_id=user_id,
                title=task_item.get("task", "Untitled Task"),
                description=task_item.get("description", ""),
                status=TaskStatus.PENDING,
                priority=int(task_item.get("priority", 5)),
                source=TaskSource.EMAIL,
                tags=["email-extracted"],
            )

            task = await self.task_repo.create_task(task_create)
            if task:
                created_tasks.append(task)

        return created_tasks

    async def extract_meetings(self, email_id: str, user_id_str: str) -> List[dict]:
        """Extract meeting requests from an email using AI with enhanced calendar integration"""
        user_id = (
            UUID(user_id_str)
            if user_id_str
            else UUID("00000000-0000-0000-0000-000000000001")
        )
        email = await self.email_repo.get_email(email_id)
        if not email:
            return []

        meeting_details = await self.llm_service.extract_meeting_details(
            email.get("body_text") or ""
        )

        if not meeting_details:
            return []

        # Enhanced meeting extraction with better calendar integration
        created_events = []

        # Validate meeting details and convert to proper datetime
        if meeting_details.get("date") and meeting_details.get("time"):
            try:
                # Create proper datetime objects
                from datetime import datetime, timedelta

                # Merge date and time strings into datetime objects
                meeting_datetime_str = (
                    f"{meeting_details['date']} {meeting_details.get('time', '00:00')}"
                )
                start_dt = datetime.strptime(meeting_datetime_str, "%Y-%m-%d %H:%M")

                # Calculate end time (if duration provided or default to 1 hour)
                duration_min = meeting_details.get("duration_minutes", 60)
                end_dt = start_dt + timedelta(minutes=duration_min)

                # Get attendees list
                attendees = meeting_details.get("attendees", [])
                attendees_list = ", ".join(attendees) if attendees else ""

                # Create enhanced event with proper defaults
                event_create = CalendarEventCreate(
                    title=meeting_details.get(
                        "title", f"Meeting from: {email.get('subject')}"
                    ),
                    description=f"From email: {email.get('subject')}\nAttendees: {attendees_list}\n\n{meeting_details.get('description', '')}",
                    start_time=start_dt,
                    end_time=end_dt,
                    location=meeting_details.get("location", ""),
                    priority=5,  # Default medium priority for meeting invitations
                )

                # Add user_id manually
                event_data = event_create.model_dump()
                event_data["user_id"] = str(user_id)
                event_data["related_email_id"] = email_id  # Link to email

                # Create calendar event
                event = await self.calendar_repo.create_event(event_data)
                if event:
                    created_events.append(event)

            except Exception as e:
                logger.error(f"Failed to process meeting details: {e}")
                # Create a basic event as fallback
                event_create = CalendarEventCreate(
                    title=meeting_details.get(
                        "title", f"Meeting from: {email.get('subject')}"
                    ),
                    description=meeting_details.get("description", ""),
                    start_time=datetime.now(),
                    end_time=datetime.now() + timedelta(hours=1),
                    location=meeting_details.get("location"),
                    priority=5,
                )

                # Add user_id manually
                event_data = event_create.model_dump()
                event_data["user_id"] = str(user_id)
                event_data["related_email_id"] = email_id  # Link to email

                event = await self.calendar_repo.create_event(event_data)
                if event:
                    created_events.append(event)

        return created_events

    async def batch_classify_recent(self, user_id: str, limit: int = 20) -> dict:
        """Batch classify recent unclassified emails"""
        emails = await self.email_repo.list_emails(
            user_id=user_id, category=None, limit=limit
        )

        results = {"processed": 0, "errors": 0, "classifications": {}}

        for email in emails:
            try:
                classification = await self.classify_email(str(email["id"]), user_id)
                results["classifications"][str(email["id"])] = classification.get(
                    "category"
                )
                results["processed"] += 1
            except Exception as e:
                logger.error(f"Error classifying email {email['id']}: {e}")
                results["errors"] += 1

        return results
