from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import HumanMessage, AIMessage
import operator
import asyncio
import logging

logger = logging.getLogger(__name__)


# Define the state structure
class InterviewState(TypedDict):
    question: str
    context: str
    is_question: bool
    needs_web_search: bool
    web_search_results: str
    document_search_results: str
    final_response: str
    error: str


# Node functions for the graph
async def detect_question(state: InterviewState) -> InterviewState:
    """Detect if the input is actually a question"""
    try:
        # Use absolute import
        from utils import is_question

        logger.info("Using utils.is_question")
    except ImportError:
        try:
            # Alternative import
            from utils import is_question

            logger.info("Using utils.is_question (direct)")
        except ImportError:
            # Fallback for when running in different environments
            def is_question(text):
                """Default question detection"""
                question_words = [
                    "what",
                    "how",
                    "why",
                    "when",
                    "where",
                    "who",
                    "can",
                    "could",
                    "would",
                    "should",
                ]
                text_lower = text.lower().strip()
                return (
                    any(text_lower.startswith(word) for word in question_words)
                    or "?" in text
                )

            logger.info("Using fallback is_question function")

    is_q = is_question(state["question"])
    logger.info(
        f"Question detection: {'Yes' if is_q else 'No'} - '{state['question']}'"
    )

    # Return full state with updated field
    return {**state, "is_question": is_q}


async def search_documents(state: InterviewState) -> InterviewState:
    """Search local documents for context"""
    try:
        # This would integrate with your existing document search
        # For now, we'll simulate the search
        logger.info(f"Searching documents for: {state['question']}")

        # In a real implementation, this would call your search function
        # local_results = await search_local_documents(state["question"])
        # context = build_context(local_results, [])

        simulated_context = f"Relevant information about '{state['question']}' from Adam's experience and background."

        return {**state, "context": simulated_context}
    except Exception as e:
        logger.error(f"Document search error: {e}")
        return {**state, "context": "No relevant documents found."}


async def check_needs_web_search(state: InterviewState) -> InterviewState:
    """Determine if web search is needed"""
    # Simple heuristic: if no local context or specific keywords
    needs_search = len(state["context"]) < 50 or any(
        keyword in state["question"].lower()
        for keyword in ["current", "latest", "news", "trend", "2024", "recent"]
    )

    logger.info(f"Web search needed: {needs_search}")
    return {**state, "needs_web_search": needs_search}


async def perform_web_search(state: InterviewState) -> InterviewState:
    """Perform web search for current information"""
    if not state["needs_web_search"]:
        return {**state, "web_search_results": ""}

    try:
        logger.info(f"Performing web search for: {state['question']}")

        # In a real implementation, this would call your web search function
        # web_results = await search_web(state["question"])
        # formatted_results = "\n".join([f"- {r.title}: {r.content[:100]}" for r in web_results])

        simulated_results = (
            f"Current information about '{state['question']}' from web search."
        )

        return {**state, "web_search_results": simulated_results}
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return {**state, "web_search_results": "Web search unavailable."}


async def generate_response(state: InterviewState) -> InterviewState:
    """Generate the final response using LangChain"""
    try:
        # Combine all context
        full_context = f"""{state["context"]}

{state["web_search_results"] if state["web_search_results"] else ""}"""

        # Use LangChain assistant to generate response
        # Import the InterviewAssistant using absolute import
        try:
            from interview_assistant import InterviewAssistant

            assistant = InterviewAssistant()
            logger.info("✓ InterviewAssistant imported successfully")
        except ImportError as e:
            try:
                from .interview_assistant import InterviewAssistant

                assistant = InterviewAssistant()
                logger.info("✓ InterviewAssistant imported (relative import)")
            except ImportError:
                logger.error(f"Failed to import InterviewAssistant: {e}")
                return {
                    **state,
                    "final_response": "Error: Failed to initialize LangChain assistant",
                    "error": str(e),
                }
        response = await assistant.generate_response(state["question"], full_context)

        logger.info(f"Generated response: {response[:100]}...")
        return {**state, "final_response": response}
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return {
            **state,
            "final_response": f"Error generating response: {str(e)}",
            "error": str(e),
        }


async def handle_non_question(state: InterviewState) -> InterviewState:
    """Handle non-question inputs"""
    response = (
        f"Acknowledged: '{state['question']}' (not processed as interview question)"
    )
    return {**state, "final_response": response}


# Create the workflow graph
def create_interview_graph():
    """Create the LangGraph workflow for interview processing"""
    logger.info("Creating interview graph")

    # Initialize the graph
    workflow = StateGraph(InterviewState)

    # Add nodes
    workflow.add_node("detect_question", detect_question)
    workflow.add_node("search_documents", search_documents)
    workflow.add_node("check_web_search", check_needs_web_search)
    workflow.add_node("web_search", perform_web_search)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("handle_non_question", handle_non_question)

    # Add edges
    workflow.add_edge("detect_question", "search_documents")
    workflow.add_edge("search_documents", "check_web_search")
    workflow.add_conditional_edges(
        "check_web_search",
        lambda state: "web_search_needed"
        if state["needs_web_search"]
        else "skip_web_search",
        {"web_search_needed": "web_search", "skip_web_search": "generate_response"},
    )
    workflow.add_edge("web_search", "generate_response")

    # Conditional routing from detect_question
    workflow.add_conditional_edges(
        "detect_question",
        lambda state: "is_question" if state["is_question"] else "not_question",
        {"is_question": "search_documents", "not_question": "handle_non_question"},
    )

    # Set entry point
    workflow.set_entry_point("detect_question")

    # Add final edges
    workflow.add_edge("handle_non_question", END)
    workflow.add_edge("generate_response", END)

    # Compile the graph
    logger.info("Compiling interview graph")
    app = workflow.compile()

    return app


# Create the graph instance
interview_graph = create_interview_graph()


# Convenience function to run the workflow
async def process_interview_question(question: str) -> dict:
    """Process an interview question through the LangGraph workflow"""
    try:
        logger.info(f"Starting process_interview_question with question: {question}")
        initial_state: InterviewState = {
            "question": question,
            "context": "",
            "is_question": False,
            "needs_web_search": False,
            "web_search_results": "",
            "document_search_results": "",
            "final_response": "",
            "error": "",
        }

        # Run the workflow
        logger.info("Invoking interview_graph.ainvoke")
        final_state = await interview_graph.ainvoke(initial_state)
        logger.info(
            f"Completed interview_graph.ainvoke with final_state: {final_state}"
        )

        return {
            "status": "processed" if not final_state.get("error") else "error",
            "response": final_state["final_response"],
            "is_question": final_state["is_question"],
        }

    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)
        return {
            "status": "error",
            "response": f"Workflow error: {str(e)}",
            "is_question": False,
            "error": str(e),
        }
