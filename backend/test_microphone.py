#!/usr/bin/env python3
"""
Microphone Integration Script for PAT System
Records audio from microphone and sends to PAT Whisper service
"""

import pyaudio
import wave
import requests
import json
import time
import threading
from io import BytesIO

# Configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
TEMP_AUDIO_FILE = "temp_recording.wav"
WHISPER_SERVICE_URL = "http://localhost:8004/transcribe"

def record_audio():
    """Record audio from microphone"""
    print("Initializing audio recording...")

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording... Speak now!")
    frames = []

    # Record for RECORD_SECONDS
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded data to a WAV file
    wf = wave.open(TEMP_AUDIO_FILE, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return TEMP_AUDIO_FILE

def send_to_whisper(audio_file_path):
    """Send audio file to Whisper service"""
    print(f"Sending audio to Whisper service at {WHISPER_SERVICE_URL}")

    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'file': (audio_file_path, audio_file, 'audio/wav')}
            response = requests.post(WHISPER_SERVICE_URL, files=files)

        if response.status_code == 200:
            result = response.json()
            print("Whisper service response:")
            print(f"  Status: {result.get('status', 'N/A')}")
            print(f"  Question: {result.get('question', 'N/A')}")
            print(f"  Answer: {result.get('answer', 'N/A')}")
            print(f"  Message: {result.get('message', 'N/A')}")
            return result
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Error sending to Whisper service: {e}")
        return None

def main():
    """Main function to record audio and send to PAT system"""
    print("=" * 50)
    print("PAT Microphone Integration Script")
    print("=" * 50)
    print("This script will:")
    print("1. Record 5 seconds of audio from your microphone")
    print("2. Send the recording to the PAT Whisper service")
    print("3. Display the transcribed question and AI-generated answer")
    print("")

    input("Press Enter to start recording (speak after pressing Enter)...")

    # Record audio
    audio_file = record_audio()

    # Send to Whisper service
    print("\nProcessing your audio...")
    result = send_to_whisper(audio_file)

    if result:
        print("\n" + "="*50)
        print("INTERVIEW SIMULATION COMPLETE")
        print("="*50)
        print("Check the teleprompter at http://localhost:8005")
        print("to see the AI-generated answer!")
    else:
        print("Failed to process audio.")

if __name__ == "__main__":
    main()