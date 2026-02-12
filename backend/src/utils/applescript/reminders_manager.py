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

    TEMPLATES_DIR = os.path.join(
        os.path.dirname(__file__), "templates", "reminders"
    )

    @classmethod
    def _load_template(cls, template_name: str) -> str:
        """Load an AppleScript template from the templates directory."""
        template_path = os.path.join(cls.TEMPLATES_DIR, f"{template_name}.applescript")
        try:
            with open(template_path, "r") as file:
                return file.read()
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            raise AppleScriptError(f"Template {template_name} not found or could not be read.")

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

        Args:
            title: Title of the reminder.
            due_date: Due date in "YYYY-MM-DD HH:MM:SS" format.
            notes: Notes for the reminder.
            priority: Priority (1=high, 2=medium, 3=low, 9=none).
            list_name: Name of the list to add the reminder to.

        Returns:
            ID of the created reminder.

        Raises:
            AppleScriptError: If the reminder could not be created.
        """
        try:
            template = cls._load_template("create_reminder")
            
            # Format due_date for AppleScript
            due_date_str = """
            if due_date:
                try:
                    due_date_obj = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
                    due_date_str = due_date_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
                except ValueError:
                    due_date_str = ""
            
            # Prepare AppleScript
            script = template + f'\ncreate_reminder("{title}", "{due_date_str}", "{notes or ''}", "{priority or ''}", "{list_name or ''}")'
            result = execute_applescript(script)
            logger.info(f"Created reminder with ID: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create reminder: {e}")
            raise AppleScriptError(f"Failed to create reminder: {e}")

    @classmethod
    def get_reminders(
        cls,
        start_date: str,
        end_date: str,
        list_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get reminders from Apple Reminders within a date range.

        Args:
            start_date: Start date in "YYYY-MM-DD HH:MM:SS" format.
            end_date: End date in "YYYY-MM-DD HH:MM:SS" format.
            list_name: Name of the list to fetch reminders from.

        Returns:
            List of reminders, each represented as a dictionary.

        Raises:
            AppleScriptError: If reminders could not be fetched.
        """
        try:
            template = cls._load_template("get_reminders")
            
            # Format dates for AppleScript
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
            
            start_date_str = start_date_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
            end_date_str = end_date_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
            
            # Prepare AppleScript
            script = template + f'\nget_reminders("{start_date_str}", "{end_date_str}", "{list_name or ''}")'
            result = execute_applescript(script)
            
            # Parse the result (AppleScript returns a list of records)
            reminders = cls._parse_reminders_result(result)
            logger.info(f"Fetched {len(reminders)} reminders")
            return reminders
            
        except Exception as e:
            logger.error(f"Failed to fetch reminders: {e}")
            raise AppleScriptError(f"Failed to fetch reminders: {e}")

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

        Args:
            reminder_id: ID of the reminder to update.
            new_title: New title for the reminder.
            new_due_date: New due date in "YYYY-MM-DD HH:MM:SS" format.
            new_notes: New notes for the reminder.
            new_priority: New priority (1=high, 2=medium, 3=low, 9=none).
            new_completed: New completion status.

        Returns:
            ID of the updated reminder.

        Raises:
            AppleScriptError: If the reminder could not be updated.
        """
        try:
            template = cls._load_template("update_reminder")
            
            # Format due_date for AppleScript
            due_date_str = """
            if new_due_date:
                try:
                    due_date_obj = datetime.strptime(new_due_date, "%Y-%m-%d %H:%M:%S")
                    due_date_str = due_date_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
                except ValueError:
                    due_date_str = ""
            
            # Prepare AppleScript
            script = template + f'\nupdate_reminder("{reminder_id}", "{new_title or ''}", "{due_date_str}", "{new_notes or ''}", "{new_priority or ''}", "{new_completed or ''}")'
            result = execute_applescript(script)
            logger.info(f"Updated reminder with ID: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update reminder: {e}")
            raise AppleScriptError(f"Failed to update reminder: {e}")

    @classmethod
    def delete_reminder(cls, reminder_id: str) -> str:
        """
        Delete a reminder from Apple Reminders.

        Args:
            reminder_id: ID of the reminder to delete.

        Returns:
            Confirmation message.

        Raises:
            AppleScriptError: If the reminder could not be deleted.
        """
        try:
            template = cls._load_template("delete_reminder")
            
            # Prepare AppleScript
            script = template + f'\ndelete_reminder("{reminder_id}")'
            result = execute_applescript(script)
            logger.info(f"Deleted reminder with ID: {reminder_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete reminder: {e}")
            raise AppleScriptError(f"Failed to delete reminder: {e}")

    @staticmethod
    def _parse_reminders_result(result: str) -> List[Dict[str, Any]]:
        """
        Parse the result from AppleScript into a list of dictionaries.
        
        Args:
            result: Raw output from AppleScript.

        Returns:
            List of reminders as dictionaries.
        """
        reminders = []
        if not result:
            return reminders
        
        # AppleScript returns records in the format:
        # {id:"id1", name:"title1", due date:date "...", body:"notes1", priority:1, completed:false}
        # This is a simplified parser for demonstration.
        # In a real implementation, you would need a more robust parser.
        
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
                        if value.startswith("\"") and value.endswith("\""):
                            value = value[1:-1]
                        elif value.startswith("date \"") and value.endswith("\""):
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


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create a reminder
    reminder_id = RemindersManager.create_reminder(
        title="Test Reminder",
        due_date="2026-02-15 12:00:00",
        notes="This is a test reminder.",
        priority=1,
        list_name="Test List"
    )
    print(f"Created reminder with ID: {reminder_id}")
    
    # Get reminders
    reminders = RemindersManager.get_reminders(
        start_date="2026-02-10 00:00:00",
        end_date="2026-02-20 23:59:59",
        list_name="Test List"
    )
    print(f"Fetched reminders: {reminders}")
    
    # Update reminder
    if reminders:
        updated_id = RemindersManager.update_reminder(
            reminder_id=reminder_id,
            new_title="Updated Test Reminder",
            new_notes="This is an updated test reminder."
        )
        print(f"Updated reminder with ID: {updated_id}")
    
    # Delete reminder
    delete_result = RemindersManager.delete_reminder(reminder_id)
    print(delete_result)
