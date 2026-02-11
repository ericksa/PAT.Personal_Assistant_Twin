#!/usr/bin/env python3
"""
PAT Core Sync Workers - Run on macOS host
Syncs data from Apple Calendar, Apple Mail, and Apple Reminders to pat-core API

Usage:
    For single run testing:
        python3 scripts/pat_sync_worker.py --service=calendar --once
        python3 scripts/pat_sync_worker.py --service=email --once
        python3 scripts/pat_sync_worker.py --service=reminders --once

    For continuous sync (in background):
        python3 scripts/pat_sync_worker.py --service=calendar --interval=3600 &
        python3 scripts/pat_sync_worker.py --service=email --interval=300 &
        python3 scripts/pat_sync_worker.py --service=reminders --interval=600 &
"""

import argparse
import time
import logging
import requests
from datetime import datetime
import subprocess
import json
import platform
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PAT_CORE_URL = "http://localhost:8010"
USER_EMAIL = "erickson.adam.m@gmail.com"
USER_ID = "00000000-0000-0000-0000-000000000001"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/sync_workers.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


class PATSyncWorker:
    """Base class for sync workers"""

    def __init__(self, service_name: str, interval: int = 300):
        self.service_name = service_name
        self.interval = interval
        self.running = False
        self.consecutive_failures = 0
        self.email_sent = False
        self.max_email_attempts = 5

    def run_applescript(self, script: str, timeout: int = 30) -> str:
        """
        Execute AppleScript command

        Returns:
            String output from AppleScript, or empty string on error
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                logger.error(
                    f"[{self.service_name}] AppleScript error: {result.stderr}"
                )
                return ""

            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"[{self.service_name}] AppleScript timeout (>{timeout}s)")
            return ""
        except Exception as e:
            logger.error(f"[{self.service_name}] AppleScript execution failed: {e}")
            return ""

    def call_api(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """
        Make API call to pat-core

        Returns:
            Dict response from API, or error dict on failure
        """
        url = f"{PAT_CORE_URL}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            else:
                response = requests.request(method, url, json=data, timeout=30)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            logger.error(
                f"[{self.service_name}] PAT Core not reachable at {PAT_CORE_URL}"
            )
            logger.info(
                f"[{self.service_name}] Ensure PAT Core is running (cd src && python3 main_pat.py)"
            )
            return {"error": "PAT Core not reachable"}
        except requests.exceptions.Timeout:
            logger.error(f"[{self.service_name}] API request timed out")
            return {"error": "API timeout"}
        except Exception as e:
            logger.error(f"[{self.service_name}] API call failed: {e}")
            return {"error": str(e)}

    def sync(self) -> dict:
        """
        Perform sync operation - override in subclasses

        Returns:
            Dict with sync results (synced count, errors, etc.)
        """
        raise NotImplementedError

    def handle_error(self, error_msg: str):
        """
        Handle errors with logging and optional email notification
        """
        logger.error(f"[{self.service_name}] {error_msg}")

        # Log to terminal and file (already configured in setup)
        # No terminal prompt for testing - removed per user request

        self.consecutive_failures += 1

        # Send email only once if not already sent
        if not self.email_sent and self.consecutive_failures >= self.max_email_attempts:
            self.send_error_notification(error_msg)
            self.email_sent = True
        elif (
            "error" not in str(error_msg).lower()
            or "unavailable" not in str(error_msg).lower()
        ):
            # Reset email flag if the error is not about availability
            self.email_sent = False

    def send_error_notification(self, error_msg: str):
        """
        Send one-time email notification about persistent errors
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # SMTP configuration (placeholder - would need real config)
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER", USER_EMAIL)
            smtp_password = os.getenv("SMTP_PASSWORD")

            if not smtp_password or smtp_password == "your_gmail_app_password_here":
                logger.warning(
                    f"[{self.service_name}] SMTP not configured, skipping email notification"
                )
                return

            # Create message
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = USER_EMAIL
            msg["Subject"] = f"PAT Sync Worker Alert: {self.service_name}"

            body = f"""
PAT Sync Worker Alert - {self.service_name}
{"=" * 50}

Service: {self.service_name}
Status: Error
Error Message: {error_msg}
Consecutive Failures: {self.consecutive_failures}
Timestamp: {datetime.now().isoformat()}

This is the first notification. You will not receive more emails until this error is fixed and resets.

Please check logs at: logs/sync_workers.log
            """

            msg.attach(MIMEText(body, "plain"))

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"[{self.service_name}] Error notification email sent")

        except Exception as e:
            logger.error(
                f"[{self.service_name}] Failed to send error notification: {e}"
            )

    def start(self):
        """
        Start sync worker loop
        """
        if platform.system() != "Darwin":
            logger.error(f"[{self.service_name}] Sync workers only work on macOS")
            logger.info(f"[{self.service_name}] Current platform: {platform.system()}")
            return

        self.running = True
        logger.info(
            f"[{self.service_name}] Starting sync worker (interval: {self.interval}s)"
        )

        try:
            while self.running:
                start_time = time.time()

                # Perform sync
                try:
                    result = self.sync()
                    synced = result.get("synced", 0)
                    errors = result.get("errors", 0)
                    message = result.get("message", "")

                    if synced > 0:
                        logger.info(
                            f"[{self.service_name}] Sync result: {synced} items synced, {errors} errors"
                        )
                        logger.info(f"[{self.service_name}] {message}")
                    elif "app_unavailable" in message.lower():
                        logger.warning(
                            f"[{self.service_name}] Apple app not available - will retry"
                        )
                    else:
                        logger.info(
                            f"[{self.service_name}] Sync check complete (no new items)"
                        )

                    # Reset failure count on success
                    if errors == 0:
                        self.consecutive_failures = 0
                        self.email_sent = False

                except Exception as e:
                    self.handle_error(f"Sync operation failed: {e}")

                # Calculate sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0, self.interval - elapsed)

                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info(f"[{self.service_name}] Sync worker stopped by user")
        finally:
            self.running = False
            logger.info(f"[{self.service_name}] Sync worker stopped")


