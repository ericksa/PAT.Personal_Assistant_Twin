#!/usr/bin/env python3
"""
PAT System Workflow Demonstration Script
Demonstrates the complete workflow without requiring audio recording
"""

import requests
import json

# Configuration
WHISPER_SERVICE_URL = "http://localhost:8004/process-question"
TELEPROMPTER_URL = "http://localhost:8005/broadcast"

def simulate_voice_input():
    """Simulate voice input with predefined questions"""
    questions = [
        "What experience do you have with Python programming?",
        "Can you tell me about a challenging project you worked on?",
        "How do you handle difficult situations at work?",
        "What are your strengths and weaknesses?",
        "Why do you want to work for our company?"
    ]

    print("Available interview questions:")
    for i, question in enumerate(questions, 1):
        print(f"{i}. {question}")

    try:
        choice = int(input("\nSelect a question number (1-5) or enter 0 for custom: "))
        if choice == 0:
            custom_question = input("Enter your custom question: ")
            return custom_question
        elif 1 <= choice <= 5:
            return questions[choice - 1]
        else:
            print("Invalid choice, using default question.")
            return questions[0]
    except ValueError:
        print("Invalid input, using default question.")
        return questions[0]

def send_to_whisper_service(question):
    """Send text question to Whisper service (simulating transcription)"""
    print(f"\nSending question to Whisper service: {question}")

    try:
        response = requests.post(
            WHISPER_SERVICE_URL,
            json={"question": question}
        )

        if response.status_code == 200:
            result = response.json()
            print("✓ Whisper service processed successfully")
            return result
        else:
            print(f"✗ Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"✗ Error communicating with Whisper service: {e}")
        return None

def display_results(result):
    """Display the results and provide instructions for teleprompter"""
    if result:
        print("\n" + "="*60)
        print("INTERVIEW SIMULATION RESULTS")
        print("="*60)
        print(f"Question: {result.get('question', 'N/A')}")
        print(f"Answer: {result.get('answer', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")

        print("\n" + "-"*40)
        print("TELEPROMPTER INSTRUCTIONS:")
        print("-"*40)
        print("1. Open your browser to: http://localhost:8005")
        print("2. The AI-generated answer should appear automatically")
        print("3. If it doesn't appear, you can manually send it with:")
        print(f"   curl -X POST {TELEPROMPTER_URL} \\")
        print("     -H \"Content-Type: application/json\" \\")
        print(f"     -d '{{\"message\": \"{result.get('answer', 'N/A')}\"}}'")
        print("-"*40)

def main():
    """Main demonstration function"""
    print("=" * 60)
    print("PAT SYSTEM WORKFLOW DEMONSTRATION")
    print("=" * 60)
    print("This script simulates the complete PAT interview workflow:")
    print("1. Voice input → 2. Transcription → 3. AI Response → 4. Teleprompter Display")
    print("")

    # Get question from user
    question = simulate_voice_input()

    # Process through the system
    result = send_to_whisper_service(question)

    # Display results
    display_results(result)

    print("\n🎉 Demo complete! The full system is ready for real microphone input.")

if __name__ == "__main__":
    main()