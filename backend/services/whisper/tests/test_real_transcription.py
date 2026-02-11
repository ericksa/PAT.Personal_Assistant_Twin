#!/usr/bin/env python3
"""Test faster-whisper transcription functionality"""

import asyncio
import time
from faster_whisper import WhisperModel


def test_transcription():
    """Test basic faster-whisper transcription"""
    print("🧪 Testing faster-whisper transcription...")

    try:
        # Load model
        print("🔄 Loading whisper model...")
        start_time = time.time()
        model = WhisperModel("base")
        load_time = time.time() - start_time
        print(f"✅ Model loaded in {load_time:.2f} seconds")

        # Test transcription
        print("🔄 Testing transcription...")
        start_time = time.time()
        segments, info = model.transcribe("speech_audio.wav")
        transcription = " ".join(segment.text for segment in segments)
        transcribe_time = time.time() - start_time

        print(f"✅ Transcription completed in {transcribe_time:.2f} seconds")
        print(f"📝 Transcription: {transcription}")
        print(
            f"🔍 Language: {info.language}, Probability: {info.language_probability:.2f}"
        )

        # Test with a more complex file
        print("\n🔄 Testing with a speech-like file...")
        start_time = time.time()
        segments, info = model.transcribe("speech_audio.wav")
        transcription = " ".join(segment.text for segment in segments)
        transcribe_time = time.time() - start_time

        print(f"✅ Speech test completed in {transcribe_time:.2f} seconds")
        print(f"📝 Transcription: {transcription}")

        return True

    except Exception as e:
        print(f"❌ Transcription test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_transcription()
    if success:
        print("\n🎉 Faster-whisper transcription test PASSED!")
    else:
        print("\n💥 Faster-whisper transcription test FAILED!")
