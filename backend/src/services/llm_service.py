# src/services/llm_service.py - LLM Service using Llama 3.2 3B via Ollama
import httpx
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.config.llm_config import LLMConfig

logger = logging.getLogger(__name__)


class LlamaLLMService:
    """Service for interacting with Llama 3.2 3B via Ollama"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.client = httpx.AsyncClient(timeout=120.0)

    async def _make_request(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        format_json: bool = False,
    ) -> str:
        """
        Helper to make Ollama API request.

        Args:
            prompt: The user prompt
            system_prompt: Optional system message
            temperature: sampling temperature
            max_tokens: maximum tokens to generate
            format_json: return JSON format

        Returns:
            Generated text
        """
        try:
            payload = {
                "model": self.config.MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                    if temperature is not None
                    else self.config.TEMPERATURE,
                    "top_p": self.config.TOP_P,
                    "num_ctx": self.config.NUM_CTX_llama32_3b,
                },
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            if format_json:
                payload["format"] = "json"

            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt

            logger.info(f"Sending request to Ollama: {self.config.API_URL}")

            response = await self.client.post(self.config.API_URL, json=payload)

            if response.status_code == 200:
                data = response.json()
                result = data.get("response", "").strip()
                logger.info(f"Got response from Ollama: {len(result)} characters")
                return result
            else:
                logger.error(
                    f"Ollama API error: {response.status_code} - {response.text}"
                )
                raise Exception(f"Ollama error: {response.status_code}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode Ollama response: {e}")
            raise Exception(f"Invalid JSON from Ollama: {e}")
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise

    async def chat_completion(
        self, messages: List[Dict[str, str]], temperature: Optional[float] = None
    ) -> str:
        """
        Get chat completion from LLM.

        Args:
            messages: List of chat messages with 'role' and 'content'
                    Examples: [{"role": "user", "content": "Hello"}]
            temperature: optional temperature override

        Returns:
            Generated response text
        """
        # Build prompt from messages
        system_msg = None
        user_prompt = ""

        for msg in messages:
            if msg.get("role") == "system":
                system_msg = msg.get("content")
            else:
                user_prompt += f"{msg['role'].upper()}: {msg['content']}\n"

        # Add assistant prompt to trigger response
        user_prompt += "ASSISTANT:"

        return await self._make_request(
            prompt=user_prompt, system_prompt=system_msg, temperature=temperature
        )

    async def completion_with_structured_output(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get structured JSON output from LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system message
            schema: Example JSON schema (for guidance)

        Returns:
            Parsed JSON dictionary
        """
        resp_text = ""
        try:
            # Add structured output instruction to prompt
            enhanced_prompt = f"""{prompt}

IMPORTANT: Respond in JSON format only."""

            if schema:
                enhanced_prompt += f"""
Use this schema as a template:
{json.dumps(schema, indent=2)}"""

            resp_text = await self._make_request(
                prompt=enhanced_prompt, system_prompt=system_prompt, format_json=True
            )

            # Parse the JSON response
            result = json.loads(resp_text)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON output: {e}")
            # Try to extract JSON from response if it's wrapped
            if "{:" in resp_text:
                start = resp_text.find("{:")
                end = resp_text.rfind("}") + 1
                try:
                    return json.loads(resp_text[start:end])
                except:
                    logger.error(f"Failed to extract JSON from response")
            raise Exception(f"LLM did not return valid JSON: {e}")

    # ===== EMAIL AI FEATURES =====

    async def classify_email(
        self, subject: str, sender: str, body: str
    ) -> Dict[str, Any]:
        """
        Classify email using Llama 3.2.

        Returns:
            Dict with category, priority (0-10), requires_action, reasoning
        """
        system_prompt = """You are an email classification assistant. Classify emails into categories and assign priorities."""

        prompt = f"""Classify this email:

Subject: {subject}
From: {sender}
Body: {body[:2000]}...  # Truncate to fit context

Categories: work, personal, urgent, newsletter, spam, notification, marketing, social, financial, travel

Assign priority (0-10):
- 0-3: Low, can wait or ignore
- 4-7: Medium, respond within a day
- 8-10: High, requires immediate attention

Determine if email requires action (true/false).

Respond in JSON:
{{"category": "...", "priority": 0-10, "requires_action": true/false, "reasoning": "..."}}"""

        result_str = await self._make_request(
            prompt=prompt, system_prompt=system_prompt, format_json=True
        )
        try:
            return json.loads(result_str)
        except:
            return {
                "category": "personal",
                "priority": 0,
                "requires_action": False,
                "reasoning": "Error parsing LLM response",
            }

    async def summarize_email(self, subject: str, body: str) -> str:
        """
        Generate concise email summary (~200 characters).
        """
        prompt = f"""Summarize this email in 1-2 sentences (under 200 characters):

Subject: {subject}
Body: {body[:3000]}...

Summary:"""

        return await self._make_request(prompt=prompt)

    async def draft_email_reply(
        self,
        subject: str,
        sender: str,
        body: str,
        tone: str = "professional",
        context: Optional[str] = None,
    ) -> str:
        """
        Draft reply to email.

        Args:
            subject: Email subject
            sender: Sender email/name
            body: Email body
            tone: Desired tone (professional, casual, formal, friendly)
            context: Additional context from thread

        Returns:
            Draft email body
        """
        context_str = f"\nContext: {context}" if context else ""

        prompt = f"""Draft a reply to this email. Tone: {tone}

Subject: {subject}
From: {sender}
Full Email:
{body[:3000]}
{context_str}

Draft reply (start with appropriate greeting):"""

        return await self._make_request(prompt=prompt)

    async def extract_tasks(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract action items and tasks from text.

        Returns:
            List of tasks with title, priority, due_date (if mentioned)
        """
        system_prompt = "You extract action items and tasks from text."

        prompt = f"""Extract all action items and tasks from this text:

{text[:3000]}...

For each task, extract:
- task: What needs to be done
- due_date: Due date if mentioned (YYYY-MM-DD format)
- priority: Implied priority (0-10)

Respond in JSON array:
[{{"task": "...", "due_date": "...", "priority": 0-10}}]"""

        result = await self._make_request(prompt, format_json=True)
        try:
            res = json.loads(result)
            return res if isinstance(res, list) else []
        except:
            return []

    async def extract_meeting_details(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract meeting details from text.

        Returns:
            Dict with title, date, time, location, attendees, or None
        """
        system_prompt = "You extract meeting details from emails or text."

        prompt = f"""Extract meeting details from this text. If not a meeting/instruction, return null:

{text[:3000]}...

Extract:
- title: meeting title
- date: date (YYYY-MM-DD)
- time: time (HH:MM)
- location: location (if any)
- duration_minutes: estimated duration
- attendees: list of emails/names

Respond in JSON, or "null" if this isn't a meeting."""

        result = await self._make_request(prompt, format_json=True)

        if not result or result.lower() == "null":
            return None

        try:
            return json.loads(result)
        except:
            return None

    # ===== CALENDAR AI FEATURES =====

    async def suggest_optimal_time(
        self,
        duration_minutes: int,
        date: str,
        existing_events: List[Dict[str, str]],
        preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Suggest optimal meeting time using AI.

        Args:
            duration_minutes: Meeting duration
            date: Date in YYYY-MM-DD format
            existing_events: List of existing events for that day
            preferences: User schedule preferences

        Returns:
            Dict with suggested_time, confidence, reasoning
        """
        events_json = json.dumps(existing_events, indent=2)
        prefs_json = json.dumps(preferences, indent=2)

        prompt = f"""Given these constraints, suggest the optimal time for a {duration_minutes}-minute meeting on {date}:

Current schedule:
{events_json}

User preferences:
{prefs_json}

Suggest a time slot that:
1. Does not overlap existing events
2. Respects travel time and preparation buffers ({preferences.get("min_time_between_meetings_minutes", 15)} mins)
3. Aligns with peak productivity hours: {preferences.get("peak_productivity_hours", [])}
4. Avoids first/last work hours if preferred
5. Considers lunch break: {preferences.get("break_start_time", "12:00")} - {preferences.get("break_end_time", "13:00")}

Respond in JSON:
{{"suggested_time": "YYYY-MM-DD HH:MM", "confidence": 0.0-1.0, "reasoning": "..."}}"""

        result = await self._make_request(prompt, format_json=True)
        try:
            return (
                json.loads(result)
                if result
                else {
                    "suggested_time": None,
                    "confidence": 0.0,
                    "reasoning": "Unable to determine",
                }
            )
        except:
            return {
                "suggested_time": None,
                "confidence": 0.0,
                "reasoning": "Error parsing response",
            }

    async def detect_conflicts_upcoming(
        self, events: List[Dict[str, Any]], days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Predict conflicts before they happen.

        Returns:
            List of predicted conflicts
        """
        events_json = json.dumps(events, indent=2)

        prompt = f"""Analyze these upcoming events and identify potential conflicts within the next {days_ahead} days:
{events_json}

Identify:
1. Time overlaps
2. Travel time conflicts (events back-to-back in different locations)
3. Preparation time needs
4. Unrealistic scheduling

For each conflict, provide:
- event1_index: index of first event
- event2_index: index of second event (if applicable)
- conflict_type: overlap, travel_time, preparation
- severity: low, medium, high
- description: explanation

Respond in JSON array or [] if no conflicts."""

        result = await self._make_request(prompt, format_json=True)
        try:
            conflicts = json.loads(result)
            return conflicts if isinstance(conflicts, list) else []
        except:
            return []

    async def optimize_daily_schedule(
        self,
        date: str,
        current_schedule: List[Dict[str, str]],
        preferences: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        AI-powered daily schedule optimization.

        Returns:
            Optimization suggestions with reasoning
        """
        schedule_json = json.dumps(current_schedule, indent=2)
        prefs_json = json.dumps(preferences, indent=2)

        prompt = f"""Optimize this daily schedule for {date}:

Current schedule:
{schedule_json}

User preferences:
{prefs_json}

Consider:
- Meeting went long? Adjust subsequent times
- Travel time between locations
- Energy peaks: morning focus, afternoon execution
- Buffer times needed
- Task priorities
- Deep work blocks
- Reduce meeting load if excessive

Respond in JSON:
{{"optimization_summary": "...", "suggested_changes": [{{"event": "...", "change": "...", "reason": "..."}}], "new_schedule": [...], "reasoning": "..."}}"""

        result = await self._make_request(prompt, format_json=True)
        try:
            return (
                json.loads(result)
                if result
                else {
                    "optimization_summary": "No changes needed",
                    "suggested_changes": [],
                    "new_schedule": current_schedule,
                    "reasoning": "",
                }
            )
        except:
            return {
                "optimization_summary": "Error parsing optimization",
                "suggested_changes": [],
                "new_schedule": current_schedule,
                "reasoning": "Parse error",
            }

    # ===== TASK AI FEATURES =====

    async def suggest_task_priorities(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        AI priority scoring for tasks.

        Returns:
            Dict mapping task_id to priority score (0-10)
        """
        tasks_json = json.dumps(tasks, indent=2)

        prompt = f"""Score these tasks by priority (0-10):

{tasks_json}

Consider:
- Urgency (due dates)
- Importance (impact)
- Dependencies (blocking others)
- Effort required

For each task, provide priority score.

Respond in JSON:
{{"task_index_0": 0-10, "task_index_1": 0-10, ...}}"""

        result = await self._make_request(prompt, format_json=True)
        try:
            priorities = json.loads(result)
        except:
            priorities = {}

        # Map back to task IDs
        task_priorities = {}
        for i, task in enumerate(tasks):
            key = f"task_index_{i}"
            if key in priorities:
                task_priorities[str(task.get("id", i))] = int(priorities[key])

        return task_priorities

    async def suggest_task_order(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """
        Suggest optimal task completion order.

        Returns:
            List of task IDs in optimal order
        """
        task_list = "\n".join(
            [
                f"- {t.get('title', f'Task {i}')} (due: {t.get('due_date', 'none')}, priority: {t.get('priority', 0)})"
                for i, t in enumerate(tasks)
            ]
        )

        prompt = f"""Suggest the optimal order to complete these tasks:

{task_list}

Consider:
- Dependencies (must do X before Y)
- Due dates
- Priorities
- Energy required (hard tasks vs easy tasks)
- Focus vs interrupt tasks

Respond in JSON array of task titles in optimal order:
["Task Title 1", "Task Title 2", ...]"""

        result = await self._make_request(prompt, format_json=True)

        try:
            order = json.loads(result)
            # Map titles back to IDs
            title_to_id = {
                str(t.get("title")): str(t.get("id")) for t in tasks if t.get("id")
            }
            return [
                title_to_id.get(title, title) for title in order if title in title_to_id
            ]
        except:
            return [
                str(t.get("id")) for t in tasks if t.get("id")
            ]  # Return original order as fallback

    # ===== GENERAL =====

    async def test_connection(self) -> bool:
        """Test connection to Ollama"""
        try:
            prompt = "Hello! Respond with just 'OK'."
            response = await self._make_request(prompt)
            return "OK" in response.upper()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
