#!/usr/bin/env python3
"""
Microphone Integration Script for PAT System
Alternative version using sounddevice library (easier to install on macOS)
"""

import sounddevice as sd
import numpy as np
import wavio
import requests
import time

# Configuration
SAMPLE_RATE = 44100
CHANNELS = 1
DURATION = 5  # seconds
TEMP_AUDIO_FILE = "temp_recording.wav"
WHISPER_SERVICE_URL = "http://localhost:8004/transcribe"

def record_audio():
    """Record audio from microphone using sounddevice"""
    print("Initializing audio recording...")
    print(f"Recording for {DURATION} seconds. Speak now!")

    # Record audio
    audio_data = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=np.int16)
    sd.wait()  # Wait for recording to finish

    print("Finished recording.")

    # Save to WAV file
    wavio.write(TEMP_AUDIO_FILE, audio_data, SAMPLE_RATE, sampwidth=2)

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