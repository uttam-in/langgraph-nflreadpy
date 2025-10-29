"""
Error Handler Module for NFL Player Performance Chatbot.

This module provides centralized error handling functions, user-friendly error messages,
and error recovery logic for the chatbot system.

Requirements addressed:
- 7.1: Implement fallback logic when data sources fail
- 7.2: Provide clear error messages when errors occur
- 7.3: Log errors with sufficient detail for debugging
- 7.4: Suggest alternative queries when no results found
- 7.5: Continue operating for subsequent queries after errors
"""

import logging
import traceback
from typing import Any, Dict, Optional, Callable
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Enumeration of error types in the chatbot system."""
    
    # Query parsing errors
    EMPTY_QUERY = "empty_query"
    QUERY_PARSING_ERROR = "query_parsing_error"
    CLARIFICATION_NEEDED = "clarification_needed"
    AMBIGUOUS_QUERY = "ambiguous_query"
    
    # Data retrieval errors
    DATA_SOURCE_UNAVAILABLE = "data_source_unavailable"
    DATA_RETRIEVAL_FAILED = "data_retrieval_failed"
    NO_DATA_FOUND = "no_data_found"
    PLAYER_NOT_FOUND = "player_not_found"
    INVALID_TIME_PERIOD = "invalid_time_period"
    
    # LLM errors
    LLM_API_ERROR = "llm_api_error"
    LLM_TIMEOUT = "llm_timeout"
    LLM_RATE_LIMIT = "llm_rate_limit"
    INSIGHT_GENERATION_ERROR = "insight_generation_error"
    
    # Memory errors
    MEMORY_ERROR = "memory_error"
    
    # Workflow errors
    WORKFLOW_ERROR = "workflow_error"
    NODE_ERROR = "node_error"
    
    # General errors
    UNKNOWN_ERROR = "unknown_error"
    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"


class ChatbotError(Exception):
    """Base exception class for chatbot errors."""
    
    def __init__(
        self,
        error_type: ErrorType,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        """
        Initialize a chatbot error.
        
        Args:
            error_type: Type of error from ErrorType enum
            message: Human-readable error message
            details: Additional error details for logging
            recoverable: Whether the error is recoverable
        """
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable
        }


# User-friendly error messages for different error types
ERROR_MESSAGES = {
    ErrorType.EMPTY_QUERY: {
        "message": "Please provide a question about NFL player statistics.",
        "suggestions": [
            "Try asking: 'How did Patrick Mahomes perform in 2023?'",
            "Or: 'Compare Josh Allen and Joe Burrow passing yards'"
        ]
    },
    
    ErrorType.QUERY_PARSING_ERROR: {
        "message": "I had trouble understanding your question. Could you rephrase it?",
        "suggestions": [
            "Try being more specific about the player name",
            "Include the time period (e.g., '2023 season', 'week 5')",
            "Specify which statistics you're interested in"
        ]
    },
    
    ErrorType.CLARIFICATION_NEEDED: {
        "message": "I need more information to answer your question accurately.",
        "suggestions": [
            "Please specify which player you're asking about",
            "Clarify the time period you're interested in",
            "Let me know which statistics you want to see"
        ]
    },
    
    ErrorType.AMBIGUOUS_QUERY: {
        "message": "Your question could be interpreted in multiple ways.",
        "suggestions": [
            "Try being more specific about what you're asking",
            "Mention the player's full name if there are multiple players with similar names",
            "Specify whether you want season totals or per-game averages"
        ]
    },
    
    ErrorType.DATA_SOURCE_UNAVAILABLE: {
        "message": "I'm having trouble accessing the statistics database right now.",
        "suggestions": [
            "Please try again in a moment",
            "Try asking about a different time period",
            "Historical data (1999-2023) may still be available"
        ]
    },
    
    ErrorType.DATA_RETRIEVAL_FAILED: {
        "message": "I couldn't retrieve the requested statistics.",
        "suggestions": [
            "Please check the player name spelling",
            "Verify the time period is valid (e.g., 1999-2024)",
            "Try asking about a different player or statistic"
        ]
    },
    
    ErrorType.NO_DATA_FOUND: {
        "message": "I couldn't find any statistics matching your query.",
        "suggestions": [
            "Double-check the player name spelling",
            "Verify the player was active during the specified time period",
            "Try a different season or broader time range",
            "Make sure the statistic is relevant for the player's position"
        ]
    },
    
    ErrorType.PLAYER_NOT_FOUND: {
        "message": "I couldn't find a player with that name.",
        "suggestions": [
            "Check the spelling of the player's name",
            "Try using the player's full name",
            "Verify the player has played in the NFL",
            "Try searching for a different player"
        ]
    },
    
    ErrorType.INVALID_TIME_PERIOD: {
        "message": "The time period you specified doesn't seem valid.",
        "suggestions": [
            "NFL seasons range from 1999 to 2024 in our database",
            "Weeks should be between 1 and 18",
            "Try specifying a valid season year"
        ]
    },
    
    ErrorType.LLM_API_ERROR: {
        "message": "I encountered an error while analyzing the statistics.",
        "suggestions": [
            "Please try your question again",
            "The issue may be temporary",
            "Try simplifying your question"
        ]
    },
    
    ErrorType.LLM_TIMEOUT: {
        "message": "The analysis is taking longer than expected.",
        "suggestions": [
            "Please try again with a simpler question",
            "Try asking about fewer players or statistics",
            "The service may be experiencing high load"
        ]
    },
    
    ErrorType.LLM_RATE_LIMIT: {
        "message": "I'm receiving too many requests right now.",
        "suggestions": [
            "Please wait a moment and try again",
            "Try asking one question at a time"
        ]
    },
    
    ErrorType.INSIGHT_GENERATION_ERROR: {
        "message": "I had trouble generating insights from the statistics.",
        "suggestions": [
            "The data was retrieved successfully, but analysis failed",
            "Please try asking your question in a different way",
            "Try asking about specific statistics rather than general performance"
        ]
    },
    
    ErrorType.MEMORY_ERROR: {
        "message": "I had trouble accessing our conversation history.",
        "suggestions": [
            "Your current question will still be processed",
            "Context from previous questions may not be available",
            "Try being explicit rather than using references like 'he' or 'that player'"
        ]
    },
    
    ErrorType.WORKFLOW_ERROR: {
        "message": "I encountered an unexpected error while processing your request.",
        "suggestions": [
            "Please try your question again",
            "Try rephrasing your question",
            "If the problem persists, try a different query"
        ]
    },
    
    ErrorType.NODE_ERROR: {
        "message": "An error occurred in one of the processing steps.",
        "suggestions": [
            "Please try again",
            "Try simplifying your question",
            "The issue may be temporary"
        ]
    },
    
    ErrorType.UNKNOWN_ERROR: {
        "message": "I encountered an unexpected error.",
        "suggestions": [
            "Please try your question again",
            "Try rephrasing your question",
            "If the problem persists, please contact support"
        ]
    },
    
    ErrorType.VALIDATION_ERROR: {
        "message": "The input provided doesn't meet the required format.",
        "suggestions": [
            "Please check your input and try again",
            "Make sure you're asking about NFL players and statistics"
        ]
    },
    
    ErrorType.CONFIGURATION_ERROR: {
        "message": "The chatbot is not properly configured.",
        "suggestions": [
            "Please contact the administrator",
            "Check that all required environment variables are set"
        ]
    }
}


def get_user_friendly_message(
    error_type: ErrorType,
    custom_message: Optional[str] = None,
    include_suggestions: bool = True
) -> str:
    """
    Get a user-friendly error message for a given error type.
    
    Args:
        error_type: Type of error from ErrorType enum
        custom_message: Optional custom message to use instead of default
        include_suggestions: Whether to include suggestions in the message
        
    Returns:
        Formatted user-friendly error message
        
    Requirements:
        - 7.2: Provides clear error messages to users
        - 7.4: Suggests alternative queries when appropriate
    """
    error_info = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES[ErrorType.UNKNOWN_ERROR])
    
    # Use custom message if provided, otherwise use default
    message = custom_message if custom_message else error_info["message"]
    
    # Add suggestions if requested
    if include_suggestions and "suggestions" in error_info:
        suggestions = error_info["suggestions"]
        if suggestions:
            message += "\n\n**Suggestions:**\n"
            for suggestion in suggestions:
                message += f"- {suggestion}\n"
    
    return message


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
) -> None:
    """
    Log an error with detailed context for debugging.
    
    Args:
        error: The exception that occurred
        context: Additional context information
        level: Logging level ('error', 'warning', 'critical')
        
    Requirements:
        - 7.3: Logs errors with sufficient detail for debugging
    """
    log_func = getattr(logger, level, logger.error)
    
    # Build log message
    error_msg = f"Error occurred: {type(error).__name__}: {str(error)}"
    
    # Add context if provided
    if context:
        error_msg += f"\nContext: {context}"
    
    # Add traceback for debugging
    if level in ["error", "critical"]:
        error_msg += f"\nTraceback:\n{traceback.format_exc()}"
    
    # Log the error
    log_func(error_msg)
    
    # If it's a ChatbotError, log additional details
    if isinstance(error, ChatbotError):
        log_func(f"Error details: {error.to_dict()}")


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    default_error_type: ErrorType = ErrorType.UNKNOWN_ERROR
) -> Dict[str, Any]:
    """
    Handle an error and return appropriate response information.
    
    This is the main error handling function that processes exceptions,
    logs them, and returns user-friendly messages.
    
    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred
        default_error_type: Default error type if not a ChatbotError
        
    Returns:
        Dictionary with error information and user message
        
    Requirements:
        - 7.2: Provides clear error messages
        - 7.3: Logs errors with detail
        - 7.5: Allows continuation after errors
    """
    # Determine error type
    if isinstance(error, ChatbotError):
        error_type = error.error_type
        error_message = error.message
        recoverable = error.recoverable
    else:
        error_type = default_error_type
        error_message = str(error)
        recoverable = True
    
    # Log the error
    log_error(error, context=context, level="error" if recoverable else "critical")
    
    # Get user-friendly message
    user_message = get_user_friendly_message(error_type, include_suggestions=True)
    
    # Return error information
    return {
        "error_type": error_type.value,
        "error_message": error_message,
        "user_message": user_message,
        "recoverable": recoverable,
        "context": context
    }


def error_handler_decorator(
    error_type: ErrorType = ErrorType.NODE_ERROR,
    log_level: str = "error"
):
    """
    Decorator for adding error handling to functions.
    
    Args:
        error_type: Default error type for this function
        log_level: Logging level for errors
        
    Returns:
        Decorated function with error handling
        
    Example:
        @error_handler_decorator(ErrorType.QUERY_PARSING_ERROR)
        def parse_query(state):
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ChatbotError as e:
                # Re-raise ChatbotError as-is
                raise
            except Exception as e:
                # Wrap other exceptions in ChatbotError
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200],  # Truncate for logging
                    "kwargs": str(kwargs)[:200]
                }
                log_error(e, context=context, level=log_level)
                raise ChatbotError(
                    error_type=error_type,
                    message=f"Error in {func.__name__}: {str(e)}",
                    details=context,
                    recoverable=True
                )
        return wrapper
    return decorator


