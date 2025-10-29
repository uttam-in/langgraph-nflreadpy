"""
LangGraph Workflow for NFL Player Performance Chatbot.

This module defines the LangGraph state machine that orchestrates the
multi-node processing pipeline for handling user queries about NFL statistics.

Requirements addressed:
- 1.3: Process queries and return responses within 10 seconds
- 7.2: Provide clear error messages when errors occur
- 7.5: Continue operating for subsequent queries after encountering errors
"""

import logging
from typing import Any, Dict, Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from models.models import ChatbotState
from nodes.query_parser import parse_query_sync
from nodes.retriever import retrieve_data_sync
from nodes.llm_node import generate_insights_sync
from nodes.memory import update_memory_sync, initialize_memory
from error_handler import (
    handle_error,
    ErrorType,
    ChatbotError,
    create_error_response,
    is_recoverable_error,
    log_error
)

logger = logging.getLogger(__name__)


# Node Functions

def entry_node(state: ChatbotState) -> ChatbotState:
    """
    Entry node that initializes the workflow state.
    
    Validates input and prepares state for processing through the pipeline.
    
    Args:
        state: Initial chatbot state with user_query
        
    Returns:
        Initialized state ready for processing
    """
    logger.info(f"Entry node: Processing query - '{state.get('user_query', '')[:50]}...'")
    
    # Initialize conversation history if not present
    if "conversation_history" not in state or state["conversation_history"] is None:
        state["conversation_history"] = initialize_memory()
    
    # Initialize error field
    if "error" not in state:
        state["error"] = None
    
    # Initialize messages list if not present
    if "messages" not in state:
        state["messages"] = []
    
    # Add user query to messages
    if state.get("user_query"):
        state["messages"].append(HumanMessage(content=state["user_query"]))
    
    # Validate user query
    if not state.get("user_query") or not state["user_query"].strip():
        state["error"] = "empty_query"
        state["generated_response"] = "Please provide a question about NFL player statistics."
        logger.warning("Entry node: Empty query received")
    
    return state


def query_parser_node(state: ChatbotState) -> ChatbotState:
    """
    Query Parser Node wrapper for the workflow.
    
    Converts natural language queries into structured format.
    
    Args:
        state: Current chatbot state
        
    Returns:
        State with parsed_query populated
        
    Requirements:
        - 7.2: Provides clear error messages
        - 7.3: Logs errors with detail
        - 7.5: Continues after errors
    """
    logger.info("Query Parser Node: Parsing user query")
    
    try:
        state = parse_query_sync(state)
        logger.info(f"Query Parser Node: Successfully parsed query - {state.get('parsed_query', {}).get('query_intent', 'unknown')}")
    except ChatbotError as e:
        # Handle known chatbot errors
        error_info = handle_error(
            e,
            context={"node": "query_parser", "query": state.get("user_query", "")[:100]}
        )
        state["error"] = error_info["error_type"]
        state["generated_response"] = error_info["user_message"]
    except Exception as e:
        # Handle unexpected errors
        error_info = handle_error(
            e,
            context={"node": "query_parser", "query": state.get("user_query", "")[:100]},
            default_error_type=ErrorType.QUERY_PARSING_ERROR
        )
        state["error"] = error_info["error_type"]
        state["generated_response"] = error_info["user_message"]
    
    return state


