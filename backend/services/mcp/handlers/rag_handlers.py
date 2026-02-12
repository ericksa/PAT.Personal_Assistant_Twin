"""
RAG (Retrieval-Augmented Generation) Handlers
Handles document search, upload, and management for the PAT knowledge base
"""

import logging
from typing import Dict, List, Any
import httpx
import os

logger = logging.getLogger(__name__)

# Service URLs
INGEST_SERVICE_URL = os.getenv("INGEST_SERVICE_URL", "http://ingest-service:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


async def search_documents(
    query: str, top_k: int = 5, threshold: float = 0.2
) -> Dict[str, Any]:
    """
    Search through uploaded documents using vector similarity search.

    Args:
        query: Search query for document retrieval
        top_k: Number of results to return (default: 5)
        threshold: Similarity threshold for filtering results (default: 0.2)

    Returns:
        Dictionary with search results and metadata
    """
    try:
        logger.info(f"Searching documents for query: {query}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{INGEST_SERVICE_URL}/search",
                json={"query": query, "top_k": top_k, "threshold": threshold},
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
                            "similarity": result.get("similarity", 0.0),
                            "metadata": result.get("metadata", {}),
                        }
                    )

                return {
                    "success": True,
                    "query": query,
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
    file_path: str, chunk_size: int = 800, chunk_overlap: int = 120
) -> Dict[str, Any]:
    """
    Upload a document to the RAG knowledge base.

    Args:
        file_path: Path to file to upload
        chunk_size: Text chunk size for processing (default: 800)
        chunk_overlap: Text chunk overlap (default: 120)

    Returns:
        Dictionary with upload status and document ID
    """
    try:
        logger.info(f"Uploading document: {file_path}")

        # Validate file exists
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {
                    "file": (os.path.basename(file_path), f, "application/octet-stream")
                }
                data = {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}

                response = await client.post(
                    f"{INGEST_SERVICE_URL}/upload",
                    files=files,
                    data=data,
                    timeout=120.0,
                )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Document uploaded successfully: {result}")
                return {
                    "success": True,
                    "document_id": result.get("document_id"),
                    "filename": result.get("filename"),
                    "chunks_processed": result.get("chunks_processed", 0),
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
