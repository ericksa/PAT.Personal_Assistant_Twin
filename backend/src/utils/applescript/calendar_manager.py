#!/usr/bin/env python3
"""
Calendar Manager

Provides CRUD operations for Apple Calendar using AppleScript.
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.utils.applescript.base_manager import execute_applescript, AppleScriptError

logger = logging.getLogger(__name__)


class CalendarManager:
    """Manager for interacting with Apple Calendar via AppleScript."""

    TEMPLATES_DIR = os.path.join(
        os.path.dirname(__file__), "templates", "calendar"
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
    def create_event(
        cls,
        title: str,
        start_time: str,
        end_time: str,
        calendar_name: str,
        location: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """
        Create a new event in Apple Calendar.

        Args:
            title: Title of the event.
            start_time: Start time in "YYYY-MM-DD HH:MM:SS" format.
            end_time: End time in "YYYY-MM-DD HH:MM:SS" format.
            calendar_name: Name of the calendar to add the event to.
            location: Location of the event.
            notes: Notes for the event.

        Returns:
            ID of the created event.

        Raises:
            AppleScriptError: If the event could not be created.
        """
        try:
            template = cls._load_template("create_event")
            
            # Format dates for AppleScript
            start_time_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_time_obj = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            
            start_time_str = start_time_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
            end_time_str = end_time_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
            
            # Prepare AppleScript
            script = template + f'\ncreate_event("{title}", "{start_time_str}", "{end_time_str}", "{location or ''}", "{notes or ''}", "{calendar_name}")'
            result = execute_applescript(script)
            logger.info(f"Created event with ID: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise AppleScriptError(f"Failed to create event: {e}")

    @classmethod
    def get_events(
        cls,
        start_time: str,
        end_time: str,
        calendar_name: str,
    ) -> List[Dict[str, Any]]:
        """
        Get events from Apple Calendar within a date range.

        Args:
            start_time: Start time in "YYYY-MM-DD HH:MM:SS" format.
            end_time: End time in "YYYY-MM-DD HH:MM:SS" format.
            calendar_name: Name of the calendar to fetch events from.

        Returns:
            List of events, each represented as a dictionary.

        Raises:
            AppleScriptError: If events could not be fetched.
        """
        try:
            template = cls._load_template("get_events")
            
            # Format dates for AppleScript
            start_time_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_time_obj = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            
            start_time_str = start_time_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
            end_time_str = end_time_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
            
            # Prepare AppleScript
            script = template + f'\nget_events("{start_time_str}", "{end_time_str}", "{calendar_name}")'
            result = execute_applescript(script)
            
            # Parse the result (AppleScript returns a list of records)
            events = cls._parse_events_result(result)
            logger.info(f"Fetched {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            raise AppleScriptError(f"Failed to fetch events: {e}")

    @classmethod
    def update_event(
        cls,
        event_id: str,
        new_title: Optional[str] = None,
        new_start_time: Optional[str] = None,
        new_end_time: Optional[str] = None,
        new_location: Optional[str] = None,
        new_notes: Optional[str] = None,
    ) -> str:
        """
        Update an existing event in Apple Calendar.

        Args:
            event_id: ID of the event to update.
            new_title: New title for the event.
            new_start_time: New start time in "YYYY-MM-DD HH:MM:SS" format.
            new_end_time: New end time in "YYYY-MM-DD HH:MM:SS" format.
            new_location: New location for the event.
            new_notes: New notes for the event.

        Returns:
            ID of the updated event.

        Raises:
            AppleScriptError: If the event could not be updated.
        """
        try:
            template = cls._load_template("update_event")
            
            # Format dates for AppleScript
            start_time_str = ""
            end_time_str = ""
            
            if new_start_time:
                start_time_obj = datetime.strptime(new_start_time, "%Y-%m-%d %H:%M:%S")
                start_time_str = start_time_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
            
            if new_end_time:
                end_time_obj = datetime.strptime(new_end_time, "%Y-%m-%d %H:%M:%S")
                end_time_str = end_time_obj.strftime("%A, %B %d, %Y at %I:%M:%S %p")
            
            # Prepare AppleScript
            script = template + f'\nupdate_event("{event_id}", "{new_title or ''}", "{start_time_str}", "{end_time_str}", "{new_location or ''}", "{new_notes or ''}")'
            result = execute_applescript(script)
            logger.info(f"Updated event with ID: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update event: {e}")
            raise AppleScriptError(f"Failed to update event: {e}")

    @classmethod
    def delete_event(cls, event_id: str) -> str:
        """
        Delete an event from Apple Calendar.

        Args:
            event_id: ID of the event to delete.

        Returns:
            Confirmation message.

        Raises:
            AppleScriptError: If the event could not be deleted.
        """
        try:
            template = cls._load_template("delete_event")
            
            # Prepare AppleScript
            script = template + f'\ndelete_event("{event_id}")'
            result = execute_applescript(script)
            logger.info(f"Deleted event with ID: {event_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete event: {e}")
            raise AppleScriptError(f"Failed to delete event: {e}")

    @staticmethod
    def _parse_events_result(result: str) -> List[Dict[str, Any]]:
        """
        Parse the result from AppleScript into a list of dictionaries.

        Args:
            result: Raw output from AppleScript.

        Returns:
            List of events as dictionaries.
        """
        events = []
        if not result:
            return events
        
        # AppleScript returns records in the format:
        # {id:"id1", summary:"title1", start date:date "...", end date:date "...", location:"location1", description:"notes1"}
        # This is a simplified parser for demonstration.
        # In a real implementation, you would need a more robust parser.
        
        # Split records (simplified logic)
        records = result.strip()[1:-1].split("}, {")
        for record in records:
            try:
                event = {}
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
                        
                        event[key] = value
                events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse event record: {record}. Error: {e}")
        
        return events


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create an event
    event_id = CalendarManager.create_event(
        title="Test Event",
        start_time="2026-02-15 12:00:00",
        end_time="2026-02-15 13:00:00",
        calendar_name="Test Calendar",
        location="Office",
        notes="This is a test event."
    )
    print(f"Created event with ID: {event_id}")
    
    # Get events
    events = CalendarManager.get_events(
        start_time="2026-02-10 00:00:00",
        end_time="2026-02-20 23:59:59",
        calendar_name="Test Calendar"
    )
    print(f"Fetched events: {events}")
    
    # Update event
    if events:
        updated_id = CalendarManager.update_event(
            event_id=event_id,
            new_title="Updated Test Event",
            new_notes="This is an updated test event."
        )
        print(f"Updated event with ID: {updated_id}")
    
    # Delete event
    delete_result = CalendarManager.delete_event(event_id)
    print(delete_result)
