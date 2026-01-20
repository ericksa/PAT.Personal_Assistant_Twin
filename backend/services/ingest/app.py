# services/ingest/app.py
import io
import logging
import os
import uuid
from typing import List, Dict

import psycopg2
import redis
from PyPDF2 import PdfReader
from docx import Document
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio
from minio.error import S3Error
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PAT Ingest Service",
    description="Document ingestion, processing, and embedding service",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from environment
MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://llm:llm@postgres:5432/llm")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))

# Initialize clients
minio_client = Minio(
    MINIO_URL.replace("http://", "").replace("https://", ""),
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

# Initialize embedding model
embedding_model = Sentence-Transformer(EMBEDDING_MODEL)

# Ensure buckets exist
buckets = ["uploads", "documents", "models"]
for bucket in buckets:
    try:
        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)
            logger.info(f"Created bucket: {bucket}")
    except S3Error as e:
        logger.error(f"Error creating bucket {bucket}: {e}")


# Database connection
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


# Redis connection
redis_client = redis.from_url(REDIS_URL)


class DocumentMetadata(BaseModel):
    filename: str
    content_type: str
    size: int
    bucket: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    document_id: str
    content: str
    filename: str
    similarity: float
    metadata: Dict


@app.on_event("startup")
async def startup_event():
    """Initialize database schema"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Create documents table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY,
                filename VARCHAR(255),
                content TEXT,
                embedding VECTOR(384),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_embedding 
            ON documents USING ivfflat (embedding vector_cosine_ops)
        """)

        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database schema initialized")

    except Exception as e:
        logger.error(f"Database initialization error: {e}")


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload document to MinIO and process"""
    try:
        # Generate unique ID
        doc_id = str(uuid.uuid4())

        # Upload to MinIO
        file_content = await file.read()
        file_size = len(file_content)

        minio_client.put_object(
            "uploads",
            f"{doc_id}_{file.filename}",
            io.BytesIO(file_content),
            file_size,
            content_type=file.content_type or "application/octet-stream"
        )

        logger.info(f"Uploaded document: {file.filename} ({file_size} bytes)")

        # Process document asynchronously
        await process_document(doc_id, file.filename, file_content, file.content_type)

        return {
            "document_id": doc_id,
            "filename": file.filename,
            "size": file_size,
            "status": "uploaded",
            "message": "Document uploaded and queued for processing"
        }

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def process_document(doc_id: str, filename: str, content: bytes, content_type: str):
    """Process document: extract text, chunk, embed, store"""
    try:
        # Extract text
        text_content = extract_text(content, content_type)

        # Chunk text
        chunks = chunk_text(text_content)

        # Generate embeddings and store
        conn = get_db_connection()
        cur = conn.cursor()

        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = embedding_model.encode(chunk).tolist()

            # Store in database
            cur.execute("""
                INSERT INTO documents (id, filename, content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()),
                filename,
                chunk,
                embedding,
                {"original_doc_id": doc_id, "chunk_index": i, "chunk_size": len(chunk)}
            ))

        conn.commit()
        cur.close()
        conn.close()

        # Move processed file to documents bucket
        minio_client.copy_object(
            "documents",
            f"{doc_id}_{filename}",
            f"uploads/{doc_id}_{filename}"
        )

        # Delete from uploads bucket
        minio_client.remove_object("uploads", f"{doc_id}_{filename}")

        logger.info(f"Processed document: {filename} ({len(chunks)} chunks)")

        # Cache processing result
        redis_client.setex(f"doc_processed:{doc_id}", 3600, "completed")

    except Exception as e:
        logger.error(f"Processing error for {filename}: {e}")
        redis_client.setex(f"doc_processed:{doc_id}", 3600, f"error: {str(e)}")


def extract_text(content: bytes, content_type: str) -> str:
    """Extract text from different file types"""
    if content_type == "application/pdf":
        pdf_reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(io.BytesIO(content))
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    else:
        return content.decode('utf-8', errors='ignore')


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks


@app.post("/search", response_model=List[SearchResult])
async def search_documents(request: SearchRequest):
    """Semantic search using embeddings"""
    try:
        # Generate query embedding
        query_embedding = embedding_model.encode(request.query).tolist()

        # Search in database
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT filename, content, embedding <=> %s as similarity
            FROM documents 
            ORDER BY embedding <=> %s
            LIMIT %s
        """, (query_embedding, query_embedding, request.top_k))

        results = []
        for row in cur.fetchall():
            results.append(SearchResult(
                document_id="",  # We don't have document IDs in this simple version
                content=row['content'],
                filename=row['filename'],
                similarity=1 - row['similarity'],  # Convert distance to similarity
                metadata={}
            ))

        cur.close()
        conn.close()

        return results

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        conn = get_db_connection()
        conn.close()
        db_healthy = True
    except:
        db_healthy = False

    try:
        # Check Redis connection
        redis_client.ping()
        redis_healthy = True
    except:
        redis_healthy = False

    try:
        # Check MinIO connection
        minio_client.bucket_exists("uploads")
        minio_healthy = True
    except:
        minio_healthy = False

    return {
        "status": "healthy" if all([db_healthy, redis_healthy, minio_healthy]) else "degraded",
        "services": {
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "minio": "healthy" if minio_healthy else "unhealthy"
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("📥 PAT Ingest Service starting...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
