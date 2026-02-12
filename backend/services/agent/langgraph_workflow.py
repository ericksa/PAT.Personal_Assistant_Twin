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
def create_full_state(state: InterviewState, updates: Dict[str, Any], function_name: str = "") -> InterviewState:
    """Create a complete state by merging updates with existing state"""
    logger.debug(f"[DEBUG] {function_name} - Creating full state")
    logger.debug(f"[DEBUG] {function_name} - Current state keys: {list(state.keys()) if isinstance(state, dict) else 'Not a dict'}")
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
            logger.debug(f"[DEBUG] {function_name} - Updated {key}: {old_value} -> {value}")
        else:
            logger.warning(f"[DEBUG] {function_name} - Trying to update unknown key: {key}")
    
    logger.debug(f"[DEBUG] {function_name} - New state keys: {list(full_state.keys())}")
    return full_state


# Node functions for the graph
async def detect_question(state: InterviewState) -> InterviewState:
    """Detect if the input is actually a question"""
    logger.info(f"[DETECT_QUESTION] Called with state: {state}")
    logger.debug(f"[DETECT_QUESTION] State type: {type(state)}")
    logger.debug(f"[DETECT_QUESTION] State keys: {list(state.keys()) if hasattr(state, 'keys') else 'No keys method'}")
    
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
        logger.info(f"[DETECT_QUESTION] Initialized messages with question: {state['question']}")

    logger.info(f"[DETECT_QUESTION] Returning state with is_question={is_q}")
    logger.debug(f"[DETECT_QUESTION] Messages: {len(messages)} messages")
    
    result = create_full_state(
        state, 
        {
            "messages": messages,
            "is_question": is_q,
        },
        "detect_question"
    )
    
    logger.info(f"[DETECT_QUESTION] Final result: {result}")
    return result


async def search_documents(state: InterviewState) -> InterviewState:
    """Search local documents for context"""
    logger.info(f"[SEARCH_DOCS] Called with state: {state}")
    logger.debug(f"[SEARCH_DOCS] State type: {type(state)}")
    logger.debug(f"[SEARCH_DOCS] State keys: {list(state.keys()) if hasattr(state, 'keys') else 'No keys method'}")
    
    try:
        # This would integrate with your existing document search
        # For now, we'll simulate the search
        logger.info(f"[SEARCH_DOCS] Searching documents for: {state['question']}")

        # In a real implementation, this would call your search function
        # local_results = await search_local_documents(state["question"])
        # context = build_context(local_results, [])

        simulated_context = f"Relevant information about '{state['question']}' from Adam's experience and background."
        logger.info(f"[SEARCH_DOCS] Generated simulated context: {simulated_context}")

        logger.info(f"[SEARCH_DOCS] Returning state with context")
        result = create_full_state(
            state, 
            {
                "context": simulated_context,
                "document_search_results": simulated_context,
            },
            "search_documents"
        )
        
        logger.info(f"[SEARCH_DOCS] Final result keys: {list(result.keys())}")
        return result
        
    except Exception as e:
        logger.error(f"[SEARCH_DOCS] Document search error: {e}")
        logger.error(f"[SEARCH_DOCS] Traceback: {traceback.format_exc()}")
        logger.info(f"[SEARCH_DOCS] Returning error state")
        result = create_full_state(
            state, 
            {
                "context": "No relevant documents found.",
                "document_search_results": "No relevant documents found.",
                "error": str(e),
            },
            "search_documents"
        )
        
        logger.info(f"[SEARCH_DOCS] Error result: {result}")
        return result


async def check_needs_web_search(state: InterviewState) -> InterviewState:
    """Determine if web search is needed"""
    logger.info(f"[CHECK_WEB] Called with state: {state}")
    logger.debug(f"[CHECK_WEB] State type: {type(state)}")
    logger.debug(f"[CHECK_WEB] State keys: {list(state.keys()) if hasattr(state, 'keys') else 'No keys method'}")
    logger.debug(f"[CHECK_WEB] Context length: {len(state.get('context', ''))}")
    logger.debug(f"[CHECK_WEB] Question: {state.get('question', '')}")
    
    # Simple heuristic: if no local context or specific keywords
    context_length = len(state["context"])
    question_lower = state["question"].lower()
    keywords = ["current", "latest", "news", "trend", "2024", "recent"]
    has_keywords = any(keyword in question_lower for keyword in keywords)
    
    needs_search = context_length < 50 or has_keywords

    logger.info(f"[CHECK_WEB] Context length: {context_length}, Has keywords: {has_keywords}, Needs search: {needs_search}")
    
    result = create_full_state(state, {"needs_web_search": needs_search}, "check_needs_web_search")
    
    logger.info(f"[CHECK_WEB] Final result: {result}")
    return result


