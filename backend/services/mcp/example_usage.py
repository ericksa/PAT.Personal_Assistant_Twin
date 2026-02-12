#!/usr/bin/env python3
"""
Example: Using the MCP Server via HTTP API
Demonstrates basic interactions with the PAT MCP Server
"""

import requests
import json

MCP_SERVER_URL = "http://localhost:8003"


def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Execute a tool via HTTP API"""
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/execute",
            json={"tool_name": tool_name, "arguments": arguments},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# Example 1: RAG Search
print("=" * 60)
print("Example 1: RAG Document Search")
print("=" * 60)
search_result = execute_tool(
    "rag_search", {"query": "Python experience", "top_k": 3, "threshold": 0.2}
)
print(json.dumps(search_result, indent=2))
print()

# Example 2: Create a Plan (MCP)
print("=" * 60)
print("Example 2: Create Multi-Step Plan")
print("=" * 60)
plan_result = execute_tool(
    "create_plan",
    {
        "goal": "Prepare for a technical interview",
        "context": "Position requires Python, React, and machine learning experience",
    },
)
print(json.dumps(plan_result, indent=2))
print()

# Example 3: Store Memory
print("=" * 60)
print("Example 3: Store Interview Memory")
print("=" * 60)
memory_result = execute_tool(
    "memory_store",
    {
        "key": "interview_topic",
        "value": "Currently discussing machine learning projects",
        "ttl": 3600,
    },
)
print(json.dumps(memory_result, indent=2))
print()

# Example 4: Retrieve Memory
print("=" * 60)
print("Example 4: Retrieve Interview Memory")
print("=" * 60)
retrieve_result = execute_tool("memory_retrieve", {"key": "interview_topic"})
print(json.dumps(retrieve_result, indent=2))
print()

# Example 5: Perform Reasoning Step
print("=" * 60)
print("Example 5: Reasoning Step")
print("=" * 60)
reasoning_result = execute_tool(
    "reason_step",
    {
        "question": "How should I structure my answer about machine learning projects?",
        "context": "I have experience with scikit-learn and TensorFlow",
    },
)
print(json.dumps(reasoning_result, indent=2))
print()

# Example 6: List Available Tools
print("=" * 60)
print("Example 6: List Available Tools")
print("=" * 60)
tools_response = requests.get(f"{MCP_SERVER_URL}/tools")
tools_response.raise_for_status()
tools = tools_response.json()
print(json.dumps(tools, indent=2))
print()

# Example 7: Health Check
print("=" * 60)
print("Example 7: Health Check")
print("=" * 60)
health_response = requests.get(f"{MCP_SERVER_URL}/health")
health_response.raise_for_status()
health = health_response.json()
print(json.dumps(health, indent=2))
print()
