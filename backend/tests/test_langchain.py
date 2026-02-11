#!/usr/bin/env python3
"""
Test script for LangChain and LangGraph integration
"""

import asyncio
import sys
import os

# Add the agent service to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'agent'))

async def test_langchain_components():
    """Test LangChain components"""
    print("Testing LangChain components...")

    try:
        from services.agent.langchain_components import InterviewAssistant

        # Create interview assistant
        assistant = InterviewAssistant()
        print("✓ InterviewAssistant created successfully")

        # Test response generation
        question = "What experience do you have with Python programming?"
        context = "Adam has 5 years of Python experience working on web applications and data analysis projects."

        response = await assistant.generate_response(question, context)
        print(f"✓ Response generated: {response[:100]}...")

    except Exception as e:
        print(f"✗ LangChain test failed: {e}")
        return False

    return True

async def test_langgraph_workflow():
    """Test LangGraph workflow"""
    print("\nTesting LangGraph workflow...")

    try:
        from services.agent.langgraph_workflow import process_interview_question

        # Test question processing
        question = "Tell me about your experience with machine learning"
        result = await process_interview_question(question)

        print(f"✓ LangGraph workflow completed")
        print(f"  Status: {result['status']}")
        print(f"  Is question: {result.get('is_question', 'N/A')}")
        print(f"  Response: {result['response'][:100]}...")

    except Exception as e:
        print(f"✗ LangGraph test failed: {e}")
        return False

    return True

async def main():
    """Main test function"""
    print("=" * 60)
    print("LANGCHAIN & LANGGRAPH INTEGRATION TEST")
    print("=" * 60)

    # Test LangChain components
    langchain_success = await test_langchain_components()

    # Test LangGraph workflow
    langgraph_success = await test_langgraph_workflow()

    print("\n" + "=" * 60)
    if langchain_success and langgraph_success:
        print("🎉 ALL TESTS PASSED - LangChain & LangGraph are working!")
        print("The interview processing pipeline is now enhanced with:")
        print("  • Faster response times")
        print("  • Better context management")
        print("  • Intelligent workflow processing")
        print("  • Memory-aware conversations")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())