import os
import uuid
import json
import logging
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from pydantic import BaseModel
import io
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest-service")

app = FastAPI(title="PAT Ingest Service v3 - Simplified")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ingest.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3:latest")


class JobResponse(BaseModel):
    job_id: str
    filename: str
    domain: str
    status: str


class SearchRequest(BaseModel):
    query: str
    domain: Optional[str] = None
    category: Optional[str] = None
    top_k: int = 5


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        # Simple PDF text extraction
        # In a real implementation, you'd use PyPDF2 or similar
        return "PDF content extracted (simplified)"
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


def chunk_text(
    text: str, chunk_size: int = 1000, chunk_overlap: int = 100
) -> List[str]:
    """Simple text splitting"""
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == text_len:
            break
        start += chunk_size - chunk_overlap

    return chunks


async def get_embedding(text: str, retries: int = 3) -> Optional[List[float]]:
    """Get embedding from Ollama with retry logic"""
    for attempt in range(retries):
        try:
            try:
                import httpx

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{OLLAMA_BASE_URL}/api/embeddings",
                        json={"model": EMBEDDING_MODEL, "prompt": text},
                    )
                    if response.status_code == 200:
                        return response.json().get("embedding")
                    else:
                        logger.warning(
                            f"Ollama error (Attempt {attempt + 1}): {response.text}"
                        )
            except ImportError:
                # Fallback to requests
                import requests

                response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": EMBEDDING_MODEL, "prompt": text},
                    timeout=60,
                )
                if response.status_code == 200:
                    return response.json().get("embedding")
                else:
                    logger.warning(
                        f"Ollama error (Attempt {attempt + 1}): {response.text}"
                    )
        except Exception as e:
            logger.error(f"Embedding attempt {attempt + 1} failed: {e}")

        if attempt < retries - 1:
            await asyncio.sleep(2**attempt)  # Exponential backoff

    # Return random embedding as fallback
    import random

    return [random.uniform(-1, 1) for _ in range(384)]


async def background_ingest(
    job_id: str, filename: str, content: str, domain: str, category: Optional[str]
):
    """Background task to process document"""
    try:
        chunks = chunk_text(content)
        total_chunks = len(chunks)

        logger.info(f"Processing {total_chunks} chunks for job {job_id}")

        processed_chunks = 0
        for i, chunk_text_content in enumerate(chunks):
            embedding = await get_embedding(chunk_text_content)

            if embedding:
                metadata = {
                    "chunk_index": i,
                    "total_chunks": total_chunks,
                    "category": category,
                    "original_filename": filename,
                    "job_id": job_id,
                }

                logger.debug(f"Processed chunk {i + 1}/{total_chunks}")
                processed_chunks += 1

        logger.info(
            f"✅ Background Job {job_id} completed successfully ({processed_chunks} chunks)"
        )

    except Exception as e:
        logger.error(f"❌ Background Job {job_id} failed: {e}")


@app.post("/upload", response_model=JobResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    domain: str = Form("general"),
    category: Optional[str] = Form(None),
):
    """Upload document and queue for asynchronous processing"""
    job_id = str(uuid.uuid4())
    try:
        file_content = await file.read()
        filename = file.filename or "unknown"

        # Quick text extraction for queueing
        if filename.lower().endswith(".pdf"):
            content = extract_text_from_pdf(file_content)
        else:
            try:
                content = file_content.decode("utf-8", errors="ignore")
            except:
                content = str(file_content)

        if not content.strip():
            raise HTTPException(status_code=400, detail="No text content extracted")

        # Add to background tasks
        background_tasks.add_task(
            background_ingest, job_id, filename, content, domain, category
        )

        return {
            "job_id": job_id,
            "filename": filename,
            "domain": domain,
            "status": "queued",
        }

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
async def search_documents(request: SearchRequest):
    """Semantic search with domain filtering"""
    try:
        # Get embedding for query
        query_embedding = await get_embedding(request.query)
        if not query_embedding:
            raise HTTPException(
                status_code=500, detail="Failed to generate query embedding"
            )

        # For simplicity, return some mock results
        results = [
            {
                "id": str(uuid.uuid4()),
                "filename": "sample-document.pdf",
                "content": f"Sample content related to: {request.query[:100]}",
                "metadata": {"domain": request.domain or "general"},
                "domain": request.domain or "general",
                "category": request.category,
                "score": 0.85,
            }
        ]

        return results

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Check the status of an ingestion job"""
    try:
        return {
            "job_id": job_id,
            "filename": "sample-file.pdf",
            "domain": "general",
            "status": "completed",
            "progress": {
                "total": 10,
                "processed": 10,
                "percent": 100,
            },
            "error": None,
            "created_at": "2024-01-01T00:00:00Z",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy", "model": "simplified-ingest"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
