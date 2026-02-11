from typing import Optional, List, Any
import subprocess
import logging
import re

logger = logging.getLogger(__name__)


class AppleScriptManager:
    """Manager for executing AppleScript commands on macOS"""

    def __init__(self):
        self.is_macos = None

    def _check_platform(self) -> bool:
        """Check if running on macOS"""
        if self.is_macos is None:
            import platform

            self.is_macos = platform.system() == "Darwin"
        return self.is_macos

    async def run_applescript(self, script: str, *args) -> Optional[Any]:
        """Execute an AppleScript command"""
        if not self._check_platform():
            logger.warning("AppleScript is only available on macOS")
            return None

        try:
            formatted_script = script

            for i, arg in enumerate(args, 1):
                safe_arg = str(arg).replace('"', '\\"')
                formatted_script = formatted_script.replace(f"{{{i}}}", safe_arg)

            result = subprocess.run(
                ["osascript", "-e", formatted_script],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.error(f"AppleScript error: {result.stderr}")
                return None

            return self._parse_output(result.stdout)

        except subprocess.TimeoutExpired:
            logger.error("AppleScript execution timed out")
            return None
        except Exception as e:
            logger.error(f"AppleScript execution failed: {e}")
            return None

    def _parse_output(self, output: str) -> any:
        """Parse AppleScript output"""
        output = output.strip()

        if not output:
            return None

        if output.startswith("{") and output.endswith("}"):
            try:
                import json

                try:
                    return json.loads(
                        output.replace(":", '":"')
                        .replace(", ", ',"')
                        .replace("{", '{"')
                        .replace("}", '"}')
                    )
                except:
                    return self._parse_applescript_dict(output)
            except:
                pass

        if output.startswith("[") and output.endswith("]"):
            try:
                import json

                json_str = output
                json_str = json_str.replace(", ", ",")
                return json.loads(json_str)
            except:
                pass

        if "," in output:
            parts = output.split(", ")
            if len(parts) > 1:
                return parts

        return output

    def _parse_applescript_dict(self, output: str) -> dict:
        """Parse AppleScript dictionary format"""
        result = {}

        pattern = r"([^:]+):\s*([^,\}]*)"
        matches = re.findall(pattern, output.strip("{}"))

        for key, value in matches:
            key = key.strip().strip('"')
            value = value.strip().strip('"')
            result[key] = value

        return result

    async def test_calendar_access(self) -> dict:
        """Test access to Apple Calendar"""
        script = """
        tell application "Calendar"
            activate
            return name of every calendar
        end tell
        """

        result = await self.run_applescript(script)

        return {
            "success": result is not None,
            "calendars": result
            if isinstance(result, list)
            else ([result] if result else []),
        }

    async def test_mail_access(self) -> dict:
        """Test access to Apple Mail"""
        script = """
        tell application "Mail"
            activate
            set msgCount to count of messages of inbox
            return msgCount
        end tell
        """

        result = await self.run_applescript(script)

        return {
            "success": result is not None,
            "inbox_count": result if isinstance(result, int) else 0,
        }

    async def test_reminders_access(self) -> dict:
        """Test access to Apple Reminders"""
        script = """
        tell application "Reminders"
            activate
            return name of every list
        end tell
        """

        result = await self.run_applescript(script)

        return {
            "success": result is not None,
            "lists": result
            if isinstance(result, list)
            else ([result] if result else []),
        }
