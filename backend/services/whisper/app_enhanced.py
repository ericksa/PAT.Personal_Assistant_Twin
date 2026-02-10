# services/whisper/app_enhanced.py - Enhanced Whisper service with streaming VAD
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket
from pydantic import BaseModel
import logging
import os
import asyncio
import httpx
import numpy as np
import librosa
import wave
import struct
import json
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PAT Enhanced Whisper Service")

# Configuration
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8000")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")


class TranscriptionRequest(BaseModel):
    audio_url: str = None


class InterviewQuestion(BaseModel):
    question: str


class VADConfig(BaseModel):
    """Configuration for Voice Activity Detection"""

    threshold: float = 0.02
    min_silence_duration_ms: int = 500
    min_chunk_duration_ms: int = 500


class StreamingAudioProcessor:
    """Enhanced audio processing with streaming transcription capabilities"""

    def __init__(self, config: VADConfig = None):
        self.buffer = bytearray()
        self.sample_rate = 16000
        self.max_buffer_size = self.sample_rate * 10  # 10 seconds buffer
        self.channels = 1
        self.sample_width = 2  # 16-bit

        # Configuration
        self.config = config or VADConfig()
        self.min_audio_length = int(
            self.sample_rate * self.config.min_chunk_duration_ms / 1000
        )

        # Model and state
        self.transcription_model = None
        self.partial_transcription = ""

    def load_transcription_model(self):
        """Load the faster-whisper model for streaming"""
        if self.transcription_model is None:
            try:
                self.transcription_model = WhisperModel(
                    WHISPER_MODEL_SIZE, device="cpu"
                )
                logger.info(
                    f"Faster-whisper model '{WHISPER_MODEL_SIZE}' loaded for streaming transcription"
                )
            except Exception as e:
                logger.error(f"Failed to load transcription model: {e}")

    def add_chunk(self, chunk: bytes):
        """Add audio chunk to buffer"""
        self.buffer.extend(chunk)
        # Limit buffer size
        if len(self.buffer) > self.max_buffer_size:
            self.buffer = self.buffer[-self.max_buffer_size :]

    def reset(self):
        """Clear the buffer and partial transcription"""
        self.buffer.clear()
        self.partial_transcription = ""

    def has_speech(self) -> bool:
        """Enhanced voice activity detection"""
        if len(self.buffer) < self.min_audio_length:
            return False

        # Use faster-whisper's built-in VAD
        if self.transcription_model:
            try:
                temp_path = "/tmp/vad_check.wav"

                with wave.open(temp_path, "wb") as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(self.sample_width)
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(self.buffer)

                segments, info = self.transcription_model.transcribe(
                    temp_path,
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=self.config.min_silence_duration_ms
                    ),
                )

                # Check if any speech segments were detected
                return any(segments)

            except Exception as e:
                logger.warning(
                    f"Advanced VAD failed, falling back to energy detection: {e}"
                )

        # Fallback to energy-based detection
        return self.energy_based_vad()

    def energy_based_vad(self) -> bool:
        """Energy-based voice activity detection (fallback)"""
        if len(self.buffer) < self.min_audio_length:
            return False

        audio_data = np.frombuffer(self.buffer, dtype=np.int16)
        audio_float = audio_data.astype(float) / 32768.0
        energy = np.sqrt(np.mean(audio_float**2))

        return energy > self.config.threshold

    def transcribe_streaming(self) -> str:
        """Perform streaming transcription with partial results"""
        if self.transcription_model is None:
            self.load_transcription_model()
            if self.transcription_model is None:
                return "Model not available"

        if len(self.buffer) < self.min_audio_length:
            return ""

        try:
            temp_path = "/tmp/stream_audio.wav"
            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.sample_width)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(self.buffer)

            segments, info = self.transcription_model.transcribe(
                temp_path,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=self.config.min_silence_duration_ms
                ),
            )

            full_text = " ".join(segment.text for segment in segments).strip()

            # Update partial transcription
            if full_text and len(full_text) > len(self.partial_transcription):
                self.partial_transcription = full_text

            return full_text

        except Exception as e:
            logger.error(f"Streaming transcription error: {e}")
            return f"Transcription error: {str(e)}"

    def transcribe_partial(self) -> str:
        """Get current partial transcription"""
        return self.partial_transcription

    def get_audio_data(self) -> bytes:
        """Get audio data as bytes"""
        return bytes(self.buffer)

    def get_audio_info(self) -> dict:
        """Get information about the current audio buffer"""
        duration_seconds = len(self.buffer) / (
            self.sample_rate * self.sample_width * self.channels
        )
        return {
            "buffer_size_bytes": len(self.buffer),
            "duration_seconds": round(duration_seconds, 2),
            "sample_rate": self.sample_rate,
            "partial_transcription": self.partial_transcription,
        }