def create_error_response(
    error_type: ErrorType,
    custom_message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.
    
    Args:
        error_type: Type of error
        custom_message: Optional custom error message
        details: Optional additional details
        
    Returns:
        Standardized error response dictionary
    """
    user_message = get_user_friendly_message(error_type, custom_message)
    
    return {
        "error": error_type.value,
        "generated_response": user_message,
        "error_details": details or {}
    }


def is_recoverable_error(error: Exception) -> bool:
    """
    Determine if an error is recoverable.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is recoverable, False otherwise
        
    Requirements:
        - 7.5: Determines if workflow can continue after error
    """
    if isinstance(error, ChatbotError):
        return error.recoverable
    
    # Most errors are recoverable by default
    # Only critical system errors are not recoverable
    non_recoverable_types = (
        MemoryError,
        SystemError,
        KeyboardInterrupt,
    )
    
    return not isinstance(error, non_recoverable_types)


def suggest_alternatives(
    error_type: ErrorType,
    context: Optional[Dict[str, Any]] = None
) -> list[str]:
    """
    Generate alternative query suggestions based on error type and context.
    
    Args:
        error_type: Type of error that occurred
        context: Context information (e.g., player name, time period)
        
    Returns:
        List of alternative query suggestions
        
    Requirements:
        - 7.4: Suggests alternative queries when no results found
    """
    suggestions = []
    
    # Get base suggestions from error messages
    error_info = ERROR_MESSAGES.get(error_type, {})
    if "suggestions" in error_info:
        suggestions.extend(error_info["suggestions"])
    
    # Add context-specific suggestions
    if context:
        if "player_name" in context:
            player = context["player_name"]
            suggestions.append(f"Try searching for '{player}' with a different time period")
            suggestions.append(f"Check if '{player}' is spelled correctly")
        
        if "season" in context:
            season = context["season"]
            suggestions.append(f"Try a different season (current: {season})")
            suggestions.append("Try asking about career statistics instead")
        
        if "statistics" in context:
            stats = context["statistics"]
            suggestions.append(f"Try different statistics than {', '.join(stats)}")
    
    return suggestions[:5]  # Limit to 5 suggestions


def format_error_for_logging(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format error information for structured logging.
    
    Args:
        error: The exception that occurred
        context: Additional context information
        
    Returns:
        Dictionary with formatted error information
        
    Requirements:
        - 7.3: Provides structured error information for logging
    """
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "timestamp": None  # Will be added by logging system
    }
    
    if isinstance(error, ChatbotError):
        error_info.update(error.to_dict())
    
    if context:
        error_info["context"] = context
    
    return error_info


