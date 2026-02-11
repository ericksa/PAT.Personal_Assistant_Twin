#!/usr/bin/env python3
"""
Simple Audio Recording Script for PAT System
Uses system commands for audio recording (macOS/Linux)
"""

import subprocess
import requests
import time
import os

# Configuration
AUDIO_FILE = "recording.wav"
WHISPER_SERVICE_URL = "http://localhost:8004/transcribe"
RECORD_DURATION = 5  # seconds

def record_audio_with_sox():
    """Record audio using sox (if available)"""
    try:
        print(f"Recording {RECORD_DURATION} seconds of audio...")
        # Record audio using sox
        subprocess.run([
            "sox", "-d", AUDIO_FILE,
            "trim", "0", str(RECORD_DURATION)
        ], check=True)
        print("Audio recorded successfully.")
        return AUDIO_FILE
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Sox not found or failed. Trying alternative method...")
        return None

def record_audio_with_ffmpeg():
    """Record audio using ffmpeg (if available)"""
    try:
        print(f"Recording {RECORD_DURATION} seconds of audio with ffmpeg...")
        # Record audio using ffmpeg
        subprocess.run([
            "ffmpeg", "-y", "-f", "avfoundation", "-i", ":0",
            "-t", str(RECORD_DURATION), AUDIO_FILE
        ], check=True, capture_output=True)
        print("Audio recorded successfully.")
        return AUDIO_FILE
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FFmpeg not found or failed.")
        return None

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

def cleanup():
    """Remove temporary audio file"""
    if os.path.exists(AUDIO_FILE):
        os.remove(AUDIO_FILE)
        print(f"Removed temporary file: {AUDIO_FILE}")

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

    # Try different recording methods
    audio_file = None

    # Method 1: Try sox
    if not audio_file:
        audio_file = record_audio_with_sox()

    # Method 2: Try ffmpeg
    if not audio_file:
        audio_file = record_audio_with_ffmpeg()

    # If no recording method worked, provide manual instructions
    if not audio_file:
        print("\nNo automatic recording method found.")
        print("Please record a short audio file manually and save it as 'recording.wav'")
        input("Press Enter after you've created the recording file...")
        if os.path.exists("recording.wav"):
            audio_file = "recording.wav"
        else:
            print("Recording file not found. Exiting.")
            return

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

    # Clean up
    cleanup()

if __name__ == "__main__":
    main()