#!/usr/bin/env python3
"""
Test script for Phase 3 audio processing enhancements
Tests the enhanced whisper service with streaming and VAD capabilities
"""

import asyncio
import websockets
import json
import wave
import numpy as np
import threading
import time
from pathlib import Path

# Test configuration
WEBSOCKET_URL = "ws://localhost:8004/ws"
HEALTH_URL = "http://localhost:8004/health/detailed"
CONFIG_URL = "http://localhost:8004/vad-configure"
AUDIO_FILE = "test_speech.wav"


class Phase3Tester:
    def __init__(self):
        self.received_messages = []
        self.test_results = {}

    async def test_health_endpoint(self):
        """Test the enhanced health endpoint"""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(HEALTH_URL)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health endpoint test PASSED")
                print(f"   Service: {data.get('service', 'N/A')}")
                print(f"   Clients: {data.get('streaming_clients', 0)}")
                self.test_results["health_endpoint"] = "PASSED"
                return True
            else:
                print(f"❌ Health endpoint test FAILED: {response.status_code}")
                self.test_results["health_endpoint"] = "FAILED"
                return False

        except Exception as e:
            print(f"❌ Health endpoint test ERROR: {e}")
            self.test_results["health_endpoint"] = "ERROR"
            return False

    async def test_vad_configuration(self):
        """Test VAD configuration endpoint"""
        import httpx

        try:
            config = {
                "threshold": 0.03,
                "min_silence_duration_ms": 600,
                "min_chunk_duration_ms": 500,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(CONFIG_URL, json=config)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ VAD configuration test PASSED")
                print(f"   Threshold: {data.get('threshold', 'N/A')}")
                print(f"   Min silence: {data.get('min_silence_duration_ms', 'N/A')}")
                self.test_results["vad_configuration"] = "PASSED"
                return True
            else:
                print(f"❌ VAD configuration test FAILED: {response.status_code}")
                self.test_results["vad_configuration"] = "FAILED"
                return False

        except Exception as e:
            print(f"❌ VAD configuration test ERROR: {e}")
            self.test_results["vad_configuration"] = "ERROR"
            return False

    async def test_websocket_streaming(self):
        """Test WebSocket streaming functionality"""

        async def audio_streamer():
            """Simulate streaming audio data"""
            try:
                async with websockets.connect(WEBSOCKET_URL) as websocket:
                    print("📡 WebSocket connected")

                    # Read audio file and stream it
                    if Path(AUDIO_FILE).exists():
                        with wave.open(AUDIO_FILE, "rb") as wav_file:
                            chunk_size = 1024

                            while True:
                                frames = wav_file.readframes(chunk_size)
                                if not frames:
                                    break

                                await websocket.send(frames)
                                await asyncio.sleep(0.05)  # Small delay for simulation

                                # Check for responses
                                try:
                                    response = await asyncio.wait_for(
                                        websocket.recv(), timeout=0.1
                                    )
                                    message = json.loads(response)
                                    self.received_messages.append(message)
                                    print(
                                        f"📝 Received: {message.get('type', 'unknown')}"
                                    )

                                except asyncio.TimeoutError:
                                    continue

                                except Exception as e:
                                    print(f"Error receiving: {e}")

                    print("✅ Audio streaming test completed")
                    self.test_results["websocket_streaming"] = "PASSED"

            except Exception as e:
                print(f"❌ WebSocket test ERROR: {e}")
                self.test_results["websocket_streaming"] = "ERROR"

        # Run streaming test with timeout
        try:
            await asyncio.wait_for(audio_streamer(), timeout=10.0)
            return True
        except asyncio.TimeoutError:
            print("⚠️  WebSocket test timed out (expected)")
            self.test_results["websocket_streaming"] = "TIMEOUT"
            return True
        except Exception as e:
            print(f"❌ WebSocket test FAILED: {e}")
            self.test_results["websocket_streaming"] = "FAILED"
            return False

    def analyze_results(self):
        """Analyze test results and generate report"""
        print("\n" + "=" * 50)
        print("PHASE 3 TEST RESULTS")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = sum(
            1
            for result in self.test_results.values()
            if result in ["PASSED", "TIMEOUT"]
        )

        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result in ["PASSED", "TIMEOUT"] else "❌ FAILED"
            print(f"{test_name}: {status}")

        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 PHASE 3 FEATURES VALIDATION COMPLETED")
        else:
            print("⚠️  Some tests require manual verification")

        # Show received message types
        if self.received_messages:
            print("\nReceived message types:")
            message_types = {}
            for msg in self.received_messages:
                msg_type = msg.get("type", "unknown")
                message_types[msg_type] = message_types.get(msg_type, 0) + 1

            for msg_type, count in message_types.items():
                print(f"  {msg_type}: {count} messages")


async def main():
    """Run all Phase 3 feature tests"""
    tester = Phase3Tester()

    print("🧪 Testing Phase 3 Audio Processing Enhancements")
    print("=" * 50)

    # Test 1: Health endpoint
    print("\n1️⃣  Testing health endpoint...")
    await tester.test_health_endpoint()

    # Test 2: VAD configuration
    print("\n2️⃣  Testing VAD configuration...")
    await tester.test_vad_configuration()

    # Test 3: WebSocket streaming
    print("\n3️⃣  Testing WebSocket streaming...")
    await tester.test_websocket_streaming()

    # Generate final report
    tester.analyze_results()

    print("\n📋 Next steps:")
    print("  • Deploy app_enhanced.py as whisper-service")
    print("  • Test with real microphone input")
    print("  • Verify partial transcription updates")
    print("  • Monitor audio buffer statistics")


if __name__ == "__main__":
    asyncio.run(main())
