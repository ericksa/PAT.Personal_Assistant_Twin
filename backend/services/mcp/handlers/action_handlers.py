"""
Action Handlers
Handles service calls and actions for the PAT agent system
"""

import logging
from typing import Dict, List, Any, Optional
import httpx
import os
import urllib.parse

logger = logging.getLogger(__name__)

# Service URLs
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8000")
TELEPROMPTER_URL = os.getenv("TELEPROMPTER_URL", "http://teleprompter-app:8000")
WHISPER_URL = os.getenv("WHISPER_URL", "http://whisper-service:8000")


async def query_agent(
    query: str, user_id: str = "default", use_web_search: bool = False
) -> Dict[str, Any]:
    """
    Query the PAT agent service with RAG-enabled responses.
    Handles interview questions, technical queries, and general assistance.

    Args:
        query: Query to process
        user_id: User identifier (default: "default")
        use_web_search: Enable web search (default: False)

    Returns:
        Dictionary with agent response and metadata
    """
    try:
        logger.info(
            f"Querying agent with: {query} (user: {user_id}, web_search: {use_web_search})"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_SERVICE_URL}/query",
                json={
                    "query": query,
                    "user_id": user_id,
                    "tools": ["web_search"] if use_web_search else [],
                },
                timeout=120.0,
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Agent response received")

                return {
                    "success": True,
                    "query": query,
                    "response": result.get("response", ""),
                    "sources": result.get("sources", []),
                    "tools_used": result.get("tools_used", []),
                    "model_used": result.get("model_used", ""),
                    "processing_time": result.get("processing_time", 0.0),
                }
            else:
                logger.error(f"Agent service error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Agent service error: {response.status_code}",
                    "query": query,
                }

    except Exception as e:
        logger.error(f"Agent query error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "query": query}


async def process_interview(
    question: str, source: str = "interviewer"
) -> Dict[str, Any]:
    """
    Process an interview question through the full pipeline:
    transcription, RAG retrieval, LLM generation, and teleprompter display.

    Args:
        question: Interview question to process
        source: Question source (default: "interviewer")

    Returns:
        Dictionary with processing results
    """
    try:
        logger.info(f"Processing interview question from {source}: {question}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_SERVICE_URL}/interview/process",
                json={"text": question, "source": source},
                timeout=120.0,
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Interview question processed successfully")

                return {
                    "success": True,
                    "question": question,
                    "source": source,
                    "status": result.get("status", ""),
                    "response": result.get("response", ""),
                    "processed": result.get("status") != "received",
                }
            else:
                logger.error(f"Interview processing error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Interview processing error: {response.status_code}",
                    "question": question,
                }

    except Exception as e:
        logger.error(f"Interview processing error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "question": question}


async def broadcast_teleprompter(message: str) -> Dict[str, Any]:
    """
    Send a message to the teleprompter service for on-screen display during interviews.

    Args:
        message: Message to display on teleprompter

    Returns:
        Dictionary with broadcast status
    """
    try:
        logger.info(f"Broadcasting to teleprompter: {message[:50]}...")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEPROMPTER_URL}/broadcast", json={"message": message}, timeout=10.0
            )

            if response.status_code == 200:
                logger.info("Message broadcast to teleprompter successfully")
                return {
                    "success": True,
                    "message": message,
                    "message_preview": message[:100] + "..."
                    if len(message) > 100
                    else message,
                }
            else:
                logger.error(f"Teleprompter broadcast error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Teleprompter error: {response.status_code}",
                    "message": message,
                }

    except Exception as e:
        logger.error(f"Teleprompter broadcast error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "message": message}


async def web_search(query: str, num_results: int = 3) -> Dict[str, Any]:
    """
    Perform web search using DuckDuckGo for current information outside the knowledge base.

    Args:
        query: Search query
        num_results: Number of results to return (default: 3)

    Returns:
        Dictionary with search results
    """
    try:
        logger.info(f"Performing web search for: {query}")

        # Use DuckDuckGo API for search
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=0"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)

            if response.status_code == 200:
                data = response.json()

                results = []

                # Extract abstract if available
                if data.get("AbstractText"):
                    results.append(
                        {
                            "title": data.get("Heading", "Result"),
                            "content": data.get("AbstractText", ""),
                            "url": data.get("AbstractURL", ""),
                            "source": "duckduckgo",
                        }
                    )

                # Add related topics
                if data.get("RelatedTopics"):
                    for topic in data.get("RelatedTopics", []):
                        if len(results) >= num_results:
                            break
                        if isinstance(topic, dict) and topic.get("Text"):
                            results.append(
                                {
                                    "title": topic.get("FirstURL", "")
                                    .split("/")[-1]
                                    .replace("_", " ")
                                    .title(),
                                    "content": topic.get("Text", ""),
                                    "url": topic.get("FirstURL", ""),
                                    "source": "duckduckgo",
                                }
                            )

                logger.info(f"Found {len(results)} web search results")

                return {
                    "success": True,
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                }
            else:
                logger.error(f"Web search error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Web search failed: {response.status_code}",
                    "results": [],
                }

    except Exception as e:
        logger.error(f"Web search error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "results": []}


async def transcribe_audio(file_path: str) -> Dict[str, Any]:
    """
    Transcribe audio file using the Whisper service.

    Args:
        file_path: Path to audio file

    Returns:
        Dictionary with transcription text and metadata
    """
    try:
        logger.info(f"Transcribing audio: {file_path}")

        # Check if file exists
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "audio/wav")}
                response = await client.post(
                    f"{WHISPER_URL}/transcribe", files=files, timeout=60.0
                )

            if response.status_code == 200:
                result = response.json()
                logger.info("Audio transcription completed")

                return {
                    "success": True,
                    "transcription": result.get("transcription", ""),
                    "duration": result.get("duration", 0.0),
                    "language": result.get("language", "unknown"),
                }
            else:
                logger.error(f"Transcription error: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Transcription failed: {response.status_code}",
                    "file_path": file_path,
                }

    except Exception as e:
        logger.error(f"Audio transcription error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "file_path": file_path}


async def health_check(service: Optional[str] = None) -> Dict[str, Any]:
    """
    Check health status of PAT services.

    Args:
        service: Specific service to check (optional)

    Returns:
        Dictionary with health status of all or specified service
    """
    try:
        services_config = {
            "agent": AGENT_SERVICE_URL,
            "teleprompter": TELEPROMPTER_URL,
            "whisper": WHISPER_URL,
        }

        results = {}

        services_to_check = [service] if service else list(services_config.keys())

        for svc in services_to_check:
            if svc not in services_config:
                results[svc] = {"status": "unknown", "error": "Unknown service"}
                continue

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{services_config[svc]}/health", timeout=5.0
                    )
                    results[svc] = {
                        "status": "healthy"
                        if response.status_code == 200
                        else "unhealthy",
                        "response_time": response.elapsed.total_seconds()
                        if hasattr(response, "elapsed")
                        else 0.0,
                    }
            except Exception as e:
                results[svc] = {"status": "unhealthy", "error": str(e)}

        return {"success": True, "services": results}

    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