# Specific error handling functions for common scenarios

def handle_data_source_error(
    error: Exception,
    source_name: str,
    player_name: Optional[str] = None,
    season: Optional[int] = None
) -> Dict[str, Any]:
    """
    Handle errors from data sources with appropriate fallback logic.
    
    Args:
        error: The exception from the data source
        source_name: Name of the data source that failed
        player_name: Player being queried
        season: Season being queried
        
    Returns:
        Error response with fallback suggestions
        
    Requirements:
        - 7.1: Implements fallback logic for data source failures
    """
    context = {
        "source": source_name,
        "player_name": player_name,
        "season": season
    }
    
    log_error(error, context=context, level="warning")
    
    # Determine if this is a temporary or permanent failure
    if "timeout" in str(error).lower() or "connection" in str(error).lower():
        error_type = ErrorType.DATA_SOURCE_UNAVAILABLE
    elif "not found" in str(error).lower():
        error_type = ErrorType.PLAYER_NOT_FOUND
    else:
        error_type = ErrorType.DATA_RETRIEVAL_FAILED
    
    return create_error_response(
        error_type=error_type,
        details=context
    )


def handle_llm_error(
    error: Exception,
    operation: str = "analysis"
) -> Dict[str, Any]:
    """
    Handle errors from LLM API calls.
    
    Args:
        error: The exception from the LLM
        operation: Description of the operation being performed
        
    Returns:
        Error response with appropriate message
    """
    context = {"operation": operation}
    
    # Determine specific LLM error type
    error_str = str(error).lower()
    if "rate" in error_str and "limit" in error_str:
        error_type = ErrorType.LLM_RATE_LIMIT
    elif "timeout" in error_str:
        error_type = ErrorType.LLM_TIMEOUT
    else:
        error_type = ErrorType.LLM_API_ERROR
    
    log_error(error, context=context, level="warning")
    
    return create_error_response(
        error_type=error_type,
        details=context
    )


