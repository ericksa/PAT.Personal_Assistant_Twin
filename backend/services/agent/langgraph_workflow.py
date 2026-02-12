from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, Sequence, List, Union, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import asyncio
import logging
import traceback

# Configure detailed logging for debugging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set up specific logging for our components
logging.getLogger("langgraph").setLevel(logging.DEBUG)
logging.getLogger("langchain").setLevel(logging.INFO)


# Define the state structure using add_messages for proper message handling
class InterviewState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    context: str
    is_question: bool
    needs_web_search: bool
    web_search_results: str
    document_search_results: str
    final_response: str
    error: str


# Helper function to create full state from partial updates
def create_full_state(
    state: InterviewState, updates: Dict[str, Any], function_name: str = ""
) -> InterviewState:
    """Create a complete state by merging updates with existing state"""
    logger.debug(f"[DEBUG] {function_name} - Creating full state")
    logger.debug(
        f"[DEBUG] {function_name} - Current state keys: {list(state.keys()) if isinstance(state, dict) else 'Not a dict'}"
    )
    logger.debug(f"[DEBUG] {function_name} - Updates: {updates}")

    full_state = {
        "messages": state.get("messages", []),
        "question": state.get("question", ""),
        "context": state.get("context", ""),
        "is_question": state.get("is_question", False),
        "needs_web_search": state.get("needs_web_search", False),
        "web_search_results": state.get("web_search_results", ""),
        "document_search_results": state.get("document_search_results", ""),
        "final_response": state.get("final_response", ""),
        "error": state.get("error", ""),
    }

    # Apply updates
    for key, value in updates.items():
        if key in full_state:
            old_value = full_state[key]
            full_state[key] = value
            logger.debug(
                f"[DEBUG] {function_name} - Updated {key}: {old_value} -> {value}"
            )
        else:
            logger.warning(
                f"[DEBUG] {function_name} - Trying to update unknown key: {key}"
            )

    logger.debug(f"[DEBUG] {function_name} - New state keys: {list(full_state.keys())}")
    return full_state


# Node functions for the graph
async def detect_question_node(state: InterviewState) -> InterviewState:
    """Detect if the input is actually a question"""
    logger.info(f"[DETECT_QUESTION] Called with state keys: {list(state.keys())}")

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
        f"[DETECT_QUESTION] Question detection result: {'Yes' if is_q else 'No'} - '{state['question']}'"
    )

    # Initialize messages if empty
    messages = list(state.get("messages", []))
    if not messages:
        messages = [HumanMessage(content=state["question"])]
        logger.info(
            f"[DETECT_QUESTION] Initialized messages with question: {state['question']}"
        )

    result = create_full_state(
        state,
        {
            "messages": messages,
            "is_question": is_q,
        },
        "detect_question",
    )

    logger.info(f"[DETECT_QUESTION] Returning state with is_question={is_q}")
    return result


async def search_documents_node(state: InterviewState) -> InterviewState:
    """Search local documents for context"""
    logger.info(f"[SEARCH_DOCS] Called - Question: {state['question'][:50]}...")

    try:
        simulated_context = f"Relevant information about '{state['question']}' from Adam's experience and background."
        logger.info(f"[SEARCH_DOCS] Generated context ({len(simulated_context)} chars)")

        result = create_full_state(
            state,
            {
                "context": simulated_context,
                "document_search_results": simulated_context,
            },
            "search_documents",
        )
        return result

    except Exception as e:
        logger.error(f"[SEARCH_DOCS] Error: {e}")
        return create_full_state(
            state,
            {
                "context": "No relevant documents found.",
                "document_search_results": "No relevant documents found.",
                "error": str(e),
            },
            "search_documents",
        )


async def check_web_search_node(state: InterviewState) -> InterviewState:
    """Determine if web search is needed"""
    logger.info(f"[CHECK_WEB] Called - Context length: {len(state['context'])}")

    context_length = len(state["context"])
    question_lower = state["question"].lower()
    keywords = ["current", "latest", "news", "trend", "2024", "recent"]
    has_keywords = any(keyword in question_lower for keyword in keywords)

    needs_search = context_length < 50 or has_keywords
    logger.info(
        f"[CHECK_WEB] Context: {context_length}, Keywords: {has_keywords}, Search needed: {needs_search}"
    )

    return create_full_state(
        state, {"needs_web_search": needs_search}, "check_web_search"
    )