def retriever_node(state: ChatbotState) -> ChatbotState:
    """
    Retriever Node wrapper for the workflow.
    
    Fetches relevant player statistics from data sources.
    
    Args:
        state: Current chatbot state with parsed_query
        
    Returns:
        State with retrieved_data populated
        
    Requirements:
        - 7.1: Implements fallback logic for data source failures
        - 7.2: Provides clear error messages
        - 7.4: Suggests alternatives when no data found
    """
    logger.info("Retriever Node: Fetching player statistics")
    
    try:
        state = retrieve_data_sync(state)
        
        if state.get("retrieved_data") is not None and not state["retrieved_data"].empty:
            logger.info(f"Retriever Node: Retrieved {len(state['retrieved_data'])} records")
        else:
            logger.warning("Retriever Node: No data retrieved")
            # Create helpful error response
            parsed_query = state.get("parsed_query", {})
            context = {
                "players": parsed_query.get("players", []),
                "season": parsed_query.get("time_period", {}).get("season")
            }
            error_response = create_error_response(
                ErrorType.NO_DATA_FOUND,
                details=context
            )
            state["error"] = error_response["error"]
            state["generated_response"] = error_response["generated_response"]
    except ChatbotError as e:
        # Handle known chatbot errors
        error_info = handle_error(
            e,
            context={
                "node": "retriever",
                "parsed_query": state.get("parsed_query", {})
            }
        )
        state["error"] = error_info["error_type"]
        state["generated_response"] = error_info["user_message"]
    except Exception as e:
        # Handle unexpected errors
        error_info = handle_error(
            e,
            context={
                "node": "retriever",
                "parsed_query": state.get("parsed_query", {})
            },
            default_error_type=ErrorType.DATA_RETRIEVAL_FAILED
        )
        state["error"] = error_info["error_type"]
        state["generated_response"] = error_info["user_message"]
    
    return state


def llm_node(state: ChatbotState) -> ChatbotState:
    """
    LLM Node wrapper for the workflow.
    
    Generates natural language insights from retrieved data.
    
    Args:
        state: Current chatbot state with retrieved_data
        
    Returns:
        State with generated_response populated
        
    Requirements:
        - 7.2: Provides clear error messages
        - 7.3: Logs errors with detail
    """
    logger.info("LLM Node: Generating insights")
    
    try:
        state = generate_insights_sync(state)
        
        if state.get("generated_response"):
            logger.info(f"LLM Node: Generated response ({len(state['generated_response'])} chars)")
        else:
            logger.warning("LLM Node: No response generated")
    except ChatbotError as e:
        # Handle known chatbot errors
        from error_handler import handle_llm_error
        error_response = handle_llm_error(e, operation="insight generation")
        state["error"] = error_response["error"]
        state["generated_response"] = error_response["generated_response"]
    except Exception as e:
        # Handle unexpected errors (likely LLM API errors)
        from error_handler import handle_llm_error
        error_response = handle_llm_error(e, operation="insight generation")
        state["error"] = error_response["error"]
        state["generated_response"] = error_response["generated_response"]
    
    return state


def memory_node(state: ChatbotState) -> ChatbotState:
    """
    Memory Node wrapper for the workflow.
    
    Updates conversation history with the latest interaction.
    
    Args:
        state: Current chatbot state with user_query and generated_response
        
    Returns:
        State with updated conversation_history
        
    Requirements:
        - 7.3: Logs errors with detail
        - 7.5: Continues workflow even if memory fails
    """
    logger.info("Memory Node: Updating conversation history")
    
    try:
        state = update_memory_sync(state)
        history_size = len(state.get("conversation_history", []))
        logger.info(f"Memory Node: History updated ({history_size} turns)")
    except Exception as e:
        # Log error but don't fail workflow for memory errors
        log_error(
            e,
            context={"node": "memory", "query": state.get("user_query", "")[:100]},
            level="warning"
        )
        logger.warning("Memory Node: Continuing despite error")
        # Memory errors are non-critical, workflow continues
    
    return state


def exit_node(state: ChatbotState) -> ChatbotState:
    """
    Exit node that finalizes the workflow state.
    
    Performs cleanup and prepares final response for return to Chainlit.
    
    Args:
        state: Final chatbot state
        
    Returns:
        Finalized state ready for response
    """
    logger.info("Exit Node: Finalizing workflow")
    
    # Ensure we have a response
    if not state.get("generated_response"):
        state["generated_response"] = (
            "I'm sorry, I couldn't process your request. "
            "Please try asking your question in a different way."
        )
    
    # Log final state
    if state.get("error"):
        logger.warning(f"Exit Node: Workflow completed with error - {state['error']}")
    else:
        logger.info("Exit Node: Workflow completed successfully")
    
    return state


