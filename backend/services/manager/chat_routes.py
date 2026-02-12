"""Chat API routes for AI assistant integration"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import logging
import json

from config import ALL_SERVICES

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)

# PAT Core API base URL - adjust if needed
PAT_CORE_BASE_URL = "http://localhost:8010"


class ChatMessage(BaseModel):
    """A message in the chat conversation"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Request to send a message to the AI assistant"""

    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None  # Context about tasks, calendar, email


class ChatResponse(BaseModel):
    """Response from the AI assistant"""

    message: str
    conversation_id: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = (
        None  # Actions to perform (e.g., create_task, schedule_event)
    )
    suggestions: Optional[List[str]] = None  # Suggested next messages


class Conversation(BaseModel):
    """A conversation with the AI assistant"""

    id: str
    messages: List[ChatMessage]
    created_at: str
    updated_at: str
    context: Optional[Dict[str, Any]] = None


# In-memory conversation storage (replace with database in production)
conversations: Dict[str, Conversation] = {}
conversation_counter = 0


async def _generate_fallback_response(message: str, intent: str) -> str:
    """Generate a fallback response when PAT Core API is unavailable"""
    message_lower = message.lower()

    if intent == "task_management":
        return "I can help you manage tasks! Please tell me what task you'd like to create or what you'd like me to do with your existing tasks."
    elif intent == "calendar_management":
        return "I can help you manage your calendar! What event or appointment would you like me to schedule for you?"
    elif intent == "email_management":
        return "I can assist with email management! Would you like me to help you compose an email, check for new messages, or organize your inbox?"
    elif intent == "assistance":
        return "I'm here to help! I can assist with managing tasks, scheduling calendar events, email handling, and your PAT services. What would you like me to help you with?"
    else:
        return "I can help you with tasks, calendar events, email management, and your PAT services. What would you like me to assist you with today?"


