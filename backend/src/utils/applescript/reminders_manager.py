#!/usr/bin/env python3
"""
Reminders Manager

Provides CRUD operations for Apple Reminders using AppleScript.
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.utils.applescript.base_manager import execute_applescript, AppleScriptError

logger = logging.getLogger(__name__)


class RemindersManager:
    """Manager for interacting with Apple Reminders via AppleScript."""

    TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates", "reminders")

    @classmethod
    def _load_template(cls, template_name: str) -> str:
        """Load an AppleScript template from the templates directory."""
        template_path = os.path.join(cls.TEMPLATES_DIR, f"{template_name}.applescript")
        try:
            with open(template_path, "r") as file:
                return file.read()
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            raise AppleScriptError(
                f"Template {template_name} not found or could not be read."
            )

    @classmethod
    def create_reminder(
        cls,
        title: str,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
        priority: Optional[int] = None,
        list_name: Optional[str] = None,
    ) -> str:
        """
        Create a new reminder in Apple Reminders.
        """
        try:
            template = cls._load_template("create_reminder")

            # Format due_date for AppleScript
            due_date_str = ""
            if due_date:
                try:
                    due_date_obj = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
                    due_date_str = due_date_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
                except ValueError:
                    due_date_str = ""

            # Prepare AppleScript
            notes_safe = (notes or "").replace('"', '\\"')
            priority_safe = str(priority) if priority else ""
            list_name_safe = (list_name or "").replace('"', '\\"')

            script = (
                template
                + f'\ncreate_reminder("{title}", "{due_date_str}", "{notes_safe}", "{priority_safe}", "{list_name_safe}")'
            )
            result = execute_applescript(script)
            logger.info(f"Created reminder with ID: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to create reminder: {e}")
            raise AppleScriptError(f"Failed to create reminder: {str(e)}")

    @classmethod
    def get_reminders(
        cls,
        start_date: str,
        end_date: str,
        list_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get reminders from Apple Reminders within a date range.
        """
        try:
            template = cls._load_template("get_reminders")

            # Format dates for AppleScript
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")

            start_date_str = start_date_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
            end_date_str = end_date_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")

            # Prepare AppleScript
            list_name_safe = (list_name or "").replace('"', '\\"')
            script = (
                template
                + f'\nget_reminders("{start_date_str}", "{end_date_str}", "{list_name_safe}")'
            )
            result = execute_applescript(script)

            # Parse the result
            reminders = cls._parse_reminders_result(result)
            logger.info(f"Fetched {len(reminders)} reminders")
            return reminders
        except Exception as e:
            logger.error(f"Failed to fetch reminders: {e}")
            raise AppleScriptError(f"Failed to fetch reminders: {str(e)}")

    @classmethod
    def update_reminder(
        cls,
        reminder_id: str,
        new_title: Optional[str] = None,
        new_due_date: Optional[str] = None,
        new_notes: Optional[str] = None,
        new_priority: Optional[int] = None,
        new_completed: Optional[bool] = None,
    ) -> str:
        """
        Update an existing reminder in Apple Reminders.
        """
        try:
            template = cls._load_template("update_reminder")

            # Format due_date for AppleScript
            due_date_str = ""
            if new_due_date:
                try:
                    due_date_obj = datetime.strptime(new_due_date, "%Y-%m-%d %H:%M:%S")
                    due_date_str = due_date_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
                except ValueError:
                    due_date_str = ""

            # Prepare AppleScript
            new_title_safe = (new_title or "").replace('"', '\\"')
            new_notes_safe = (new_notes or "").replace('"', '\\"')
            new_priority_safe = str(new_priority) if new_priority else ""
            new_completed_safe = (
                str(new_completed).lower() if new_completed is not None else ""
            )

            script = (
                template
                + f'\nupdate_reminder("{reminder_id}", "{new_title_safe}", "{due_date_str}", "{new_notes_safe}", "{new_priority_safe}", "{new_completed_safe}")'
            )
            result = execute_applescript(script)
            logger.info(f"Updated reminder with ID: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to update reminder: {e}")
            raise AppleScriptError(f"Failed to update reminder: {str(e)}")

    @classmethod
    def delete_reminder(cls, reminder_id: str) -> str:
        """
        Delete a reminder from Apple Reminders.
        """
        try:
            template = cls._load_template("delete_reminder")
            script = template + f'\ndelete_reminder("{reminder_id}")'
            result = execute_applescript(script)
            logger.info(f"Deleted reminder with ID: {reminder_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete reminder: {e}")
            raise AppleScriptError(f"Failed to delete reminder: {str(e)}")

    @staticmethod
    def _parse_reminders_result(result: str) -> List[Dict[str, Any]]:
        """
        Parse the result from AppleScript into a list of dictionaries.
        """
        reminders = []
        if not result:
            return reminders

        # Split records (simplified logic)
        records = result.strip()[1:-1].split("}, {")
        for record in records:
            try:
                reminder = {}
                parts = record.split(", ")
                for part in parts:
                    if ":" in part:
                        key, value = part.split(":", 1)
                        key = key.strip()
                        value = value.strip()

                        # Clean up values
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith('date "') and value.endswith('"'):
                            value = value[6:-1]
                        elif value.lower() in ["true", "false"]:
                            value = value.lower() == "true"
                        elif value.isdigit():
                            value = int(value)

                        reminder[key] = value
                reminders.append(reminder)
            except Exception as e:
                logger.warning(f"Failed to parse reminder record: {record}. Error: {e}")
        return reminders
