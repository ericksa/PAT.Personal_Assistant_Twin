"""
Memory Handlers
Handles short-term and long-term memory operations using Redis for the MCP stack
"""

import logging
from typing import Dict, List, Any, Optional
import json
import redis
import os
from datetime import datetime
import re

logger = logging.getLogger(__name__)

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Initialize Redis client
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("✓ Redis connection established")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    redis_client = None


async def store_memory(
    key: str, value: str, ttl: Optional[int] = None
) -> Dict[str, Any]:
    """
    Store information in short-term memory (Redis) for later retrieval.

    Args:
        key: Memory key/identifier
        value: Memory value/content
        ttl: Time to live in seconds (optional)

    Returns:
        Dictionary with storage status
    """
    try:
        if not redis_client:
            return {"success": False, "error": "Redis not available"}

        # Add timestamp to stored data
        memory_data = {
            "value": value,
            "stored_at": datetime.utcnow().isoformat(),
            "key": key,
        }

        # Store as JSON
        serialized_data = json.dumps(memory_data)

        # Set with optional TTL
        if ttl:
            redis_client.setex(f"memory:{key}", ttl, serialized_data)
        else:
            redis_client.set(f"memory:{key}", serialized_data)

        # Also add to a list of all memory keys for search
        memory_entry = f"{key}|{datetime.utcnow().timestamp()}"
        redis_client.lpush("memory_keys", memory_entry)

        logger.info(f"Stored memory: {key} (TTL: {ttl if ttl else 'none'})")

        return {
            "success": True,
            "key": key,
            "ttl": ttl,
            "timestamp": memory_data["stored_at"],
        }

    except Exception as e:
        logger.error(f"Memory store error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "key": key}


async def retrieve_memory(key: str) -> Dict[str, Any]:
    """
    Retrieve information from short-term memory.

    Args:
        key: Memory key to retrieve

    Returns:
        Dictionary with retrieved memory data or error
    """
    try:
        if not redis_client:
            return {"success": False, "error": "Redis not available"}

        # Retrieve from Redis
        data = redis_client.get(f"memory:{key}")

        if data is None:
            return {
                "success": False,
                "error": f"Memory key not found: {key}",
                "key": key,
            }

        # Parse JSON
        memory_data = json.loads(data or "{}")

        logger.info(f"Retrieved memory: {key}")

        return {
            "success": True,
            "key": key,
            "value": memory_data.get("value", ""),
            "stored_at": memory_data.get("stored_at", ""),
            "data": memory_data,
        }

    except Exception as e:
        logger.error(f"Memory retrieve error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "key": key}


async def search_memory(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Search through stored memories for relevant information to current context.

    Args:
        query: Search query to match against memory keys and values
        limit: Maximum number of results to return

    Returns:
        Dictionary with search results
    """
    try:
        if not redis_client:
            return {"success": False, "error": "Redis not available", "results": []}

        logger.info(f"Searching memories for: {query}")

        # Get all memory keys
        memory_keys = redis_client.lrange("memory_keys", 0, -1) or []

        results = []
        query_lower = query.lower()

        # Simple text matching search
        for key_entry in memory_keys:
            if len(results) >= limit:
                break

            # Parse key entry (format: key|timestamp)
            parts = key_entry.split("|")
            if len(parts) < 1:
                continue

            key = parts[0]

            # Retrieve memory value
            data = redis_client.get(f"memory:{key}")
            if not data:
                continue

            try:
                memory_data = json.loads(data)
                value = memory_data.get("value", "")

                # Check if query matches key or value
                if query_lower in key.lower() or query_lower in value.lower():
                    # Simple relevance score
                    score = 0.0
                    if query_lower in key.lower():
                        score += 0.7
                    if query_lower in value.lower():
                        score += 0.3

                    results.append(
                        {
                            "key": key,
                            "value": value,
                            "stored_at": memory_data.get("stored_at", ""),
                            "relevance_score": score,
                        }
                    )
            except json.JSONDecodeError:
                continue

        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        logger.info(f"Found {len(results)} matching memories")

        return {
            "success": True,
            "query": query,
            "results": results,
            "total_results": len(results),
        }

    except Exception as e:
        logger.error(f"Memory search error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "results": []}


async def list_all_memories(limit: int = 100) -> Dict[str, Any]:
    """
    List all stored memories with their metadata.

    Args:
        limit: Maximum number of memories to return

    Returns:
        Dictionary with all memories
    """
    try:
        if not redis_client:
            return {"success": False, "error": "Redis not available", "memories": []}

        logger.info("Listing all memories")

        # Get all memory keys
        memory_keys = redis_client.lrange("memory_keys", 0, limit - 1)

        memories = []

        for key_entry in memory_keys:
            parts = key_entry.split("|")
            if len(parts) < 1:
                continue

            key = parts[0]

            # Get metadata
            data = redis_client.get(f"memory:{key}")
            if data:
                try:
                    memory_data = json.loads(data)
                    memories.append(
                        {
                            "key": key,
                            "stored_at": memory_data.get("stored_at", ""),
                            "value_preview": memory_data.get("value", "")[:100] + "...",
                        }
                    )
                except json.JSONDecodeError:
                    continue

        return {"success": True, "memories": memories, "total_count": len(memories)}

    except Exception as e:
        logger.error(f"List memories error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "memories": []}


async def delete_memory(key: str) -> Dict[str, Any]:
    """
    Delete a specific memory from storage.

    Args:
        key: Memory key to delete

    Returns:
        Dictionary with deletion status
    """
    try:
        if not redis_client:
            return {"success": False, "error": "Redis not available"}

        # Check if key exists
        data = redis_client.get(f"memory:{key}")
        if data is None:
            return {"success": False, "error": f"Memory key not found: {key}"}

        # Delete memory
        redis_client.delete(f"memory:{key}")

        # Remove from keys list
        memory_keys = redis_client.lrange("memory_keys", 0, -1)
        for key_entry in memory_keys:
            if key_entry.startswith(f"{key}|"):
                redis_client.lrem("memory_keys", 0, key_entry)
                break

        logger.info(f"Deleted memory: {key}")

        return {"success": True, "key": key, "message": "Memory deleted successfully"}

    except Exception as e:
        logger.error(f"Delete memory error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "key": key}
