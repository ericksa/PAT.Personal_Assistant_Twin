import sounddevice as sd
import numpy as np
import requests
import queue
import threading
from faster_whisper import WhisperModel
import time


class AudioCapture:
    def __init__(self):
        self.sample_rate = 16000
        self.chunk_duration = 3  # seconds
        self.audio_queue = queue.Queue()
        self.model = WhisperModel("base.en", device="cpu", compute_type="int8")

    def audio_callback(self, indata, frames, time, status):
        """Capture audio chunks"""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(indata.copy())

    def transcribe_continuous(self):
        """Continuous transcription with silence detection"""
        accumulated_audio = []
        silence_threshold = 0.01
        min_audio_length = 2.0  # seconds

        while True:
            try:
                # Collect audio chunks
                while not self.audio_queue.empty():
                    chunk = self.audio_queue.get()
                    accumulated_audio.extend(chunk.flatten())

                # Process if we have sufficient audio
                if len(accumulated_audio) > self.sample_rate * min_audio_length:
                    audio_array = np.array(accumulated_audio)

                    # Basic silence detection
                    if np.max(np.abs(audio_array)) > silence_threshold:
                        segments, info = self.model.transcribe(
                            audio_array,
                            beam_size=5,
                            vad_filter=True
                        )

                        transcript = " ".join([segment.text for segment in segments]).strip()

                        if transcript and len(transcript) > 5:
                            print(f"Transcribed: {transcript}")
                            self.send_to_brain(transcript)

                    accumulated_audio = []

                time.sleep(0.1)

            except Exception as e:
                print(f"Transcription error: {e}")
                accumulated_audio = []
                time.sleep(1)

    def send_to_brain(self, text):
        """Send transcription to brain service"""
        try:
            response = requests.post(
                "http://localhost:8000/api/process_audio",
                json={"text": text, "source": "interview"},
                timeout=10
            )
            print(f"Brain response: {response.status_code}")
        except Exception as e:
            print(f"Error sending to brain: {e}")

    def start(self):
        """Start audio capture system"""
        print("Initializing audio capture...")

        # Start transcription thread
        transcribe_thread = threading.Thread(target=self.transcribe_continuous, daemon=True)
        transcribe_thread.start()

        # Start audio stream
        with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=self.audio_callback,
                blocksize=int(self.sample_rate * self.chunk_duration)
        ):
            print("Audio capture started. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Stopping audio capture...")


if __name__ == "__main__":
    capture = AudioCapture()
    capture.start()