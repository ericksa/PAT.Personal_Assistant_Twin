# services/agent/app.py - Fixed version
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import asyncio

try:
    import httpx
except ImportError:
    import requests as httpx

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PAT Agent Service",
    description="AI agent with RAG, web search, and tool orchestration",
    version="1.0.0",
)


# WebSocket Connection Manager for live interview updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


interview_manager = ConnectionManager()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://llm:llm@localhost:5432/llm")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lm_studio")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234")
INGEST_SERVICE_URL = os.getenv("INGEST_SERVICE_URL", "http://localhost:8001")
TOP_K = int(os.getenv("TOP_K", "5"))
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.2"))


class QueryRequest(BaseModel):
    query: str
    user_id: str = "default"
    domain: Optional[str] = None
    category: Optional[str] = None
    stream: bool = False
    tools: List[str] = []


class QueryResponse(BaseModel):
    response: str
    sources: List[Dict] = []
    tools_used: List[str] = []
    model_used: str = "pat-agent"
    processing_time: float = 0.0
    domain: Optional[str] = None


class WebSearchResult(BaseModel):
    title: str
    content: str
    url: str
    source: str


# Model for live interview input
class InterviewRequest(BaseModel):
    text: str
    source: str = "interviewer"


# Simple test endpoint
@app.get("/test-interview")
async def test_interview():
    return {"message": "Interview endpoint working"}


# WebSocket endpoint for teleprompter
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time teleprompter updates"""
    await interview_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle ping messages
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        interview_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        interview_manager.disconnect(websocket)


# Endpoint to process live interview input
@app.post("/interview/process")
async def process_interview_input(request: InterviewRequest):
    """Process live interview input and send response to teleprompter"""
    question = request.text
    logger.info(f"Processing interview question: {question}")

    try:
        # Simple question detection
        is_question = any(
            word in question.lower()
            for word in ["what", "how", "why", "when", "where", "who", "?"]
        )

        if not is_question:
            logger.info(f"Text doesn't appear to be a question: {question}")
            return {"status": "received", "question": question, "processed": False}

        # Get context from local documents
        local_results = await search_local_documents(question)

        # Build simple context
        context = "Relevant information:\n"
        for result in local_results[:3]:
            context += f"- {result.get('filename', 'Document')}: {result.get('content', '')[:300]}...\n"

        # Get AI response using configured provider
        response_text = await get_ai_response(question, context)

        # Send response to teleprompter service (if available)
        try:
            if hasattr(httpx, "AsyncClient"):
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "http://localhost:8005/broadcast",
                        json={"message": response_text},
                        timeout=10,
                    )
            else:
                # Fallback for requests library
                response = httpx.post(
                    "http://localhost:8005/broadcast",
                    json={"message": response_text},
                    timeout=10,
                )
            logger.info(f"Successfully sent response to teleprompter service")
        except Exception as e:
            logger.warning(f"Could not send to teleprompter service: {e}")

        logger.info(f"Processed question: {response_text[:100]}...")
        return {
            "status": "processed",
            "question": question,
            "response": response_text,
        }

    except Exception as e:
        logger.error(f"Error processing interview question: {e}")
        error_message = f"Error processing question: {str(e)}"
        return {"status": "error", "question": question, "error": str(e)}


@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """Main query endpoint - orchestrates RAG + web search + tools"""
    start_time = datetime.now()

    try:
        # 1. Search local documents with domain isolation
        local_results = await search_local_documents(
            request.query, domain=request.domain, category=request.category
        )

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
            processing_time=processing_time,
            domain=request.domain,
        )

    except Exception as e:
        logger.error(f"Agent error: {e}")
        return QueryResponse(
            response=f"Sorry, I encountered an error: {str(e)}",
            sources=[],
            tools_used=[],
            processing_time=(datetime.now() - start_time).total_seconds(),
        )


async def search_local_documents(
    query: str, domain: Optional[str] = None, category: Optional[str] = None
) -> List[Dict]:
    """Search local documents via ingest service with domain filtering"""
    try:
        payload = {"query": query, "top_k": TOP_K}
        if domain:
            payload["domain"] = domain
        if category:
            payload["category"] = category

        if hasattr(httpx, "AsyncClient"):
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{INGEST_SERVICE_URL}/search",
                    json=payload,
                    timeout=30,
                )
                if response.status_code == 200:
                    return response.json()
        else:
            # Fallback for requests library
            response = httpx.post(
                f"{INGEST_SERVICE_URL}/search",
                json=payload,
                timeout=30,
            )
            if response.status_code == 200:
                return response.json()
        return []
    except Exception as e:
        logger.warning(f"Document search failed: {e}")
        return []


def should_use_web_search(query: str, local_results: List[Dict]) -> bool:
    """Determine if web search is needed"""
    current_keywords = [
        "current",
        "today",
        "latest",
        "news",
        "weather",
        "stock",
        "price",
    ]
    if any(keyword in query.lower() for keyword in current_keywords):
        return True
    return len(local_results) == 0


async def search_web(query: str) -> List[WebSearchResult]:
    """Perform web search using DuckDuckGo"""
    try:
        import urllib.parse

        # Simple DuckDuckGo search
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"

        if hasattr(httpx, "AsyncClient"):
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                data = response.json()
        else:
            response = httpx.get(url, timeout=10)
            data = response.json()

        results = []
        if data.get("AbstractText"):
            results.append(
                WebSearchResult(
                    title=data.get("Heading", "DuckDuckGo Result"),
                    content=data.get("AbstractText", ""),
                    url=data.get("AbstractURL", ""),
                    source="duckduckgo",
                )
            )

        return results

    except Exception as e:
        logger.warning(f"Web search failed: {e}")
        return []


def build_context(local_results: List[Dict], web_results: List[WebSearchResult]) -> str:
    """Build context from local and web results"""
    context_parts = []

    if local_results:
        context_parts.append("Relevant documents:")
        for result in local_results[:3]:
            context_parts.append(
                f"- {result.get('filename', 'Document')}: {result.get('content', '')[:300]}..."
            )

    if web_results:
        context_parts.append("\nCurrent information from web:")
        for result in web_results[:2]:
            context_parts.append(f"- {result.title}: {result.content[:200]}...")

    return "\n".join(context_parts)


async def get_ai_response(query: str, context: str) -> str:
    """Get AI response using configured LLM provider"""
    logger.info(f"get_ai_response called with query: {query}")

    prompt = f"""You are PAT (Personal Assistant Twin). Use the following information to answer the user's question.