class CalendarSyncWorker(PATSyncWorker):
    """Sync events from Apple Calendar to pat-core"""

    def __init__(self, interval: int = 3600):
        super().__init__("calendar", interval)
        self.calendar_name = "PAT-cal"

    def sync(self) -> dict:
        """Sync from Apple Calendar"""
        logger.info(f"[calendar] Syncing from Apple Calendar '{self.calendar_name}'...")

        # Create Apple Calendar directory to list calendar events
        script = f"""
        tell application "Calendar"
            tell calendar "{self.calendar_name}"
                set eventList to every event whose start date is greater than (current date) - (72 * hours)
                set idList to {{
                }}
                repeat with currentEvent in eventList
                    set end of idList to uid of currentEvent
                end repeat
                return idList
            end tell
        end tell
        """

        apple_ids = self.run_applescript(script)

        if not apple_ids:
            return {
                "synced": 0,
                "updated": 0,
                "errors": 1,
                "message": "[calendar] No events found or Calendar app unavailable",
            }

        # Parse AppleScript list format
        if apple_ids.startswith("{") and apple_ids.endswith("}"):
            apple_ids_list = apple_ids[1:-1].split(", ")
        else:
            apple_ids_list = [apple_ids]

        logger.info(f"[calendar] Found {len(apple_ids_list)} events in Apple Calendar")

        # Call PAT Core sync API
        result = self.call_api(
            f"/pat/calendar/sync?calendar_name={self.calendar_name}&hours_back=72",
            method="POST",
        )

        logger.info(f"[calendar] PAT Core sync result: {result}")

        return result


