# services/agent/llm.py
import httpx
from config import OLLAMA_BASE_URL, LLM_MODEL_INTERVIEW, LLM_MODEL_GENERAL, logger

async def get_ai_response(query: str, context: str, is_interview: bool = False) -> str:
    """Get AI response using Ollama"""
    model = LLM_MODEL_INTERVIEW if is_interview else LLM_MODEL_GENERAL
    prompt = f"""You are an AI assistant for job interviews. Use the following context to answer the question. {context} Question: {query} Answer:"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "No response from LLM").strip()
            else:
                return "Unable to get response from LLM"
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return "Error communicating with LLM"

class OllamaEmbeddingClient:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    async def embed(self, texts):
        """Generate embeddings for texts using correct endpoint"""
        if isinstance(texts, str):
            texts = [texts]
        embeddings = []
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                for text in texts:
                    # Use /api/embeddings instead of /api/embed
                    resp = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model, "prompt": text},
                        timeout=60
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    embeddings.append(result.get("embedding", []))
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Return empty embeddings instead of raising exception
            return [[] for _ in texts]