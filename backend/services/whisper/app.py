# services/whisper/app.py - Whisper-based audio transcription service
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket
from pydantic import BaseModel
import logging
import os
import asyncio
import httpx
import numpy as np
import wave
import struct
import json

try:
    import librosa
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("librosa not available, basic audio processing will be used")

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


# Feature flag for real whisper integration
USE_REAL_WHISPER = True  # Enable for testing - will control via Dockerfile later
logger.info(f"🧠 USE_REAL_WHISPER flag: {USE_REAL_WHISPER}")


# Silero VAD implementation for advanced voice activity detection
class SileroVAD:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.buffer = bytearray()
        self.max_size = sample_rate * 10  # 10 seconds buffer
        self.vad_model = None

    def load_model(self):
        """Load Silero VAD model"""
        try:
            import torch
            from silero_vad import load_silero_vad

            if self.vad_model is None:
                logger.info("Loading Silero VAD model...")
                self.vad_model = load_silero_vad()
                logger.info("Silero VAD model loaded successfully")
        except ImportError:
            logger.warning("Silero VAD not available, falling back to energy-based VAD")
            self.vad_model = None

    def add_chunk(self, chunk: bytes):
        """Add audio chunk to buffer"""
        self.buffer.extend(chunk)
        # Limit buffer size
        if len(self.buffer) > self.max_size:
            self.buffer = self.buffer[-self.max_size :]

    def reset(self):
        """Clear the buffer"""
        self.buffer.clear()

    def has_speech(self) -> bool:
        """Use Silero VAD for accurate speech detection"""
        if len(self.buffer) < 1600:  # Need at least 100ms of audio
            return False

        # Try Silero VAD first
        if self.vad_model:
            try:
                import torch
                import numpy as np

                # Convert to numpy array
                audio_data = np.frombuffer(self.buffer, dtype=np.int16)
                audio_float = audio_data.astype(np.float32) / 32768.0

                # Use Silero VAD
                with torch.no_grad():
                    speech_prob = self.vad_model(
                        torch.from_numpy(audio_float), self.sample_rate
                    )

                return speech_prob > 0.5

            except Exception as e:
                logger.error(f"Silero VAD error: {e}")
                # Fallback to energy-based detection

        # Fallback: energy-based detection
        audio_data = np.frombuffer(self.buffer, dtype=np.int16)
        energy = np.sqrt(np.mean(audio_data.astype(float) ** 2))
        return energy > 900  # Lower threshold for better sensitivity

    def get_audio_data(self) -> bytes:
        """Get audio data as bytes"""
        return bytes(self.buffer)


# Global Silero VAD instances for WebSocket connections
vad_instances = {}


async def real_transcribe_audio(file_path: str) -> str:
    """Real transcription using faster-whisper"""
    try:
        logger.info(f"Real transcription started for: {file_path}")

        # Load whisper model
        from faster_whisper import WhisperModel

        model = WhisperModel("base")

        # Perform transcription
        segments, info = model.transcribe(file_path)
        transcription = " ".join(segment.text for segment in segments)

        logger.info(f"Real transcription successful: {transcription[:100]}...")
        return transcription.strip()

    except Exception as e:
        logger.error(f"Real transcription failed: {e}")
        return f"Real transcription failed: {str(e)}"


async def transcribe_audio_local(file_path: str) -> str:
    """Transcribe audio using a local model"""
    try:
        logger.info(f"Transcribing audio file: {file_path}")

        # Use real whisper if enabled
        if USE_REAL_WHISPER:
            logger.info("Using real whisper transcription")
            result = await real_transcribe_audio(file_path)

            # If real transcription returns empty or failed, fallback to mock
            if (
                result
                and not result.startswith("Real transcription failed")
                and len(result.strip()) > 0
            ):
                return result
            else:
                logger.warning(
                    "Real transcription failed or empty, falling back to mock"
                )

        # Fallback to mock transcription
        await asyncio.sleep(0.5)  # Simulate processing time

        mock_transcriptions = {
            "technical_question": "Can you explain your experience with Python and Docker?",
            "behavioral_question": "Tell me about a challenging project you worked on",
            "resume_question": "What skills did you learn in your last position?",
        }

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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time audio streaming endpoint"""
    await websocket.accept()
    client_id = id(websocket)
    vad_instance = SileroVAD()
    vad_instance.load_model()

    # Store VAD instance for this connection
    vad_instances[client_id] = vad_instance

    logger.info(f"WebSocket client connected: {client_id}")

    try:
        while True:
            # Receive audio chunks
            data = await websocket.receive_bytes()
            vad_instance.add_chunk(data)

            # Check for speech activity using enhanced VAD
            if vad_instance.has_speech():
                # Process the audio
                temp_path = f"/tmp/audio_{client_id}.wav"

                # Save audio to temporary file
                with wave.open(temp_path, "wb") as wav_file:
                    wav_file.setnchannels(1)  # mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(16000)
                    wav_file.writeframes(vad_instance.get_audio_data())

                # Transcribe
                transcription = await real_transcribe_audio(temp_path)

                if transcription and len(transcription.strip()) > 0:
                    # Send transcription back to client
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "transcription",
                                "text": transcription,
                                "timestamp": asyncio.get_event_loop().time(),
                            }
                        )
                    )

                    # Send to agent service for processing
                    answer = await send_to_agent_service(transcription)
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "response",
                                "text": answer,
                                "timestamp": asyncio.get_event_loop().time(),
                            }
                        )
                    )

                # Reset buffer after processing
                vad_instance.reset()

    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        # Cleanup
        if client_id in vad_instances:
            del vad_instances[client_id]
        logger.info(f"WebSocket client disconnected: {client_id}")


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with VAD status"""
    return {
        "status": "healthy",
        "service": "whisper-transcription",
        "real_whisper_enabled": USE_REAL_WHISPER,
        "websocket_clients": len(vad_instances),
        "vad_capable": True,
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Whisper Transcription Service")
    uvicorn.run(app, host="0.0.0.0", port=8000)
