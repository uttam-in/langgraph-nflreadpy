"""
NFL Player Performance Chatbot - Main Chainlit Application

This is the entry point for the Chainlit-based chat interface that allows users
to query NFL player statistics through natural language conversations.

Requirements addressed:
- 8.1: Provide web-based chat UI accessible through browser
- 8.2: Display messages in chat history immediately
- 8.3: Stream responses from LangGraph Workflow in real-time
- 8.4: Maintain chat history visibility throughout session
- 8.5: Provide visual indicators when processing queries
- 1.1: Accept natural language questions about player statistics
"""

import chainlit as cl
from dotenv import load_dotenv
import os
import logging
from typing import Dict, Any
import uuid

from workflow import compile_workflow, configure_logging
from models.models import ChatbotState
from nodes.memory import initialize_memory
from error_handler import handle_error, ErrorType, log_error
from logging_config import create_context_logger
from cache_utils import configure_cache, warm_kaggle_cache, print_cache_statistics

# Highlight live data support and give users ideas for queries
SAMPLE_QUERIES = [
    "What were Patrick Mahomes' passing yards in week 10 of 2024?",
    "Show me Travis Kelce's receiving stats for the 2024 season",
    "Compare Patrick Mahomes and Josh Allen passing yards in 2024",
    "How many touchdowns did Christian McCaffrey score this season?",
    "What are Tyreek Hill's receiving yards in 2024?",
    "How did Lamar Jackson perform in week 15?"
]

# Load environment variables
load_dotenv()

# Configure logging
configure_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Configure and warm cache on startup
logger.info("Initializing cache system...")
configure_cache(
    kaggle_cache_enabled=os.getenv("KAGGLE_CACHE_ENABLED", "true").lower() == "true",
    nflreadpy_ttl_hours=int(os.getenv("NFLREADPY_CACHE_TTL_HOURS", "24")),
    query_cache_capacity=int(os.getenv("QUERY_CACHE_CAPACITY", "100")),
    query_cache_ttl_hours=int(os.getenv("QUERY_CACHE_TTL_HOURS", "1"))
)

# Warm Kaggle cache on startup if enabled
if os.getenv("WARM_KAGGLE_CACHE_ON_STARTUP", "true").lower() == "true":
    logger.info("Warming Kaggle cache on startup...")
    kaggle_path = os.getenv("KAGGLE_DATA_PATH")
    if warm_kaggle_cache(kaggle_path):
        logger.info("Kaggle cache warmed successfully")
    else:
        logger.warning("Failed to warm Kaggle cache - will load on first use")


@cl.on_chat_start
async def start():
    """
    Initialize chat session when a user connects.
    
    This function sets up the LangGraph workflow and initializes
    the conversation context for the session.
    
    Requirements:
        - 8.1: Provides web-based chat UI
        - 8.4: Initializes chat history for the session
        - 3.5: Initializes empty conversation context
    """
    logger.info("New chat session started")
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    cl.user_session.set("session_id", session_id)
    
    # Send welcome message
    sample_queries_text = "\n".join(f"- '{query}'" for query in SAMPLE_QUERIES)
    welcome_msg = await cl.Message(
        content="Welcome to the NFL Player Performance Chatbot! 🏈\n\n"
                "Powered by live data from nflreadpy so you can ask about the latest games and stats.\n\n"
                "**✨ New: Conversation Memory!**\n"
                "I now remember our conversation and can handle follow-up questions:\n"
                "- Use pronouns like 'he', 'his', 'them'\n"
                "- Ask 'What about week 10?' without repeating the player name\n"
                "- Say 'Compare them' to compare previously mentioned players\n\n"
                "**Try asking questions like:**\n"
                f"{sample_queries_text}\n\n"
                "What would you like to know?"
    ).send()
    
    try:
        # Initialize LangGraph workflow
        logger.info("Compiling LangGraph workflow")
        workflow = compile_workflow()
        cl.user_session.set("workflow", workflow)
        logger.info("LangGraph workflow compiled and stored in session")
        
        # Initialize conversation history
        conversation_history = initialize_memory()
        cl.user_session.set("conversation_history", conversation_history)
        logger.info("Conversation history initialized")
        
    except Exception as e:
        log_error(e, context={"session_id": session_id}, level="error")
        await cl.Message(
            content="⚠️ There was an error initializing the chatbot. "
                    "Some features may not work correctly. Please try refreshing the page."
        ).send()


