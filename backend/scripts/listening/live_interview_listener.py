live_interview_listener.py

  #!/usr/bin/env python3
  """
  Live Interview Listener
  Captures system audio/microphone, transcribes speech, and sends to PAT agent service
  """

  import soundcard as sc
  import numpy as np
  import requests
  import threading
  import queue
  import time
  import json
  import logging
  from typing import Optional
  from faster_whisper import WhisperModel

  # Configure logging
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  )
  logger = logging.getLogger(__name__)

  # --- CONFIGURATION ---
  class Config:
      # Agent service endpoint
      AGENT_SERVICE_URL = "http://localhost:8002/interview/process"

      # Whisper model settings
      WHISPER_MODEL_SIZE = "base.en"  # Options: tiny.en, base.en, small.en, medium.en
      WHISPER_DEVICE = "auto"  # auto, cpu, cuda

      # Audio settings
      SAMPLE_RATE = 16000
      RECORD_DURATION = 5  # seconds
      AUDIO_THRESHOLD = 0.02  # Silence threshold (0-1)

      # Processing settings
      MIN_TRANSCRIPTION_LENGTH = 10  # Minimum characters to send
      MAX_RETRY_ATTEMPTS = 3
      RETRY_DELAY = 2  # seconds

  class AudioTranscriber:
      """Handles audio transcription using faster-whisper"""

      def __init__(self, model_size: str = "base.en", device: str = "auto"):
          logger.info(f"Loading Whisper model: {model_size}")

          # Auto-detect device
          if device == "auto":
              try:
                  import torch
                  device = "cuda" if torch.cuda.is_available() else "cpu"
              except ImportError:
                  device = "cpu"

          try:
              compute_type = "float16" if device == "cuda" else "int8"
              self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
              logger.info(f"Whisper model loaded on {device}")
          except Exception as e:
              logger.error(f"Failed to load Whisper model: {e}")
              raise

      def transcribe(self, audio_data: np.ndarray) -> str:
          """Transcribe audio data to text"""
          try:
              segments, info = self.model.transcribe(
                  audio_data,
                  beam_size=5,
                  vad_filter=True,  # Enable voice activity detection
                  vad_parameters=dict(min_silence_duration_ms=500)
              )

              # Combine all segments
              full_text = "".join(segment.text for segment in segments).strip()
              return full_text
          except Exception as e:
              logger.error(f"Transcription error: {e}")
              return ""

  class AudioManager:
      """Manages audio recording and processing"""

      def __init__(self, config: Config):
          self.config = config
          self.audio_queue = queue.Queue()
          self.transcriber = AudioTranscriber(
              model_size=config.WHISPER_MODEL_SIZE,
              device=config.WHISPER_DEVICE
          )
          self.is_recording = False
          self.is_processing = False

      def start_listening(self):
          """Start listening for audio"""
          logger.info("🎙️ Starting audio listener...")

          # Start recording and processing threads
          self.is_recording = True
          self.is_processing = True

          record_thread = threading.Thread(target=self._record_audio, daemon=True)
          process_thread = threading.Thread(target=self._process_audio, daemon=True)

          record_thread.start()
          process_thread.start()

          logger.info("🎧 Audio listener started. Press Ctrl+C to stop.")
          return record_thread, process_thread

      def stop_listening(self):
          """Stop listening for audio"""
          logger.info("🛑 Stopping audio listener...")
          self.is_recording = False
          self.is_processing = False

      def _record_audio(self):
          """Record audio from system audio and/or microphone"""
          logger.info("🎤 Starting audio recording...")

          try:
              # Try system audio loopback first
              self._record_system_audio()
          except Exception as e:
              logger.warning(f"System audio recording failed: {e}")
              logger.info(" Falling back to microphone only...")
              try:
                  self._record_microphone_only()
              except Exception as e2:
                  logger.error(f"Microphone recording also failed: {e2}")
                  logger.error("❌ Unable to capture audio. Please check your audio settings.")

      def _record_system_audio(self):
          """Record system audio (what you hear)"""
          # Get default speaker as loopback device
          speaker = sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True)
          logger.info(f"Recording system audio from: {speaker.name}")

          with speaker.recorder(samplerate=self.config.SAMPLE_RATE) as recorder:
              while self.is_recording:
                  try:
                      # Record audio chunk
                      data = recorder.record(numframes=self.config.SAMPLE_RATE * self.config.RECORD_DURATION)

                      # Check if audio level exceeds threshold (VAD)
                      audio_level = np.sqrt(np.mean(data**2))
                      if audio_level > self.config.AUDIO_THRESHOLD:
                          logger.debug(f"Audio detected (level: {audio_level:.4f})")
                          # Convert to mono if stereo
                          mono_data = data[:, 0] if len(data.shape) > 1 else data
                          self.audio_queue.put(mono_data)
                      else:
                          logger.debug(f"Silence detected (level: {audio_level:.4f})")

                  except Exception as e:
                      logger.error(f"Recording error: {e}")
                      break

      def _record_microphone_only(self):
          """Fallback to microphone-only recording"""
          mic = sc.default_microphone()
          logger.info(f"Recording from microphone: {mic.name}")

          with mic.recorder(samplerate=self.config.SAMPLE_RATE) as recorder:
              while self.is_recording:
                  try:
                      data = recorder.record(numframes=self.config.SAMPLE_RATE * self.config.RECORD_DURATION)

                      # Check if audio level exceeds threshold
                      audio_level = np.sqrt(np.mean(data**2))
                      if audio_level > self.config.AUDIO_THRESHOLD:
                          logger.debug(f"Microphone audio detected (level: {audio_level:.4f})")
                          # Convert to mono if stereo
                          mono_data = data[:, 0] if len(data.shape) > 1 else data
                          self.audio_queue.put(mono_data)

                  except Exception as e:
                      logger.error(f"Microphone recording error: {e}")
                      break

      def _process_audio(self):
          """Process queued audio and send transcriptions"""
          logger.info("🔄 Starting audio processing...")

          while self.is_processing:
              try:
                  # Wait for audio with timeout
                  audio_data = self.audio_queue.get(timeout=1.0)

                  # Transcribe audio
                  transcription = self.transcriber.transcribe(audio_data)

                  # Process transcription if long enough
                  if len(transcription) >= self.config.MIN_TRANSCRIPTION_LENGTH:
                      logger.info(f"📝 Transcribed: {transcription}")
                      self._send_to_agent(transcription)
                  else:
                      logger.debug(f"⏭️  Skipping short transcription: '{transcription}'")

              except queue.Empty:
                  # No audio to process, continue loop
                  continue
              except Exception as e:
                  logger.error(f"Audio processing error: {e}")

      def _send_to_agent(self, text: str):
          """Send transcribed text to agent service with retry logic"""
          payload = {
              "text": text.strip(),
              "source": "interviewer"
          }

          for attempt in range(self.config.MAX_RETRY_ATTEMPTS):
              try:
                  logger.debug(f"📤 Sending to agent (attempt {attempt + 1}): {text[:50]}...")

                  response = requests.post(
                      self.config.AGENT_SERVICE_URL,
                      json=payload,
                      timeout=30,
                      headers={'Content-Type': 'application/json'}
                  )

                  if response.status_code == 200:
                      logger.info("✅ Successfully sent to agent service")
                      return True
                  else:
                      logger.warning(f"⚠️  Agent service returned {response.status_code}: {response.text}")

              except requests.exceptions.ConnectionError:
                  logger.error(f"🔌 Connection error (attempt {attempt + 1})")
              except requests.exceptions.Timeout:
                  logger.error(f"⏰ Timeout error (attempt {attempt + 1})")
              except Exception as e:
                  logger.error(f"❌ Request error (attempt {attempt + 1}): {e}")

              # Retry with delay
              if attempt < self.config.MAX_RETRY_ATTEMPTS - 1:
                  logger.info(f"🔁 Retrying in {self.config.RETRY_DELAY} seconds...")
                  time.sleep(self.config.RETRY_DELAY)

          logger.error("💥 Failed to send to agent service after all retries")
          return False

  def main():
      """Main entry point"""
      logger.info("🚀 Starting Live Interview Listener")
      logger.info("Ensure your Docker services are running:")
      logger.info("  docker-compose up -d")

      # Create config
      config = Config()

      # Create audio manager
      audio_manager = AudioManager(config)

      # Start listening
      try:
          record_thread, process_thread = audio_manager.start_listening()

          # Keep main thread alive
          logger.info("🎙️  Listening for interview audio... Press Ctrl+C to stop")
          while True:
              time.sleep(1)

      except KeyboardInterrupt:
          logger.info("\n🛑 Keyboard interrupt received")
          audio_manager.stop_listening()
          logger.info("👋 Interview listener stopped")

  if __name__ == "__main__":
      main()