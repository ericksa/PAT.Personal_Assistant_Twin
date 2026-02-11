#!/usr/bin/env python3
"""Create a realistic test audio file with speech-like content"""

import librosa
import soundfile as sf
import numpy as np


def create_speech_audio():
    # Generate speech-like audio with varying frequencies
    sample_rate = 16000
    duration = 3
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Create speech-like signal with multiple frequencies
    signal = (
        0.3 * np.sin(2 * np.pi * 120 * t)  # Fundamental frequency
        + 0.2 * np.sin(2 * np.pi * 240 * t)  # First harmonic
        + 0.1 * np.sin(2 * np.pi * 360 * t)  # Second harmonic
    )

    # Add some variation to simulate speech cadence
    envelope = np.sin(2 * np.pi * 3 * t) * 0.5 + 0.5
    signal = signal * envelope

    # Save as WAV file
    sf.write("speech_audio.wav", signal, sample_rate)
    print("✅ Created speech_audio.wav (3-second speech-like signal)")


if __name__ == "__main__":
    create_speech_audio()