{context}

Question: {query}

Answer:"""

    if LLM_PROVIDER == "lm_studio":
        try:
            if hasattr(httpx, "AsyncClient"):
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{LM_STUDIO_BASE_URL}/v1/chat/completions",
                        json={
                            "model": "glm-4.6v-flash",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.7,
                            "max_tokens": 2048,
                        },
                        timeout=120,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return (
                            data.get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "No response from LM Studio")
                        )
                    else:
                        return f"LM Studio error: {response.status_code}"
            else:
                response = httpx.post(
                    f"{LM_STUDIO_BASE_URL}/v1/chat/completions",
                    json={
                        "model": "glm-4.6v-flash",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 2048,
                    },
                    timeout=120,
                )
                if response.status_code == 200:
                    data = response.json()
                    return (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "No response from LM Studio")
                    )
                else:
                    return f"LM Studio error: {response.status_code}"
        except Exception as e:
            logger.error(f"LM Studio error: {e}")
            return f"Error communicating with LM Studio: {str(e)}"

    elif LLM_PROVIDER == "ollama":
        try:
            if hasattr(httpx, "AsyncClient"):
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{OLLAMA_BASE_URL}/api/generate",
                        json={"model": "llama3:8b", "prompt": prompt, "stream": False},
                        timeout=120,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data.get("response", "No response from Ollama")
                    else:
                        return f"Ollama error: {response.status_code}"
            else:
                response = httpx.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={"model": "llama3:8b", "prompt": prompt, "stream": False},
                    timeout=120,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "No response from Ollama")
                else:
                    return f"Ollama error: {response.status_code}"
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"Error communicating with Ollama: {str(e)}"
    else:
        return f"Unsupported LLM provider: {LLM_PROVIDER}"


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Simple health check
        return {
            "status": "healthy",
            "services": {
                "llm_provider": LLM_PROVIDER,
                "ingest_url": INGEST_SERVICE_URL,
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    print("🤖 PAT Agent Service starting...")
    print(f"🧠 LLM Provider: {LLM_PROVIDER}")
    uvicorn.run(app, host="0.0.0.0", port=8002)