async def web_search_node(state: InterviewState) -> InterviewState:
    """Perform web search for current information"""
    logger.info(f"[WEB_SEARCH] Called - Needs search: {state['needs_web_search']}")

    if not state["needs_web_search"]:
        logger.info(f"[WEB_SEARCH] Skipping web search (not needed)")
        return create_full_state(state, {"web_search_results": ""}, "web_search")

    try:
        logger.info(
            f"[WEB_SEARCH] Performing web search for: {state['question'][:50]}..."
        )
        simulated_results = (
            f"Current information about '{state['question']}' from web search."
        )
        logger.info(f"[WEB_SEARCH] Generated results ({len(simulated_results)} chars)")

        return create_full_state(
            state, {"web_search_results": simulated_results}, "web_search"
        )

    except Exception as e:
        logger.error(f"[WEB_SEARCH] Error: {e}")
        return create_full_state(
            state,
            {
                "web_search_results": "Web search unavailable.",
                "error": str(e),
            },
            "web_search",
        )


async def generate_response_node(state: InterviewState) -> InterviewState:
    """Generate the final response using LangChain"""
    logger.info(f"[GEN_RESPONSE] Called - Question: {state['question'][:50]}...")

    try:
        full_context = f"""{state["context"]}

{state["web_search_results"] if state["web_search_results"] else ""}"""
        logger.info(f"[GEN_RESPONSE] Context length: {len(full_context)} chars")

        # Use LangChain assistant to generate response
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
                return create_full_state(
                    state,
                    {
                        "final_response": "Error: Failed to initialize LangChain assistant",
                        "error": str(e),
                    },
                    "generate_response",
                )

        response = await assistant.generate_response(state["question"], full_context)
        logger.info(f"[GEN_RESPONSE] Generated response ({len(response)} chars)")

        new_messages = [AIMessage(content=response)]

        return create_full_state(
            state,
            {
                "final_response": response,
                "messages": new_messages,
            },
            "generate_response",
        )

    except Exception as e:
        logger.error(f"[GEN_RESPONSE] Error: {e}")
        return create_full_state(
            state,
            {
                "final_response": f"Error generating response: {str(e)}",
                "error": str(e),
            },
            "generate_response",
        )


async def handle_non_question_node(state: InterviewState) -> InterviewState:
    """Handle non-question inputs"""
    logger.info(f"[HANDLE_NON_Q] Called - Question: {state['question'][:50]}...")

    response = (
        f"Acknowledged: '{state['question']}' (not processed as interview question)"
    )
    new_messages = [AIMessage(content=response)]

    logger.info(f"[HANDLE_NON_Q] Response: {response}")

    return create_full_state(
        state,
        {
            "final_response": response,
            "messages": new_messages,
        },
        "handle_non_question",
    )


# Create the workflow graph
def create_interview_graph():
    """Create the LangGraph workflow for interview processing"""
    logger.info("Creating interview graph")

    # Initialize the graph
    workflow = StateGraph(InterviewState)

    # Add nodes
    workflow.add_node("detect_question", detect_question_node)
    workflow.add_node("search_documents", search_documents_node)
    workflow.add_node("check_web_search", check_web_search_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("generate_response", generate_response_node)
    workflow.add_node("handle_non_question", handle_non_question_node)

    # Add edges
    # REMOVED: workflow.add_edge("detect_question", "search_documents")  <-- This was wrong!

    workflow.add_edge("search_documents", "check_web_search")

    # Conditional routing from web search check
    workflow.add_conditional_edges(
        "check_web_search",
        lambda state: "web_search_needed"
        if state["needs_web_search"]
        else "skip_web_search",
        {"web_search_needed": "web_search", "skip_web_search": "generate_response"},
    )

    workflow.add_edge("web_search", "generate_response")

    # Conditional routing from question detection
    workflow.add_conditional_edges(
        "detect_question",
        lambda state: "is_question" if state["is_question"] else "not_question",
        {
            "is_question": "search_documents",  # Only go to search if it's a question
            "not_question": "handle_non_question",  # Go to non-question handler if not a question
        },
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
        logger.info(
            f"[MAIN] Starting process_interview_question with: {question[:100]}..."
        )

        # Initialize state
        initial_state: InterviewState = {
            "messages": [HumanMessage(content=question)],
            "question": question,
            "context": "",
            "is_question": False,
            "needs_web_search": False,
            "web_search_results": "",
            "document_search_results": "",
            "final_response": "",
            "error": "",
        }

        logger.info(
            f"[MAIN] Initializing state with keys: {list(initial_state.keys())}"
        )

        # Run the workflow
        logger.info("[MAIN] Invoking interview_graph.ainvoke")
        final_state = await interview_graph.ainvoke(initial_state)

        logger.info(f"[MAIN] Completed workflow - keys: {list(final_state.keys())}")
        logger.info(
            f"[MAIN] Response preview: {final_state.get('final_response', '')[:100]}..."
        )

        return {
            "status": "processed" if not final_state.get("error") else "error",
            "response": final_state["final_response"],
            "is_question": final_state["is_question"],
            "messages": final_state.get("messages", []),
        }

    except Exception as e:
        logger.error(f"[MAIN] Workflow error: {e}")
        logger.error(f"[MAIN] Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "response": f"Workflow error: {str(e)}",
            "is_question": False,
            "error": str(e),
            "messages": [],
        }
