# services/agent/langchain_components.py - LangChain components for PAT Agent Service
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama  # Updated import for newer LangChain versions
from langchain_core.tools import tool  # Updated import for tools
import asyncio
import logging

logger = logging.getLogger(__name__)

# Tool for web search
@tool
def web_search_tool(query: str) -> str:
    """Search the web for current information"""
    # This would integrate with your existing web search functionality
    return f"Web search results for '{query}' would appear here."

# Tool for document search
@tool
def document_search_tool(query: str) -> str:
    """Search local documents for relevant information"""
    # This would integrate with your existing document search functionality
    return f"Document search results for '{query}' would appear here."

# Create tools for the agent
def create_interview_tools():
    """Create tools for the interview assistant agent"""
    return [web_search_tool, document_search_tool]

def create_interview_agent():
    """Create a LangChain agent for interview assistance"""
    from langchain_ollama import ChatOllama
    try:
        from langchain.agents import create_react_agent
    except ImportError:
        # Fallback for newer LangChain versions
        from langchain.agents import create_react_agent

    llm = ChatOllama(
        model="llama3:8b",
        base_url="http://host.docker.internal:11434",
        temperature=0.7
    )

    tools = create_interview_tools()

    # Create the agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=ChatPromptTemplate.from_messages([
            ("system", """You are PAT (Personal Assistant Twin), helping with interview preparation.

            You have access to tools that can help answer questions:
            - web_search: For current information and facts
            - document_search: For information about Adam's experience and background

            Use the tools when needed to provide comprehensive answers.
            Always provide clear, professional responses suitable for reading aloud."""),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
    )

    return agent