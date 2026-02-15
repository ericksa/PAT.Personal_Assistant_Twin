"""
Permission validator for MCP tool execution requests.
"""

from typing import List


class PermissionValidator:
    """
    Simple permission validator that checks if a given tool name is allowed.
    The whitelist can be extended or loaded from configuration in the future.
    """

    # Hard-coded whitelist of allowed tool names
    _WHITELIST: List[str] = [
        "calendar.list_events",
        "calendar.create_event",
        # Add more allowed tools here as needed
    ]

    def is_allowed(self, tool_name: str) -> bool:
        """
        Check if the provided tool_name is in the whitelist.

        Args:
            tool_name: The name of the tool to validate.

        Returns:
            True if the tool is allowed, False otherwise.
        """
        # Normalise the tool name (strip whitespace, lower case) if desired
        normalized_name = tool_name.strip()
        return normalized_name in self._WHITELIST

    def get_allowed_tools(self) -> List[str]:
        """
        Return the current list of allowed tool names.
        Useful for debugging or introspection.
        """
        return list(self._WHITELIST)