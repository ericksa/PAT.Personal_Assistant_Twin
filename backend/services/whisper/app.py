# services/whisper/app.py - Whisper-based audio transcription service
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import logging
import os
import asyncio
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PAT Whisper Transcription Service")

# Configuration
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8000")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # base, small, medium, large


class TranscriptionRequest(BaseModel):
    audio_url: str = None


class InterviewQuestion(BaseModel):
    question: str


async def transcribe_audio_local(file_path: str) -> str:
    """Transcribe audio using a local model"""
    try:
        # Placeholder for Whisper integration
        # In production, you'd use whisper.cpp or a Python Whisper library

        # Simulate transcription processing
        logger.info(f"Transcribing audio file: {file_path}")
        await asyncio.sleep(0.5)  # Simulate processing time

        # Mock transcription - in real implementation, use proper Whisper model
        # This would be replaced with actual transcription logic
        mock_transcriptions = {
            "technical_question": "Can you explain your experience with Python and Docker?",
            "behavioral_question": "Tell me about a challenging project you worked on",
            "resume_question": "What skills did you learn in your last position?",
        }

        # For demo purposes, return a mock response
        # In production, this would use whisper.cpp or Python whisper library
        return mock_transcriptions.get(
            "technical_question", "I heard an interview question"
        )

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


async def send_to_agent_service(question: str) -> str:
    """Send transcribed question to agent service for RAG response"""
    try:
        logger.info(f"Sending request to agent service: {AGENT_SERVICE_URL}/query")
        logger.info(f"Request payload: {{'query': '{question}', 'user_id': 'default'}}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_SERVICE_URL}/query",
                json={"query": question, "user_id": "default"},
                timeout=120,  # Increase timeout to 120 seconds for LLM processing
            )

            logger.info(f"Agent service response status: {response.status_code}")
            logger.info(f"Agent service response text: {response.text}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Agent service response JSON: {result}")
                answer = result.get("response", "No response from agent service")
                logger.info(f"Extracted answer: {answer}")
                return answer
            else:
                logger.error(f"Agent service error: {response.status_code}")
                return f"Agent service unavailable: {response.status_code}"

    except Exception as e:
        logger.error(f"Agent service communication error: {e}", exc_info=True)
        return f"Failed to communicate with agent service: {str(e)}"


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Upload audio file for transcription and processing"""
    try:
        if not file.content_type or not file.content_type.startswith("audio/"):
            # Allow files without explicit content type
            logger.warning(
                f"File has no content type or not audio: {file.content_type}"
            )
            # Continue processing but log warning

        # Save uploaded file temporarily
        filename = file.filename or "audio_file.wav"
        temp_path = f"/tmp/{filename}"

        # Read file content
        content = await file.read()

        # Save temporarily (in production, use proper storage)
        with open(temp_path, "wb") as f:
            f.write(content)

        # Transcribe audio
        question = await transcribe_audio_local(temp_path)

        # Send to agent service for RAG response
        answer = await send_to_agent_service(question)

        # Cleanup temp file
        os.unlink(temp_path)

        return {
            "status": "processed",
            "question": question,
            "answer": answer,
            "message": "Audio transcribed and processed successfully",
        }

    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Audio processing failed: {str(e)}"
        )


@app.post("/process-question")
async def process_text_question(request: InterviewQuestion):
    """Process text-based interview question (for testing)"""
    try:
        answer = await send_to_agent_service(request.question)

        return {"status": "processed", "question": request.question, "answer": answer}

    except Exception as e:
        logger.error(f"Question processing error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Question processing failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "whisper-transcription"}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Whisper Transcription Service")
    uvicorn.run(app, host="0.0.0.0", port=8000)