class EmailSyncWorker(PATSyncWorker):
    """Sync emails from Apple Mail to pat-core"""

    def __init__(self, interval: int = 300):
        super().__init__("email", interval)

    def sync(self) -> dict:
        """Sync from Apple Mail"""
        logger.info(f"[email] Syncing from Apple Mail...")

        # List recent emails from INBOX
        script = """
        tell application "Mail"
            tell inbox
                set messageList to every message
                set idList to {{
                }}
                repeat with currentMessage in first 100 items of messageList
                    set end of idList to message id of currentMessage
                end repeat
                return idList
            end tell
        end tell
        """

        apple_ids = self.run_applescript(script)

        if not apple_ids:
            return {
                "synced": 0,
                "updated": 0,
                "errors": 1,
                "message": "[email] No emails found or Mail app unavailable",
            }

        # Parse AppleScript list format
        if apple_ids.startswith("{") and apple_ids.endswith("}"):
            apple_ids_list = apple_ids[1:-1].split(", ")
        else:
            apple_ids_list = [apple_ids]

        logger.info(f"[email] Found {len(apple_ids_list)} emails in INBOX")

        # Call PAT Core sync API
        result = self.call_api("/pat/emails/sync?limit=100", method="POST")

        logger.info(f"[email] PAT Core sync result: {result}")

        return result


class RemindersSyncWorker(PATSyncWorker):
    """Sync reminders from Apple Reminders to pat-core"""

    def __init__(self, interval: int = 600):
        super().__init__("reminders", interval)

    def sync(self) -> dict:
        """Sync from Apple Reminders"""
        logger.info(f"[reminders] Syncing from Apple Reminders...")

        # List all reminders
        script = """
        tell application "Reminders"
            set allLists to name of every list
            set idList to {{
            }}
            repeat with currentList in allLists
                try
                    set listRef to list currentList
                    set allReminders to every reminder of listRef
                    repeat with currentReminder in allReminders
                        set end of idList to id of currentReminder
                    end repeat
                end try
            end repeat
            return idList
        end tell
        """

        apple_ids = self.run_applescript(script)

        if not apple_ids:
            return {
                "synced": 0,
                "updated": 0,
                "errors": 1,
                "message": "[reminders] No reminders found or Reminders app unavailable",
            }

        # Parse AppleScript list format
        if apple_ids.startswith("{") and apple_ids.endswith("}"):
            apple_ids_list = apple_ids[1:-1].split(", ")
        else:
            apple_ids_list = [apple_ids]

        logger.info(f"[reminders] Found {len(apple_ids_list)} reminders")

        # Call PAT Core sync API
        result = self.call_api("/pat/tasks/sync?limit=100", method="POST")

        logger.info(f"[reminders] PAT Core sync result: {result}")

        return result


def main():
    parser = argparse.ArgumentParser(
        description="PAT Core Sync Worker - Run on macOS host",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test single syncs
  python3 scripts/pat_sync_worker.py --service=calendar --once
  python3 scripts/pat_sync_worker.py --service=email --once
  python3 scripts/pat_sync_worker.py --service=reminders --once
  
  # Run continuous workers (in background)
  python3 scripts/pat_sync_worker.py --service=calendar --interval=3600 &
  python3 scripts/pat_sync_worker.py --service=email --interval=300 &
  python3 scripts/pat_sync_worker.py --service=reminders --interval=600 &
        """,
    )
    parser.add_argument(
        "--service",
        choices=["calendar", "email", "reminders"],
        help="Service to sync",
        required=True,
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Sync interval in seconds (default: 300)",
    )
    parser.add_argument(
        "--once", action="store_true", help="Run once and exit (for testing)"
    )

    args = parser.parse_args()

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Create worker
    workers = {
        "calendar": CalendarSyncWorker,
        "email": EmailSyncWorker,
        "reminders": RemindersSyncWorker,
    }

    # Set default intervals
    if args.interval == 300:  # Default
        interval_map = {"calendar": 3600, "email": 300, "reminders": 600}
        worker_interval = interval_map.get(args.service, args.interval)
    else:
        worker_interval = args.interval

    worker = workers[args.service](interval=worker_interval)

    if args.once:
        result = worker.sync()
        print(json.dumps(result, indent=2, default=str))
    else:
        worker.start()


if __name__ == "__main__":
    main()
