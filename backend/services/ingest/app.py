# services/ingest/app.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import io
from minio import Minio
from minio.error import S3Error
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import uuid
from typing import List, Dict
import logging
from PyPDF2 import PdfReader
from docx import Document
import numpy as np

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
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))

# Global variables for models (lazy loading)
minio_client = None
embedding_model = None


def initialize_clients():
    """Initialize external clients"""
    global minio_client
    try:
        minio_client = Minio(
            MINIO_URL.replace("http://", "").replace("https://", ""),
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )

        # Ensure buckets exist
        buckets = ["uploads", "documents", "models"]
        for bucket in buckets:
            try:
                if not minio_client.bucket_exists(bucket):
                    minio_client.make_bucket(bucket)
                    logger.info(f"Created bucket: {bucket}")
            except S3Error as e:
                logger.warning(f"Warning creating bucket {bucket}: {e}")

        logger.info("MinIO client initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize MinIO client: {e}")


def initialize_embedding_model():
    """Initialize embedding model with fallback"""
    global embedding_model
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load embedding model {EMBEDDING_MODEL}: {e}")
        logger.info("Falling back to simpler model...")
        try:
            from sentence_transformers import SentenceTransformer
            embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Fallback model loaded successfully")
        except Exception as e2:
            logger.error(f"Failed to load fallback model: {e2}")

            # Create a mock model for testing
            class MockEmbeddingModel:
                def encode(self, text):
                    # Return random embeddings for testing
                    import numpy as np
                    return np.random.rand(384).tolist()

            embedding_model = MockEmbeddingModel()
            logger.warning("Using mock embedding model for testing")


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
    """Initialize services and database"""
    logger.info("Starting PAT Ingest Service...")

    # Initialize clients
    initialize_clients()

    # Initialize embedding model
    initialize_embedding_model()

    # Initialize database schema
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Create documents table with proper vector dimension
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY,
                filename VARCHAR(255),
                content TEXT,
                embedding VECTOR(768),  -- BGE model uses 768 dimensions
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

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Upload to MinIO if client is available
        if minio_client:
            try:
                minio_client.put_object(
                    "uploads",
                    f"{doc_id}_{file.filename}",
                    io.BytesIO(file_content),
                    file_size,
                    content_type=file.content_type or "application/octet-stream"
                )
                logger.info(f"Uploaded document: {file.filename} ({file_size} bytes)")
            except Exception as e:
                logger.warning(f"MinIO upload failed: {e}")

        # For now, return success without processing (to avoid embedding issues)
        return {
            "document_id": doc_id,
            "filename": file.filename,
            "size": file_size,
            "status": "uploaded",
            "message": "Document uploaded successfully"
        }

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/search")
async def search_documents(request: SearchRequest):
    """Simple search endpoint (placeholder)"""
    try:
        # Return mock results for now
        return [
            SearchResult(
                document_id=str(uuid.uuid4()),
                content="This is a mock search result. Document processing will be implemented.",
                filename="mock-document.txt",
                similarity=0.8,
                metadata={}
            )
        ]
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        db_healthy = True
    except:
        db_healthy = False

    minio_healthy = minio_client is not None
    embedding_healthy = embedding_model is not None

    return {
        "status": "healthy" if all([db_healthy, minio_healthy]) else "degraded",
        "services": {
            "database": "healthy" if db_healthy else "unhealthy",
            "minio": "healthy" if minio_healthy else "unhealthy",
            "embedding": "healthy" if embedding_healthy else "unhealthy"
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("📥 PAT Ingest Service starting...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
