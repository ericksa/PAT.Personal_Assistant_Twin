from requests import packages
import soundcard as sc
import numpy as np
import requests
from faster_whisper import WhisperModel
import threading
import queue
import time

# CONFIG
AGENT_URL = "http://localhost:8002/interview/analyze"
MODEL_SIZE = "base.en"
THRESHOLD = 0.02

# Initialize Whisper
print("Loading Whisper model...")
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

audio_queue = queue.Queue()


def audio_listener():
    """Capture system audio"""
    default_speaker = sc.default_speaker()
    default_mic = sc.default_microphone()

    print("Listening to system audio... Press Ctrl+C to stop.")

    with default_mic.record(samplerate=48000, channels=2) as rec:
        for data in rec:
            # Check for audio above threshold
            if np.max(np.abs(data)) > THRESHOLD:
                audio_queue.put(data.copy())


def transcription_worker():
    """Process audio queue"""
    while True:
        if not audio_queue.empty():
            audio_data = audio_queue.get()

            # Convert to mono and resample
            audio_mono = np.mean(audio_data, axis=1)

            try:
                # Transcribe
                segments, info = model.transcribe(audio_mono, beam_size=5)
                transcript = " ".join([segment.text for segment in segments]).strip()

                if transcript and len(transcript) > 5:
                    print(f"🎤 Heard: {transcript}")

                    # Send to agent-service
                    response = requests.post(AGENT_URL, json={"text": transcript})
                    if response.status_code == 200:
                        print(f"✅ Response: {response.json()['response']['answer']}")
                    else:
                        print(f"❌ Error: {response.status_code}")

            except Exception as e:
                print(f"❌ Transcription error: {e}")

        time.sleep(0.5)


if __name__ == "__main__":
    # Start threads
    audio_thread = threading.Thread(target=audio_listener, daemon=True)
    transcribe_thread = threading.Thread(target=transcription_worker, daemon=True)

    audio_thread.start()
    transcribe_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("👋 Shutting down...")