# Conditional Edge Functions

def should_continue_after_entry(state: ChatbotState) -> Literal["query_parser", "exit"]:
    """
    Determine whether to continue to query parser or exit after entry node.
    
    Args:
        state: Current chatbot state
        
    Returns:
        Next node name: "query_parser" or "exit"
    """
    # Check for errors in entry node
    if state.get("error") == "empty_query":
        logger.info("Routing: Entry -> Exit (empty query)")
        return "exit"
    
    logger.info("Routing: Entry -> Query Parser")
    return "query_parser"


def should_continue_after_parser(state: ChatbotState) -> Literal["retriever", "exit"]:
    """
    Determine whether to continue to retriever or exit after query parser.
    
    Args:
        state: Current chatbot state
        
    Returns:
        Next node name: "retriever" or "exit"
    """
    # Check for parsing errors
    if state.get("error") and "query_parser" in state["error"]:
        logger.info("Routing: Query Parser -> Exit (parsing error)")
        return "exit"
    
    # Check if clarification is needed
    if state.get("error") == "clarification_needed":
        logger.info("Routing: Query Parser -> Exit (clarification needed)")
        return "exit"
    
    # Check if query was parsed successfully
    if not state.get("parsed_query"):
        logger.warning("Routing: Query Parser -> Exit (no parsed query)")
        state["error"] = "parsing_failed"
        state["generated_response"] = "I couldn't understand your question. Please try rephrasing it."
        return "exit"
    
    logger.info("Routing: Query Parser -> Retriever")
    return "retriever"


def should_continue_after_retriever(state: ChatbotState) -> Literal["llm", "exit"]:
    """
    Determine whether to continue to LLM or exit after retriever.
    
    Args:
        state: Current chatbot state
        
    Returns:
        Next node name: "llm" or "exit"
    """
    # Check for retrieval errors
    if state.get("error") and "retriever" in state["error"]:
        logger.info("Routing: Retriever -> Exit (retrieval error)")
        return "exit"
    
    # Check if data was retrieved
    retrieved_data = state.get("retrieved_data")
    if retrieved_data is None or retrieved_data.empty:
        logger.info("Routing: Retriever -> Exit (no data)")
        if not state.get("generated_response"):
            state["generated_response"] = (
                "I couldn't find any statistics matching your query. "
                "Please check the player name and time period."
            )
        return "exit"
    
    logger.info("Routing: Retriever -> LLM")
    return "llm"


def should_continue_after_llm(state: ChatbotState) -> Literal["memory", "exit"]:
    """
    Determine whether to continue to memory or exit after LLM.
    
    Args:
        state: Current chatbot state
        
    Returns:
        Next node name: "memory" or "exit"
    """
    # Check for LLM errors
    if state.get("error") and "llm" in state["error"]:
        logger.warning("Routing: LLM -> Memory (with error, but continuing)")
        # Continue to memory even with errors to maintain conversation history
        return "memory"
    
    # Check if response was generated
    if not state.get("generated_response"):
        logger.warning("Routing: LLM -> Exit (no response generated)")
        state["generated_response"] = "I couldn't generate a response. Please try again."
        return "exit"
    
    logger.info("Routing: LLM -> Memory")
    return "memory"


# Workflow Builder

