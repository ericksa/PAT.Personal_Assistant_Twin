import os
import uuid
import json
import logging
import asyncio
import psycopg2
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from pydantic import BaseModel
import httpx
from PyPDF2 import PdfReader
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import io
import redis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest-service")

app = FastAPI(title="PAT Ingest Service v3 - Async")

# Instrument app for Prometheus metrics
Instrumentator().instrument(app).expose(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://llm:llm@postgres:5432/llm")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3:latest")

# Redis for task signaling
r = redis.from_url(REDIS_URL)


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
        pdf = PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


def chunk_text(
    text: str, chunk_size: int = 1000, chunk_overlap: int = 100
) -> List[str]:
    """Simple recursive-style text splitting"""
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
        except Exception as e:
            logger.error(f"Embedding attempt {attempt + 1} failed: {e}")

        if attempt < retries - 1:
            await asyncio.sleep(2**attempt)  # Exponential backoff

    return None


async def background_ingest(
    job_id: str, filename: str, content: str, domain: str, category: Optional[str]
):
    """Background task to process document"""
    conn = None
    cur = None
    try:
        chunks = chunk_text(content)
        total_chunks = len(chunks)

        # Update job status
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "UPDATE ingestion_jobs SET total_chunks = %s, status = 'processing' WHERE id = %s",
            (total_chunks, job_id),
        )
        conn.commit()

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

                cur.execute(
                    """
                    INSERT INTO documents (id, filename, content, embedding, metadata, domain, category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        str(uuid.uuid4()),
                        filename,
                        chunk_text_content,
                        embedding,
                        json.dumps(metadata),
                        domain,
                        category,
                    ),
                )
                processed_chunks += 1

                # Update progress every chunk
                cur.execute(
                    "UPDATE ingestion_jobs SET processed_chunks = %s, updated_at = NOW() WHERE id = %s",
                    (processed_chunks, job_id),
                )
                conn.commit()

        # Mark as completed
        cur.execute(
            "UPDATE ingestion_jobs SET status = 'completed', updated_at = NOW() WHERE id = %s",
            (job_id,),
        )
        conn.commit()
        logger.info(f"✅ Background Job {job_id} completed successfully.")

    except Exception as e:
        logger.error(f"❌ Background Job {job_id} failed: {e}")
        if conn and cur:
            try:
                cur.execute(
                    "UPDATE ingestion_jobs SET status = 'failed', error_message = %s, updated_at = NOW() WHERE id = %s",
                    (str(e), job_id),
                )
                conn.commit()
            except:
                pass
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


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
            content = file_content.decode("utf-8", errors="ignore")

        if not content.strip():
            raise HTTPException(status_code=400, detail="No text content extracted")

        # Register job in DB
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO ingestion_jobs (id, filename, domain, status) VALUES (%s, %s, %s, 'queued')",
            (job_id, filename, domain),
        )
        conn.commit()
        cur.close()
        conn.close()

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
        # 1. Get embedding for query
        query_embedding = await get_embedding(request.query)
        if not query_embedding:
            raise HTTPException(
                status_code=500, detail="Failed to generate query embedding"
            )

        # 2. Search database
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Build query with optional filters
        query_parts = [
            "SELECT id, filename, content, metadata, domain, category, (embedding <=> %s::vector) as distance FROM documents"
        ]
        params: List[Any] = [json.dumps(query_embedding)]

        filters = []
        if request.domain:
            filters.append("domain = %s")
            params.append(request.domain)
        if request.category:
            filters.append("category = %s")
            params.append(request.category)

        if filters:
            query_parts.append("WHERE " + " AND ".join(filters))

        query_parts.append("ORDER BY distance ASC LIMIT %s")
        params.append(request.top_k)

        sql = " ".join(query_parts)
        cur.execute(sql, tuple(params))
        results = cur.fetchall()

        formatted_results = []
        for r in results:
            # Cosine similarity is 1 - cosine distance
            score = 1 - float(r[6])
            formatted_results.append(
                {
                    "id": r[0],
                    "filename": r[1],
                    "content": r[2],
                    "metadata": r[3],
                    "domain": r[4],
                    "category": r[5],
                    "score": score,
                }
            )

        cur.close()
        conn.close()
        return formatted_results

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Check the status of an ingestion job"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "SELECT filename, domain, status, total_chunks, processed_chunks, error_message, created_at FROM ingestion_jobs WHERE id = %s",
            (job_id,),
        )
        job = cur.fetchone()
        cur.close()
        conn.close()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "job_id": job_id,
            "filename": job[0],
            "domain": job[1],
            "status": job[2],
            "progress": {
                "total": job[3],
                "processed": job[4],
                "percent": (job[4] / job[3] * 100) if job[3] > 0 else 0,
            },
            "error": job[5],
            "created_at": job[6],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy", "model": EMBEDDING_MODEL}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