# Agent Service URL
AGENT_SERVICE_URL = "http://localhost:8002"


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Send a message to the AI assistant and get a response"""
    try:
        # ... existing conversation code ...
        conversation_id = request.conversation_id
        if not conversation_id:
            global conversation_counter
            conversation_counter += 1
            conversation_id = f"conv_{conversation_counter}"

        if conversation_id not in conversations:
            conversations[conversation_id] = Conversation(
                id=conversation_id,
                messages=[],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                context=request.context or {},
            )

        conversation = conversations[conversation_id]
        user_message = ChatMessage(
            role="user", content=request.message, timestamp=datetime.now().isoformat()
        )
        conversation.messages.append(user_message)

        # Call Agent Service for RAG-enabled response
        ai_response_content = ""
        sources = []

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                agent_request = {
                    "query": request.message,
                    "user_id": "00000000-0000-0000-0000-000000000001",
                    "domain": None,  # Search across all domains by default
                }

                # Set system instructions via context if needed
                # For now, Agent Service uses its own prompt, but we can enhance it here

                response = await client.post(
                    f"{AGENT_SERVICE_URL}/query", json=agent_request, timeout=60.0
                )

                if response.status_code == 200:
                    agent_data = response.json()
                    ai_response_content = agent_data.get("response", "")
                    sources = agent_data.get("sources", [])

                    # Add sources to the response for referencing
                    if sources:
                        ai_response_content += "\n\n**Sources:**\n"
                        for s in sources[:3]:
                            filename = s.get("filename", "Unknown")
                            ai_response_content += f"- {filename}\n"
                else:
                    raise Exception(f"Agent Service returned {response.status_code}")

        except Exception as e:
            logger.warning(f"Agent Service unavailable, falling back to simple AI: {e}")
            # Fallback to Core API or simple response
            ai_response_content = await _generate_fallback_response(
                request.message, "assistance"
            )

        # Parse AI response for actions (keeping the existing fragile logic for now)
        actions = await _parse_actions_from_response(ai_response_content)

        assistant_message = ChatMessage(
            role="assistant",
            content=ai_response_content,
            timestamp=datetime.now().isoformat(),
        )
        conversation.messages.append(assistant_message)
        conversation.updated_at = datetime.now().isoformat()

        return ChatResponse(
            message=assistant_message.content,
            conversation_id=conversation_id,
            actions=actions,
        )

        conversation = conversations[conversation_id]

        # Add user message to conversation
        user_message = ChatMessage(
            role="user", content=request.message, timestamp=datetime.now().isoformat()
        )
        conversation.messages.append(user_message)

        # Enhance context with current service status
        enhanced_context = request.context or {}
        enhanced_context.update(
            {
                "conversation_id": conversation_id,
                "message_history": [
                    {"role": msg.role, "content": msg.content}
                    for msg in conversation.messages[-5:]  # Last 5 messages for context
                ],
                "available_services": list(ALL_SERVICES.keys()),
                "user_intent": await _extract_intent(request.message),
            }
        )

        # Try to call PAT Core API for AI response, fallback to simple response if unavailable
        ai_response_content = ""
        pat_response = {}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Backend expects a list of messages
                messages = [
                    {
                        "role": "system",
                        "content": "You are PAT (Personal Assistant Twin). Help the user manage their services and life.",
                    },
                ]

                # Add history from conversation
                for msg in conversation.messages[-5:]:
                    messages.append({"role": msg.role, "content": msg.content})

                response = await client.post(
                    f"{PAT_CORE_BASE_URL}/pat/chat/completions",
                    json={"messages": messages},
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    pat_response = response.json()
                    # Backend returns {"status": "success", "response": "..."}
                    ai_response_content = pat_response.get("response", "")
                else:
                    raise Exception(
                        f"PAT Core API returned {response.status_code}: {response.text}"
                    )
        except Exception as e:
            logger.warning(f"PAT Core API unavailable, using fallback AI: {e}")
            # Fallback to simple response if PAT Core API is not available
            ai_response_content = await _generate_fallback_response(
                request.message, enhanced_context["user_intent"]
            )

        # Parse AI response for actions
        actions = await _parse_actions_from_response(ai_response_content)

        # Add assistant message to conversation
        assistant_message = ChatMessage(
            role="assistant",
            content=ai_response_content,
            timestamp=datetime.now().isoformat(),
        )
        conversation.messages.append(assistant_message)
        conversation.updated_at = datetime.now().isoformat()

        # Return response to client
        return ChatResponse(
            message=assistant_message.content,
            conversation_id=conversation_id,
            actions=actions,
            suggestions=pat_response.get("suggestions") if pat_response else None,
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a conversation by ID"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversations[conversation_id]


@router.get("/chat/conversations", response_model=List[Conversation])
async def list_conversations():
    """List all conversations"""
    return list(conversations.values())


@router.delete("/chat/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    del conversations[conversation_id]
    return {"success": True, "message": "Conversation deleted"}


async def _extract_intent(message: str) -> str:
    """Extract user intent from message using simple keyword matching"""
    message_lower = message.lower()

    if any(word in message_lower for word in ["task", "todo", "remind", "reminder"]):
        return "task_management"
    elif any(
        word in message_lower for word in ["calendar", "schedule", "event", "meeting"]
    ):
        return "calendar_management"
    elif any(word in message_lower for word in ["email", "mail", "message", "inbox"]):
        return "email_management"
    elif any(word in message_lower for word in ["help", "assist", "guide", "how"]):
        return "assistance"
    else:
        return "general_chat"


async def _parse_actions_from_response(response: str) -> List[Dict[str, Any]]:
    """Parse AI response for actionable commands"""
    actions = []
    response_lower = response.lower()

    # Look for action patterns in the response
    patterns = {
        "create_task": ["create task", "add task", "new task", "schedule task"],
        "create_event": [
            "schedule meeting",
            "add event",
            "create calendar",
            "schedule appointment",
        ],
        "send_email": ["send email", "write email", "compose email"],
        "create_reminder": ["set reminder", "remind me", "create reminder"],
    }

    for action_type, keywords in patterns.items():
        if any(keyword in response_lower for keyword in keywords):
            actions.append(
                {
                    "type": action_type,
                    "status": "pending",
                    "description": f"Action detected: {action_type}",
                }
            )

    return actions


@router.post("/chat/execute-action")
async def execute_action(action: Dict[str, Any]):
    """Execute a detected action (task, event, email, reminder)"""
    action_type = action.get("type")

    try:
        if action_type == "create_task":
            return await _create_task(action)
        elif action_type == "create_event":
            return await _create_event(action)
        elif action_type == "send_email":
            return await _send_email(action)
        elif action_type == "create_reminder":
            return await _create_reminder(action)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown action type: {action_type}"
            )
    except Exception as e:
        logger.error(f"Action execution error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _create_task(action: Dict[str, Any]) -> Dict[str, Any]:
    """Create a task via PAT Core API"""
    task_data = {
        "title": action.get("title", "New Task"),
        "description": action.get("description", ""),
        "priority": action.get("priority", "medium"),
        "due_date": action.get("due_date"),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{PAT_CORE_BASE_URL}/pat/tasks",
                json=task_data,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "action_type": "create_task",
                    "result": response.json(),
                }
            else:
                raise Exception(f"Failed to create task: {response.text}")
    except Exception as e:
        logger.warning(f"PAT Core API unavailable for task creation: {e}")
        return {
            "success": False,
            "action_type": "create_task",
            "error": "PAT Core API not available",
        }


async def _create_event(action: Dict[str, Any]) -> Dict[str, Any]:
    """Create a calendar event via PAT Core API"""
    event_data = {
        "title": action.get("title", "New Event"),
        "start_time": action.get("start_time"),
        "end_time": action.get("end_time"),
        "description": action.get("description", ""),
        "location": action.get("location", ""),
        "attendees": action.get("attendees", []),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{PAT_CORE_BASE_URL}/pat/calendar/events",
                json=event_data,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "action_type": "create_event",
                    "result": response.json(),
                }
            else:
                raise Exception(f"Failed to create event: {response.text}")
    except Exception as e:
        logger.warning(f"PAT Core API unavailable for event creation: {e}")
        return {
            "success": False,
            "action_type": "create_event",
            "error": "PAT Core API not available",
        }


async def _send_email(action: Dict[str, Any]) -> Dict[str, Any]:
    """Send an email via PAT Core API"""
    email_data = {
        "recipient": action.get("recipient"),
        "subject": action.get("subject", ""),
        "body": action.get("body", ""),
        "priority": action.get("priority", "normal"),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{PAT_CORE_BASE_URL}/pat/emails/send",
                json=email_data,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "action_type": "send_email",
                    "result": response.json(),
                }
            else:
                raise Exception(f"Failed to send email: {response.text}")
    except Exception as e:
        logger.warning(f"PAT Core API unavailable for email: {e}")
        return {
            "success": False,
            "action_type": "send_email",
            "error": "PAT Core API not available",
        }


async def _create_reminder(action: Dict[str, Any]) -> Dict[str, Any]:
    """Create a reminder via PAT Core API"""
    reminder_data = {
        "title": action.get("title", "New Reminder"),
        "notes": action.get("notes", ""),
        "due_date": action.get("due_date"),
        "priority": action.get("priority", "medium"),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{PAT_CORE_BASE_URL}/pat/tasks",  # Reminders use same endpoint as tasks
                json=reminder_data,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "action_type": "create_reminder",
                    "result": response.json(),
                }
            else:
                raise Exception(f"Failed to create reminder: {response.text}")
    except Exception as e:
        logger.warning(f"PAT Core API unavailable for reminder: {e}")
        return {
            "success": False,
            "action_type": "create_reminder",
            "error": "PAT Core API not available",
        }
