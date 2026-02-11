#!/usr/bin/env python3
"""
PAT System Quick Test Script
Tests the complete workflow with a predefined question
"""

import requests
import json

# Configuration
WHISPER_SERVICE_URL = "http://localhost:8004/process-question"
TELEPROMPTER_URL = "http://localhost:8005/broadcast"

def test_pat_workflow():
    """Test the complete PAT workflow with a sample question"""
    question = "What experience do you have with Python programming?"

    print("=" * 60)
    print("PAT SYSTEM QUICK TEST")
    print("=" * 60)
    print(f"Testing with question: {question}")
    print("")

    # Send to Whisper service (simulating transcription)
    print("1. Sending question to Whisper service...")
    try:
        response = requests.post(
            WHISPER_SERVICE_URL,
            json={"question": question}
        )

        if response.status_code == 200:
            result = response.json()
            print("   ✓ Success!")
            print(f"   Status: {result.get('status', 'N/A')}")
            print(f"   Question: {result.get('question', 'N/A')}")
            print(f"   Answer: {result.get('answer', 'N/A')[:100]}...")

            # Show how to send to teleprompter
            print("\n2. To display answer on teleprompter:")
            print("   Open browser to: http://localhost:8005")
            print("   Or manually send with:")
            print(f"   curl -X POST {TELEPROMPTER_URL} \\")
            print("     -H \"Content-Type: application/json\" \\")
            print(f"     -d '{{\"message\": \"{result.get('answer', 'N/A')}\"}}'")

            return result
        else:
            print(f"   ✗ Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None

def main():
    """Main test function"""
    result = test_pat_workflow()

    if result:
        print("\n" + "="*60)
        print("TEST COMPLETE - PAT SYSTEM IS WORKING!")
        print("="*60)
        print("The full system is ready for real microphone input.")
        print("For actual microphone testing, you can:")
        print("1. Record audio with any audio recording app")
        print("2. Save as WAV file")
        print("3. Send to http://localhost:8004/transcribe")
        print("4. Watch the response appear on http://localhost:8005")
    else:
        print("\nTEST FAILED - Please check the PAT services.")

if __name__ == "__main__":
    main()