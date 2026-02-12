#!/usr/bin/env python3
"""
AppleScript Mail Manager
Provides specialized functions for interacting with Apple Mail
"""

import logging
from typing import List, Optional, Dict, Any
from .base_manager import AppleScriptManager, execute_applescript

logger = logging.getLogger(__name__)


class MailManager(AppleScriptManager):
    """Specific manager for Apple Mail operations"""

    async def send_email(
        self, recipient: str, subject: str, body: str, cc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email via Apple Mail.
        """
        cc_clause = ""
        if cc:
            cc_str = ", ".join([f'"{c}"' for c in cc])
            cc_clause = f"make new cc recipient at end of cc recipients with properties {{address:{{{cc_str}}}}}"

        script = f"""
        tell application "Mail"
            set newMessage to make new outgoing message with properties {{subject:"{subject}", content:"{body}", visible:true}}
            tell newMessage
                make new to recipient at end of to recipients with properties {{address:"{recipient}"}}
                {cc_clause}
                send
            end tell
        end tell
        """
        try:
            await self.run_applescript(script)
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def reply_to_email(
        self, message_id: str, body: str, reply_all: bool = False
    ) -> bool:
        """
        Reply to a specific email in Apple Mail.
        """
        script = f"""
        tell application "Mail"
            set originalMessage to first message of inbox whose message id is "{message_id}"
            set theReply to reply originalMessage with opening window and reply to all {str(reply_all).lower()}
            tell theReply
                set content to "{body}" & return & content
                send
            end tell
        end tell
        """
        try:
            await self.run_applescript(script)
            return True
        except Exception as e:
            logger.error(f"Failed to reply to email: {e}")
            return False

    async def get_unread_count(self) -> int:
        """Get count of unread messages in inbox"""
        script = 'tell application "Mail" to get unread count of inbox'
        try:
            result = await self.run_applescript(script)
            return int(result) if result else 0
        except:
            return 0

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read in Apple Mail"""
        script = f"""
        tell application "Mail"
            set currentEmail to first message of inbox whose message id is "{message_id}"
            set read status of currentEmail to true
        end tell
        """
        try:
            await self.run_applescript(script)
            return True
        except:
            return False

    async def archive_email(self, message_id: str) -> bool:
        """Move email to Archive folder"""
        script = f"""
        tell application "Mail"
            set currentEmail to first message of inbox whose message id is "{message_id}"
            set archiveMailbox to mailbox "Archive" of account (name of account of mailbox of currentEmail)
            move currentEmail to archiveMailbox
        end tell
        """
        try:
            await self.run_applescript(script)
            return True
        except:
            return False
