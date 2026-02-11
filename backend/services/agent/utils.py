# services/agent/utils.py - Utility functions for PAT Agent Service
import re

def is_question(text: str) -> bool:
    """Detect if text is likely a question"""
    question_patterns = [
        r'^.*\?$',  # Ends with question mark
        r'^(what|who|when|where|why|how|can|could|would|should|is|are|do|does|did)',  # Question words
        r'^.*tell me about',  # Common interview phrases
        r'^.*explain',
        r'^.*describe',
        r'^.*experience with',
        r'^.*project',
        r'^.*challenge',
    ]
    
    text_lower = text.lower().strip()
    
    # Check if it ends with question mark
    if text_lower.endswith('?'):
        return True
    
    # Check patterns
    for pattern in question_patterns:
        if re.match(pattern, text_lower, re.IGNORECASE):
            return True
    
    return False

def build_context_from_results(search_results: list) -> str:
    """Build context string from search results"""
    if not search_results:
        return "No relevant information found."

    context_parts = []
    for i, result in enumerate(search_results[:5], 1):
        if isinstance(result, dict):
            filename = result.get('filename', 'Unknown')
            content = result.get('text', '')
            similarity = result.get('similarity', 0)

            context_parts.append(
                f"Document {i} ({filename}, similarity: {similarity:.2f}):\n"
                f"{content}\n\n"
            )

    return "\n".join(context_parts) if context_parts else "No content available."