async def perform_web_search(state: InterviewState) -> InterviewState:
    """Perform web search for current information"""
    logger.info(f"[WEB_SEARCH] Called with state: {state}")
    logger.debug(f"[WEB_SEARCH] State type: {type(state)}")
    logger.debug(f"[WEB_SEARCH] State keys: {list(state.keys()) if hasattr(state, 'keys') else 'No keys method'}")
    logger.debug(f"[WEB_SEARCH] Needs web search: {state.get('needs_web_search', False)}")
    
    if not state["needs_web_search"]:
        logger.info(f"[WEB_SEARCH] Web search not needed, returning empty results")
        result = create_full_state(state, {"web_search_results": ""}, "perform_web_search")
        return result

    try:
        logger.info(f"[WEB_SEARCH] Performing web search for: {state['question']}")

        # In a real implementation, this would call your web search function
        # web_results = await search_web(state["question"])
        # formatted_results = "\n".join([f"- {r.title}: {r.content[:100]}" for r in web_results])

        simulated_results = (
            f"Current information about '{state['question']}' from web search."
        )

        logger.info(f"[WEB_SEARCH] Generated web results: {simulated_results}")
        result = create_full_state(state, {"web_search_results": simulated_results}, "perform_web_search")
        
        logger.info(f"[WEB_SEARCH] Final result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[WEB_SEARCH] Web search error: {e}")
        logger.error(f"[WEB_SEARCH] Traceback: {traceback.format_exc()}")
        result = create_full_state(
            state, 
            {
                "web_search_results": "Web search unavailable.",
                "error": str(e),
            },
            "perform_web_search"
        )
        
        logger.info(f"[WEB_SEARCH] Error result: {result}")
        return result


async def generate_response(state: InterviewState) -> InterviewState:
    """Generate the final response using LangChain"""
    logger.info(f"[GEN_RESPONSE] Called with state: {state}")
    logger.debug(f"[GEN_RESPONSE] State type: {type(state)}")
    logger.debug(f"[GEN_RESPONSE] State keys: {list(state.keys()) if hasattr(state, 'keys') else 'No keys method'}")
    logger.debug(f"[GEN_RESPONSE] Question: {state.get('question', '')}")
    logger.debug(f"[GEN_RESPONSE] Context: {len(state.get('context', ''))} chars")
    logger.debug(f"[GEN_RESPONSE] Web results: {len(state.get('web_search_results', ''))} chars")
    
    try:
        # Combine all context
        full_context = f"""{state["context"]}

{state["web_search_results"] if state["web_search_results"] else ""}"""

        logger.info(f"[GEN_RESPONSE] Full context length: {len(full_context)} chars")

        # Use LangChain assistant to generate response
        # Import the InterviewAssistant using absolute import
        try:
            from interview_assistant import InterviewAssistant

            assistant = InterviewAssistant()
            logger.info("✓ InterviewAssistant imported successfully")
        except ImportError as e:
            logger.warning(f"[GEN_RESPONSE] Importing from interview_assistant failed: {e}")
            try:
                from .interview_assistant import InterviewAssistant

                assistant = InterviewAssistant()
                logger.info("✓ InterviewAssistant imported (relative import)")
            except ImportError:
                logger.error(f"[GEN_RESPONSE] Failed to import InterviewAssistant: {e}")
                result = create_full_state(
                    state, 
                    {
                        "final_response": "Error: Failed to initialize LangChain assistant",
                        "error": str(e),
                    },
                    "generate_response"
                )
                
                logger.info(f"[GEN_RESPONSE] Import error result: {result}")
                return result
        
        logger.info(f"[GEN_RESPONSE] Generating response for question: {state['question'][:50]}...")
        response = await assistant.generate_response(state["question"], full_context)
        logger.info(f"[GEN_RESPONSE] Generated response: {response[:100]}...")

        # Add the AI response to messages
        new_messages = [AIMessage(content=response)]
        logger.info(f"[GEN_RESPONSE] Added {len(new_messages)} messages")

        result = create_full_state(
            state, 
            {
                "final_response": response,
                "messages": new_messages,
            },
            "generate_response"
        )
        
        logger.info(f"[GEN_RESPONSE] Final result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[GEN_RESPONSE] Response generation error: {e}")
        logger.error(f"[GEN_RESPONSE] Traceback: {traceback.format_exc()}")
        result = create_full_state(
            state, 
            {
                "final_response": f"Error generating response: {str(e)}",
                "error": str(e),
            },
            "generate_response"
        )
        
        logger.info(f"[GEN_RESPONSE] Error result: {result}")
        return result


