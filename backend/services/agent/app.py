# services/agent/app.py
import logging
import os
from datetime import datetime
from typing import List, Dict

import httpx
import psycopg2
import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PAT Agent Service",
    description="AI agent with RAG, web search, and tool orchestration",
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

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://llm:llm@postgres:5432/llm")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mlx")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
INGEST_SERVICE_URL = "http://ingest-service:8000"
TOP_K = int(os.getenv("TOP_K", "5"))
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.2"))

# Initialize clients
redis_client = redis.from_url(REDIS_URL)


class QueryRequest(BaseModel):
    query: str
    user_id: str = "default"
    stream: bool = False
    tools: List[str] = []


class QueryResponse(BaseModel):
    response: str
    sources: List[Dict] = []
    tools_used: List[str] = []
    model_used: str = "pat-agent"
    processing_time: float = 0.0


class WebSearchResult(BaseModel):
    title: str
    content: str
    url: str
    source: str


@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """Main query endpoint - orchestrates RAG + web search + tools"""
    start_time = datetime.now()

    try:
        # 1. Search local documents
        local_results = await search_local_documents(request.query)

        # 2. Perform web search if needed
        web_results = []
        if should_use_web_search(request.query, local_results):
            web_results = await search_web(request.query)

        # 3. Generate context-aware prompt
        context = build_context(local_results, web_results)

        # 4. Get AI response
        response = await get_ai_response(request.query, context)

        processing_time = (datetime.now() - start_time).total_seconds()

        return QueryResponse(
            response=response,
            sources=local_results,
            tools_used=[],
            model_used=LLM_PROVIDER,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Agent error: {e}")
        return QueryResponse(
            response=f"Sorry, I encountered an error: {str(e)}",
            sources=[],
            tools_used=[],
            processing_time=(datetime.now() - start_time).total_seconds()
        )


async def search_local_documents(query: str) -> List[Dict]:
    """Search local documents via ingest service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{INGEST_SERVICE_URL}/search",
                json={"query": query, "top_k": TOP_K},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
        return []
    except Exception as e:
        logger.error(f"Document search error: {e}")
        return []


def should_use_web_search(query: str, local_results: List[Dict]) -> bool:
    """Determine if web search is needed"""
    # If no local results or query asks for current info
    current_keywords = ['current', 'today', 'latest', 'news', 'weather', 'stock', 'price']
    if any(keyword in query.lower() for keyword in current_keywords):
        return True
    return len(local_results) == 0


async def search_web(query: str) -> List[WebSearchResult]:
    """Perform web search using DuckDuckGo"""
    try:
        import urllib.parse
        import httpx

        # Simple DuckDuckGo search (you can enhance this)
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            data = response.json()

            results = []
            if data.get('AbstractText'):
                results.append(WebSearchResult(
                    title=data.get('Heading', 'DuckDuckGo Result'),
                    content=data.get('AbstractText', ''),
                    url=data.get('AbstractURL', ''),
                    source='duckduckgo'
                ))

            return results

    except Exception as e:
        logger.error(f"Web search error: {e}")
        return []


def build_context(local_results: List[Dict], web_results: List[WebSearchResult]) -> str:
    """Build context from local and web results"""
    context_parts = []

    if local_results:
        context_parts.append("Relevant documents:")
        for result in local_results[:3]:
            context_parts.append(f"- {result.get('filename', 'Document')}: {result.get('content', '')[:300]}...")

    if web_results:
        context_parts.append("\nCurrent information from web:")
        for result in web_results[:2]:
            context_parts.append(f"- {result.title}: {result.content[:200]}...")

    return "\n".join(context_parts)


async def get_ai_response(query: str, context: str) -> str:
    """Get AI response using configured LLM provider"""
    prompt = f"""You are PAT (Personal Assistant Twin). Use the following information to answer the user's question.

{context}

Question: {query}

Answer:"""

    if LLM_PROVIDER == "mlx":
        # For MLX, we assume it's running locally
        # In a real implementation, you'd call your MLX service
        return f"This would be handled by your MLX service. Query: {query}"
    elif LLM_PROVIDER == "ollama":
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": "llama2",
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=120
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "No response from Ollama")
                else:
                    return "Unable to get response from Ollama"
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return "Error communicating with Ollama"
    else:
        return f"Unsupported LLM provider: {LLM_PROVIDER}"


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

    try:
        # Check Redis connection
        redis_client.ping()
        redis_healthy = True
    except:
        redis_healthy = False

    try:
        # Check ingest service
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{INGEST_SERVICE_URL}/health", timeout=5)
            ingest_healthy = response.status_code == 200
    except:
        ingest_healthy = False

    return {
        "status": "healthy" if all([db_healthy, redis_healthy, ingest_healthy]) else "degraded",
        "services": {
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "ingest": "healthy" if ingest_healthy else "unhealthy",
            "llm_provider": LLM_PROVIDER
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("🤖 PAT Agent Service starting...")
    print(f"🧠 LLM Provider: {LLM_PROVIDER}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
