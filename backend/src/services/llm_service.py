from typing import Dict, Any, List, Optional
import httpx
import asyncio


class LLMService:
    """Service for interacting with Llama 3.2 3B via Ollama"""

    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"
    ):
        self.base_url = base_url
        self.model = model

    async def classify_email(self, subject: str, body: str) -> Dict[str, Any]:
        """Classify an email using the LLM"""
        prompt = f"""
        Classify this email into one of these categories: work, personal, promotional, notification.

        Subject: {subject}
        Body: {body[:500]}

        Respond with JSON: {{"category": "category", "priority": "high|medium|low", "requires_action": true|false, "reasoning": "brief reason"}}
        """

        return await self._call_ollama(prompt)

    async def summarize_email(self, subject: str, body: str) -> Dict[str, Any]:
        """Summarize an email using the LLM"""
        prompt = f"""
        Summarize this concisely.

        Subject: {subject}
        Body: {body[:1000]}

        Respond with JSON: {{"summary": "2-3 sentence summary", "key_points": ["point1", "point2"]}}
        """

        return await self._call_ollama(prompt)

    async def draft_email_reply(
        self, subject: str, body: str, tone: str = "professional", context: str = ""
    ) -> Dict[str, Any]:
        """Draft a reply to an email"""
        prompt = f"""
        Draft a reply. Tone: {tone}. Context: {context}

        Original:
        Subject: {subject}
        Body: {body[:500]}

        Respond with JSON: {{"reply": "your reply", "subject": "reply subject"}}
        """

        return await self._call_ollama(prompt)

    async def extract_tasks_from_email(self, subject: str, body: str) -> list:
        """Extract tasks from an email"""
        prompt = f"""
        Extract actionable tasks.

        Subject: {subject}
        Body: {body[:1000]}

        Respond with JSON array: [{{"title": "task", "description": "details", "priority": "high|medium|low"}}]
        """

        result = await self._call_ollama(prompt)
        if isinstance(result, dict) and "tasks" in result:
            return result["tasks"]
        return result if isinstance(result, list) else []

    async def extract_meetings_from_email(
        self, subject: str, body: str
    ) -> Dict[str, Any]:
        """Extract meeting details from an email"""
        prompt = f"""
        Extract meeting details.

        Subject: {subject}
        Body: {body[:1000]}

        Respond with JSON: {{
            "title": "Meeting title",
            "start_date": "YYYY-MM-DD",
            "start_time": "HH:MM",
            "end_date": "YYYY-MM-DD",
            "end_time": "HH:MM",
            "location": "location",
            "description": "description"
        }}
        """

        return await self._call_ollama(prompt)

    async def suggest_task_priority(
        self, title: str, description: str, due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Suggest priority for a task"""
        due_hint = f"Due: {due_date}" if due_date else "No due date"

        prompt = f"""
        Suggest priority for this task.

        Title: {title}
        Description: {description}
        {due_hint}

        Respond with JSON: {{"priority": "urgent|high|medium|low", "reason": "reasoning"}}
        """

        return await self._call_ollama(prompt)

    async def optimize_schedule(
        self,
        events: List[Dict],
        task_title: str,
        task_description: str,
        duration_minutes: int,
    ) -> Dict[str, Any]:
        """Optimize schedule for a new task"""
        events_str = str(events[:5])

        prompt = f"""
        Suggest best time for this task.

        Existing events: {events_str}
        Task: {task_title} - {task_description}
        Duration: {duration_minutes} min

        Respond with JSON: {{
            "suggested_times": [{{"date": "YYYY-MM-DD", "time": "HH:MM", "reason": "reason"}}],
            "reason": "overall strategy"
        }}
        """

        return await self._call_ollama(prompt)

    async def parse_task_from_text(self, description: str) -> Dict[str, Any]:
        """Parse a task from text"""
        prompt = f"""
        Parse this into a structured task.

        Description: {description}

        Respond with JSON: {{
            "title": "main title",
            "description": "description",
            "priority": "high|medium|low",
            "tags": ["tag1", "tag2"],
            "due_date": "YYYY-MM-DD or null"
        }}
        """

        return await self._call_ollama(prompt)

    async def _call_ollama(self, prompt: str) -> Dict[str, Any]:
        """Call Ollama API"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                response.raise_for_status()

                data = response.json()
                if "response" in data:
                    import json

                    try:
                        return json.loads(data["response"])
                    except json.JSONDecodeError:
                        return {"raw": data["response"]}

                return data

        except httpx.RequestError as e:
            return {"error": f"Ollama request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    async def test_connection(self) -> bool:
        """Test connection to Ollama"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()

                models = response.json().get("models", [])
                return any(m.get("name") == self.model for m in models)

        except Exception:
            return False