# Global streaming processors for WebSocket connections
streaming_processors = {}


async def real_transcribe_audio(file_path: str) -> str:
    """Real transcription using faster-whisper"""
    try:
        logger.info(f"Real transcription started for: {file_path}")

        model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu")

        segments, info = model.transcribe(file_path)
        transcription = " ".join(segment.text for segment in segments)

        logger.info(f"Real transcription successful: {transcription[:100]}...")
        return transcription.strip()

    except Exception as e:
        logger.error(f"Real transcription failed: {e}")
        return f"Transcription failed: {str(e)}"


async def send_to_agent_service(question: str) -> str:
    """Send transcribed question to agent service for RAG response"""
    try:
        logger.info(f"Sending to agent service: {AGENT_SERVICE_URL}/query")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_SERVICE_URL}/query",
                json={"query": question, "user_id": "default"},
                timeout=120,
            )

        if response.status_code == 200:
            result = response.json()
            answer = result.get("response", "No response from agent service")
            logger.info(f"Agent response received: {answer[:100]}...")
            return answer
        else:
            logger.error(f"Agent service error: {response.status_code}")
            return f"Agent service unavailable: {response.status_code}"

    except Exception as e:
        logger.error(f"Agent service communication error: {e}", exc_info=True)
        return f"Agent service error: {str(e)}"


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Upload audio file for transcription and processing"""
    try:
        filename = file.filename or "audio_file.wav"
        temp_path = f"/tmp/{filename}"

        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        question = await real_transcribe_audio(temp_path)
        answer = await send_to_agent_service(question)

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
    """Process text-based interview question"""
    try:
        answer = await send_to_agent_service(request.question)
        return {"status": "processed", "question": request.question, "answer": answer}

    except Exception as e:
        logger.error(f"Question processing error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Question processing failed: {str(e)}"
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time audio streaming endpoint with enhanced VAD"""
    await websocket.accept()
    client_id = id(websocket)

    # Create streaming processor for this connection
    processor = StreamingAudioProcessor()
    streaming_processors[client_id] = processor

    logger.info(f"WebSocket client connected: {client_id}")

    try:
        while True:
            data = await websocket.receive_bytes()
            processor.add_chunk(data)

            # Check for speech activity
            if processor.has_speech():
                # Perform streaming transcription
                transcription = processor.transcribe_streaming()
                partial = processor.transcribe_partial()

                if transcription:
                    # Send transcription back to client
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "transcription",
                                "text": transcription,
                                "partial": partial,
                                "timestamp": asyncio.get_event_loop().time(),
                                "status": "processing",
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
                                "status": "complete",
                            }
                        )
                    )

                    # Reset processor for next utterance
                    processor.reset()

            # Send audio stats periodically
            audio_info = processor.get_audio_info()
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "audio_info",
                        "buffer_size": audio_info["buffer_size_bytes"],
                        "duration": audio_info["duration_seconds"],
                        "partial": audio_info["partial_transcription"],
                    }
                )
            )

    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        if client_id in streaming_processors:
            del streaming_processors[client_id]
        logger.info(f"WebSocket client disconnected: {client_id}")


@app.post("/vad-configure")
async def configure_vad(config: VADConfig):
    """Configure VAD parameters for all active connections"""
    for processor in streaming_processors.values():
        processor.config = config

    return {
        "status": "configured",
        "threshold": config.threshold,
        "min_silence_duration_ms": config.min_silence_duration_ms,
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "enhanced-whisper",
        "streaming_clients": len(streaming_processors),
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with streaming processor info"""
    processor_info = []
    for client_id, processor in streaming_processors.items():
        info = processor.get_audio_info()
        info["client_id"] = client_id
        processor_info.append(info)

    return {
        "status": "healthy",
        "service": "enhanced-whisper",
        "streaming_clients": len(streaming_processors),
        "processors": processor_info,
        "model_size": WHISPER_MODEL_SIZE,
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Enhanced Whisper Transcription Service")
    uvicorn.run(app, host="0.0.0.0", port=8000)