def create_workflow() -> StateGraph:
    """
    Create and configure the LangGraph workflow.
    
    Builds the state machine with all nodes and edges for processing
    NFL player statistics queries.
    
    Returns:
        Configured StateGraph ready for compilation
        
    Requirements:
        - 1.3: Orchestrates query processing pipeline
        - 7.2: Implements error handling with clear messages
        - 7.5: Allows continuation after errors
    """
    logger.info("Creating LangGraph workflow")
    
    # Initialize the state graph
    workflow = StateGraph(ChatbotState)
    
    # Add nodes to the workflow
    workflow.add_node("entry", entry_node)
    workflow.add_node("query_parser", query_parser_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("llm", llm_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("exit", exit_node)
    
    # Set entry point
    workflow.set_entry_point("entry")
    
    # Add conditional edges for error handling
    workflow.add_conditional_edges(
        "entry",
        should_continue_after_entry,
        {
            "query_parser": "query_parser",
            "exit": "exit"
        }
    )
    
    workflow.add_conditional_edges(
        "query_parser",
        should_continue_after_parser,
        {
            "retriever": "retriever",
            "exit": "exit"
        }
    )
    
    workflow.add_conditional_edges(
        "retriever",
        should_continue_after_retriever,
        {
            "llm": "llm",
            "exit": "exit"
        }
    )
    
    workflow.add_conditional_edges(
        "llm",
        should_continue_after_llm,
        {
            "memory": "memory",
            "exit": "exit"
        }
    )
    
    # Memory always goes to exit
    workflow.add_edge("memory", "exit")
    
    # Exit is the end
    workflow.add_edge("exit", END)
    
    logger.info("LangGraph workflow created successfully")
    
    return workflow


def compile_workflow() -> Any:
    """
    Compile the workflow into an executable graph.
    
    Returns:
        Compiled workflow ready for execution
    """
    workflow = create_workflow()
    compiled = workflow.compile()
    
    logger.info("LangGraph workflow compiled successfully")
    
    return compiled


# Convenience function for running the workflow

def run_workflow(user_query: str, session_state: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run the workflow with a user query.
    
    Convenience function for executing the workflow with a single query.
    Useful for testing and simple integrations.
    
    Args:
        user_query: The user's natural language query
        session_state: Optional existing session state with conversation history
        
    Returns:
        Final state dictionary with generated_response
        
    Requirements:
        - 7.2: Provides clear error messages
        - 7.5: Continues operating after errors
        
    Example:
        >>> result = run_workflow("How did Patrick Mahomes perform in 2023?")
        >>> print(result["generated_response"])
    """
    # Compile workflow
    app = compile_workflow()
    
    # Initialize state
    initial_state: ChatbotState = {
        "messages": [],
        "user_query": user_query,
        "parsed_query": {},
        "retrieved_data": None,
        "generated_response": "",
        "conversation_history": session_state.get("conversation_history", []) if session_state else [],
        "error": None,
        "session_id": session_state.get("session_id") if session_state else None
    }
    
    # Run workflow
    logger.info(f"Running workflow for query: '{user_query[:50]}...'")
    
    try:
        final_state = app.invoke(initial_state)
        logger.info("Workflow execution completed")
        return final_state
    except Exception as e:
        # Handle workflow-level errors
        error_info = handle_error(
            e,
            context={"query": user_query[:100]},
            default_error_type=ErrorType.WORKFLOW_ERROR
        )
        
        return {
            **initial_state,
            "error": error_info["error_type"],
            "generated_response": error_info["user_message"]
        }


# Logging configuration

def configure_logging(level: str = "INFO"):
    """
    Configure logging for the workflow.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Requirements:
        - 7.3: Configures logging with appropriate detail
    """
    from logging_config import setup_logging
    
    setup_logging(
        log_level=level,
        console_output=True,
        detailed_format=False
    )
    
    logger.info(f"Logging configured at {level} level")


if __name__ == "__main__":
    # Configure logging
    configure_logging("INFO")
    
    # Test the workflow
    test_query = "How did Patrick Mahomes perform in the 2023 season?"
    
    logger.info("=" * 80)
    logger.info("Testing NFL Player Performance Chatbot Workflow")
    logger.info("=" * 80)
    
    result = run_workflow(test_query)
    
    logger.info("=" * 80)
    logger.info("WORKFLOW RESULT")
    logger.info("=" * 80)
    logger.info(f"Query: {test_query}")
    logger.info(f"Error: {result.get('error', 'None')}")
    logger.info(f"Response: {result.get('generated_response', 'No response')[:200]}...")
    logger.info("=" * 80)