def handle_validation_error(
    field: str,
    value: Any,
    expected: str
) -> Dict[str, Any]:
    """
    Handle validation errors for input data.
    
    Args:
        field: Name of the field that failed validation
        value: The invalid value
        expected: Description of expected value
        
    Returns:
        Error response with validation details
    """
    context = {
        "field": field,
        "value": str(value),
        "expected": expected
    }
    
    logger.warning(f"Validation error: {field} = {value}, expected {expected}")
    
    return create_error_response(
        error_type=ErrorType.VALIDATION_ERROR,
        custom_message=f"Invalid {field}: expected {expected}, got {value}",
        details=context
    )


# Error recovery functions

def attempt_recovery(
    error: Exception,
    recovery_func: Callable,
    max_attempts: int = 3,
    **kwargs
) -> Any:
    """
    Attempt to recover from an error by retrying with a recovery function.
    
    Args:
        error: The original error
        recovery_func: Function to call for recovery
        max_attempts: Maximum number of recovery attempts
        **kwargs: Arguments to pass to recovery function
        
    Returns:
        Result from recovery function if successful
        
    Raises:
        Original error if recovery fails
        
    Requirements:
        - 7.1: Implements error recovery logic
        - 7.5: Allows continuation after errors
    """
    logger.info(f"Attempting error recovery with {recovery_func.__name__}")
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"Recovery attempt {attempt + 1}/{max_attempts}")
            result = recovery_func(**kwargs)
            logger.info("Recovery successful")
            return result
        except Exception as e:
            logger.warning(f"Recovery attempt {attempt + 1} failed: {e}")
            if attempt == max_attempts - 1:
                logger.error("All recovery attempts failed")
                raise error
    
    raise error
