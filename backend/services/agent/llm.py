# services/agent/llm.py - LLM integration for PAT Agent Service
import logging
import httpx
from config import logger

async def get_ai_response(question: str, context: str, is_interview: bool = False) -> str:
    """Get AI response using configured LLM provider"""
    try:
        prompt = f"""You are PAT (Personal Assistant Twin) helping Adam during interviews.

Context Information:
{context}

Question: {question}

Please provide a concise, professional answer that Adam can read aloud.
Make it sound natural and conversational.

Answer:"""

        # Use Ollama for local LLM processing
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://host.docker.internal:11434/api/generate",
                json={
                    "model": "deepseek-v3.1:671b-cloud",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "No response from LLM")
            else:
                logger.error(f"LLM error: {response.status_code}")
                return f"Unable to get response: {response.status_code}"
                
    except Exception as e:
        logger.error(f"LLM processing error: {e}")
        return f"Error generating response: {str(e)}"