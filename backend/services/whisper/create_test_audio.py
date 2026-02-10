#!/usr/bin/env python3
"""Create a test audio file for whisper service testing"""

import librosa
import soundfile as sf
import numpy as np


# Create a simple sine wave audio file
def create_test_audio():
    # Generate a 5-second sine wave at 440Hz
    sample_rate = 16000
    duration = 5
    t = np.linspace(0, duration, int(sample_rate * duration))
    signal = 0.5 * np.sin(2 * np.pi * 440 * t)

    # Save as WAV file
    sf.write("test_audio.wav", signal, sample_rate)
    print("✅ Created test_audio.wav (5-second 440Hz tone)")


if __name__ == "__main__":
    create_test_audio()
