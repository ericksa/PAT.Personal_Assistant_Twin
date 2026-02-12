#!/usr/bin/env python3
"""
AppleScript Manager Base
Provides utilities for executing AppleScript commands
"""

import subprocess
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AppleScriptError(Exception):
    """Custom exception for AppleScript errors"""

    pass


def execute_applescript(script: str) -> str:
    """
    Execute AppleScript command and return output.

    Args:
        script: AppleScript code to execute

    Returns:
        Output from AppleScript

    Raises:
        AppleScriptError if execution fails
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"AppleScript execution failed: {error_msg}")
            raise AppleScriptError(f"AppleScript error: {error_msg}")

        output = result.stdout.strip()
        logger.debug(
            f"AppleScript output: {output[:200]}..." if len(output) > 200 else output
        )
        return output

    except subprocess.TimeoutExpired:
        logger.error("AppleScript execution timed out")
        raise AppleScriptError("AppleScript execution timed out")
    except Exception as e:
        logger.error(f"Error executing AppleScript: {e}")
        raise AppleScriptError(f"Failed to execute AppleScript: {e}")


def list_calendars() -> List[str]:
    """Get list of all calendar names"""
    script = """
tell application "Calendar" to get the name of every calendar
"""
    try:
        result = execute_applescript(script)
        # Parse result: AppleScript returns list as comma-separated
        calendars = [cal.strip() for cal in result.split(",")]
        logger.info(f"Found {len(calendars)} calendars: {calendars}")
        return calendars
    except Exception as e:
        logger.error(f"Failed to list calendars: {e}")
        return []


def get_event_ids(
    calendar_name: str, start_date_str: str, end_date_str: str
) -> List[str]:
    """
    Get event IDs from calendar within date range.

    Args:
        calendar_name: Name of Apple calendar
        start_date_str: Start date in format compatible with AppleScript
        end_date_str: End date

    Returns:
        List of event IDs
    """
    script = f'''
tell application "Calendar"
    set eventIds to {{}}
    tell calendar "{calendar_name}"
        set startDate to date "{start_date_str}"
        set endDate to date "{end_date_str}"
        repeat with currentEvent in every event whose (start date ≥ startDate and start date ≤ endDate)
            set end of eventIds to id of currentEvent
        end repeat
    end tell
    return eventIds
end tell
'''
    try:
        result = execute_applescript(script)
        logger.info(f"Get event IDs from {calendar_name}: {result}")
        return []
    except Exception as e:
        logger.error(f"Failed to get event IDs: {e}")
        return []


class AppleScriptManager:
    """Manager for AppleScript operations"""

    async def run_applescript(self, script: str, *args) -> Any:
        """
        Execute AppleScript command and return result.

        Args:
            script: AppleScript code (f-string template)
            args: Arguments to format into script
        """
        formatted_script = script.format(*args) if args else script
        result = execute_applescript(formatted_script)

        # Try to parse as JSON if it looks like it
        if result.startswith("{") or result.startswith("["):
            try:
                return json.loads(result)
            except:
                pass

        # Split by comma if it looks like a list
        if "," in result and not ":" in result:
            return [x.strip() for x in result.split(",")]

        return result


if __name__ == "__main__":
    # Test listing calendars
    calendars = list_calendars()
    print(f"Calendars: {calendars}")