@cl.on_message
async def main(message: cl.Message):
    """
    Process incoming user messages through the LangGraph workflow.
    
    This function handles user input, processes it through the workflow,
    and streams the response back to the user with visual indicators.
    
    Args:
        message: The user's message from Chainlit
        
    Requirements:
        - 8.2: Display user message in chat history immediately
        - 8.3: Stream responses from workflow in real-time
        - 8.5: Provide visual indicators during processing
        - 1.1: Accept and process natural language questions
        - 1.3: Return responses within 10 seconds
    """
    # Get user query
    user_query = message.content
    logger.info(f"Processing user query: '{user_query[:50]}...'")
    
    # Get workflow and conversation history from session
    workflow = cl.user_session.get("workflow")
    conversation_history = cl.user_session.get("conversation_history", [])
    session_id = cl.user_session.get("session_id")
    
    # Check if workflow is initialized
    if workflow is None:
        logger.error("Workflow not initialized in session")
        await cl.Message(
            content="⚠️ The chatbot is not properly initialized. Please refresh the page and try again."
        ).send()
        return
    
    # Create a message for processing indicator
    processing_msg = cl.Message(content="")
    await processing_msg.send()
    
    try:
        # Show processing indicator
        processing_msg.content = "🔄 Processing your query..."
        await processing_msg.update()
        
        # Initialize state for workflow
        initial_state: ChatbotState = {
            "messages": [],
            "user_query": user_query,
            "parsed_query": {},
            "retrieved_data": None,
            "generated_response": "",
            "conversation_history": conversation_history,
            "error": None,
            "session_id": session_id
        }
        
        logger.info("Invoking LangGraph workflow")
        
        # Update processing indicator
        if conversation_history:
            processing_msg.content = "🔍 Analyzing your question (using conversation context)..."
        else:
            processing_msg.content = "🔍 Analyzing your question..."
        await processing_msg.update()
        
        # Execute workflow
        final_state = workflow.invoke(initial_state)
        
        logger.info("Workflow execution completed")
        
        # Remove processing indicator
        await processing_msg.remove()
        
        # Get the generated response
        response = final_state.get("generated_response", "")
        error = final_state.get("error")
        
        # Handle errors
        if error:
            logger.warning(f"Workflow completed with error: {error}")
            if not response:
                response = (
                    "I encountered an issue while processing your request. "
                    "Please try rephrasing your question or ask something else."
                )
        
        # Check if we have a response
        if not response:
            logger.error("No response generated by workflow")
            response = (
                "I'm sorry, I couldn't generate a response to your query. "
                "Please try asking your question in a different way."
            )
        
        # Stream the response to the user
        # For now, we'll send it all at once, but this could be enhanced
        # to stream token-by-token if the LLM node supports streaming
        response_msg = cl.Message(content="")
        await response_msg.send()
        
        # Simulate streaming by updating the message
        # In a real streaming implementation, you'd update incrementally
        response_msg.content = response
        await response_msg.update()
        
        logger.info(f"Response sent to user ({len(response)} chars)")
        
        # Update conversation history in session
        updated_history = final_state.get("conversation_history", conversation_history)
        cl.user_session.set("conversation_history", updated_history)
        
        logger.info(f"Conversation history updated ({len(updated_history)} turns)")
        
    except Exception as e:
        # Handle unexpected errors
        error_info = handle_error(
            e,
            context={
                "session_id": session_id,
                "query": user_query[:100]
            },
            default_error_type=ErrorType.WORKFLOW_ERROR
        )
        
        # Remove processing indicator
        try:
            await processing_msg.remove()
        except:
            pass
        
        # Send user-friendly error message
        await cl.Message(content=error_info["user_message"]).send()


@cl.on_chat_end
async def end():
    """
    Handle chat session cleanup when user disconnects.
    
    This function performs any necessary cleanup when a chat session ends.
    """
    session_id = cl.user_session.get("session_id")
    logger.info(f"Chat session ended: {session_id}")


@cl.on_settings_update
async def settings_update(settings: Dict[str, Any]):
    """
    Handle settings updates from the user.
    
    This function can be used to allow users to configure chatbot behavior.
    
    Args:
        settings: Dictionary of updated settings
    """
    logger.info(f"Settings updated: {settings}")
    
    # You could implement settings like:
    # - Preferred data source
    # - Response verbosity
    # - Time period defaults
    # etc.


if __name__ == "__main__":
    # Verify environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set in environment variables")
        print("\n" + "="*80)
        print("⚠️  WARNING: OPENAI_API_KEY not found!")
        print("="*80)
        print("Please set up your environment variables:")
        print("1. Copy .env.example to .env")
        print("2. Add your OpenAI API key to the .env file")
        print("3. Restart the application")
        print("="*80 + "\n")
    else:
        logger.info("Environment variables loaded successfully")
        print("\n" + "="*80)
        print("🏈 NFL Player Performance Chatbot")
        print("="*80)
        print("Starting Chainlit application...")
        print("The chatbot will be available at: http://localhost:8000")
        print("="*80 + "\n")
