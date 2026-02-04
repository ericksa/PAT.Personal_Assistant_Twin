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
from datetime import datetime
import json

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
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3:latest")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))

# Global variables for models (lazy loading)
minio_client = None
embedding_model = None
redis_client = None


class OllamaEmbeddingClient:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    async def embed(self, texts):
        """Generate embeddings for texts"""
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                for text in texts:
                    resp = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model, "prompt": text},
                        timeout=60
                    )
                    resp.raise_for_status()
                    embeddings.append(resp.json()["embedding"])
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

async def get_ai_response(query: str, context: str) -> str:
    """Get AI response using configured LLM provider"""
    prompt = f"""You are PAT (Personal Assistant Twin). Use the following information to answer the user's question.

Context Information:
{context}

Question: {query}

Answer:"""

    if LLM_PROVIDER == "ollama":
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": "llama2",  # or "llama3" if you have it
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9
                        }
                    },
                    timeout=120
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "No response from Ollama")
                else:
                    return f"Unable to get response from Ollama: {response.status_code}"
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"Error communicating with Ollama: {str(e)}"
    else:
        return f"Using basic response for query: {query}"


# Data models
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


def initialize_clients():
    """Initialize external clients"""
    global minio_client, redis_client
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

    # Initialize Redis
    try:
        redis_client = redis.from_url(REDIS_URL)
        logger.info("Redis client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {e}")


def initialize_embedding_model():
    """Initialize embedding model using Ollama embeddings"""
    global embedding_model
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    ollama_embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

    try:
        embedding_model = OllamaEmbeddingClient(ollama_base_url, ollama_embedding_model)
        logger.info(f"Using Ollama embedding model: {ollama_embedding_model}")
    except Exception as e:
        logger.error(f"Failed to initialize Ollama embedding client: {e}")
        raise


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF content"""
    try:
        from PyPDF2 import PdfReader
        import io as pyio

        pdf_file = pyio.BytesIO(pdf_content)
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.warning(f"Could not extract text from PDF: {e}")
        return "Binary file content - text extraction failed"


@app.on_event("startup")
async def startup_event():
    """Initialize services and database"""
    logger.info("Starting PAT Ingest Service...")

    # Initialize clients
    initialize_clients()
    initialize_embedding_model()

    # Initialize database schema
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Enable pgvector extension
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"Could not enable pgvector extension: {e}")
            logger.info("Continuing without vector support...")

        # Create documents table
        try:
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
        except Exception as e:
            logger.warning(f"Could not create table with VECTOR type: {e}")
            # Fallback to TEXT for embedding
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id UUID PRIMARY KEY,
                    filename VARCHAR(255),
                    content TEXT,
                    embedding TEXT,  -- Fallback to TEXT
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Created table with TEXT embedding (fallback mode)")

        # Create index if vector is available
        try:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_embedding 
                ON documents USING ivfflat (embedding vector_cosine_ops)
            """)
        except Exception as e:
            logger.warning(f"Could not create vector index: {e}")

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
        logger.info(f"Uploading document: {file.filename}")

        # Generate unique ID
        doc_id = str(uuid.uuid4())

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Extract text content based on file type
        content_str = ""
        if file.content_type == "application/pdf":
            content_str = extract_text_from_pdf(file_content)
            logger.info(f"Extracted {len(content_str)} characters from PDF")
        else:
            # Handle text files
            try:
                content_str = file_content.decode('utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"Could not decode as UTF-8, treating as binary: {e}")
                content_str = f"Binary file content ({file.content_type}) - {len(file_content)} bytes"

        # Generate embedding
        embedding_str = "[]"
        if embedding_model and content_str:
            try:
                # Only generate embedding if we have text content
                if content_str.strip():
                    embeddings = await embedding_model.embed([content_str])
                    embedding_vector = embeddings[0] if embeddings else []
                    embedding_str = json.dumps(embedding_vector)
                    logger.info(f"Generated embedding with {len(embedding_vector)} dimensions")
                else:
                    logger.info("No text content to embed")
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                embedding_str = "[]"

        # Store in database
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO documents (id, filename, content, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            doc_id,
            file.filename,
            content_str,
            embedding_str,
            json.dumps({
                "content_type": file.content_type or "application/octet-stream",
                "size": file_size,
                "uploaded_at": str(datetime.now())
            })
        ))

        conn.commit()
        cur.close()
        conn.close()

        # Store embedding in Redis
        if redis_client and embedding_str != "[]" and embedding_str != '"[]"':
            try:
                redis_client.set(f"embedding:{doc_id}", embedding_str)
                logger.info(f"Stored embedding in Redis for document {doc_id}")
            except Exception as e:
                logger.warning(f"Failed to store embedding in Redis: {e}")

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
                logger.info(f"Uploaded document to MinIO: {file.filename} ({file_size} bytes)")
            except Exception as e:
                logger.warning(f"MinIO upload failed: {e}")

        return {
            "document_id": doc_id,
            "filename": file.filename,
            "size": file_size,
            "status": "uploaded",
            "message": "Document uploaded and processed successfully"
        }

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/search")
async def search_documents(request: SearchRequest):
    """Search documents using embeddings"""
    try:
        # ... (code before this point is fine) ...

        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Try vector search first if we have query embedding
        if query_embedding:
            try:
                query_embedding_str = json.dumps(query_embedding)
                cur.execute("""
                    SELECT id, filename, content, metadata,
                           embedding <-> %s::vector as distance
                    FROM documents 
                    -- FIX 1: Use vector_dims() to check for non-empty vectors
                    WHERE vector_dims(embedding) > 0 
                    ORDER BY distance ASC
                    LIMIT %s
                """, (query_embedding_str, request.top_k))

                results = cur.fetchall()

                search_results = []
                for row in results:
                    search_results.append(SearchResult(
                        document_id=str(row['id']),
                        content=row['content'][:500] + ("..." if len(row['content']) > 500 else ""),
                        filename=row['filename'],
                        similarity=max(0, 1 - float(row['distance'])) if row['distance'] else 0.0,
                        metadata=row['metadata'] if row['metadata'] else {}
                    ))

                if search_results:
                    # Close connection only when returning successfully
                    cur.close()
                    conn.close()
                    return search_results

            except Exception as e:
                logger.warning(f"Vector search failed, falling back to text search: {e}")
                # FIX 2: Rollback the aborted transaction to allow further queries
                conn.rollback()

        # Text-based search fallback (this will now work)
        search_pattern = f"%{request.query}%"
        cur.execute("""
            SELECT id, filename, content, metadata
            FROM documents 
            WHERE content ILIKE %s OR filename ILIKE %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (search_pattern, search_pattern, request.top_k))

        results = cur.fetchall()

        # Always close your connection and cursor
        cur.close()
        conn.close()

        search_results = []
        for row in results:
            search_results.append(SearchResult(
                document_id=str(row['id']),
                content=row['content'][:500] + ("..." if len(row['content']) > 500 else ""),
                filename=row['filename'],
                similarity=0.5,  # Default similarity for text search
                metadata=row['metadata'] if row['metadata'] else {}
            ))

        return search_results

    except Exception as e:
        # This outer catch will handle other errors, like connection failure
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
    redis_healthy = redis_client is not None

    return {
        "status": "healthy" if all([db_healthy, minio_healthy, embedding_healthy, redis_healthy]) else "degraded",
        "services": {
            "database": "healthy" if db_healthy else "unhealthy",
            "minio": "healthy" if minio_healthy else "unhealthy",
            "embedding": "healthy" if embedding_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy"
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("📥 PAT Ingest Service starting...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
