# services/agent/utils.py
from config import logger

def is_question(text: str) -> bool:
    """Detect if text is a question"""
    text = text.strip().lower()
    return "?" in text or any(word in text for word in ["what", "how", "why", "when", "where", "who", "tell me", "describe", "explain"])

def build_context(local_results: list, web_results: list = None) -> str:
    """Build context from RAG results"""
    context_parts = []
    if local_results:
        context_parts.append("Relevant documents:")
        for i, result in enumerate(local_results[:3]):
            content = result.get("text", "")[:500] + "..." if len(result.get("text", "")) > 500 else result.get("text", "")
            filename = result.get("filename", "Unknown")
            context_parts.append(f"- Document {i+1} ({filename}): {content}")
    if web_results:
        context_parts.append("\nCurrent information from web:")
        for result in web_results[:2]:
            content = result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", "")
            context_parts.append(f"- {result.get('title', '')}: {content}")
    return "\n".join(context_parts)