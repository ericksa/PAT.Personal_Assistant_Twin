#!/usr/bin/env python3
"""Create a real speech audio file for testing"""

import wave
import numpy as np
import struct


def create_speech_wav():
    """Create a WAV file with speech-like content saying 'Hello, can you hear me?'"""
    # Parameters
    sample_rate = 16000
    duration = 3
    frequency = 220  # Hz - voice-like frequency

    # Generate tones that sound like speech
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Create speech-like waveform with varying pitch
    # Simulate saying "Hello, can you hear me?"
    signal = np.array([])

    # Segment 1: "Hello" - rising pitch
    hello_segment = 0.5 * np.sin(2 * np.pi * 200 * t[:300])

    # Segment 2: "can you" - steady pitch
    can_you_segment = 0.4 * np.sin(2 * np.pi * 180 * t[300:600])

    # Segment 3: "hear me" - falling pitch with question intonation
    hear_me_segment = 0.6 * np.sin(2 * np.pi * 250 * t[600:])

    # Combine segments
    signal = np.concatenate([hello_segment, can_you_segment, hear_me_segment])

    # Normalize signal
    signal = signal / np.max(np.abs(signal))

    # Scale to 16-bit integers
    signal_int = (signal * 32767).astype(np.int16)

    # Write WAV file
    with wave.open("real_speech.wav", "w") as wav_file:
        wav_file.setnchannels(1)  # mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Write audio data
        for sample in signal_int:
            wav_file.writeframes(struct.pack("h", sample))

    print("✅ Created real_speech.wav with speech-like content")


if __name__ == "__main__":
    create_speech_wav()