async def handle_non_question(state: InterviewState) -> InterviewState:
    """Handle non-question inputs"""
    logger.info(f"[HANDLE_NON_Q] Called with state: {state}")
    logger.debug(f"[HANDLE_NON_Q] State type: {type(state)}")
    logger.debug(f"[HANDLE_NON_Q] State keys: {list(state.keys()) if hasattr(state, 'keys') else 'No keys method'}")
    
    response = (
        f"Acknowledged: '{state['question']}' (not processed as interview question)"
    )

    # Add the AI response to messages
    new_messages = [AIMessage(content=response)]
    logger.info(f"[HANDLE_NON_Q] Response: {response}")
    logger.info(f"[HANDLE_NON_Q] Messages: {len(new_messages)}")

    result = create_full_state(
        state, 
        {
            "final_response": response,
            "messages": new_messages,
        },
        "handle_non_question"
    )
    
    logger.info(f"[HANDLE_NON_Q] Final result: {result}")
    return result

            logger.info("Using fallback is_question function")

    is_q = is_question(state["question"])
    logger.info(
        f"Question detection: {'Yes' if is_q else 'No'} - '{state['question']}'"
    )

    # Initialize messages if empty
    messages = list(state.get("messages", []))
    if not messages:
        messages = [HumanMessage(content=state["question"])]

    return create_full_state(
        state,
        {
            "messages": messages,
            "is_question": is_q,
        },
    )


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

        return create_full_state(
            state,
            {
                "context": simulated_context,
                "document_search_results": simulated_context,
            },
        )
    except Exception as e:
        logger.error(f"Document search error: {e}")
        return create_full_state(
            state,
            {
                "context": "No relevant documents found.",
                "document_search_results": "No relevant documents found.",
                "error": str(e),
            },
        )


async def check_needs_web_search(state: InterviewState) -> InterviewState:
    """Determine if web search is needed"""
    # Simple heuristic: if no local context or specific keywords
    needs_search = len(state["context"]) < 50 or any(
        keyword in state["question"].lower()
        for keyword in ["current", "latest", "news", "trend", "2024", "recent"]
    )

    logger.info(f"Web search needed: {needs_search}")
    return create_full_state(state, {"needs_web_search": needs_search})


async def perform_web_search(state: InterviewState) -> InterviewState:
    """Perform web search for current information"""
    if not state["needs_web_search"]:
        return create_full_state(state, {"web_search_results": ""})

    try:
        logger.info(f"Performing web search for: {state['question']}")

        # In a real implementation, this would call your web search function
        # web_results = await search_web(state["question"])
        # formatted_results = "\n".join([f"- {r.title}: {r.content[:100]}" for r in web_results])

        simulated_results = (
            f"Current information about '{state['question']}' from web search."
        )

        return create_full_state(state, {"web_search_results": simulated_results})
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return create_full_state(
            state,
            {
                "web_search_results": "Web search unavailable.",
                "error": str(e),
            },
        )


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
                return create_full_state(
                    state,
                    {
                        "final_response": "Error: Failed to initialize LangChain assistant",
                        "error": str(e),
                    },
                )

        response = await assistant.generate_response(state["question"], full_context)
        logger.info(f"Generated response: {response[:100]}...")

        # Add the AI response to messages
        new_messages = [AIMessage(content=response)]

        return create_full_state(
            state,
            {
                "final_response": response,
                "messages": new_messages,
            },
        )
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return create_full_state(
            state,
            {
                "final_response": f"Error generating response: {str(e)}",
                "error": str(e),
            },
        )


async def handle_non_question(state: InterviewState) -> InterviewState:
    """Handle non-question inputs"""
    response = (
        f"Acknowledged: '{state['question']}' (not processed as interview question)"
    )

    # Add the AI response to messages
    new_messages = [AIMessage(content=response)]

    return create_full_state(
        state,
        {
            "final_response": response,
            "messages": new_messages,
        },
    )


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

        # Run the workflow
        logger.info("Invoking interview_graph.ainvoke")
        final_state = await interview_graph.ainvoke(initial_state)
        logger.info(
            f"Completed interview_graph.ainvoke with final_state keys: {final_state.keys()}"
        )

        return {
            "status": "processed" if not final_state.get("error") else "error",
            "response": final_state["final_response"],
            "is_question": final_state["is_question"],
            "messages": final_state.get("messages", []),
        }

    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)
        return {
            "status": "error",
            "response": f"Workflow error: {str(e)}",
            "is_question": False,
            "error": str(e),
            "messages": [],
        }
