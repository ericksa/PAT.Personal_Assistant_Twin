# services/agent/app.py
from fastapi import FastAPI, WebSocket, HTTPException
from pydantic import BaseModel
from config import logger
from rag import search_documents
from llm import get_ai_response
from utils import is_question, build_context

app = FastAPI(title="PAT Agent Service")


# Pydantic models
class AudioInput(BaseModel):
    text: str


# Import teleprompter module only if it exists
manager = None
try:
    from teleprompter import manager
    logger.info("Teleprompter module loaded successfully")
except ImportError:
    logger.warning("Teleprompter module not found - continuing without teleprompter support")


@app.post("/interview/analyze")
async def analyze_interview_question(input_data: AudioInput):
    question = input_data.text.strip()
    logger.info(f"Interview question received: {question}")

    if not is_question(question):
        answer = "This doesn't seem like a question. Please ask something specific."
        logger.info(f"Not a question: {question}")
    else:
        # Search documents through ingest service
        local_results = await search_documents(question, is_interview=True)

        if not local_results:
            answer = "I couldn't find any relevant information in my documents."
            logger.warning(f"No RAG results for: {question}")
        else:
            context = build_context(local_results)
            answer = await get_ai_response(question, context, is_interview=True)
            logger.info(f"Answer generated for: {question}")

    # Broadcast to teleprompter if available
    if manager:
        try:
            await manager.broadcast_to_teleprompter(answer)
        except Exception as e:
            logger.error(f"Failed to broadcast to teleprompter: {e}")
    
    return {"status": "processed", "answer": answer}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)