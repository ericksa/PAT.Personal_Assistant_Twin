#!/usr/bin/env python3
"""
Simple microphone test script
"""

import soundcard as sc
import numpy as np
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_microphone():
    """Test microphone input"""
    logger.info("🎙️  Testing microphone...")

    try:
        # Get default microphone
        mic = sc.default_microphone()
        logger.info(f"Using microphone: {mic.name}")

        # Test recording
        logger.info("🎤 Recording 5 seconds of audio...")
        with mic.recorder(samplerate=16000) as recorder:
            # Record for 5 seconds
            for i in range(5):
                data = recorder.record(numframes=16000)
                # Calculate audio level
                audio_level = np.sqrt(np.mean(data**2))
                logger.info(f"Second {i+1}: Audio level = {audio_level:.6f}")

                # Check if we're getting audio
                if audio_level > 0.001:
                    logger.info("✅ Audio detected - microphone is working!")
                else:
                    logger.warning("⚠️  Low audio level - check microphone settings")

                time.sleep(1)

        logger.info("🏁 Microphone test completed")
        return True

    except Exception as e:
        logger.error(f"❌ Microphone test failed: {e}")
        return False

def list_audio_devices():
    """List available audio devices"""
    logger.info("📋 Available audio devices:")

    # List speakers (for loopback)
    logger.info("Speakers (for loopback):")
    for speaker in sc.all_speakers():
        logger.info(f"  - {speaker.name}")

    # List microphones
    logger.info("Microphones:")
    for mic in sc.all_microphones():
        logger.info(f"  - {mic.name}")

if __name__ == "__main__":
    logger.info("🔧 Audio Device Test")

    # List devices
    list_audio_devices()

    # Test microphone
    logger.info("\n--- Microphone Test ---")
    test_microphone()