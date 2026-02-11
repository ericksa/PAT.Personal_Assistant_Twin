# services/agent/llm.py - LLM integration for PAT Agent Service
import logging
import httpx
import os

# Setup logger
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

async def get_ai_response(question: str, context: str, is_interview: bool = False) -> str:
    """Get AI response using configured LLM provider"""
    try:
        if is_interview:
            prompt = f"""You are PAT (Personal Assistant Twin) helping Adam during interviews.

Context Information:
{context}

Question: {question}

Please provide a concise, professional answer that Adam can read aloud.
Make it sound natural and conversational.

Answer:"""
        else:
            prompt = f"""You are PAT (Personal Assistant Twin).

Context Information:
{context}

Question: {question}

Answer:"""

        # Use configured LLM provider
        if LLM_PROVIDER == "ollama":
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": "llama3:8b",  # Will use Metal acceleration on M1
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7 if is_interview else 0.8,
                            "top_p": 0.9,
                            "top_k": 40,
                            "num_ctx": 2048
                        }
                    },
                    timeout=30  # Reduced timeout for faster failure detection
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "No response from LLM")
                else:
                    logger.error(f"LLM error: {response.status_code}")
                    return f"Unable to get response: {response.status_code}"
        else:
            # Fallback for other providers or local testing
            return f"This would be handled by your {LLM_PROVIDER} service. Question: {question}"

    except Exception as e:
        logger.error(f"LLM processing error: {e}")
        return f"Error generating response: {str(e)}"