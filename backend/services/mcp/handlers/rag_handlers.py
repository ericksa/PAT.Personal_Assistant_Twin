"""
RAG (Retrieval-Augmented Generation) Handlers
Handles document search, upload, and management for the PAT knowledge base
"""

import logging
from typing import Dict, List, Any, Optional
import httpx
import os

logger = logging.getLogger(__name__)

# Service URLs
INGEST_SERVICE_URL = os.getenv("INGEST_SERVICE_URL", "http://ingest-service:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


async def search_documents(
    query: str,
    top_k: int = 5,
    threshold: float = 0.2,
    domain: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search through uploaded documents using vector similarity search.
    """
    try:
        logger.info(f"Searching documents for query: {query} [Domain: {domain}]")

        async with httpx.AsyncClient() as client:
            payload = {"query": query, "top_k": top_k, "threshold": threshold}
            if domain:
                payload["domain"] = domain
            if category:
                payload["category"] = category

            response = await client.post(
                f"{INGEST_SERVICE_URL}/search",
                json=payload,
                timeout=30.0,
            )

            if response.status_code == 200:
                results = response.json()
                logger.info(f"Found {len(results)} document matches")

                # Format results for MCP response
                formatted_results = []
                for result in results:
                    formatted_results.append(
                        {
                            "filename": result.get("filename", "Unknown"),
                            "content": result.get("content", ""),
                            "score": result.get("score", 0.0),
                            "domain": result.get("domain", "general"),
                            "category": result.get("category"),
                            "metadata": result.get("metadata", {}),
                        }
                    )

                return {
                    "success": True,
                    "query": query,
                    "domain": domain,
                    "results": formatted_results,
                    "total_results": len(formatted_results),
                }
            else:
                logger.error(f"Ingest service returned status {response.status_code}")
                return {
                    "success": False,
                    "error": f"Ingest service error: {response.status_code}",
                    "results": [],
                }

    except Exception as e:
        logger.error(f"Document search error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "results": []}


async def upload_document(
    file_path: str, domain: str = "general", category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a document to the RAG knowledge base with domain isolation.
    """
    try:
        logger.info(f"Uploading document: {file_path} [Domain: {domain}]")

        # Validate file exists
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {
                    "file": (os.path.basename(file_path), f, "application/octet-stream")
                }
                data = {"domain": domain}
                if category:
                    data["category"] = category

                response = await client.post(
                    f"{INGEST_SERVICE_URL}/upload",
                    files=files,
                    data=data,
                    timeout=120.0,
                )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Document upload queued successfully: {result}")
                return {
                    "success": True,
                    "job_id": result.get("job_id"),
                    "filename": result.get("filename"),
                    "domain": result.get("domain"),
                    "status": result.get("status"),
                }
            else:
                logger.error(f"Upload failed with status {response.status_code}")
                return {
                    "success": False,
                    "error": f"Upload failed: {response.status_code}",
                    "details": response.text,
                }

    except Exception as e:
        logger.error(f"Document upload error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def list_documents() -> Dict[str, Any]:
    """
    List all documents currently stored in the RAG system.

    Returns:
        Dictionary with document list and metadata
    """
    try:
        logger.info("Listing all documents in RAG system")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{INGEST_SERVICE_URL}/documents", timeout=10.0)

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "documents": result.get("documents", []),
                    "total_count": len(result.get("documents", [])),
                }
            else:
                logger.error(f"Failed to list documents: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Error listing documents: {response.status_code}",
                    "documents": [],
                }

    except Exception as e:
        logger.error(f"List documents error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "documents": []}


async def get_ingestion_status(job_id: str) -> Dict[str, Any]:
    """
    Check the status of an asynchronous ingestion job.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{INGEST_SERVICE_URL}/job/{job_id}", timeout=10.0
            )
            if response.status_code == 200:
                return {"success": True, "status": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"Status check failed: {response.status_code}",
                }
    except Exception as e:
        return {"success": False, "error": str(e)}
